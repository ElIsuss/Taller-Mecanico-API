"""Servicios de autenticación, usuarios y registro atómico."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import Conflicto, NoEncontrado
from app.core.security import (
    constant_time_verify,
    create_access_token,
    decode_access_token,
    hash_password,
)
from app.modules.clientes.models import Cliente
from app.modules.usuarios import schemas
from app.modules.usuarios.models import AsignacionRol, IntentoAcceso, Usuario


async def obtener_usuario(session: AsyncSession, usuario_id: int) -> Usuario:
    """Obtener usuario por ID (uso interno)."""
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if usuario is None:
        raise NoEncontrado("El usuario indicado no existe")
    return usuario


async def chequear_bloqueo(
    session: AsyncSession, email: str, ip: str
) -> tuple[bool, int, int]:
    """Verifica si el par (email, ip) está bloqueado por exceder 5 intentos fallidos en 60s (RN-08).
    
    Retorna: (bloqueado, fallos_ventana, retry_after_segundos)
    """
    email_norm = email.lower().strip()
    ahora_utc = datetime.now(timezone.utc)
    hace_60s = ahora_utc - timedelta(seconds=60)

    try:
        # 1. Obtener la fecha del último login exitoso (si hubo) para reiniciar el conteo
        stmt_exito = (
            select(func.max(IntentoAcceso.cuando))
            .where(
                IntentoAcceso.email == email_norm,
                IntentoAcceso.ip == ip,
                IntentoAcceso.exito == True,
            )
        )
        res_exito = await session.execute(stmt_exito)
        ultimo_exito = res_exito.scalar_one_or_none()

        # 2. Contar fallos dentro de la ventana de 60s posteriores al último éxito
        stmt_fallos = (
            select(func.count(IntentoAcceso.id))
            .where(
                IntentoAcceso.email == email_norm,
                IntentoAcceso.ip == ip,
                IntentoAcceso.exito == False,
                IntentoAcceso.cuando >= hace_60s,
            )
        )
        if ultimo_exito is not None:
            stmt_fallos = stmt_fallos.where(IntentoAcceso.cuando > ultimo_exito)

        res_fallos = await session.execute(stmt_fallos)
        fallos = res_fallos.scalar_one_or_none() or 0

        bloqueado = fallos >= 5
        return bloqueado, fallos, 60
    except Exception:
        # En caso de error de BD, no bloquear preventivamente
        return False, 0, 0


async def registrar_intento_acceso(
    session: AsyncSession, email: str, ip: str, exito: bool
) -> None:
    """Registra de forma persistente un intento de acceso en la tabla intento_acceso.
    
    Usa una sesión separada para sobrevivir al rollback de la sesión principal si el login falla.
    """
    email_norm = email.lower().strip()
    try:
        if session.bind:
            async with AsyncSession(session.bind) as sep_session:
                async with sep_session.begin():
                    intento = IntentoAcceso(email=email_norm, ip=ip, exito=exito)
                    sep_session.add(intento)
                return
    except Exception:
        pass

    # Fallback si no hay bind separado o ocurrió excepción
    try:
        intento = IntentoAcceso(email=email_norm, ip=ip, exito=exito)
        session.add(intento)
        await session.flush()
    except Exception:
        pass


async def autenticar_usuario(
    session: AsyncSession, email: str, password: str, ip: str | None = None
) -> Optional[Usuario]:
    """Autentica un usuario verificando credenciales.
    
    - Aplica RN-08: verifica bloqueo previo por 5 intentos fallidos en 60s.
    - Aplica RN-09: respuesta y tiempo constantes si el usuario existe o no.
    - Registra el intento de forma persistente.
    """
    email_norm = email.lower().strip()
    client_ip = ip or "desconocido"

    # 1. Verificar bloqueo previo (RN-08)
    bloqueado, _, _ = await chequear_bloqueo(session, email_norm, client_ip)
    if bloqueado:
        await registrar_intento_acceso(session, email_norm, client_ip, exito=False)
        return None

    # 2. Consultar usuario en BD
    stmt = select(Usuario).where(Usuario.email == email_norm)
    res = await session.execute(stmt)
    usuario = res.scalar_one_or_none()

    # 3. Verificación de contraseña en tiempo constante (RN-09)
    # Siempre ejecuta bcrypt (con dummy si no existe)
    hash_a_verificar = usuario.password_hash if usuario else None
    valido = await constant_time_verify(password, hash_a_verificar)

    if not valido or usuario is None:
        await registrar_intento_acceso(session, email_norm, client_ip, exito=False)
        return None

    # 4. Éxito: registrar intento exitoso (reinicia la cuenta efectiva)
    await registrar_intento_acceso(session, email_norm, client_ip, exito=True)
    return usuario


async def registrar_usuario_atomico(
    session: AsyncSession, data: schemas.Register
) -> Usuario:
    """Registro atómico: usuario + rol CLIENTE + ficha cliente (RN-02 / US-002).
    
    Toda la operación se confirma en una sola transacción o se descarta por completo.
    """
    email_norm = data.email.lower().strip()

    # 1. Validar que el email no exista
    res_usr = await session.execute(select(Usuario).where(Usuario.email == email_norm))
    if res_usr.scalar_one_or_none() is not None:
        raise Conflicto("Email ya registrado")

    # 2. Validar que el documento no pertenezca ya a un cliente
    res_cli = await session.execute(
        select(Cliente).where(Cliente.documento == data.documento.strip())
    )
    if res_cli.scalar_one_or_none() is not None:
        raise Conflicto("Documento ya registrado")

    # 3. Hashear password fuera del event loop (bcrypt con BCRYPT_ROUNDS)
    hashed = await hash_password(data.password)

    # 4. Crear usuario
    usuario = Usuario(
        email=email_norm,
        nombre=data.nombre.strip(),
        password_hash=hashed,
        activo=True,
        debe_cambiar_password=False,
    )
    session.add(usuario)
    await session.flush()

    # 5. Crear asignación de rol CLIENTE
    asignacion = AsignacionRol(
        usuario_id=usuario.id,
        rol="CLIENTE",
    )
    session.add(asignacion)

    # 6. Crear ficha de cliente vinculada
    cliente = Cliente(
        usuario_id=usuario.id,
        nombre=data.nombre.strip(),
        documento=data.documento.strip(),
        telefono=data.telefono or "",
    )
    session.add(cliente)
    await session.flush()

    return usuario


async def crear_token_usuario(usuario: Usuario, roles: list[str] | None = None) -> str:
    """Genera JWT access token con claims sub, iat, exp, roles."""
    roles_list = roles if roles is not None else ["CLIENTE"]
    return create_access_token(
        data={"sub": str(usuario.id), "roles": roles_list}
    )
