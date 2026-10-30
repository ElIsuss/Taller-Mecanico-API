"""Unit-of-work wrapper for the user domain."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository
from app.modules.usuarios.repository import (
    AsignacionRolRepository,
    EventoSeguridadRepository,
    IntentoAccesoRepository,
    UsuarioRepository,
)


class UsuarioUnitOfWork(UnitOfWork):
    """Transaction boundary for user-related writes."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__(session_factory=session_factory, session=session)
        self.usuarios = self._register_repository(UsuarioRepository(self.session))
        self.asignaciones_rol = self._register_repository(
            AsignacionRolRepository(self.session)
        )
        self.eventos_seguridad = self._register_repository(
            EventoSeguridadRepository(self.session)
        )
        self.intentos_acceso = self._register_repository(
            IntentoAccesoRepository(self.session)
        )
        self.clientes = self._register_repository(ClienteRepository(self.session))


__all__ = ["UsuarioUnitOfWork"]
