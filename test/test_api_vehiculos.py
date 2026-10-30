"""Tests de integración de /vehiculos (C-03 tareas 3.2, 3.3 y 3.4)."""

import pytest


@pytest.mark.asyncio
async def test_crud_vehiculo(client, seed):
    cliente = await seed.cliente()
    creado = await client.post(
        "/vehiculos",
        json={
            "cliente_id": cliente.id,
            "patente": "AAA111",
            "marca": "Toyota",
            "modelo": "Corolla",
            "anio": 2020,
        },
    )
    assert creado.status_code == 201
    vehiculo = creado.json()
    assert "borrado_en" not in vehiculo

    listado = await client.get(f"/vehiculos?cliente_id={cliente.id}")
    assert listado.status_code == 200
    assert listado.json()["total"] == 1

    actualizado = await client.patch(
        f"/vehiculos/{vehiculo['id']}", json={"modelo": "Corolla Cross"}
    )
    assert actualizado.status_code == 200
    assert actualizado.json()["modelo"] == "Corolla Cross"
    assert actualizado.json()["marca"] == "Toyota"


@pytest.mark.asyncio
async def test_cliente_inexistente_devuelve_404(client):
    response = await client.post(
        "/vehiculos",
        json={
            "cliente_id": 999,
            "patente": "AAA111",
            "marca": "M",
            "modelo": "X",
            "anio": 2020,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patente_duplicada_entre_vigentes_devuelve_409(client, seed):
    cliente = await seed.cliente()
    datos = {
        "cliente_id": cliente.id,
        "patente": "AAA111",
        "marca": "M",
        "modelo": "X",
        "anio": 2020,
    }
    assert (await client.post("/vehiculos", json=datos)).status_code == 201
    assert (await client.post("/vehiculos", json=datos)).status_code == 409


@pytest.mark.asyncio
async def test_anio_fuera_de_rango_devuelve_422(client, seed):
    cliente = await seed.cliente()
    response = await client.post(
        "/vehiculos",
        json={
            "cliente_id": cliente.id,
            "patente": "AAA111",
            "marca": "M",
            "modelo": "X",
            "anio": 1949,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_baja_logica_y_reutilizacion_de_patente(client, seed):
    cliente = await seed.cliente()
    vehiculo = await seed.vehiculo(cliente.id, patente="AAA111")

    baja = await client.delete(f"/vehiculos/{vehiculo.id}")
    assert baja.status_code == 204
    assert (await client.get(f"/vehiculos/{vehiculo.id}")).status_code == 404

    listado = await client.get("/vehiculos")
    assert listado.json()["total"] == 0

    reutilizada = await client.post(
        "/vehiculos",
        json={
            "cliente_id": cliente.id,
            "patente": "AAA111",
            "marca": "M",
            "modelo": "X",
            "anio": 2021,
        },
    )
    assert reutilizada.status_code == 201


@pytest.mark.asyncio
async def test_baja_bloqueada_por_orden_abierta(client, seed):
    usuario = await seed.usuario()
    cliente = await seed.cliente()
    vehiculo = await seed.vehiculo(cliente.id)
    repuesto = await seed.repuesto()

    orden = await client.post(
        "/ordenes",
        json={
            "vehiculo_id": vehiculo.id,
            "falla": "Ruido",
            "usuario_id": usuario.id,
            "items": [{"repuesto_id": repuesto.id, "cantidad": 1}],
        },
    )
    assert orden.status_code == 201

    baja = await client.delete(f"/vehiculos/{vehiculo.id}")
    assert baja.status_code == 409
