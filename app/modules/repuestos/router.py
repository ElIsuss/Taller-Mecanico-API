"""Endpoints REST de repuestos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagina, PaginaParams, construir_pagina
from app.modules.repuestos import service
from app.modules.repuestos.schemas import (
    HistorialPrecioRead,
    MovimientoStockRead,
    ReposicionCreate,
    RepuestoCreate,
    RepuestoRead,
    RepuestoUpdate,
)

router = APIRouter(prefix="/repuestos", tags=["repuestos"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
RepuestoId = Annotated[int, Path(ge=1)]


@router.get(
    "",
    response_model=Pagina[RepuestoRead],
    summary="Listar repuestos",
    description="Devuelve los repuestos vigentes, con búsqueda opcional por descripción.",
)
async def listar_repuestos(
    session: SessionDep,
    params: Annotated[PaginaParams, Depends()],
    busqueda: Annotated[str | None, Query(max_length=200)] = None,
) -> Pagina[RepuestoRead]:
    repuestos, total = await service.listar_repuestos(
        session, params.offset, params.size, busqueda
    )
    return construir_pagina(
        [RepuestoRead.model_validate(r) for r in repuestos], total, params
    )


@router.post(
    "",
    response_model=RepuestoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear repuesto",
    description="Da de alta un repuesto del catálogo.",
)
async def crear_repuesto(
    data: RepuestoCreate, session: SessionDep
) -> RepuestoRead:
    repuesto = await service.crear_repuesto(session, data)
    return RepuestoRead.model_validate(repuesto)


@router.get(
    "/{repuesto_id}",
    response_model=RepuestoRead,
    summary="Consultar repuesto",
    description="Devuelve un repuesto vigente por su identificador.",
)
async def obtener_repuesto(
    repuesto_id: RepuestoId, session: SessionDep
) -> RepuestoRead:
    repuesto = await service.obtener_repuesto(session, repuesto_id)
    return RepuestoRead.model_validate(repuesto)


@router.patch(
    "/{repuesto_id}",
    response_model=RepuestoRead,
    summary="Actualizar repuesto",
    description="Actualiza código, descripción o precio; el stock solo cambia por reposición.",
)
async def actualizar_repuesto(
    repuesto_id: RepuestoId, data: RepuestoUpdate, session: SessionDep
) -> RepuestoRead:
    repuesto = await service.actualizar_repuesto(session, repuesto_id, data)
    return RepuestoRead.model_validate(repuesto)


@router.delete(
    "/{repuesto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Dar de baja repuesto",
    description="Da de baja lógica un repuesto del catálogo.",
)
async def borrar_repuesto(repuesto_id: RepuestoId, session: SessionDep) -> Response:
    await service.borrar_repuesto(session, repuesto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{repuesto_id}/reposiciones",
    response_model=MovimientoStockRead,
    status_code=status.HTTP_201_CREATED,
    summary="Reponer stock",
    description="Registra un movimiento positivo y aumenta el stock del repuesto.",
)
async def reponer_stock(
    repuesto_id: RepuestoId,
    data: ReposicionCreate,
    session: SessionDep,
) -> MovimientoStockRead:
    movimiento = await service.reponer_stock(session, repuesto_id, data)
    return MovimientoStockRead.model_validate(movimiento)


@router.get(
    "/{repuesto_id}/historial-precios",
    response_model=Pagina[HistorialPrecioRead],
    summary="Historial de precios",
    description="Devuelve los cambios de precio del repuesto, del más reciente al más antiguo.",
)
async def listar_historial_precios(
    repuesto_id: RepuestoId,
    session: SessionDep,
    params: Annotated[PaginaParams, Depends()],
) -> Pagina[HistorialPrecioRead]:
    historial, total = await service.listar_historial_precios(
        session, repuesto_id, params.offset, params.size
    )
    return construir_pagina(
        [HistorialPrecioRead.model_validate(h) for h in historial], total, params
    )
