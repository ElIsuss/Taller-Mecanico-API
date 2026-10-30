"""Spare-parts repository definitions."""

from sqlalchemy import func, select

from app.core.repository import BaseRepository, SoftDeleteRepository
from app.modules.repuestos.models import (
    HistorialPrecioRepuesto,
    MovimientoStock,
    Repuesto,
)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class RepuestoRepository(SoftDeleteRepository[Repuesto]):
    model = Repuesto

    async def list_page(
        self, offset: int, limit: int, query: str | None = None
    ) -> tuple[list[Repuesto], int]:
        session = self._require_session()
        filtros = [Repuesto.borrado_en.is_(None)]
        if query:
            patron = f"%{_escape_like(query)}%"
            filtros.append(Repuesto.descripcion.ilike(patron, escape="\\"))
        total = await session.scalar(
            select(func.count()).select_from(Repuesto).where(*filtros)
        )
        result = await session.scalars(
            select(Repuesto)
            .where(*filtros)
            .order_by(Repuesto.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result), int(total or 0)


class MovimientoStockRepository(BaseRepository[MovimientoStock]):
    model = MovimientoStock

    async def list_for_repuesto(
        self, repuesto_id: int, offset: int, limit: int
    ) -> tuple[list[MovimientoStock], int]:
        session = self._require_session()
        filtros = MovimientoStock.repuesto_id == repuesto_id
        total = await session.scalar(
            select(func.count())
            .select_from(MovimientoStock)
            .where(filtros)
        )
        result = await session.scalars(
            select(MovimientoStock)
            .where(filtros)
            .order_by(MovimientoStock.cuando.desc(), MovimientoStock.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result), int(total or 0)


class HistorialPrecioRepuestoRepository(BaseRepository[HistorialPrecioRepuesto]):
    model = HistorialPrecioRepuesto

    async def list_for_repuesto(
        self, repuesto_id: int, offset: int, limit: int
    ) -> tuple[list[HistorialPrecioRepuesto], int]:
        session = self._require_session()
        filtros = HistorialPrecioRepuesto.repuesto_id == repuesto_id
        total = await session.scalar(
            select(func.count())
            .select_from(HistorialPrecioRepuesto)
            .where(filtros)
        )
        result = await session.scalars(
            select(HistorialPrecioRepuesto)
            .where(filtros)
            .order_by(
                HistorialPrecioRepuesto.cuando.desc(),
                HistorialPrecioRepuesto.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result), int(total or 0)


__all__ = [
    "HistorialPrecioRepuestoRepository",
    "MovimientoStockRepository",
    "RepuestoRepository",
]
