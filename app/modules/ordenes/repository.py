"""Order-domain repository definitions."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository
from app.modules.clientes.models import Vehiculo
from app.modules.ordenes.models import (
    EstadoOrden,
    HistorialEstadoOrden,
    ItemOrden,
    OrdenTrabajo,
)
from app.modules.repuestos.models import Repuesto


class EstadoOrdenRepository(BaseRepository[EstadoOrden]):
    model = EstadoOrden

    async def list_page(self, offset: int, limit: int) -> tuple[list[EstadoOrden], int]:
        session = self._require_session()
        total = await session.scalar(select(func.count()).select_from(EstadoOrden))
        result = await session.scalars(
            select(EstadoOrden)
            .order_by(EstadoOrden.posicion)
            .offset(offset)
            .limit(limit)
        )
        return list(result), int(total or 0)


class OrdenTrabajoRepository(BaseRepository[OrdenTrabajo]):
    model = OrdenTrabajo

    @staticmethod
    def _loaded_order_query() -> Select[tuple[OrdenTrabajo]]:
        return select(OrdenTrabajo).options(
            selectinload(OrdenTrabajo.items).selectinload(ItemOrden.repuesto),
            selectinload(OrdenTrabajo.vehiculo).selectinload(Vehiculo.cliente),
            selectinload(OrdenTrabajo.historial_estados),
        )

    async def get_loaded(self, orden_id: int, lock: bool = False) -> OrdenTrabajo | None:
        session = self._require_session()
        stmt = self._loaded_order_query().where(OrdenTrabajo.id == orden_id)
        if lock:
            stmt = stmt.with_for_update()
        return await session.scalar(stmt)

    async def get_vehicle_with_client(self, vehiculo_id: int) -> Vehiculo | None:
        session = self._require_session()
        stmt = (
            select(Vehiculo)
            .options(selectinload(Vehiculo.cliente))
            .where(Vehiculo.id == vehiculo_id)
        )
        return await session.scalar(stmt)

    async def list_page(
        self,
        offset: int,
        limit: int,
        estado: str | None = None,
        vehiculo_id: int | None = None,
    ) -> tuple[list[OrdenTrabajo], int]:
        session = self._require_session()
        filtros = []
        if estado is not None:
            filtros.append(OrdenTrabajo.estado == estado)
        if vehiculo_id is not None:
            filtros.append(OrdenTrabajo.vehiculo_id == vehiculo_id)
        total = await session.scalar(
            select(func.count()).select_from(OrdenTrabajo).where(*filtros)
        )
        result = await session.scalars(
            self._loaded_order_query()
            .where(*filtros)
            .order_by(OrdenTrabajo.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result), int(total or 0)

    async def get_repuestos(
        self, repuesto_ids: list[int], lock: bool = False
    ) -> list[Repuesto]:
        if not repuesto_ids:
            return []
        session = self._require_session()
        stmt = select(Repuesto).where(Repuesto.id.in_(repuesto_ids))
        if lock:
            stmt = stmt.with_for_update()
        return list(await session.scalars(stmt))


class ItemOrdenRepository(BaseRepository[ItemOrden]):
    model = ItemOrden


class HistorialEstadoOrdenRepository(BaseRepository[HistorialEstadoOrden]):
    model = HistorialEstadoOrden


__all__ = [
    "EstadoOrdenRepository",
    "HistorialEstadoOrdenRepository",
    "ItemOrdenRepository",
    "OrdenTrabajoRepository",
]
