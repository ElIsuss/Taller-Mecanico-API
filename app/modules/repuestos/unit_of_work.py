"""Unit-of-work wrapper for the spare-parts domain."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.unit_of_work import UnitOfWork
from app.modules.repuestos.repository import (
    HistorialPrecioRepuestoRepository,
    MovimientoStockRepository,
    RepuestoRepository,
)
from app.modules.usuarios.repository import UsuarioRepository


class RepuestoUnitOfWork(UnitOfWork):
    """Transaction boundary for repuesto stock and price writes."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        super().__init__(session_factory=session_factory, session=session)
        self.repuestos = self._register_repository(RepuestoRepository(self.session))
        self.movimientos_stock = self._register_repository(
            MovimientoStockRepository(self.session)
        )
        self.historial_precios = self._register_repository(
            HistorialPrecioRepuestoRepository(self.session)
        )
        self.usuarios = self._register_repository(UsuarioRepository(self.session))


__all__ = ["RepuestoUnitOfWork"]
