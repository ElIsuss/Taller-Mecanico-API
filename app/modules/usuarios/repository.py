"""User-domain repository definitions."""

from app.core.repository import BaseRepository
from app.modules.usuarios.models import AsignacionRol, Usuario


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    model = AsignacionRol


__all__ = ["UsuarioRepository", "AsignacionRolRepository"]
