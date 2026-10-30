"""Unit-of-work wrapper for the client domain."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository, VehiculoRepository
from app.modules.usuarios.repository import UsuarioRepository


class ClienteUnitOfWork(UnitOfWork):
    """Transaction boundary for client and vehicle writes."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__(session_factory=session_factory, session=session)
        self.clientes = self._register_repository(ClienteRepository(self.session))
        self.vehiculos = self._register_repository(VehiculoRepository(self.session))
        self.usuarios = self._register_repository(UsuarioRepository(self.session))


__all__ = ["ClienteUnitOfWork"]
