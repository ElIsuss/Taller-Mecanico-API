"""Dependencias globales de FastAPI: autenticación y sesión actual."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import decode_access_token
from app.modules.usuarios.models import Usuario


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
        iat = payload.get("iat")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    result = await session.execute(
        select(Usuario).where(Usuario.id == int(user_id))
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
