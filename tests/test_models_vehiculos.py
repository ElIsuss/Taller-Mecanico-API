"""Tests for app.modules.vehiculos.models (C-02 task 2.3)."""

from sqlalchemy import inspect
from sqlmodel import SQLModel

import app.modules.vehiculos.models as vehiculos_models

def test_vehiculos_module_imports_without_errors():
    """The vehiculos models module must import cleanly (task 2.3 acceptance)."""
    assert vehiculos_models is not None


def test_vehiculo_model_has_expected_columns_and_fk():
    """vehiculo: id, cliente_id, patente, marca, modelo, anio, borrado_en."""
    inspector = inspect(SQLModel.metadata.tables["vehiculo"])
    columns = {c.name for c in inspector.columns}
    expected = {"id", "cliente_id", "patente", "marca", "modelo", "anio", "borrado_en"}
    assert expected <= columns, f"vehiculo missing: {sorted(expected - columns)}"

    fk_targets = {fk.target_fullname for fk in inspector.foreign_keys}
    assert "cliente.id" in fk_targets


def test_vehiculo_patente_partial_unique_index():
    """vehiculo.patente es unica solo entre los vigentes (borrado_en IS NULL)."""
    index = next(
        ix
        for ix in SQLModel.metadata.tables["vehiculo"].indexes
        if ix.name == "ix_vehiculo_patente_uc"
    )
    assert index.unique is True
    where = index.dialect_options["postgresql"].get("where")
    assert where is not None
    assert "BORRADO_EN IS NULL" in str(where).upper()


def test_vehiculo_cliente_id_not_nullable_and_indexed():
    """Todo vehiculo pertenece a un cliente, y la FK esta indexada."""
    table = SQLModel.metadata.tables["vehiculo"]
    assert table.c.cliente_id.nullable is False
    indexed_columns = {tuple(col.name for col in ix.columns) for ix in table.indexes}
    assert ("cliente_id",) in indexed_columns


def test_vehiculo_anio_check_constraint():
    """anio debe estar entre 1950 y 2100."""
    checks = {
        c.name: str(c.sqltext)
        for c in SQLModel.metadata.tables["vehiculo"].constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert "ck_vehiculo_anio" in checks
    assert "1950" in checks["ck_vehiculo_anio"] and "2100" in checks["ck_vehiculo_anio"]


def test_vehiculo_borrado_en_is_timezone_aware():
    """borrado_en es timestamptz y nullable."""
    col = SQLModel.metadata.tables["vehiculo"].c.borrado_en
    assert col.type.timezone is True
    assert col.nullable is True


def test_vehiculo_relationships_declared():
    """Vehiculo navega a cliente y ordenes."""
    Vehiculo = vehiculos_models.Vehiculo
    assert hasattr(Vehiculo, "cliente")
    assert hasattr(Vehiculo, "ordenes")
