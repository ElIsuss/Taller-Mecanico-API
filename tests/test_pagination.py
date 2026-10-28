"""Tests unitarios de paginación (C-03 tarea 1.1)."""

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import Invalido, register_exception_handlers
from app.core.pagination import (
    PaginaParams,
    calcular_pages,
    construir_pagina,
)

app = FastAPI()
register_exception_handlers(app)


@app.get("/paginado")
async def paginado(params: PaginaParams = Depends()):
    return {"page": params.page, "size": params.size}


@pytest.mark.asyncio
async def test_page_cero_es_rechazada():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/paginado?page=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_size_mayor_a_cien_es_rechazado():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/paginado?size=101")
    assert response.status_code == 422


def test_calcular_pages_lista_vacia_es_cero():
    assert calcular_pages(0, 20) == 0


def test_calcular_pages_redondea_hacia_arriba():
    assert calcular_pages(5, 2) == 3


def test_construir_pagina_arma_el_envoltorio():
    params = PaginaParams(page=2, size=2)
    pagina = construir_pagina([1, 2], total=5, params=params)
    assert pagina.items == [1, 2]
    assert pagina.total == 5
    assert pagina.pages == 3
    assert pagina.page == 2


def test_construir_pagina_rechaza_pagina_fuera_de_rango():
    params = PaginaParams(page=4, size=2)
    with pytest.raises(Invalido):
        construir_pagina([], total=5, params=params)


def test_construir_pagina_vacia_permite_primera_pagina():
    params = PaginaParams(page=1, size=20)
    pagina = construir_pagina([], total=0, params=params)
    assert pagina.pages == 0
