"""Reglas de negocio del módulo de repuestos."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NoEncontrado
from app.modules.auth.service import obtener_usuario
from app.modules.ordenes.models import HistorialPrecioRepuesto, MovimientoStock
from app.modules.repuestos.models import Repuesto
from app.modules.repuestos.schemas import (
    ReposicionCreate,
    RepuestoCreate,
    RepuestoUpdate,
)


def _escapar_like(texto: str) -> str:
    return (
        texto.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


async def obtener_repuesto(session: AsyncSession, repuesto_id: int) -> Repuesto:
    repuesto = await session.scalar(
        select(Repuesto).where(
            Repuesto.id == repuesto_id,
            Repuesto.borrado_en.is_(None),
        )
    )
    if repuesto is None:
        raise NoEncontrado("El repuesto no existe")
    return repuesto


async def crear_repuesto(session: AsyncSession, data: RepuestoCreate) -> Repuesto:
    async with session.begin():
        repuesto = Repuesto(**data.model_dump())
        session.add(repuesto)
        await session.flush()
    return repuesto


async def listar_repuestos(
    session: AsyncSession,
    offset: int,
    limit: int,
    busqueda: str | None = None,
) -> tuple[list[Repuesto], int]:
    filtros = [Repuesto.borrado_en.is_(None)]
    if busqueda:
        patron = f"%{_escapar_like(busqueda)}%"
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


async def actualizar_repuesto(
    session: AsyncSession, repuesto_id: int, data: RepuestoUpdate
) -> Repuesto:
    async with session.begin():
        repuesto = await obtener_repuesto(session, repuesto_id)
        cambios = data.model_dump(exclude_unset=True)
        usuario_id = cambios.pop("usuario_id", None)

        precio_nuevo = cambios.get("precio")
        if "precio" in cambios and precio_nuevo != repuesto.precio:
            await obtener_usuario(session, usuario_id)
            session.add(
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
        await session.flush()
    return repuesto


async def reponer_stock(
    session: AsyncSession, repuesto_id: int, data: ReposicionCreate
) -> MovimientoStock:
    async with session.begin():
        repuesto = await obtener_repuesto(session, repuesto_id)
        await obtener_usuario(session, data.usuario_id)
        movimiento = MovimientoStock(
            repuesto_id=repuesto.id,
            usuario_id=data.usuario_id,
            cantidad=data.cantidad,
            motivo=data.motivo,
            cuando=datetime.now(timezone.utc),
        )
        session.add(movimiento)
        repuesto.stock += data.cantidad
        await session.flush()
    return movimiento


async def borrar_repuesto(session: AsyncSession, repuesto_id: int) -> None:
    async with session.begin():
        repuesto = await obtener_repuesto(session, repuesto_id)
        repuesto.borrado_en = datetime.now(timezone.utc)
        await session.flush()


async def listar_historial_precios(
    session: AsyncSession,
    repuesto_id: int,
    offset: int,
    limit: int,
) -> tuple[list[HistorialPrecioRepuesto], int]:
    await obtener_repuesto(session, repuesto_id)
    total = await session.scalar(
        select(func.count())
        .select_from(HistorialPrecioRepuesto)
        .where(HistorialPrecioRepuesto.repuesto_id == repuesto_id)
    )
    result = await session.scalars(
        select(HistorialPrecioRepuesto)
        .where(HistorialPrecioRepuesto.repuesto_id == repuesto_id)
        .order_by(HistorialPrecioRepuesto.cuando.desc(), HistorialPrecioRepuesto.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result), int(total or 0)
