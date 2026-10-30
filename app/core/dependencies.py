"""Dependencias globales de FastAPI: autenticación y sesión actual."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import decode_access_token
from app.modules.usuarios.models import AsignacionRol, Usuario


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Usuario:
    """Obtiene el usuario autenticado desde la cookie access_token.
    
    - Extrae la cookie `access_token`.
    - Decodifica el JWT y valida su firma y expiración.
    - Aplica RN-07: si la contraseña fue cambiada con posterioridad a la emisión (iat),
      la sesión previa queda invalidada sin truncar a segundos.
    - Valida que el usuario exista y esté activo.
    """
    token: Optional[str] = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        user_id_int = int(user_id)
        iat = payload.get("iat")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    result = await session.execute(
        select(Usuario).where(Usuario.id == user_id_int)
    )
    usuario = result.scalar_one_or_none()

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
        )

    # RN-07: Invalidar sesiones emitidas antes del cambio de contraseña
    if usuario.password_cambiada_en is not None and iat is not None:
        cambiada_ts = usuario.password_cambiada_en.timestamp()
        if float(iat) < cambiada_ts:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to password change",
            )

    return usuario


async def obtener_roles_vigentes(
    session: AsyncSession,
    usuario_id: int,
) -> list[str]:
    """Consulta rol/roles vigentes en la base para el usuario autenticado."""
    stmt = (
        select(AsignacionRol.rol)
        .where(AsignacionRol.usuario_id == usuario_id)
        .where(AsignacionRol.revocada_en.is_(None))
        .where(or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > func.now()))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def requiere_rol(*roles_permitidos: str):
    """Dependency factory que valida roles vigentes consultados en cada petición."""
    roles = tuple(str(r).upper() for r in roles_permitidos)

    async def role_checker(
        request: Request,
        usuario: Usuario = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> Usuario:
        path = request.url.path.rstrip("/")
        if usuario.debe_cambiar_password and not (
            path.startswith("/auth") or path.startswith("/health")
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Debe cambiar su contraseña antes de continuar",
            )

        roles_vigentes = await obtener_roles_vigentes(session, usuario.id)
        if not set(roles_vigentes) & set(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return usuario

    return role_checker
