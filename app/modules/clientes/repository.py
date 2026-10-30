"""Client-domain repository definitions."""

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.repository import BaseRepository, SoftDeleteRepository
from app.modules.clientes.models import Cliente, Vehiculo
from app.modules.ordenes.models import EstadoOrden, OrdenTrabajo


class ClienteRepository(BaseRepository[Cliente]):
    model = Cliente

    async def get_with_vehicles(self, cliente_id: int) -> Cliente | None:
        session = self._require_session()
        stmt = (
            select(Cliente)
            .options(selectinload(Cliente.vehiculos))
            .where(Cliente.id == cliente_id)
        )
        return await session.scalar(stmt)

    async def list_page(self, offset: int, limit: int) -> tuple[list[Cliente], int]:
        session = self._require_session()
        total = await session.scalar(select(func.count()).select_from(Cliente))
        result = await session.scalars(
            select(Cliente).order_by(Cliente.id).offset(offset).limit(limit)
        )
        return list(result), int(total or 0)

    async def count_vehicles(self, cliente_id: int) -> int:
        session = self._require_session()
        result = await session.scalar(
            select(func.count())
            .select_from(Vehiculo)
            .where(Vehiculo.cliente_id == cliente_id)
        )
        return int(result or 0)


class VehiculoRepository(SoftDeleteRepository[Vehiculo]):
    model = Vehiculo

    async def list_page(
        self, offset: int, limit: int, cliente_id: int | None = None
    ) -> tuple[list[Vehiculo], int]:
        session = self._require_session()
        filtros = [Vehiculo.borrado_en.is_(None)]
        if cliente_id is not None:
            filtros.append(Vehiculo.cliente_id == cliente_id)
        total = await session.scalar(
            select(func.count()).select_from(Vehiculo).where(*filtros)
        )
        result = await session.scalars(
            select(Vehiculo)
            .where(*filtros)
            .order_by(Vehiculo.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result), int(total or 0)

    async def count_open_orders(self, vehiculo_id: int) -> int:
        session = self._require_session()
        result = await session.scalar(
            select(func.count())
            .select_from(OrdenTrabajo)
            .join(EstadoOrden, OrdenTrabajo.estado == EstadoOrden.codigo)
            .where(
                OrdenTrabajo.vehiculo_id == vehiculo_id,
                EstadoOrden.es_final.is_(False),
            )
        )
        return int(result or 0)


__all__ = ["ClienteRepository", "VehiculoRepository"]
