"""Reglas de negocio del catálogo de estados y de las órdenes de trabajo."""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.exceptions import Conflicto, Invalido, NoEncontrado
from app.modules.ordenes.models import (
    EstadoOrden,
    HistorialEstadoOrden,
    ItemOrden,
    OrdenTrabajo,
)
from app.modules.ordenes.schemas import (
    HistorialEstadoOrdenRead,
    ItemOrdenRead,
    OrdenCreate,
    OrdenRead,
    OrdenUpdate,
)
from app.modules.ordenes.unit_of_work import OrdenUnitOfWork
from app.modules.repuestos.models import Repuesto
from app.modules.repuestos.service import registrar_movimiento_stock

PENDIENTE = "PENDIENTE"
EN_REPARACION = "EN_REPARACION"
TERMINADA = "TERMINADA"
CANCELADA = "CANCELADA"


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


async def _obtener_estado(uow: OrdenUnitOfWork, codigo: str) -> EstadoOrden:
    estado = await uow.estados.get_by_id(codigo)
    if estado is None:
        raise Conflicto("El catálogo de estados de orden está incompleto")
    return estado


def _a_read(orden: OrdenTrabajo) -> OrdenRead:
    return OrdenRead(
        id=orden.id,
        estado=orden.estado,
        patente=orden.vehiculo.patente,
        total=orden.total,
        creada_en=orden.creada_en,
        mecanico_id=orden.mecanico_id,
        falla=orden.falla,
        cliente=orden.vehiculo.cliente.nombre,
        items=[
            ItemOrdenRead(
                repuesto_id=item.repuesto_id,
                codigo=item.repuesto.codigo,
                descripcion=item.repuesto.descripcion,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                subtotal=(item.precio_unitario * item.cantidad).quantize(
                    Decimal("0.01")
                ),
            )
            for item in orden.items
        ],
        historial=[
            HistorialEstadoOrdenRead.model_validate(registro)
            for registro in sorted(
                orden.historial_estados,
                key=lambda registro: (registro.cuando, registro.id or 0),
            )
        ],
    )


async def _cargar_orden(
    uow: OrdenUnitOfWork, orden_id: int, bloquear: bool = False
) -> OrdenTrabajo:
    orden = await uow.ordenes.get_loaded(orden_id, lock=bloquear)
    if orden is None:
        raise NoEncontrado("La orden no existe")
    return orden


async def _cambiar_estado(
    uow: OrdenUnitOfWork,
    orden: OrdenTrabajo,
    hasta: str,
    usuario_id: int,
) -> None:
    await _obtener_estado(uow, hasta)
    registro = HistorialEstadoOrden(
        orden_id=orden.id,
        desde_estado=orden.estado,
        hasta_estado=hasta,
        usuario_id=usuario_id,
        cuando=_ahora(),
    )
    await uow.historial_estados.add(registro)
    orden.historial_estados.append(registro)
    orden.estado = hasta


async def listar_estados(
    uow: OrdenUnitOfWork, offset: int, limit: int
) -> tuple[list[EstadoOrden], int]:
    async with uow:
        return await uow.estados.list_page(offset, limit)


async def obtener_estado(uow: OrdenUnitOfWork, codigo: str) -> EstadoOrden:
    async with uow:
        estado = await uow.estados.get_by_id(codigo)
        if estado is None:
            raise NoEncontrado("El estado no existe")
        return estado


async def crear_orden(uow: OrdenUnitOfWork, data: OrdenCreate) -> OrdenRead:
    async with uow:
        await _obtener_estado(uow, PENDIENTE)

        vehiculo = await uow.ordenes.get_vehicle_with_client(data.vehiculo_id)
        if vehiculo is None:
            raise Conflicto("El vehículo indicado no existe")
        if vehiculo.borrado_en is not None:
            raise Conflicto("El vehículo está dado de baja")

        usuario_id = data.usuario_id or vehiculo.cliente.usuario_id
        if usuario_id is None:
            raise Invalido("No se pudo determinar el usuario que abre la orden")
        if await uow.usuarios.get_by_id(usuario_id) is None:
            raise NoEncontrado("El usuario indicado no existe")

        repuesto_ids = [item.repuesto_id for item in data.items]
        repuestos = await uow.ordenes.get_repuestos(repuesto_ids)
        por_id = {repuesto.id: repuesto for repuesto in repuestos}
        for repuesto_id in repuesto_ids:
            repuesto = por_id.get(repuesto_id)
            if repuesto is None:
                raise Conflicto(f"El repuesto {repuesto_id} no existe")
            if repuesto.borrado_en is not None:
                raise Conflicto(f"El repuesto {repuesto.codigo} está dado de baja")

        orden = OrdenTrabajo(
            vehiculo_id=data.vehiculo_id,
            mecanico_id=None,
            estado=PENDIENTE,
            falla=data.falla,
            creada_en=_ahora(),
            total=Decimal("0"),
        )
        await uow.ordenes.add(orden)
        await uow.flush()

        total = Decimal("0")
        for item_data in data.items:
            repuesto = por_id[item_data.repuesto_id]
            await uow.items.add(
                ItemOrden(
                    orden_id=orden.id,
                    repuesto_id=repuesto.id,
                    cantidad=item_data.cantidad,
                    precio_unitario=repuesto.precio,
                )
            )
            total += repuesto.precio * item_data.cantidad

        orden.total = total.quantize(Decimal("0.01"))
        await uow.historial_estados.add(
            HistorialEstadoOrden(
                orden_id=orden.id,
                desde_estado=None,
                hasta_estado=PENDIENTE,
                usuario_id=usuario_id,
                cuando=_ahora(),
            )
        )
        await uow.flush()

        return _a_read(await _cargar_orden(uow, orden.id))


