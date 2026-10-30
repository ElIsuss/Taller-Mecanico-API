"""Unit-of-work wrapper for the client domain."""

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository, VehiculoRepository


class ClienteUnitOfWork(UnitOfWork):
    """Transaction boundary for client and vehicle writes."""

    def __init__(self, session_factory=None, session=None):
        super().__init__(session_factory=session_factory, session=session)
        self.clientes = self._register_repository(ClienteRepository(self.session))
        self.vehiculos = self._register_repository(VehiculoRepository(self.session))


__all__ = ["ClienteUnitOfWork"]
