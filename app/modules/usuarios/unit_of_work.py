"""Unit-of-work wrapper for the user domain."""

from app.core.unit_of_work import UnitOfWork
from app.modules.usuarios.repository import AsignacionRolRepository, UsuarioRepository


class UsuarioUnitOfWork(UnitOfWork):
    """Transaction boundary for user-related writes."""

    def __init__(self, session_factory=None, session=None):
        super().__init__(session_factory=session_factory, session=session)
        self.usuarios = self._register_repository(UsuarioRepository(self.session))
        self.asignaciones_rol = self._register_repository(
            AsignacionRolRepository(self.session)
        )


__all__ = ["UsuarioUnitOfWork"]
