"""Reglas de negocio del módulo de clientes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflicto, NoEncontrado
from app.modules.auth.service import obtener_usuario
from app.modules.clientes.models import Cliente
from app.modules.clientes.schemas import ClienteCreate, ClienteUpdate
from app.modules.vehiculos.models import Vehiculo


async def obtener_cliente(session: AsyncSession, cliente_id: int) -> Cliente:
    cliente = await session.get(Cliente, cliente_id)
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
