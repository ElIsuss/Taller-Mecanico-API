"""Endpoints REST de clientes y vehículos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import requiere_rol
from app.core.pagination import Pagina, PaginaParams, construir_pagina
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    VehiculoCreate,
    VehiculoDeClienteCreate,
    VehiculoRead,
    VehiculoUpdate,
)

router = APIRouter(prefix="/clientes", tags=["clientes"])
router_vehiculos = APIRouter(prefix="/vehiculos", tags=["vehiculos"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClienteId = Annotated[int, Path(ge=1)]
VehiculoId = Annotated[int, Path(ge=1)]


@router.get(
    "",
    response_model=Pagina[ClienteRead],
    summary="Listar clientes",
    description="Devuelve los clientes de forma paginada.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def listar_clientes(
    session: SessionDep,
    params: Annotated[PaginaParams, Depends()],
) -> Pagina[ClienteRead]:
    clientes, total = await service.listar_clientes(
        session, params.offset, params.size
    )
    return construir_pagina(
        [ClienteRead.model_validate(c) for c in clientes], total, params
    )


@router.post(
    "",
    response_model=ClienteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cliente",
    description="Da de alta una ficha de cliente.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def crear_cliente(
    data: ClienteCreate, session: SessionDep
) -> ClienteRead:
    cliente = await service.crear_cliente(session, data)
    return ClienteRead.model_validate(cliente)


@router.get(
    "/{cliente_id}",
    response_model=ClienteDetalleRead,
    summary="Consultar cliente",
    description="Devuelve un cliente con sus vehículos por su identificador.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def obtener_cliente(
    cliente_id: ClienteId, session: SessionDep
) -> ClienteDetalleRead:
    cliente = await service.obtener_cliente(session, cliente_id)
    return ClienteDetalleRead.model_validate(cliente)


@router.post(
    "/{cliente_id}/vehiculos",
    response_model=VehiculoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear vehículo de un cliente",
    description="Da de alta un vehículo asociado al cliente indicado.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def crear_vehiculo_de_cliente(
    cliente_id: ClienteId,
    data: VehiculoDeClienteCreate,
    session: SessionDep,
) -> VehiculoRead:
    vehiculo = await service.crear_vehiculo(
        session, VehiculoCreate(cliente_id=cliente_id, **data.model_dump())
    )
    return VehiculoRead.model_validate(vehiculo)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Actualizar cliente",
    description="Actualiza solo los campos enviados del cliente.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def actualizar_cliente(
    cliente_id: ClienteId, data: ClienteUpdate, session: SessionDep
) -> ClienteRead:
    cliente = await service.actualizar_cliente(session, cliente_id, data)
    return ClienteRead.model_validate(cliente)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Borrar cliente",
    description="Borra el cliente si no tiene vehículos asociados.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def borrar_cliente(cliente_id: ClienteId, session: SessionDep) -> Response:
    await service.borrar_cliente(session, cliente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_vehiculos.get(
    "",
    response_model=Pagina[VehiculoRead],
    summary="Listar vehículos",
    description="Devuelve los vehículos vigentes de forma paginada.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
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


@router_vehiculos.post(
    "",
    response_model=VehiculoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear vehículo",
    description="Da de alta un vehículo asociado a un cliente.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def crear_vehiculo(
    data: VehiculoCreate, session: SessionDep
) -> VehiculoRead:
    vehiculo = await service.crear_vehiculo(session, data)
    return VehiculoRead.model_validate(vehiculo)


@router_vehiculos.get(
    "/{vehiculo_id}",
    response_model=VehiculoRead,
    summary="Consultar vehículo",
    description="Devuelve un vehículo vigente por su identificador.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def obtener_vehiculo(
    vehiculo_id: VehiculoId, session: SessionDep
) -> VehiculoRead:
    vehiculo = await service.obtener_vehiculo(session, vehiculo_id)
    return VehiculoRead.model_validate(vehiculo)


@router_vehiculos.patch(
    "/{vehiculo_id}",
    response_model=VehiculoRead,
    summary="Actualizar vehículo",
    description="Actualiza solo los campos enviados del vehículo.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def actualizar_vehiculo(
    vehiculo_id: VehiculoId, data: VehiculoUpdate, session: SessionDep
) -> VehiculoRead:
    vehiculo = await service.actualizar_vehiculo(session, vehiculo_id, data)
    return VehiculoRead.model_validate(vehiculo)


@router_vehiculos.delete(
    "/{vehiculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Dar de baja vehículo",
    description="Da de baja lógica un vehículo sin órdenes abiertas.",
    dependencies=[Depends(requiere_rol("ADMIN", "RECEPCION"))],
)
async def borrar_vehiculo(vehiculo_id: VehiculoId, session: SessionDep) -> Response:
    await service.borrar_vehiculo(session, vehiculo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
