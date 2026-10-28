"""Endpoints REST de clientes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination import Pagina, PaginaParams, construir_pagina
from app.modules.clientes import service
from app.modules.clientes.schemas import ClienteCreate, ClienteRead, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["clientes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClienteId = Annotated[int, Path(ge=1)]


@router.get(
    "",
    response_model=Pagina[ClienteRead],
    summary="Listar clientes",
    description="Devuelve los clientes de forma paginada.",
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
)
async def crear_cliente(
    data: ClienteCreate, session: SessionDep
) -> ClienteRead:
    cliente = await service.crear_cliente(session, data)
    return ClienteRead.model_validate(cliente)


@router.get(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Consultar cliente",
    description="Devuelve un cliente por su identificador.",
)
async def obtener_cliente(cliente_id: ClienteId, session: SessionDep) -> ClienteRead:
    cliente = await service.obtener_cliente(session, cliente_id)
    return ClienteRead.model_validate(cliente)


@router.patch(
    "/{cliente_id}",
    response_model=ClienteRead,
    summary="Actualizar cliente",
    description="Actualiza solo los campos enviados del cliente.",
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
)
async def borrar_cliente(cliente_id: ClienteId, session: SessionDep) -> Response:
    await service.borrar_cliente(session, cliente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
