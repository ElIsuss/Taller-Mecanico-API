"""Reglas de negocio del módulo de clientes y vehículos."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import Conflicto, NoEncontrado
from app.modules.clientes.models import Cliente, Vehiculo
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    VehiculoCreate,
    VehiculoUpdate,
)
from app.modules.ordenes.models import EstadoOrden, OrdenTrabajo
from app.modules.usuarios.service import obtener_usuario


async def obtener_cliente(session: AsyncSession, cliente_id: int) -> Cliente:
    cliente = await session.scalar(
        select(Cliente)
        .options(selectinload(Cliente.vehiculos))
        .where(Cliente.id == cliente_id)
    )
    if cliente is None:
        raise NoEncontrado("El cliente no existe")
    return cliente


async def crear_cliente(session: AsyncSession, data: ClienteCreate) -> Cliente:
    async with session.begin():
        if data.usuario_id is not None:
            await obtener_usuario(session, data.usuario_id)
        cliente = Cliente(**data.model_dump())
        session.add(cliente)
        await session.flush()
    return cliente


async def listar_clientes(
    session: AsyncSession, offset: int, limit: int
) -> tuple[list[Cliente], int]:
    total = await session.scalar(select(func.count()).select_from(Cliente))
    result = await session.scalars(
        select(Cliente).order_by(Cliente.id).offset(offset).limit(limit)
    )
    return list(result), int(total or 0)


async def actualizar_cliente(
    session: AsyncSession, cliente_id: int, data: ClienteUpdate
) -> Cliente:
    async with session.begin():
        cliente = await obtener_cliente(session, cliente_id)
        cambios = data.model_dump(exclude_unset=True)
        if "usuario_id" in cambios and cambios["usuario_id"] is not None:
            await obtener_usuario(session, cambios["usuario_id"])
        for campo, valor in cambios.items():
            setattr(cliente, campo, valor)
        await session.flush()
    return cliente


async def borrar_cliente(session: AsyncSession, cliente_id: int) -> None:
    async with session.begin():
        cliente = await obtener_cliente(session, cliente_id)
        cantidad = await session.scalar(
            select(func.count())
            .select_from(Vehiculo)
            .where(Vehiculo.cliente_id == cliente_id)
        )
        if int(cantidad or 0) > 0:
            raise Conflicto("No se puede borrar un cliente con vehículos asociados")
        await session.delete(cliente)
        await session.flush()


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
