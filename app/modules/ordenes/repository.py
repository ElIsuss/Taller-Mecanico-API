"""Order-domain repository definitions."""

from app.core.repository import BaseRepository
from app.modules.ordenes.models import (
    EstadoOrden,
    HistorialEstadoOrden,
    ItemOrden,
    OrdenTrabajo,
)


class EstadoOrdenRepository(BaseRepository[EstadoOrden]):
    model = EstadoOrden


class OrdenTrabajoRepository(BaseRepository[OrdenTrabajo]):
    model = OrdenTrabajo


class ItemOrdenRepository(BaseRepository[ItemOrden]):
    model = ItemOrden


class HistorialEstadoOrdenRepository(BaseRepository[HistorialEstadoOrden]):
    model = HistorialEstadoOrden


__all__ = [
    "EstadoOrdenRepository",
    "OrdenTrabajoRepository",
    "ItemOrdenRepository",
    "HistorialEstadoOrdenRepository",
]
