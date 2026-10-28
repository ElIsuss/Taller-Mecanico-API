"""Tests de integración de /clientes (C-03 tareas 2.2 y 2.3)."""

import pytest


@pytest.mark.asyncio
async def test_crud_cliente(client, seed):
    creado = await client.post(
        "/clientes",
        json={
            "nombre": "Ana Pérez",
            "documento": "DOC-001",
            "telefono": "555-1000",
        },
    )
    assert creado.status_code == 201
    cliente = creado.json()
    assert cliente["nombre"] == "Ana Pérez"
    assert "borrado_en" not in cliente

    listado = await client.get("/clientes")
    assert listado.status_code == 200
    pagina = listado.json()
    assert pagina["total"] == 1
    assert pagina["pages"] == 1

    detalle = await client.get(f"/clientes/{cliente['id']}")
    assert detalle.status_code == 200

    actualizado = await client.patch(
        f"/clientes/{cliente['id']}", json={"telefono": "555-2000"}
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["telefono"] == "555-2000"
    assert actualizado.json()["nombre"] == "Ana Pérez"

    borrado = await client.delete(f"/clientes/{cliente['id']}")
    assert borrado.status_code == 204
    assert (await client.get(f"/clientes/{cliente['id']}")).status_code == 404


@pytest.mark.asyncio
async def test_documento_duplicado_devuelve_409(client, seed):
    datos = {"nombre": "Ana", "documento": "DOC-001", "telefono": "555"}
    assert (await client.post("/clientes", json=datos)).status_code == 201
    repetido = await client.post("/clientes", json=datos)
    assert repetido.status_code == 409


@pytest.mark.asyncio
async def test_usuario_ya_vinculado_devuelve_409(client, seed):
    usuario = await seed.usuario()
    assert (
        await client.post(
            "/clientes",
            json={
                "nombre": "Ana",
                "documento": "DOC-001",
                "telefono": "555",
                "usuario_id": usuario.id,
            },
        )
    ).status_code == 201
    segundo = await client.post(
        "/clientes",
        json={
            "nombre": "Otra",
            "documento": "DOC-002",
            "telefono": "555",
            "usuario_id": usuario.id,
        },
    )
    assert segundo.status_code == 409


@pytest.mark.asyncio
async def test_campo_desconocido_devuelve_422(client):
    response = await client.post(
        "/clientes",
        json={
            "nombre": "Ana",
            "documento": "DOC-001",
            "telefono": "555",
            "rol": "ADMIN",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cliente_con_vehiculos_no_se_borra(client, seed):
    cliente = await seed.cliente()
    await seed.vehiculo(cliente.id)
    response = await client.delete(f"/clientes/{cliente.id}")
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_pagina_fuera_de_rango_devuelve_422(client, seed):
    await seed.cliente()
    response = await client.get("/clientes?page=2&size=20")
    assert response.status_code == 422
