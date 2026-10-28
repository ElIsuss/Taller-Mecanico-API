"""Tests de integración de /estados-orden (C-03 tareas 5.1 y 5.2)."""

import pytest


@pytest.mark.asyncio
async def test_listado_ordenado_por_posicion(client, seed):
    response = await client.get("/estados-orden")
    assert response.status_code == 200
    datos = response.json()
    assert datos["total"] == 4
    codigos = [estado["codigo"] for estado in datos["items"]]
    assert codigos == ["PENDIENTE", "EN_REPARACION", "TERMINADA", "CANCELADA"]


@pytest.mark.asyncio
async def test_consulta_por_codigo(client, seed):
    response = await client.get("/estados-orden/TERMINADA")
    assert response.status_code == 200
    assert response.json()["es_final"] is True


@pytest.mark.asyncio
async def test_codigo_inexistente_devuelve_404(client, seed):
    response = await client.get("/estados-orden/NO_EXISTE")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_catalogo_no_permite_escrituras(client, seed):
    assert (await client.post("/estados-orden", json={})).status_code == 405
    assert (
        await client.patch("/estados-orden/PENDIENTE", json={})
    ).status_code == 405
    assert (await client.delete("/estados-orden/PENDIENTE")).status_code == 405
