"""Reglas de negocio del módulo de repuestos."""

from datetime import datetime, timezone
from typing import Protocol

from app.core.exceptions import NoEncontrado
from app.modules.repuestos.models import (
    HistorialPrecioRepuesto,
    MovimientoStock,
    Repuesto,
)
from app.modules.repuestos.schemas import (
    ReposicionCreate,
    RepuestoCreate,
    RepuestoUpdate,
)
from app.modules.repuestos.repository import MovimientoStockRepository
from app.modules.repuestos.unit_of_work import RepuestoUnitOfWork


class _StockUnitOfWork(Protocol):
    movimientos_stock: MovimientoStockRepository

    async def flush(self) -> None: ...


async def _obtener_repuesto(
    uow: RepuestoUnitOfWork, repuesto_id: int
) -> Repuesto:
    repuesto = await uow.repuestos.get_active_by_id(repuesto_id)
    if repuesto is None:
        raise NoEncontrado("El repuesto no existe")
    return repuesto


async def obtener_repuesto(
    uow: RepuestoUnitOfWork, repuesto_id: int
) -> Repuesto:
    async with uow:
        return await _obtener_repuesto(uow, repuesto_id)


async def crear_repuesto(
    uow: RepuestoUnitOfWork, data: RepuestoCreate
) -> Repuesto:
    async with uow:
        if data.stock_inicial > 0:
            if await uow.usuarios.get_by_id(data.usuario_id) is None:
                raise NoEncontrado("El usuario indicado no existe")
        repuesto = Repuesto(
            codigo=data.codigo,
            descripcion=data.descripcion,
            precio=data.precio,
            stock=0,
        )
        await uow.repuestos.add(repuesto)
        await uow.flush()
        if data.stock_inicial > 0:
            await registrar_movimiento_stock(
                uow,
                repuesto,
                cantidad=data.stock_inicial,
                motivo="Stock inicial",
                usuario_id=data.usuario_id,
            )
        return repuesto


async def registrar_movimiento_stock(
    uow: _StockUnitOfWork,
    repuesto: Repuesto,
    cantidad: int,
    motivo: str,
    usuario_id: int,
    orden_id: int | None = None,
) -> MovimientoStock:
    """Punto único de escritura del stock (RN-14)."""
    repuesto.stock += cantidad
    movimiento = MovimientoStock(
        repuesto_id=repuesto.id,
        orden_id=orden_id,
        usuario_id=usuario_id,
        cantidad=cantidad,
        motivo=motivo,
        cuando=datetime.now(timezone.utc),
    )
    await uow.movimientos_stock.add(movimiento)
    await uow.flush()
    return movimiento


async def listar_repuestos(
    uow: RepuestoUnitOfWork,
    offset: int,
    limit: int,
    q: str | None = None,
) -> tuple[list[Repuesto], int]:
    async with uow:
        return await uow.repuestos.list_page(offset, limit, q)


async def actualizar_repuesto(
    uow: RepuestoUnitOfWork, repuesto_id: int, data: RepuestoUpdate
) -> Repuesto:
    async with uow:
        repuesto = await _obtener_repuesto(uow, repuesto_id)
        cambios = data.model_dump(exclude_unset=True)
        usuario_id = cambios.pop("usuario_id", None)

        precio_nuevo = cambios.get("precio")
        if "precio" in cambios and precio_nuevo != repuesto.precio:
            if usuario_id is None or await uow.usuarios.get_by_id(usuario_id) is None:
                raise NoEncontrado("El usuario indicado no existe")
            await uow.historial_precios.add(
                HistorialPrecioRepuesto(
                    repuesto_id=repuesto.id,
                    usuario_id=usuario_id,
                    precio_anterior=repuesto.precio,
                    precio_nuevo=precio_nuevo,
                    cuando=datetime.now(timezone.utc),
                )
            )

        for campo, valor in cambios.items():
            setattr(repuesto, campo, valor)
        await uow.flush()
        return repuesto


async def reponer_stock(
    uow: RepuestoUnitOfWork, repuesto_id: int, data: ReposicionCreate
) -> MovimientoStock:
    async with uow:
        repuesto = await _obtener_repuesto(uow, repuesto_id)
        if await uow.usuarios.get_by_id(data.usuario_id) is None:
            raise NoEncontrado("El usuario indicado no existe")
        return await registrar_movimiento_stock(
            uow,
            repuesto,
            cantidad=data.cantidad,
            motivo=data.motivo,
            usuario_id=data.usuario_id,
        )


async def borrar_repuesto(uow: RepuestoUnitOfWork, repuesto_id: int) -> None:
    async with uow:
        repuesto = await _obtener_repuesto(uow, repuesto_id)
        await uow.repuestos.soft_delete(repuesto)


async def listar_historial_precios(
    uow: RepuestoUnitOfWork,
    repuesto_id: int,
    offset: int,
    limit: int,
) -> tuple[list[HistorialPrecioRepuesto], int]:
    async with uow:
        await _obtener_repuesto(uow, repuesto_id)
        return await uow.historial_precios.list_for_repuesto(
            repuesto_id, offset, limit
        )


async def listar_movimientos(
    uow: RepuestoUnitOfWork,
    repuesto_id: int,
    offset: int,
    limit: int,
) -> tuple[list[MovimientoStock], int]:
    async with uow:
        await _obtener_repuesto(uow, repuesto_id)
        return await uow.movimientos_stock.list_for_repuesto(
            repuesto_id, offset, limit
        )
