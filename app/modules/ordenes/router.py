"""Endpoints REST del catálogo de estados y de las órdenes de trabajo."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import requiere_rol
from app.core.pagination import Pagina, PaginaParams, construir_pagina
from app.modules.ordenes import service
from app.modules.ordenes.notificaciones import enviar_aviso_cliente
from app.modules.ordenes.schemas import (
    EstadoOrdenCodigo,
    EstadoOrdenRead,
    OrdenAccion,
    OrdenCreate,
    OrdenRead,
    OrdenUpdate,
)
from app.modules.ordenes.unit_of_work import OrdenUnitOfWork

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_orden_uow(session: SessionDep) -> OrdenUnitOfWork:
    return OrdenUnitOfWork(session=session)


OrdenUowDep = Annotated[OrdenUnitOfWork, Depends(get_orden_uow)]
OrdenId = Annotated[int, Path(ge=1)]

router_estados = APIRouter(prefix="/estados-orden", tags=["estados-orden"])
router = APIRouter(prefix="/ordenes", tags=["ordenes"])


@router_estados.get(
    "",
    response_model=Pagina[EstadoOrdenRead],
    summary="Listar estados de orden",
    description="Devuelve el catálogo de estados ordenado por posición.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"))],
)
async def listar_estados(
    uow: OrdenUowDep,
    params: Annotated[PaginaParams, Depends()],
) -> Pagina[EstadoOrdenRead]:
    estados, total = await service.listar_estados(uow, params.offset, params.size)
    return construir_pagina(
        [EstadoOrdenRead.model_validate(e) for e in estados], total, params
    )


@router_estados.get(
    "/{codigo}",
    response_model=EstadoOrdenRead,
    summary="Consultar estado de orden",
    description="Devuelve un estado del catálogo por su código.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"))],
)
async def obtener_estado(codigo: str, uow: OrdenUowDep) -> EstadoOrdenRead:
    estado = await service.obtener_estado(uow, codigo)
    return EstadoOrdenRead.model_validate(estado)


@router.get(
    "",
    response_model=Pagina[OrdenRead],
    summary="Listar órdenes",
    description="Devuelve las órdenes de forma paginada, filtrables por estado y vehículo.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"))],
)
async def listar_ordenes(
    uow: OrdenUowDep,
    params: Annotated[PaginaParams, Depends()],
    estado: Annotated[EstadoOrdenCodigo | None, Query()] = None,
    vehiculo_id: Annotated[int | None, Query(ge=1)] = None,
) -> Pagina[OrdenRead]:
    ordenes, total = await service.listar_ordenes(
        uow,
        params.offset,
        params.size,
        estado.value if estado is not None else None,
        vehiculo_id,
    )
    return construir_pagina(ordenes, total, params)


@router.post(
    "",
    response_model=OrdenRead,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir orden",
    description="Abre una orden PENDIENTE con sus ítems y el total calculado.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def crear_orden(data: OrdenCreate, uow: OrdenUowDep) -> OrdenRead:
    return await service.crear_orden(uow, data)


@router.get(
    "/{orden_id}",
    response_model=OrdenRead,
    summary="Consultar orden",
    description="Devuelve una orden con su estado, total e ítems.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"))],
)
async def obtener_orden(orden_id: OrdenId, uow: OrdenUowDep) -> OrdenRead:
    return await service.obtener_orden(uow, orden_id)


@router.patch(
    "/{orden_id}",
    response_model=OrdenRead,
    summary="Actualizar orden",
    description="Actualiza falla o mecánico mientras la orden está PENDIENTE.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def actualizar_orden(
    orden_id: OrdenId, data: OrdenUpdate, uow: OrdenUowDep
) -> OrdenRead:
    return await service.actualizar_orden(uow, orden_id, data)


@router.post(
    "/{orden_id}/iniciar",
    response_model=OrdenRead,
    summary="Iniciar orden",
    description="Pasa una orden PENDIENTE a EN_REPARACION.",
    dependencies=[Depends(requiere_rol("ADMIN", "MECANICO"))],
)
async def iniciar_orden(
    orden_id: OrdenId, data: OrdenAccion, uow: OrdenUowDep
) -> OrdenRead:
    return await service.iniciar_orden(uow, orden_id, data.usuario_id)


@router.post(
    "/{orden_id}/terminar",
    response_model=OrdenRead,
    summary="Terminar orden",
    description="Termina una orden EN_REPARACION y descuenta el stock de sus ítems.",
    dependencies=[Depends(requiere_rol("ADMIN", "MECANICO"))],
)
async def terminar_orden(
    orden_id: OrdenId,
    data: OrdenAccion,
    uow: OrdenUowDep,
    background_tasks: BackgroundTasks,
) -> OrdenRead:
    orden = await service.terminar_orden(uow, orden_id, data.usuario_id)
    background_tasks.add_task(
        enviar_aviso_cliente, orden.id, orden.cliente, orden.estado
    )
    return orden


@router.post(
    "/{orden_id}/cancelar",
    response_model=OrdenRead,
    summary="Cancelar orden",
    description="Cancela una orden PENDIENTE.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "CLIENTE"))],
)
async def cancelar_orden(
    orden_id: OrdenId,
    data: OrdenAccion,
    uow: OrdenUowDep,
    background_tasks: BackgroundTasks,
) -> OrdenRead:
    orden = await service.cancelar_orden(uow, orden_id, data.usuario_id)
    background_tasks.add_task(
        enviar_aviso_cliente, orden.id, orden.cliente, orden.estado
    )
    return orden
