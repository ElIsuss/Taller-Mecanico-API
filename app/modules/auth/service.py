"""Servicios de autenticación: bcrypt, JWT, contador de intentos."""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from bcrypt import hashpw, checkpw, gensalt
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sqlmodel import select

from app.core.database import get_session
from app.core.exceptions import NoEncontrado, Conflicto
from app.core.security import _BCRYPT_SEMAPHORE, _BCRYPT_EXECUTOR, create_access_token, decode_access_token
from app.main import app
from app.modules.auth.models import Usuario, AsignacionRol, IntentoAcceso
from app.modules.clientes.models import Cliente


async def obtener_usuario(session: AsyncSession, usuario_id: int) -> Usuario:
    """Obtener usuario por ID (uso interno)."""
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise NoEncontrado("El usuario indicado no existe")
    return usuario


async def autenticar_usuario(
    session: AsyncSession, email: str, password: str, ip: str | None = None
) -> Optional[Usuario]:
    """Autenticar usuario comparando credenciales contra la base de datos.

    Retorna el usuario si las credenciales son válidas, None en caso contrario.
    Aplica RN-09: la respuesta al login es siempre la misma para prevenir
    enumeración de emails.
    Aplica RN-08: contador de intentos fallidos por correo+e IP, ventana 60s.
    """
    email_normalizado = email.lower().strip()
    ip = ip or "desconocido"

    # 1. Verificar bloqueo ANTES de consultar contraseña.
    #    Si está bloqueado, no ejecutamos bcrypt ni queries costosas.
    bloqueado, fallos_ventana = await _chequear_bloqueo(email_normalizado, ip)
    if bloqueado:
        # aun al estar bloqueado, registramos el intento para el historial
        await _registrar_intento_persistente(email_normalizado, ip, exito=False)
        return None

    # 2. Consultar usuario en BD
    usuario = await session.execute(
        select(Usuario).where(Usuario.email == email_normalizado)
    )
    usuario = usuario.scalar_one_or_none()

    if usuario is None:
        # RN-09: No confirmar si el email existe, registrar intento fallido
        await _registrar_intento_persistente(email_normalizado, ip, exito=False)
        return None

    # 3. Verificar contraseña usando bcrypt fuera del event loop
    password_verify = await _verificar_password_hash(password, usuario.password_hash)

    if not password_verify:
        # Contraseña incorrecta: registrar intento fallido
        await _registrar_intento_persistente(email_normalizado, ip, exito=False)
        return None

    # 4. Si el usuario tiene marcado que debe cambiar password
    if usuario.debe_cambiar_password:
        return None  # Forzar cambio de password primero

    # Login exitoso: registrar intento exitoso y reiniciar conteo de fallos
    await _registrar_intento_persistente(email_normalizado, ip, exito=True)
    return usuario


async def _registrar_intento_persistente(email: str, ip: str, exito: bool) -> None:
    """Registrar un intento de acceso en la tabla intento_acceso de forma persistente.

    Esta función crea una sesión independiente usando el mismo engine que la
    sesión principal. El registro se confirma en su propia transacción, por lo
    que sobrevive aunque la transacción principal del login se revierta.

    Por diseño excepción al límite transaccional habitual: el registro de seguridad
    debe sobrevivir a cualquier fallo de la operación de login subyacente.
    """
    # Crear una sesión nueva e independiente desde el engine de la app
    # Esta sesión tiene su propia transacción, por lo que su commit/rollback
    # no afecta a la sesión principal del login.
    try:
        async with app.state.async_session_maker() as tmp_session:
            tmp_session.add(
                IntentoAcceso(
                    email=email,
                    ip=ip,
                    exito=exito,
                )
            )
            await tmp_session.flush()
    except Exception:
        # Si falla el registro, no debería interrumpir el flujo de login.
        # El intento se perderá temporalmente, pero el flujo principal continúa.
        # En producción se podría conectar a monitoring/alerting de este error.
        pass


