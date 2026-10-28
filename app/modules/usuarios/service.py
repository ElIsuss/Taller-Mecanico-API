"""Consultas de usuarios usadas por los servicios mientras no hay sesión."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NoEncontrado
from app.modules.usuarios.models import Usuario


async def obtener_usuario(session: AsyncSession, usuario_id: int) -> Usuario:
    usuario = await session.get(Usuario, usuario_id)
    if usuario is None:
        raise NoEncontrado("El usuario indicado no existe")
    return usuario
