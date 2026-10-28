"""Endpoints REST de vehículos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagina, PaginaParams, construir_pagina
from app.modules.vehiculos import service
from app.modules.vehiculos.schemas import (
    VehiculoCreate,
    VehiculoRead,
    VehiculoUpdate,
)

router = APIRouter(prefix="/vehiculos", tags=["vehiculos"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
VehiculoId = Annotated[int, Path(ge=1)]


@router.get(
    "",
    response_model=Pagina[VehiculoRead],
    summary="Listar vehículos",
    description="Devuelve los vehículos vigentes de forma paginada.",
)
async def listar_vehiculos(
    session: SessionDep,
    params: Annotated[PaginaParams, Depends()],
    cliente_id: Annotated[int | None, Query(ge=1)] = None,
) -> Pagina[VehiculoRead]:
    vehiculos, total = await service.listar_vehiculos(
        session, params.offset, params.size, cliente_id
    )
    return construir_pagina(
        [VehiculoRead.model_validate(v) for v in vehiculos], total, params
    )


@router.post(
    "",
    response_model=VehiculoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear vehículo",
    description="Da de alta un vehículo asociado a un cliente.",
)
async def crear_vehiculo(
    data: VehiculoCreate, session: SessionDep
) -> VehiculoRead:
    vehiculo = await service.crear_vehiculo(session, data)
    return VehiculoRead.model_validate(vehiculo)


@router.get(
    "/{vehiculo_id}",
    response_model=VehiculoRead,
    summary="Consultar vehículo",
    description="Devuelve un vehículo vigente por su identificador.",
)
async def obtener_vehiculo(
    vehiculo_id: VehiculoId, session: SessionDep
) -> VehiculoRead:
    vehiculo = await service.obtener_vehiculo(session, vehiculo_id)
    return VehiculoRead.model_validate(vehiculo)


@router.patch(
    "/{vehiculo_id}",
    response_model=VehiculoRead,
    summary="Actualizar vehículo",
    description="Actualiza solo los campos enviados del vehículo.",
)
async def actualizar_vehiculo(
    vehiculo_id: VehiculoId, data: VehiculoUpdate, session: SessionDep
) -> VehiculoRead:
    vehiculo = await service.actualizar_vehiculo(session, vehiculo_id, data)
    return VehiculoRead.model_validate(vehiculo)


@router.delete(
    "/{vehiculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Dar de baja vehículo",
    description="Da de baja lógica un vehículo sin órdenes abiertas.",
)
async def borrar_vehiculo(vehiculo_id: VehiculoId, session: SessionDep) -> Response:
    await service.borrar_vehiculo(session, vehiculo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
