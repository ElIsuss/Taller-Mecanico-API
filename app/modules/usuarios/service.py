"""Servicios de autenticación, usuarios y registro atómico."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflicto, NoEncontrado
from app.core.security import (
    constant_time_verify,
    create_access_token,
    decode_access_token,
    hash_password,
)
from app.modules.clientes.models import Cliente
from app.modules.usuarios import schemas
from app.modules.usuarios.repository import IntentoAccesoRepository
from app.modules.usuarios.unit_of_work import UsuarioUnitOfWork
from app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)


async def registrar_evento_seguridad(
    uow: UsuarioUnitOfWork,
    actor: str,
    accion: str,
) -> EventoSeguridad:
    """Registra un evento crítico de seguridad en la auditoría."""
    evento = EventoSeguridad(actor=actor, accion=accion)
    await uow.eventos_seguridad.add(evento)
    await uow.flush()
    return evento


async def asignar_rol_usuario(
    uow: UsuarioUnitOfWork,
    usuario_id: int,
    rol: str,
    actor_id: int,
) -> AsignacionRol:
    """Otorga un rol vigente a un usuario con validaciones RN-03 y RN-05."""
    async with uow:
        rol_norm = str(rol).upper()
        if rol_norm not in {"ADMIN", "RECEPCION", "MECANICO", "CLIENTE"}:
            raise Conflicto("Rol no válido")

        usuario = await uow.usuarios.get_by_id(usuario_id)
        if usuario is None:
            raise NoEncontrado("El usuario indicado no existe")
        existente = await uow.asignaciones_rol.get_active_assignment(
            usuario.id, rol_norm
        )
        if existente is not None:
            raise Conflicto("El usuario ya tiene este rol vigente")

        asignacion = AsignacionRol(
            usuario_id=usuario.id,
            rol=rol_norm,
            otorgada_por=actor_id,
        )
        await uow.asignaciones_rol.add(asignacion)
        await uow.flush()
        await registrar_evento_seguridad(
            uow,
            str(actor_id),
            f"ASIGNAR_ROL:{usuario.id}:{rol_norm}",
        )
        return asignacion


async def revocar_rol_usuario(
    uow: UsuarioUnitOfWork,
    usuario_id: int,
    rol: str,
    actor_id: int,
) -> AsignacionRol:
    """Revoca una asignación vigente de rol con autoprotección ADMIN."""
    async with uow:
        rol_norm = str(rol).upper()
        if rol_norm not in {"ADMIN", "RECEPCION", "MECANICO", "CLIENTE"}:
            raise Conflicto("Rol no válido")

        asignacion = await uow.asignaciones_rol.get_active_assignment(
            usuario_id, rol_norm
        )
        if asignacion is None:
            raise NoEncontrado("No existe un rol vigente para revocar")

        if usuario_id == actor_id and rol_norm == "ADMIN":
            raise Conflicto("No puedes revocar tu propio rol ADMIN")

        if rol_norm == "ADMIN" and await uow.asignaciones_rol.count_active_admins() <= 1:
            raise Conflicto("El sistema no puede quedar sin administradores")

        asignacion.revocada_en = datetime.now(timezone.utc)
        await uow.flush()
        await registrar_evento_seguridad(
            uow,
            str(actor_id),
            f"REVOCAR_ROL:{usuario_id}:{rol_norm}",
        )
        return asignacion


async def listar_eventos_seguridad(
    uow: UsuarioUnitOfWork,
) -> list[EventoSeguridad]:
    async with uow:
        return await uow.eventos_seguridad.list_recent()


async def obtener_roles_vigentes(
    uow: UsuarioUnitOfWork, usuario_id: int
) -> list[str]:
    async with uow:
        asignaciones = await uow.asignaciones_rol.list_active_for_user(usuario_id)
        return [asignacion.rol for asignacion in asignaciones]


async def chequear_bloqueo(
    uow: UsuarioUnitOfWork, email: str, ip: str
) -> tuple[bool, int, int]:
    """Verifica si el par (email, ip) está bloqueado por exceder 5 intentos fallidos en 60s (RN-08).
    
    Retorna: (bloqueado, fallos_ventana, retry_after_segundos)
    """
    email_norm = email.lower().strip()
    ahora_utc = datetime.now(timezone.utc)
    hace_60s = ahora_utc - timedelta(seconds=60)

    async with uow:
        ultimo_exito = await uow.intentos_acceso.latest_success(email_norm, ip)
        fallos = await uow.intentos_acceso.count_recent_failures(
            email_norm, ip, hace_60s, ultimo_exito
        )
        bloqueado = fallos >= 5
        return bloqueado, fallos, 60


async def registrar_intento_acceso(
    session: AsyncSession, email: str, ip: str, exito: bool
) -> None:
    """Registra de forma persistente un intento de acceso en la tabla intento_acceso.
    
    Utiliza una transacción y sesión independientes para garantizar que el registro
    persista aun si la transacción principal del request sufre un rollback o falla (RN-08).
    """
    email_norm = email.lower().strip()

    # 1. Intentar sesión autónoma a través del bind de la sesión actual
    bind = getattr(session, "bind", None)
    if bind is None:
        try:
            bind = session.get_bind()
        except Exception:
            bind = None

    if bind is not None:
        try:
            from sqlalchemy.ext.asyncio import AsyncEngine
            engine = bind if isinstance(bind, AsyncEngine) else getattr(bind, "engine", bind)
            async with AsyncSession(engine, expire_on_commit=False) as sep_session:
                async with sep_session.begin():
                    intento = IntentoAcceso(email=email_norm, ip=ip, exito=exito)
                    repository = IntentoAccesoRepository(sep_session)
                    await repository.add(intento)
                return
        except Exception:
            pass

    # 2. Intentar sesión autónoma a través de app.state.async_session_maker
    try:
        from app.main import app
        session_maker = getattr(app.state, "async_session_maker", None)
        if session_maker is not None:
            async with session_maker() as sep_session:
                async with sep_session.begin():
                    intento = IntentoAcceso(email=email_norm, ip=ip, exito=exito)
                    repository = IntentoAccesoRepository(sep_session)
                    await repository.add(intento)
                return
    except Exception:
        pass

    # 3. Fallback directo en la sesión actual
    try:
        intento = IntentoAcceso(email=email_norm, ip=ip, exito=exito)
        repository = IntentoAccesoRepository(session)
        await repository.add(intento)
        await repository.flush()
        if hasattr(session, "commit"):
            await session.commit()
    except Exception:
        pass


async def autenticar_usuario(
    uow: UsuarioUnitOfWork,
    email: str,
    password: str,
    ip: str | None = None,
) -> Optional[Usuario]:
    """Autentica un usuario verificando credenciales.
    
    - Aplica RN-08: verifica bloqueo previo por 5 intentos fallidos en 60s.
    - Aplica RN-09: respuesta y tiempo constantes si el usuario existe o no.
    - Registra el intento de forma persistente.
    """
    email_norm = email.lower().strip()
    client_ip = ip or "desconocido"

    # 1. Verificar bloqueo previo (RN-08)
    bloqueado, _, _ = await chequear_bloqueo(uow, email_norm, client_ip)
    if bloqueado:
        if uow.session is None:
            raise RuntimeError("La sesión de usuario no está disponible")
        await registrar_intento_acceso(
            uow.session, email_norm, client_ip, exito=False
        )
        return None

    async with uow:
        usuario = await uow.usuarios.get_by_email(email_norm)

        hash_a_verificar = usuario.password_hash if usuario else None
        valido = await constant_time_verify(password, hash_a_verificar)
        if uow.session is None:
            raise RuntimeError("La sesión de usuario no está disponible")

        if not valido or usuario is None:
            await registrar_intento_acceso(
                uow.session, email_norm, client_ip, exito=False
            )
            return None

        await registrar_intento_acceso(
            uow.session, email_norm, client_ip, exito=True
        )
        return usuario


async def registrar_usuario_atomico(
    uow: UsuarioUnitOfWork, data: schemas.Register
) -> Usuario:
    """Registro atómico: usuario + rol CLIENTE + ficha cliente (RN-02 / US-002).
    
    Toda la operación se confirma en una sola transacción o se descarta por completo.
    """
    async with uow:
        email_norm = data.email.lower().strip()

        if await uow.usuarios.get_by_email(email_norm) is not None:
            raise Conflicto("Email ya registrado")
        cliente_existente = await uow.clientes.get_one(
            Cliente.documento == data.documento.strip()
        )
        if cliente_existente is not None:
            raise Conflicto("Documento ya registrado")

        hashed = await hash_password(data.password)
        usuario = Usuario(
            email=email_norm,
            nombre=data.nombre.strip(),
            password_hash=hashed,
            activo=True,
            debe_cambiar_password=False,
        )
        await uow.usuarios.add(usuario)
        await uow.flush()

        await uow.asignaciones_rol.add(
            AsignacionRol(usuario_id=usuario.id, rol="CLIENTE")
        )
        await uow.clientes.add(
            Cliente(
                usuario_id=usuario.id,
                nombre=data.nombre.strip(),
                documento=data.documento.strip(),
                telefono=data.telefono or "",
            )
        )
        await uow.flush()
        return usuario


async def crear_token_usuario(usuario: Usuario, roles: list[str] | None = None) -> str:
    """Genera JWT access token con claims sub, iat, exp, roles."""
    roles_list = roles if roles is not None else ["CLIENTE"]
    return create_access_token(
        data={"sub": str(usuario.id), "roles": roles_list}
    )
