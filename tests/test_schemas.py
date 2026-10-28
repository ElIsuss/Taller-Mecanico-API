"""Tests de los contratos Pydantic (C-03 tareas 2.1, 3.1, 4.1, 6.1)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
)
from app.modules.ordenes.schemas import (
    OrdenCreate,
    OrdenUpdate,
    ItemOrdenCreate,
)
from app.modules.repuestos.schemas import RepuestoRead, RepuestoUpdate
from app.modules.vehiculos.schemas import VehiculoCreate, VehiculoRead


def test_cliente_create_rechaza_campos_desconocidos():
    with pytest.raises(ValidationError):
        ClienteCreate(
            nombre="Ana",
            documento="123",
            telefono="555",
            rol="ADMIN",
        )


def test_cliente_update_solo_expone_campos_enviados():
    data = ClienteUpdate(telefono="555-9999")
    assert data.model_dump(exclude_unset=True) == {"telefono": "555-9999"}


def test_cliente_read_no_expone_campos_internos():
    assert set(ClienteRead.model_fields) == {
        "id",
        "usuario_id",
        "nombre",
        "documento",
        "telefono",
    }


def test_vehiculo_rechaza_anio_fuera_de_rango():
    with pytest.raises(ValidationError):
        VehiculoCreate(
            cliente_id=1,
            patente="AAA111",
            marca="M",
            modelo="X",
            anio=1949,
        )
    with pytest.raises(ValidationError):
        VehiculoCreate(
            cliente_id=1,
            patente="AAA111",
            marca="M",
            modelo="X",
            anio=2101,
        )


def test_vehiculo_read_no_expone_borrado_en():
    assert "borrado_en" not in VehiculoRead.model_fields


def test_repuesto_update_rechaza_stock():
    with pytest.raises(ValidationError):
        RepuestoUpdate(stock=5)


def test_repuesto_update_precio_requiere_actor():
    with pytest.raises(ValidationError):
        RepuestoUpdate(precio=Decimal("12.00"))
    data = RepuestoUpdate(precio=Decimal("12.00"), usuario_id=1)
    assert data.usuario_id == 1


def test_repuesto_read_no_expone_borrado_en():
    assert "borrado_en" not in RepuestoRead.model_fields


def test_orden_create_requiere_al_menos_un_item():
    with pytest.raises(ValidationError):
        OrdenCreate(
            vehiculo_id=1,
            falla="Falla",
            usuario_id=1,
            items=[],
        )


def test_orden_create_rechaza_repuestos_repetidos():
    with pytest.raises(ValidationError):
        OrdenCreate(
            vehiculo_id=1,
            falla="Falla",
            usuario_id=1,
            items=[
                ItemOrdenCreate(repuesto_id=1, cantidad=1),
                ItemOrdenCreate(repuesto_id=1, cantidad=2),
            ],
        )


def test_orden_create_rechaza_total_enviado():
    with pytest.raises(ValidationError):
        OrdenCreate(
            vehiculo_id=1,
            falla="Falla",
            usuario_id=1,
            items=[ItemOrdenCreate(repuesto_id=1, cantidad=1)],
            total="999.00",
        )


def test_orden_update_rechaza_items_y_total():
    with pytest.raises(ValidationError):
        OrdenUpdate(items=[])
    with pytest.raises(ValidationError):
        OrdenUpdate(total="10.00")
