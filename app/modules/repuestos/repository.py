"""Spare-parts repository definitions."""

from app.core.repository import BaseRepository, SoftDeleteRepository
from app.modules.repuestos.models import (
    HistorialPrecioRepuesto,
    MovimientoStock,
    Repuesto,
)


class RepuestoRepository(SoftDeleteRepository[Repuesto]):
    model = Repuesto


class MovimientoStockRepository(BaseRepository[MovimientoStock]):
    model = MovimientoStock


class HistorialPrecioRepuestoRepository(BaseRepository[HistorialPrecioRepuesto]):
    model = HistorialPrecioRepuesto


__all__ = [
    "RepuestoRepository",
    "MovimientoStockRepository",
    "HistorialPrecioRepuestoRepository",
]
