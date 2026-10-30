"""Tests de integración de /repuestos (C-03 tareas 4.2 a 4.5)."""

from decimal import Decimal

import pytest


@pytest.mark.asyncio
async def test_crud_y_busqueda_de_repuestos(client, seed):
    usuario = await seed.usuario()
    creado = await client.post(
        "/repuestos",
        json={
            "codigo": "REP-001",
            "descripcion": "Filtro de aceite",
            "precio": "10.00",
            "stock_inicial": 3,
            "usuario_id": usuario.id,
        },
    )
    assert creado.status_code == 201
    repuesto = creado.json()
    assert Decimal(repuesto["precio"]) == Decimal("10.00")
    assert repuesto["stock"] == 3
    assert "borrado_en" not in repuesto

    movimientos = await client.get(f"/repuestos/{repuesto['id']}/movimientos")
    assert movimientos.status_code == 200
    assert movimientos.json()["items"][0]["motivo"] == "Stock inicial"

    busqueda = await client.get("/repuestos?q=filtro")
    assert busqueda.status_code == 200
    assert busqueda.json()["total"] == 1

    sin_resultados = await client.get("/repuestos?q=inexistente")
    assert sin_resultados.json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 20,
        "pages": 1,
    }


@pytest.mark.asyncio
async def test_busqueda_escapa_comodines(client, seed):
    await seed.repuesto(codigo="REP-001", descripcion="Filtro 100%")
    await seed.repuesto(codigo="REP-002", descripcion="Filtro 100x")

    response = await client.get("/repuestos", params={"q": "100%"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["descripcion"] == "Filtro 100%"


@pytest.mark.asyncio
async def test_codigo_duplicado_devuelve_409(client, seed):
    datos = {
        "codigo": "REP-001",
        "descripcion": "Filtro",
        "precio": "10.00",
    }
    assert (await client.post("/repuestos", json=datos)).status_code == 201
    assert (await client.post("/repuestos", json=datos)).status_code == 409


@pytest.mark.asyncio
async def test_precio_no_positivo_devuelve_422(client):
    response = await client.post(
        "/repuestos",
        json={"codigo": "REP-001", "descripcion": "Filtro", "precio": "0"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_stock_y_precio_sin_actor_devuelven_422(client, seed):
    repuesto = await seed.repuesto()
    stock = await client.patch(
        f"/repuestos/{repuesto.id}", json={"stock": 99}
    )
    assert stock.status_code == 422

    sin_actor = await client.patch(
        f"/repuestos/{repuesto.id}", json={"precio": "12.00"}
    )
    assert sin_actor.status_code == 422

    codigo = await client.patch(
        f"/repuestos/{repuesto.id}", json={"codigo": "OTRO"}
    )
    assert codigo.status_code == 422


@pytest.mark.asyncio
async def test_cambio_de_precio_registra_historial(client, seed):
    usuario = await seed.usuario()
    repuesto = await seed.repuesto(precio="10.00")

    cambio = await client.patch(
        f"/repuestos/{repuesto.id}",
        json={"precio": "12.50", "usuario_id": usuario.id},
    )
    assert cambio.status_code == 200
    assert Decimal(cambio.json()["precio"]) == Decimal("12.50")

    historial = await client.get(f"/repuestos/{repuesto.id}/precios")
    assert historial.status_code == 200
    datos = historial.json()
    assert datos["total"] == 1
    linea = datos["items"][0]
    assert Decimal(linea["precio_anterior"]) == Decimal("10.00")
    assert Decimal(linea["precio_nuevo"]) == Decimal("12.50")
    assert linea["usuario_id"] == usuario.id

    igual = await client.patch(
        f"/repuestos/{repuesto.id}",
        json={"precio": "12.50", "usuario_id": usuario.id},
    )
    assert igual.status_code == 200
    historial_igual = await client.get(f"/repuestos/{repuesto.id}/precios")
    assert historial_igual.json()["total"] == 1


@pytest.mark.asyncio
async def test_reposicion_aumenta_stock(client, seed):
    usuario = await seed.usuario()
    repuesto = await seed.repuesto(stock=5)

    reposicion = await client.post(
        f"/repuestos/{repuesto.id}/reponer",
        json={"cantidad": 7, "motivo": "compra", "usuario_id": usuario.id},
    )
    assert reposicion.status_code == 200
    assert reposicion.json()["cantidad"] == 7

    detalle = await client.get(f"/repuestos/{repuesto.id}")
    assert detalle.json()["stock"] == 12

    movimientos = await client.get(f"/repuestos/{repuesto.id}/movimientos")
    assert movimientos.json()["total"] == 1
    assert movimientos.json()["items"][0]["motivo"] == "compra"

    invalida = await client.post(
        f"/repuestos/{repuesto.id}/reponer",
        json={"cantidad": 0, "motivo": "compra", "usuario_id": usuario.id},
    )
    assert invalida.status_code == 422


@pytest.mark.asyncio
async def test_reposicion_de_repuesto_borrado_devuelve_404(client, seed):
    usuario = await seed.usuario()
    repuesto = await seed.repuesto()
    assert (await client.delete(f"/repuestos/{repuesto.id}")).status_code == 204

    response = await client.post(
        f"/repuestos/{repuesto.id}/reponer",
        json={"cantidad": 1, "motivo": "compra", "usuario_id": usuario.id},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_baja_logica_excluye_del_catalogo(client, seed):
    repuesto = await seed.repuesto()
    assert (await client.delete(f"/repuestos/{repuesto.id}")).status_code == 204
    assert (await client.get(f"/repuestos/{repuesto.id}")).status_code == 404
    listado = await client.get("/repuestos")
    assert listado.json()["total"] == 0
