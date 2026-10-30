"""Reglas de negocio del módulo de clientes y vehículos."""

from app.core.exceptions import Conflicto, NoEncontrado
from app.modules.clientes.models import Cliente, Vehiculo
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    VehiculoCreate,
    VehiculoUpdate,
)
from app.modules.clientes.unit_of_work import ClienteUnitOfWork


async def _obtener_cliente(uow: ClienteUnitOfWork, cliente_id: int) -> Cliente:
    cliente = await uow.clientes.get_with_vehicles(cliente_id)
    if cliente is None:
        raise NoEncontrado("El cliente no existe")
    return cliente


async def _obtener_vehiculo(uow: ClienteUnitOfWork, vehiculo_id: int) -> Vehiculo:
    vehiculo = await uow.vehiculos.get_active_by_id(vehiculo_id)
    if vehiculo is None:
        raise NoEncontrado("El vehículo no existe")
    return vehiculo


async def obtener_cliente(uow: ClienteUnitOfWork, cliente_id: int) -> Cliente:
    async with uow:
        return await _obtener_cliente(uow, cliente_id)


async def crear_cliente(uow: ClienteUnitOfWork, data: ClienteCreate) -> Cliente:
    async with uow:
        if data.usuario_id is not None:
            if await uow.usuarios.get_by_id(data.usuario_id) is None:
                raise NoEncontrado("El usuario indicado no existe")
        cliente = Cliente(**data.model_dump())
        await uow.clientes.add(cliente)
        await uow.flush()
        return cliente


async def listar_clientes(
    uow: ClienteUnitOfWork, offset: int, limit: int
) -> tuple[list[Cliente], int]:
    async with uow:
        return await uow.clientes.list_page(offset, limit)


async def actualizar_cliente(
    uow: ClienteUnitOfWork, cliente_id: int, data: ClienteUpdate
) -> Cliente:
    async with uow:
        cliente = await _obtener_cliente(uow, cliente_id)
        cambios = data.model_dump(exclude_unset=True)
        usuario_id = cambios.get("usuario_id")
        if usuario_id is not None and await uow.usuarios.get_by_id(usuario_id) is None:
            raise NoEncontrado("El usuario indicado no existe")
        for campo, valor in cambios.items():
            setattr(cliente, campo, valor)
        await uow.flush()
        return cliente


async def borrar_cliente(uow: ClienteUnitOfWork, cliente_id: int) -> None:
    async with uow:
        cliente = await _obtener_cliente(uow, cliente_id)
        if await uow.clientes.count_vehicles(cliente_id) > 0:
            raise Conflicto("No se puede borrar un cliente con vehículos asociados")
        await uow.clientes.remove(cliente)


async def obtener_vehiculo(uow: ClienteUnitOfWork, vehiculo_id: int) -> Vehiculo:
    async with uow:
        return await _obtener_vehiculo(uow, vehiculo_id)


async def crear_vehiculo(uow: ClienteUnitOfWork, data: VehiculoCreate) -> Vehiculo:
    async with uow:
        await _obtener_cliente(uow, data.cliente_id)
        vehiculo = Vehiculo(**data.model_dump())
        await uow.vehiculos.add(vehiculo)
        await uow.flush()
        return vehiculo


async def listar_vehiculos(
    uow: ClienteUnitOfWork,
    offset: int,
    limit: int,
    cliente_id: int | None = None,
) -> tuple[list[Vehiculo], int]:
    async with uow:
        return await uow.vehiculos.list_page(offset, limit, cliente_id)


async def actualizar_vehiculo(
    uow: ClienteUnitOfWork, vehiculo_id: int, data: VehiculoUpdate
) -> Vehiculo:
    async with uow:
        vehiculo = await _obtener_vehiculo(uow, vehiculo_id)
        cambios = data.model_dump(exclude_unset=True)
        if "cliente_id" in cambios:
            await _obtener_cliente(uow, cambios["cliente_id"])
        for campo, valor in cambios.items():
            setattr(vehiculo, campo, valor)
        await uow.flush()
        return vehiculo


async def borrar_vehiculo(uow: ClienteUnitOfWork, vehiculo_id: int) -> None:
    async with uow:
        vehiculo = await _obtener_vehiculo(uow, vehiculo_id)
        if await uow.vehiculos.count_open_orders(vehiculo_id) > 0:
            raise Conflicto("No se puede dar de baja un vehículo con órdenes abiertas")
        await uow.vehiculos.soft_delete(vehiculo)
