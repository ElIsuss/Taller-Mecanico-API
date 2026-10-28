"""Reglas de negocio del módulo de vehículos."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflicto, NoEncontrado
from app.modules.clientes.service import obtener_cliente
from app.modules.ordenes.models import EstadoOrden, OrdenTrabajo
from app.modules.vehiculos.models import Vehiculo
from app.modules.vehiculos.schemas import VehiculoCreate, VehiculoUpdate


async def obtener_vehiculo(session: AsyncSession, vehiculo_id: int) -> Vehiculo:
    vehiculo = await session.scalar(
        select(Vehiculo).where(
            Vehiculo.id == vehiculo_id,
            Vehiculo.borrado_en.is_(None),
        )
    )
    if vehiculo is None:
        raise NoEncontrado("El vehículo no existe")
    return vehiculo


async def crear_vehiculo(session: AsyncSession, data: VehiculoCreate) -> Vehiculo:
    async with session.begin():
        await obtener_cliente(session, data.cliente_id)
        vehiculo = Vehiculo(**data.model_dump())
        session.add(vehiculo)
        await session.flush()
    return vehiculo


async def listar_vehiculos(
    session: AsyncSession,
    offset: int,
    limit: int,
    cliente_id: int | None = None,
) -> tuple[list[Vehiculo], int]:
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


async def actualizar_vehiculo(
    session: AsyncSession, vehiculo_id: int, data: VehiculoUpdate
) -> Vehiculo:
    async with session.begin():
        vehiculo = await obtener_vehiculo(session, vehiculo_id)
        cambios = data.model_dump(exclude_unset=True)
        if "cliente_id" in cambios:
            await obtener_cliente(session, cambios["cliente_id"])
        for campo, valor in cambios.items():
            setattr(vehiculo, campo, valor)
        await session.flush()
    return vehiculo


async def borrar_vehiculo(session: AsyncSession, vehiculo_id: int) -> None:
    async with session.begin():
        vehiculo = await obtener_vehiculo(session, vehiculo_id)
        abiertas = await session.scalar(
            select(func.count())
            .select_from(OrdenTrabajo)
            .join(EstadoOrden, OrdenTrabajo.estado == EstadoOrden.codigo)
            .where(
                OrdenTrabajo.vehiculo_id == vehiculo_id,
                EstadoOrden.es_final.is_(False),
            )
        )
        if int(abiertas or 0) > 0:
            raise Conflicto("No se puede dar de baja un vehículo con órdenes abiertas")
        vehiculo.borrado_en = datetime.now(timezone.utc)
        await session.flush()
