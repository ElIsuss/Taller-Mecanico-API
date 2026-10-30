"""Unit-of-work wrapper for the order domain."""

from app.core.unit_of_work import UnitOfWork
from app.modules.ordenes.repository import (
    EstadoOrdenRepository,
    HistorialEstadoOrdenRepository,
    ItemOrdenRepository,
    OrdenTrabajoRepository,
)


class OrdenUnitOfWork(UnitOfWork):
    """Transaction boundary for work-order writes."""

    def __init__(self, session_factory=None, session=None):
        super().__init__(session_factory=session_factory, session=session)
        self.ordenes = self._register_repository(OrdenTrabajoRepository(self.session))
        self.items = self._register_repository(ItemOrdenRepository(self.session))
        self.estados = self._register_repository(EstadoOrdenRepository(self.session))
        self.historial_estados = self._register_repository(
            HistorialEstadoOrdenRepository(self.session)
        )


__all__ = ["OrdenUnitOfWork"]
