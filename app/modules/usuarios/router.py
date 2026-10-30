"""Endpoints REST de autenticación y perfil de usuario."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.security import delete_access_token_cookie, set_access_token_cookie
from app.modules.usuarios import schemas, service
from app.modules.usuarios.models import AsignacionRol, Usuario

router = APIRouter(prefix="/auth", tags=["autenticación"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/login",
    response_model=schemas.Me,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Login con email y contraseña. Aplica RN-08 (429 con Retry-After) y RN-09 (401 constante).",
)
async def login(
    data: schemas.Login,
    request: Request,
    session: SessionDep,
    response: Response,
) -> schemas.Me:
    """Login de usuario.
    
    - Aplica RN-08: si se superan 5 fallos en ventana de 60s, responde 429 con encabezado Retry-After.
    - Aplica RN-09: responde 401 'Invalid credentials' tanto si el usuario no existe como si la clave es errónea.
    - Establece la cookie HttpOnly access_token con SameSite=Lax.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Verificar si ya está bloqueado antes de evaluar credenciales (RN-08)
    bloqueado, _, retry_after = await service.chequear_bloqueo(session, data.email, client_ip)
    if bloqueado:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente más tarde.",
            headers={"Retry-After": str(retry_after)},
        )

    usuario = await service.autenticar_usuario(
        session, data.email, data.password, ip=client_ip
    )

    if usuario is None:
        # RN-09: mensaje unificado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
        )

    # Consultar roles vigentes en base de datos (RN-04)
    stmt = (
        select(AsignacionRol.rol)
        .where(AsignacionRol.usuario_id == usuario.id)
        .where(AsignacionRol.revocada_en.is_(None))
    )
    result = await session.execute(stmt)
    roles = result.scalars().all()
    rol_principal = roles[0] if roles else "CLIENTE"

    token = await service.crear_token_usuario(usuario, roles=roles)
    set_access_token_cookie(response, token)

    return schemas.Me(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=rol_principal,
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
    - Contraseña hasheada fuera del event loop (bcrypt con BCRYPT_ROUNDS).
    - Retorna 201 Created y emite cookie de sesión.
    """
    usuario = await service.registrar_usuario_atomico(session, data)

    token = await service.crear_token_usuario(usuario, roles=["CLIENTE"])
    set_access_token_cookie(response, token)

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
    description="Invalida la cookie access_token.",
)
async def logout(
    response: Response,
) -> Response:
    """Cerrar sesión.
    
    - Invalida la cookie access_token estableciendo Max-Age=0.
    - Idempotente: responde 204 aún sin sesión previa.
    """
    delete_access_token_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get(
    "/yo",
    response_model=schemas.Me,
    summary="Perfil del usuario autenticado",
    description="Devuelve los datos del usuario sin password_hash consultando roles vigentes (RN-04).",
)
async def perfil(
    session: SessionDep,
    current_usuario: Usuario = Depends(get_current_user),
) -> schemas.Me:
    """Obtener el perfil del usuario autenticado.
    
    - Requiere cookie access_token válida.
    - No expone password_hash.
    - Consulta roles vigentes en base de datos en cada petición (RN-04).
    """
    stmt = (
        select(AsignacionRol.rol)
        .where(AsignacionRol.usuario_id == current_usuario.id)
        .where(AsignacionRol.revocada_en.is_(None))
    )
    result = await session.execute(stmt)
    roles = result.scalars().all()
    rol_principal = roles[0] if roles else "CLIENTE"

    return schemas.Me(
        id=current_usuario.id,
        email=current_usuario.email,
        nombre=current_usuario.nombre,
        rol=rol_principal,
        iat=int(time.time()),
    )