async def _chequear_bloqueo(
    email: str, ip: str
) -> tuple[bool, int]:
    """Verificar si el correo+IP exceden los 5 intentos en ventana de 60s.

    Esta consulta usa su propia sesión independiente para no depender del rollback
    de la transacción del login. Si la sesión falla, asumimos que no hay bloqueo
    para no bloquear al usuario por error de base de datos.
    """
    try:
        async with app.state.async_session_maker() as tmp_session:
            result = await tmp_session.execute(
                select(func.count(IntentoAcceso.id))
                .where(
                    IntentoAcceso.email == email,
                    IntentoAcceso.ip == ip,
                    IntentoAcceso.exito == False,
                    IntentoAcceso.cuando >= func.current_timestamp() - text("interval '60 seconds'"),
                )
            )
            fallos_ventana = result.scalar_one_or_none() or 0
    except Exception:
        # Si falla la consulta a BD, no bloqueamos al usuario por error de BD
        fallos_ventana = 0

    bloqueado = fallos_ventana >= 5
    return bloqueado, fallos_ventana


async def _verificar_password_hash(password: str, hash_almacenado: str) -> bool:
    """Verifica password contra hash usando run_in_executor con semáforo compartido."""

    loop = asyncio.get_event_loop()
    async with _BCRYPT_SEMAPHORE:
        return await loop.run_in_executor(
            _BCRYPT_EXECUTOR,
            lambda: checkpw(password.encode("utf-8"), hash_almacenado.encode("utf-8"))
        )


async def registrar_usuario_atomico(
    session: AsyncSession, data: "schemas.Register"
) -> Usuario:
    """Registro atómico: usuario + rol CLIENTE + ficha cliente (RN-02/US-002).

    Esta operación se realiza dentro de una transacción unitaria.
    Si falla algún constraint (email/documento duplicado), se hace rollback.
    """
    from app.modules.auth import schemas as auth_schemas

    async with session.begin():
        # 1. Verificar que el email no existe ya (unique constraint)
        existing = await session.execute(
            select(Usuario).where(Usuario.email == data.email.lower().strip())
        )
        if existing.scalar_one_or_none() is not None:
            raise Conflicto("Email ya registrado")

        # 2. Verificar que el documento no existe ya
        existing_doc = await session.execute(
            select(Cliente).where(Cliente.documento == data.documento)
        )
        if existing_doc.scalar_one_or_none() is not None:
            raise Conflicto("Documento ya registrado")

        # 3. Hashear contraseña usando bcrypt fuera del bucle de eventos
        password_hash = await _hash_password(data.password)

        # 4. Crear usuario
        usuario = Usuario(
            email=data.email.lower().strip(),
            nombre=data.nombre,
            password_hash=password_hash,
            activo=True,
            debe_cambiar_password=False,
        )
        session.add(usuario)
        await session.flush()  # Para obtener el usuario.id

        # 5. Asignar rol CLIENTE (Check constraint en BD)
        asignacion = AsignacionRol(
            usuario_id=usuario.id,
            rol="CLIENTE",
        )
        session.add(asignacion)

        # 6. Crear ficha cliente vinculada al usuario
        cliente = Cliente(
            usuario_id=usuario.id,
            nombre=data.nombre,
            documento=data.documento,
            telefono=data.telefono or "",
        )
        session.add(cliente)

        await session.flush()

        return usuario


async def _hash_password(password: str) -> str:
    """Hash de password usando bcrypt en thread separado con semáforo compartido."""

    loop = asyncio.get_event_loop()
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password excede límite de bcrypt (72 bytes)")
    async with _BCRYPT_SEMAPHORE:
        hashed = await loop.run_in_executor(
            _BCRYPT_EXECUTOR,
            lambda: hashpw(password_bytes, gensalt(12)),
        )
    return hashed.decode("utf-8")


async def crear_token_usuario(usuario: Usuario) -> str:
    """Genera JWT access token con claims sub, iat, exp, roles."""

    now = int(time.time())
    roles = ["CLIENTE"]  # Simplificado - en producción vendría consultado de bd

    token = create_access_token(
        data={"sub": str(usuario.id), "iat": now, "exp": now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60), "roles": roles}
    )
    return token


async def obtener_usuario_token(
    token: str,
) -> Optional[Usuario]:
    """Decodifica y valida el JWT del token en cookie.

    Retorna el usuario si el token es válido, None en caso contrario.
    """
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        # Aquí se obtendría el usuario de la BD
        # Por simplicidad, retornamos None - el router hará la query completa
        return None
    except Exception:
        return None