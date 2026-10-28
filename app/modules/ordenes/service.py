"""Reglas de negocio del catálogo de estados y de las órdenes de trabajo."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import Conflicto, NoEncontrado
from app.modules.auth.service import obtener_usuario
from app.modules.ordenes.models import (
    EstadoOrden,
    HistorialEstadoOrden,
    ItemOrden,
    MovimientoStock,
    OrdenTrabajo,
)
from app.modules.ordenes.schemas import (
    ItemOrdenRead,
    OrdenCreate,
    OrdenRead,
    OrdenUpdate,
)
from app.modules.repuestos.models import Repuesto
from app.modules.vehiculos.models import Vehiculo

PENDIENTE = "PENDIENTE"
EN_REPARACION = "EN_REPARACION"
TERMINADA = "TERMINADA"
CANCELADA = "CANCELADA"


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


async def _obtener_estado(session: AsyncSession, codigo: str) -> EstadoOrden:
    estado = await session.get(EstadoOrden, codigo)
    if estado is None:
        raise Conflicto("El catálogo de estados de orden está incompleto")
    return estado


def _a_read(orden: OrdenTrabajo, items: list[ItemOrden]) -> OrdenRead:
    return OrdenRead(
        id=orden.id,
        vehiculo_id=orden.vehiculo_id,
        mecanico_id=orden.mecanico_id,
        estado=orden.estado,
        falla=orden.falla,
        creada_en=orden.creada_en,
        total=orden.total,
        items=[ItemOrdenRead.model_validate(item) for item in items],
    )


async def _cargar_orden(
    session: AsyncSession, orden_id: int, bloquear: bool = False
) -> OrdenTrabajo:
    stmt = (
        select(OrdenTrabajo)
        .options(selectinload(OrdenTrabajo.items))
        .where(OrdenTrabajo.id == orden_id)
    )
    if bloquear:
        stmt = stmt.with_for_update()
    orden = await session.scalar(stmt)
    if orden is None:
        raise NoEncontrado("La orden no existe")
    return orden


async def _cambiar_estado(
    session: AsyncSession,
    orden: OrdenTrabajo,
    hasta: str,
    usuario_id: int,
) -> None:
    await _obtener_estado(session, hasta)
    session.add(
        HistorialEstadoOrden(
            orden_id=orden.id,
            desde_estado=orden.estado,
            hasta_estado=hasta,
            usuario_id=usuario_id,
            cuando=_ahora(),
        )
    )
    orden.estado = hasta


async def listar_estados(
    session: AsyncSession, offset: int, limit: int
) -> tuple[list[EstadoOrden], int]:
    total = await session.scalar(select(func.count()).select_from(EstadoOrden))
    result = await session.scalars(
        select(EstadoOrden)
        .order_by(EstadoOrden.posicion)
        .offset(offset)
        .limit(limit)
    )
    return list(result), int(total or 0)


async def obtener_estado(session: AsyncSession, codigo: str) -> EstadoOrden:
    estado = await session.get(EstadoOrden, codigo)
    if estado is None:
        raise NoEncontrado("El estado no existe")
    return estado


async def crear_orden(session: AsyncSession, data: OrdenCreate) -> OrdenRead:
    async with session.begin():
        await obtener_usuario(session, data.usuario_id)
        await _obtener_estado(session, PENDIENTE)

        vehiculo = await session.get(Vehiculo, data.vehiculo_id)
        if vehiculo is None:
            raise NoEncontrado("El vehículo no existe")
        if vehiculo.borrado_en is not None:
            raise Conflicto("El vehículo está dado de baja")

        if data.mecanico_id is not None:
            await obtener_usuario(session, data.mecanico_id)

        repuesto_ids = [item.repuesto_id for item in data.items]
        repuestos = list(
            await session.scalars(
                select(Repuesto).where(Repuesto.id.in_(repuesto_ids))
            )
        )
        por_id = {repuesto.id: repuesto for repuesto in repuestos}
        for repuesto_id in repuesto_ids:
            repuesto = por_id.get(repuesto_id)
            if repuesto is None:
                raise NoEncontrado(f"El repuesto {repuesto_id} no existe")
            if repuesto.borrado_en is not None:
                raise Conflicto(f"El repuesto {repuesto.codigo} está dado de baja")

        orden = OrdenTrabajo(
            vehiculo_id=data.vehiculo_id,
            mecanico_id=data.mecanico_id,
            estado=PENDIENTE,
            falla=data.falla,
            creada_en=_ahora(),
            total=Decimal("0"),
        )
        session.add(orden)
        await session.flush()

        items: list[ItemOrden] = []
        total = Decimal("0")
        for item_data in data.items:
            repuesto = por_id[item_data.repuesto_id]
            item = ItemOrden(
                orden_id=orden.id,
                repuesto_id=repuesto.id,
                cantidad=item_data.cantidad,
                precio_unitario=repuesto.precio,
            )
            session.add(item)
            items.append(item)
            total += repuesto.precio * item_data.cantidad

        orden.total = total.quantize(Decimal("0.01"))
        session.add(
            HistorialEstadoOrden(
                orden_id=orden.id,
                desde_estado=None,
                hasta_estado=PENDIENTE,
                usuario_id=data.usuario_id,
                cuando=_ahora(),
            )
        )
        await session.flush()

    return _a_read(orden, items)


async def listar_ordenes(
    session: AsyncSession,
    offset: int,
    limit: int,
    estado: str | None = None,
    vehiculo_id: int | None = None,
) -> tuple[list[OrdenRead], int]:
    filtros = []
    if estado is not None:
        filtros.append(OrdenTrabajo.estado == estado)
    if vehiculo_id is not None:
        filtros.append(OrdenTrabajo.vehiculo_id == vehiculo_id)
    total = await session.scalar(
        select(func.count()).select_from(OrdenTrabajo).where(*filtros)
    )
    result = await session.scalars(
        select(OrdenTrabajo)
        .options(selectinload(OrdenTrabajo.items))
        .where(*filtros)
        .order_by(OrdenTrabajo.id.desc())
        .offset(offset)
        .limit(limit)
    )
    ordenes = [_a_read(orden, orden.items) for orden in result]
    return ordenes, int(total or 0)


async def obtener_orden(session: AsyncSession, orden_id: int) -> OrdenRead:
    orden = await _cargar_orden(session, orden_id)
    return _a_read(orden, orden.items)


async def actualizar_orden(
    session: AsyncSession, orden_id: int, data: OrdenUpdate
) -> OrdenRead:
    async with session.begin():
        orden = await _cargar_orden(session, orden_id)
        if orden.estado != PENDIENTE:
            raise Conflicto("Solo se puede actualizar una orden en estado PENDIENTE")
        cambios = data.model_dump(exclude_unset=True)
        if cambios.get("mecanico_id") is not None:
            await obtener_usuario(session, cambios["mecanico_id"])
        for campo, valor in cambios.items():
            setattr(orden, campo, valor)
        await session.flush()
        return _a_read(orden, orden.items)


async def iniciar_orden(
    session: AsyncSession, orden_id: int, usuario_id: int
) -> OrdenRead:
    async with session.begin():
        orden = await _cargar_orden(session, orden_id)
        if orden.estado != PENDIENTE:
            raise Conflicto("Solo se puede iniciar una orden en estado PENDIENTE")
        await obtener_usuario(session, usuario_id)
        if orden.mecanico_id is None:
            orden.mecanico_id = usuario_id
        await _cambiar_estado(session, orden, EN_REPARACION, usuario_id)
        await session.flush()
        return _a_read(orden, orden.items)


async def cancelar_orden(
    session: AsyncSession, orden_id: int, usuario_id: int
) -> OrdenRead:
    async with session.begin():
        orden = await _cargar_orden(session, orden_id)
        if orden.estado != PENDIENTE:
            raise Conflicto("Solo se puede cancelar una orden en estado PENDIENTE")
        await obtener_usuario(session, usuario_id)
        await _cambiar_estado(session, orden, CANCELADA, usuario_id)
        await session.flush()
        return _a_read(orden, orden.items)


async def terminar_orden(
    session: AsyncSession, orden_id: int, usuario_id: int
) -> OrdenRead:
    async with session.begin():
        orden = await _cargar_orden(session, orden_id, bloquear=True)
        if orden.estado != EN_REPARACION:
            raise Conflicto("Solo se puede terminar una orden en estado EN_REPARACION")
        await obtener_usuario(session, usuario_id)
        await _obtener_estado(session, TERMINADA)

        repuesto_ids = [item.repuesto_id for item in orden.items]
        repuestos = list(
            await session.scalars(
                select(Repuesto)
                .where(Repuesto.id.in_(repuesto_ids))
                .with_for_update()
            )
        )
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
            repuesto.stock -= item.cantidad
            session.add(
                MovimientoStock(
                    repuesto_id=repuesto.id,
                    orden_id=orden.id,
                    usuario_id=usuario_id,
                    cantidad=-item.cantidad,
                    motivo="terminación",
                    cuando=_ahora(),
                )
            )

        await _cambiar_estado(session, orden, TERMINADA, usuario_id)
        await session.flush()
        return _a_read(orden, orden.items)
