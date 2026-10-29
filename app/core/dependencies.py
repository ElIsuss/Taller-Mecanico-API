from __future__ import annotations

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.exceptions import NoEncontrado
from app.core.security import decode_access_token
from app.modules.auth.models import Usuario


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Usuario:
    """Obtener usuario actual desde la cookie access_token.

    - Lee la cookie `access_token` de la petición
    - Decodifica el JWT y valida los claims
    - Consulta el usuario en la base de datos
    - Retorna 401 si no hay sesión válida
    """
    token: Optional[str] = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
            )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    usuario = await session.execute(
        select(Usuario).where(Usuario.id == int(user_id))
    )
    usuario = usuario.scalar_one_or_none()

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=401,
            detail="Account disabled",
        )

    return usuario