"""Tests de los handlers de errores (C-03 tarea 1.2)."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    Conflicto,
    Invalido,
    NoEncontrado,
    register_exception_handlers,
)

app = FastAPI()
register_exception_handlers(app)


@app.get("/no-encontrado")
async def no_encontrado():
    raise NoEncontrado("No existe")


@app.get("/conflicto")
async def conflicto():
    raise Conflicto("Conflicto")


@app.get("/invalido")
async def invalido():
    raise Invalido("Inválido")


class _ErrorPostgres(Exception):
    def __init__(self, sqlstate: str) -> None:
        self.sqlstate = sqlstate


@app.get("/integridad/{estado}")
async def integridad(estado: str):
    raise IntegrityError("INSERT ...", None, _ErrorPostgres(estado))


@app.get("/inesperado")
async def inesperado():
    raise RuntimeError("detalle interno que no debe salir")


async def _get(path: str):
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as ac:
        return await ac.get(path)


@pytest.mark.asyncio
async def test_no_encontrado_devuelve_404():
    response = await _get("/no-encontrado")
    assert response.status_code == 404
    assert response.json() == {"detail": "No existe"}


@pytest.mark.asyncio
async def test_conflicto_devuelve_409():
    response = await _get("/conflicto")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_invalido_devuelve_422():
    response = await _get("/invalido")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unicidad_devuelve_409_sin_sql():
    response = await _get("/integridad/23505")
    assert response.status_code == 409
    assert "INSERT" not in response.text


@pytest.mark.asyncio
async def test_fk_devuelve_409():
    response = await _get("/integridad/23503")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_check_devuelve_422():
    response = await _get("/integridad/23514")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_error_inesperado_devuelve_500_generico():
    response = await _get("/inesperado")
    assert response.status_code == 500
    assert response.json() == {"detail": "Ocurrió un error inesperado"}
    assert "detalle interno" not in response.text
