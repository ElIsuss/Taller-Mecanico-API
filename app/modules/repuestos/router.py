"""Endpoints REST de repuestos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import requiere_rol
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
from app.modules.repuestos.unit_of_work import RepuestoUnitOfWork

router = APIRouter(prefix="/repuestos", tags=["repuestos"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_repuesto_uow(session: SessionDep) -> RepuestoUnitOfWork:
    return RepuestoUnitOfWork(session=session)


RepuestoUowDep = Annotated[RepuestoUnitOfWork, Depends(get_repuesto_uow)]
RepuestoId = Annotated[int, Path(ge=1)]


@router.get(
    "",
    response_model=Pagina[RepuestoRead],
    summary="Listar repuestos",
    description="Devuelve los repuestos vigentes, con búsqueda opcional por descripción.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"))],
)
async def listar_repuestos(
    uow: RepuestoUowDep,
    params: Annotated[PaginaParams, Depends()],
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> Pagina[RepuestoRead]:
    repuestos, total = await service.listar_repuestos(
        uow, params.offset, params.size, q
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
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def crear_repuesto(
    data: RepuestoCreate, uow: RepuestoUowDep
) -> RepuestoRead:
    repuesto = await service.crear_repuesto(uow, data)
    return RepuestoRead.model_validate(repuesto)


@router.get(
    "/{repuesto_id}",
    response_model=RepuestoRead,
    summary="Consultar repuesto",
    description="Devuelve un repuesto vigente por su identificador.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO", "CLIENTE"))],
)
async def obtener_repuesto(
    repuesto_id: RepuestoId, uow: RepuestoUowDep
) -> RepuestoRead:
    repuesto = await service.obtener_repuesto(uow, repuesto_id)
    return RepuestoRead.model_validate(repuesto)


@router.patch(
    "/{repuesto_id}",
    response_model=RepuestoRead,
    summary="Actualizar repuesto",
    description="Actualiza la descripción o el precio; el stock solo cambia por reposición.",
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def actualizar_repuesto(
    repuesto_id: RepuestoId, data: RepuestoUpdate, uow: RepuestoUowDep
) -> RepuestoRead:
    repuesto = await service.actualizar_repuesto(uow, repuesto_id, data)
    return RepuestoRead.model_validate(repuesto)


@router.delete(
    "/{repuesto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Dar de baja repuesto",
    description="Da de baja lógica un repuesto del catálogo.",
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def borrar_repuesto(repuesto_id: RepuestoId, uow: RepuestoUowDep) -> Response:
    await service.borrar_repuesto(uow, repuesto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{repuesto_id}/reponer",
    response_model=MovimientoStockRead,
    status_code=status.HTTP_200_OK,
    summary="Reponer stock",
    description="Registra un movimiento positivo y aumenta el stock del repuesto.",
    dependencies=[Depends(requiere_rol("ADMIN"))],
)
async def reponer_stock(
    repuesto_id: RepuestoId,
    data: ReposicionCreate,
    uow: RepuestoUowDep,
) -> MovimientoStockRead:
    movimiento = await service.reponer_stock(uow, repuesto_id, data)
    return MovimientoStockRead.model_validate(movimiento)


@router.get(
    "/{repuesto_id}/movimientos",
    response_model=Pagina[MovimientoStockRead],
    summary="Movimientos de stock",
    description="Devuelve los movimientos del repuesto, del más reciente al más antiguo.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO"))],
)
async def listar_movimientos(
    repuesto_id: RepuestoId,
    uow: RepuestoUowDep,
    params: Annotated[PaginaParams, Depends()],
) -> Pagina[MovimientoStockRead]:
    movimientos, total = await service.listar_movimientos(
        uow, repuesto_id, params.offset, params.size
    )
    return construir_pagina(
        [MovimientoStockRead.model_validate(m) for m in movimientos],
        total,
        params,
    )


@router.get(
    "/{repuesto_id}/precios",
    response_model=Pagina[HistorialPrecioRead],
    summary="Historial de precios",
    description="Devuelve los cambios de precio del repuesto, del más reciente al más antiguo.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION", "MECANICO"))],
)
async def listar_historial_precios(
    repuesto_id: RepuestoId,
    uow: RepuestoUowDep,
    params: Annotated[PaginaParams, Depends()],
) -> Pagina[HistorialPrecioRead]:
    historial, total = await service.listar_historial_precios(
        uow, repuesto_id, params.offset, params.size
    )
    return construir_pagina(
        [HistorialPrecioRead.model_validate(h) for h in historial], total, params
    )