async def listar_ordenes(
    uow: OrdenUnitOfWork,
    offset: int,
    limit: int,
    estado: str | None = None,
    vehiculo_id: int | None = None,
) -> tuple[list[OrdenRead], int]:
    async with uow:
        ordenes, total = await uow.ordenes.list_page(
            offset, limit, estado, vehiculo_id
        )
        return [_a_read(orden) for orden in ordenes], total


async def obtener_orden(uow: OrdenUnitOfWork, orden_id: int) -> OrdenRead:
    async with uow:
        return _a_read(await _cargar_orden(uow, orden_id))


async def actualizar_orden(
    uow: OrdenUnitOfWork, orden_id: int, data: OrdenUpdate
) -> OrdenRead:
    async with uow:
        orden = await _cargar_orden(uow, orden_id)
        if orden.estado != PENDIENTE:
            raise Conflicto("Solo se puede actualizar una orden en estado PENDIENTE")
        cambios = data.model_dump(exclude_unset=True)
        mecanico_id = cambios.get("mecanico_id")
        if mecanico_id is not None:
            if await uow.usuarios.get_by_id(mecanico_id) is None:
                raise NoEncontrado("El usuario indicado no existe")
        for campo, valor in cambios.items():
            setattr(orden, campo, valor)
        await uow.flush()
        return _a_read(orden)


async def iniciar_orden(
    uow: OrdenUnitOfWork, orden_id: int, usuario_id: int
) -> OrdenRead:
    async with uow:
        orden = await _cargar_orden(uow, orden_id)
        if orden.estado != PENDIENTE:
            raise Conflicto("Solo se puede iniciar una orden en estado PENDIENTE")
        if await uow.usuarios.get_by_id(usuario_id) is None:
            raise NoEncontrado("El usuario indicado no existe")
        if orden.mecanico_id is None:
            orden.mecanico_id = usuario_id
        await _cambiar_estado(uow, orden, EN_REPARACION, usuario_id)
        await uow.flush()
        return _a_read(orden)


async def cancelar_orden(
    uow: OrdenUnitOfWork, orden_id: int, usuario_id: int
) -> OrdenRead:
    async with uow:
        orden = await _cargar_orden(uow, orden_id)
        if orden.estado != PENDIENTE:
            raise Conflicto("Solo se puede cancelar una orden en estado PENDIENTE")
        if await uow.usuarios.get_by_id(usuario_id) is None:
            raise NoEncontrado("El usuario indicado no existe")
        await _cambiar_estado(uow, orden, CANCELADA, usuario_id)
        await uow.flush()
        return _a_read(orden)


async def terminar_orden(
    uow: OrdenUnitOfWork, orden_id: int, usuario_id: int
) -> OrdenRead:
    async with uow:
        orden = await _cargar_orden(uow, orden_id, bloquear=True)
        if orden.estado != EN_REPARACION:
            raise Conflicto("Solo se puede terminar una orden en estado EN_REPARACION")
        if await uow.usuarios.get_by_id(usuario_id) is None:
            raise NoEncontrado("El usuario indicado no existe")
        await _obtener_estado(uow, TERMINADA)

        repuesto_ids = [item.repuesto_id for item in orden.items]
        repuestos = await uow.ordenes.get_repuestos(repuesto_ids, lock=True)
        por_id = {repuesto.id: repuesto for repuesto in repuestos}

        for item in orden.items:
            repuesto = por_id.get(item.repuesto_id)
            if repuesto is None:
                raise Conflicto("Un repuesto de la orden ya no está disponible")
            if repuesto.stock < item.cantidad:
                raise Conflicto(
                    f"Stock insuficiente para el repuesto {repuesto.codigo}"
                )

        for item in orden.items:
            repuesto = por_id[item.repuesto_id]
            await registrar_movimiento_stock(
                uow,
                repuesto,
                cantidad=-item.cantidad,
                motivo="terminación",
                usuario_id=usuario_id,
                orden_id=orden.id,
            )

        await _cambiar_estado(uow, orden, TERMINADA, usuario_id)
        await uow.flush()
        return _a_read(orden)
