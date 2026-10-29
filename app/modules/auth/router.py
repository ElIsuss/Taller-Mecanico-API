"""Endpoints REST de autenticación."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import Conflicto, NoEncontrado
from app.core.security import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core import cookies as cookie_utils
from app.core.redis_client import ya_bloqueado
from app.modules.auth import schemas, service
from app.modules.auth.service import autenticar_usuario, crear_token_usuario, obtener_usuario_token
from app.modules.auth.models import Usuario, AsignacionRol
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["autenticación"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/login",
    response_model=schemas.Me,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Login con email y contraseña. Retorna 401 siempre igual (RN-09). Aplica RN-08: 5 intentos fallidos → 429 con Retry-After.",
)
async def login(
    data: schemas.Login,
    request: Request,
    session: SessionDep,
    response: Response,
) -> schemas.Me:
    """Login de usuario.

    - Aplica RN-09: responde 401 `{"detail": "Invalid credentials"}`
      tanto si el email no existe como si la contraseña es incorrecta.
    - Aplica RN-08: contador de intentos fallidos por correo+e IP, ventana 60s.
      A los 5 fallos, responde 429 con encabezado Retry-After.
    - Genera JWT y establece cookie `access_token` HttpOnly.
    - No verifica contraseña si el usuario está bloqueado.
    """
    # Obtener dirección IP del cliente
    ip = request.client.host if request.client else "desconocido"

    # Verificar si el correo+IP están bloqueados (5 intentos fallidos en ventana 60s)
    from sqlalchemy import select, func
    from app.modules.auth.models import IntentoAcceso

    ahora = __import__("time").time()
    hace_60 = ahora - 60

    result = await session.execute(
        select(IntentoAcceso).where(
            IntentoAcceso.email == data.email.lower().strip(),
            IntentoAcceso.ip == ip,
            IntentoAcceso.exito == False,
            IntentoAcceso.cuando >= func.current_timestamp() - func.text("interval '60 seconds'"),
        )
    )
    intentos_recientes = result.scalars().all()
    fallos_ventana = len(intentos_recientes)

    if fallos_ventana >= 5:
        # RN-08: Bloqueo activo - responder 429 con Retry-After
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente más tarde.",
            headers={"Retry-After": "900"},  # 15 minutos en segundos
        )

    # Si no está bloqueado, proceder con la autenticación
    usuario = await service.autenticar_usuario(session, data.email, data.password, ip=ip)

    if usuario is None:
        # RN-09: Mismo error aunque el email no exista
        # RN-08: Ya registró el intento fallido dentro de autenticar_usuario
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Login exitoso: generar token y establecer cookie
    token = await crear_token_usuario(usuario)

    # Establecer cookie access_token
    cookie_utils.set_access_token_cookie(response, token)

    return schemas.Me(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol if hasattr(usuario, "rol") else "CLIENTE",
        iat=int(time.time()),
    )


@router.post(
    "/register",
    response_model=schemas.Me,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo cliente",
    description="Registro atómico: usuario + rol CLIENTE + ficha cliente (RN-02).",
)
async def register(
    data: schemas.Register,
    session: SessionDep,
    response: Response,
) -> schemas.Me:
    """Registro de nuevo cliente.

    - Creación atómica: usuario + asignacion_rol CLIENTE + ficha cliente.
    - Contraseña hasheada con bcrypt fuera del event loop.
    - Retorna 201 Created con datos básicos (sin password_hash).
    """
    usuario = await service.registrar_usuario_atomico(session, data)

    # Generar token inmediato tras registro
    token = await crear_token_usuario(usuario)

    # Establecer cookie access_token
    cookie_utils.set_access_token_cookie(response, token)

    return schemas.Me(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol="CLIENTE",
        iat=int(time.time()),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
    description="Invalidar la cookie access_token.",
)
async def logout(
    response: Response,
) -> Response:
    """Cerrar sesión.

    - Borra la cookie access_token usando Set-Cookie con Max-Age=0.
    - Operación idempotente: responde 204 aunque no haya sesión activa.
    """
    cookie_utils.delete_access_token_cookie(response)
    return response


@router.get(
    "/yo",
    response_model=schemas.Me,
    summary="Perfil del usuario autenticado",
    description="Devuelve los datos del usuario sin password_hash (RN-04).",
)
async def perfil(
    session: SessionDep,
    current_usuario: Usuario = Depends(get_current_user),
) -> schemas.Me:
    """Obtener perfil del usuario autenticado.

    - Requiere cookie `access_token` válida.
    - Retorna 401 si no hay sesión válida.
    - No incluye password_hash en la respuesta.
    - Incluye roles vigentes consultados en base (RN-04): solo asignaciones
      con `revocada_en IS NULL`, consultadas en cada petición.
    """
    from app.modules.auth.schemas import Me as MeSchema

    # Consultar roles vigentes en base de datos (RN-04)
    # Asignaciones no revocadas (revocada_en IS NULL) para este usuario
    result = await session.execute(
        select(AsignacionRol.rol)
        .where(AsignacionRol.usuario_id == current_usuario.id)
        .where(AsignacionRol.revocada_en.is_(None))
    )
    vigentes = result.scalars().all()

    # Determinar el rol principal (primero vigente o 'CLIENTE' por default)
    rol_principal = vigentes[0] if vigentes else "CLIENTE"

    return MeSchema(
        id=current_usuario.id,
        email=current_usuario.email,
        nombre=current_usuario.nombre,
        rol=rol_principal,
        iat=int(time.time()),
    )