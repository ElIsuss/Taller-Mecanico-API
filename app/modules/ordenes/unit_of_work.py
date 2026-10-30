"""Unit-of-work wrapper for the order domain."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import VehiculoRepository
from app.modules.ordenes.repository import (
    EstadoOrdenRepository,
    HistorialEstadoOrdenRepository,
    ItemOrdenRepository,
    OrdenTrabajoRepository,
)
from app.modules.repuestos.repository import MovimientoStockRepository, RepuestoRepository
from app.modules.usuarios.repository import UsuarioRepository


class OrdenUnitOfWork(UnitOfWork):
    """Transaction boundary for work-order writes."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__(session_factory=session_factory, session=session)
        self.ordenes = self._register_repository(OrdenTrabajoRepository(self.session))
        self.items = self._register_repository(ItemOrdenRepository(self.session))
        self.estados = self._register_repository(EstadoOrdenRepository(self.session))
        self.historial_estados = self._register_repository(
            HistorialEstadoOrdenRepository(self.session)
        )
        self.vehiculos = self._register_repository(VehiculoRepository(self.session))
        self.repuestos = self._register_repository(RepuestoRepository(self.session))
        self.movimientos_stock = self._register_repository(
            MovimientoStockRepository(self.session)
        )
        self.usuarios = self._register_repository(UsuarioRepository(self.session))


__all__ = ["OrdenUnitOfWork"]
