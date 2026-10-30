"""Tests de integración de /ordenes y su ciclo de vida (C-03 tareas 6.2 a 6.7)."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.main import app
from app.modules.ordenes.models import HistorialEstadoOrden
from app.modules.repuestos.models import MovimientoStock


async def _crear_orden(client, seed, cantidad: int = 3, stock: int = 10):
    usuario = await seed.usuario()
    cliente = await seed.cliente()
    vehiculo = await seed.vehiculo(cliente.id)
    repuesto = await seed.repuesto(precio="10.00", stock=stock)
    response = await client.post(
        "/ordenes",
        json={
            "vehiculo_id": vehiculo.id,
            "falla": "Ruido en motor",
            "usuario_id": usuario.id,
            "items": [{"repuesto_id": repuesto.id, "cantidad": cantidad}],
        },
    )
    return response, usuario, vehiculo, repuesto


async def _movimientos(orden_id: int):
    async with app.state.async_session_maker() as session:
        return list(
            await session.scalars(
                select(MovimientoStock).where(MovimientoStock.orden_id == orden_id)
            )
        )


async def _historial(orden_id: int):
    async with app.state.async_session_maker() as session:
        return list(
            await session.scalars(
                select(HistorialEstadoOrden)
                .where(HistorialEstadoOrden.orden_id == orden_id)
                .order_by(HistorialEstadoOrden.id)
            )
        )


@pytest.mark.asyncio
async def test_ciclo_completo_de_orden(client, seed):
    usuario = await seed.usuario()
    cliente = await seed.cliente()
    vehiculo = await seed.vehiculo(cliente.id)
    r1 = await seed.repuesto(codigo="REP-001", precio="10.00", stock=10)
    r2 = await seed.repuesto(codigo="REP-002", precio="5.50", stock=10)

    creada = await client.post(
        "/ordenes",
        json={
            "vehiculo_id": vehiculo.id,
            "falla": "Ruido en motor",
            "usuario_id": usuario.id,
            "items": [
                {"repuesto_id": r1.id, "cantidad": 3},
                {"repuesto_id": r2.id, "cantidad": 2},
            ],
        },
    )
    assert creada.status_code == 201
    orden = creada.json()
    assert orden["estado"] == "PENDIENTE"
    assert Decimal(orden["total"]) == Decimal("41.00")
    assert orden["patente"] == vehiculo.patente
    assert orden["cliente"] == cliente.nombre
    assert len(orden["items"]) == 2
    assert orden["mecanico_id"] is None
    item = next(i for i in orden["items"] if i["repuesto_id"] == r1.id)
    assert {"repuesto_id", "codigo", "descripcion", "cantidad", "precio_unitario", "subtotal"} <= set(item)
    assert Decimal(item["subtotal"]) == Decimal("30.00")
    assert orden["historial"] == [
        {
            "desde_estado": None,
            "hasta_estado": "PENDIENTE",
            "usuario_id": usuario.id,
            "cuando": orden["historial"][0]["cuando"],
        }
    ]

    detalle = await client.get(f"/ordenes/{orden['id']}")
    assert detalle.status_code == 200

    listado = await client.get(
        "/ordenes",
        params={"estado": "PENDIENTE", "vehiculo_id": vehiculo.id},
    )
    assert listado.json()["total"] == 1

    actualizada = await client.patch(
        f"/ordenes/{orden['id']}",
        json={"falla": "Ruido en caja", "mecanico_id": usuario.id},
    )
    assert actualizada.status_code == 200
    assert actualizada.json()["falla"] == "Ruido en caja"
    assert actualizada.json()["mecanico_id"] == usuario.id

    iniciada = await client.post(
        f"/ordenes/{orden['id']}/iniciar", json={"usuario_id": usuario.id}
    )
    assert iniciada.status_code == 200
    assert iniciada.json()["estado"] == "EN_REPARACION"

    terminada = await client.post(
        f"/ordenes/{orden['id']}/terminar", json={"usuario_id": usuario.id}
    )
    assert terminada.status_code == 200
    assert terminada.json()["estado"] == "TERMINADA"

    stock1 = await client.get(f"/repuestos/{r1.id}")
    stock2 = await client.get(f"/repuestos/{r2.id}")
    assert stock1.json()["stock"] == 7
    assert stock2.json()["stock"] == 8

    movimientos = await _movimientos(orden["id"])
    assert sorted(m.cantidad for m in movimientos) == [-3, -2]
    assert all(m.usuario_id == usuario.id for m in movimientos)
    assert all(m.motivo == "terminación" for m in movimientos)

    historial = await _historial(orden["id"])
    assert [h.hasta_estado for h in historial] == [
        "PENDIENTE",
        "EN_REPARACION",
        "TERMINADA",
    ]
    assert historial[0].desde_estado is None

    cancelar_terminada = await client.post(
        f"/ordenes/{orden['id']}/cancelar", json={"usuario_id": usuario.id}
    )
    assert cancelar_terminada.status_code == 409


@pytest.mark.asyncio
async def test_cancelacion_de_orden(client, seed):
    creada, usuario, _, _ = await _crear_orden(client, seed)
    orden_id = creada.json()["id"]

    cancelada = await client.post(
        f"/ordenes/{orden_id}/cancelar", json={"usuario_id": usuario.id}
    )
    assert cancelada.status_code == 200
    assert cancelada.json()["estado"] == "CANCELADA"

    otra_vez = await client.post(
        f"/ordenes/{orden_id}/cancelar", json={"usuario_id": usuario.id}
    )
    assert otra_vez.status_code == 409

    iniciar_cancelada = await client.post(
        f"/ordenes/{orden_id}/iniciar", json={"usuario_id": usuario.id}
    )
    assert iniciar_cancelada.status_code == 409


@pytest.mark.asyncio
async def test_transiciones_invalidas(client, seed):
    creada, usuario, _, _ = await _crear_orden(client, seed)
    orden_id = creada.json()["id"]

    terminar_pendiente = await client.post(
        f"/ordenes/{orden_id}/terminar", json={"usuario_id": usuario.id}
    )
    assert terminar_pendiente.status_code == 409

    assert (
        await client.post(
            f"/ordenes/{orden_id}/iniciar", json={"usuario_id": usuario.id}
        )
    ).status_code == 200

    iniciar_dos_veces = await client.post(
        f"/ordenes/{orden_id}/iniciar", json={"usuario_id": usuario.id}
    )
    assert iniciar_dos_veces.status_code == 409

    patch_iniciada = await client.patch(
        f"/ordenes/{orden_id}", json={"falla": "Otra"}
    )
    assert patch_iniciada.status_code == 409


@pytest.mark.asyncio
async def test_stock_insuficiente_no_deja_escrituras(client, seed):
    creada, usuario, _, repuesto = await _crear_orden(
        client, seed, cantidad=5, stock=2
    )
    orden_id = creada.json()["id"]

    assert (
        await client.post(
            f"/ordenes/{orden_id}/iniciar", json={"usuario_id": usuario.id}
        )
    ).status_code == 200

    fallo = await client.post(
        f"/ordenes/{orden_id}/terminar", json={"usuario_id": usuario.id}
    )
    assert fallo.status_code == 409

    detalle = await client.get(f"/ordenes/{orden_id}")
    assert detalle.json()["estado"] == "EN_REPARACION"

    stock = await client.get(f"/repuestos/{repuesto.id}")
    assert stock.json()["stock"] == 2

    assert await _movimientos(orden_id) == []


@pytest.mark.asyncio
async def test_validaciones_de_apertura(client, seed):
    usuario = await seed.usuario()
    cliente = await seed.cliente()
    vehiculo = await seed.vehiculo(cliente.id)
    repuesto = await seed.repuesto()

    base = {
        "vehiculo_id": vehiculo.id,
        "falla": "Falla",
        "usuario_id": usuario.id,
        "items": [{"repuesto_id": repuesto.id, "cantidad": 1}],
    }

    sin_items = await client.post("/ordenes", json={**base, "items": []})
    assert sin_items.status_code == 422

    repetidos = await client.post(
        "/ordenes",
        json={
            **base,
            "items": [
                {"repuesto_id": repuesto.id, "cantidad": 1},
                {"repuesto_id": repuesto.id, "cantidad": 2},
            ],
        },
    )
    assert repetidos.status_code == 422

    con_total = await client.post("/ordenes", json={**base, "total": "999.00"})
    assert con_total.status_code == 422

    vehiculo_inexistente = await client.post(
        "/ordenes", json={**base, "vehiculo_id": 999999}
    )
    assert vehiculo_inexistente.status_code == 409

    repuesto_inexistente = await client.post(
        "/ordenes",
        json={**base, "items": [{"repuesto_id": 999999, "cantidad": 1}]},
    )
    assert repuesto_inexistente.status_code == 409

    usuario_inexistente = await client.post(
        "/ordenes", json={**base, "usuario_id": 999999}
    )
    assert usuario_inexistente.status_code == 404


@pytest.mark.asyncio
async def test_no_se_puede_abrir_orden_con_dados_de_baja(client, seed):
    usuario = await seed.usuario()
    cliente = await seed.cliente()
    vehiculo = await seed.vehiculo(cliente.id)
    repuesto = await seed.repuesto()

    assert (await client.delete(f"/vehiculos/{vehiculo.id}")).status_code == 204
    con_vehiculo_borrado = await client.post(
        "/ordenes",
        json={
            "vehiculo_id": vehiculo.id,
            "falla": "Falla",
            "usuario_id": usuario.id,
            "items": [{"repuesto_id": repuesto.id, "cantidad": 1}],
        },
    )
    assert con_vehiculo_borrado.status_code == 409

    otro_vehiculo = await seed.vehiculo(cliente.id)
    assert (await client.delete(f"/repuestos/{repuesto.id}")).status_code == 204
    con_repuesto_borrado = await client.post(
        "/ordenes",
        json={
            "vehiculo_id": otro_vehiculo.id,
            "falla": "Falla",
            "usuario_id": usuario.id,
            "items": [{"repuesto_id": repuesto.id, "cantidad": 1}],
        },
    )
    assert con_repuesto_borrado.status_code == 409


@pytest.mark.asyncio
async def test_body_de_referencia_sin_usuario_id(client, seed):
    usuario = await seed.usuario(nombre="Laura Gómez")
    cliente = await seed.cliente(nombre="Ana Pérez", usuario_id=usuario.id)
    vehiculo = await seed.vehiculo(cliente.id, patente="AB123CD")
    repuesto = await seed.repuesto(codigo="REP-001", descripcion="Filtro", precio="10.00")

    creada = await client.post(
        "/ordenes",
        json={
            "vehiculo_id": vehiculo.id,
            "falla": "Ruido en motor",
            "items": [{"repuesto_id": repuesto.id, "cantidad": 2}],
        },
    )
    assert creada.status_code == 201
    orden = creada.json()
    assert orden["patente"] == "AB123CD"
    assert orden["cliente"] == "Ana Pérez"
    assert orden["historial"][0]["usuario_id"] == usuario.id


@pytest.mark.asyncio
async def test_filtro_de_estado_invalido_devuelve_422(client):
    assert (await client.get("/ordenes?estado=NO_EXISTE")).status_code == 422


@pytest.mark.asyncio
async def test_patch_valida_mecanico_y_campos(client, seed):
    creada, _, _, _ = await _crear_orden(client, seed)
    orden_id = creada.json()["id"]

    inexistente = await client.patch(
        f"/ordenes/{orden_id}", json={"mecanico_id": 999999}
    )
    assert inexistente.status_code == 404

    items = await client.patch(
        f"/ordenes/{orden_id}", json={"items": [], "falla": "X"}
    )
    assert items.status_code == 422
