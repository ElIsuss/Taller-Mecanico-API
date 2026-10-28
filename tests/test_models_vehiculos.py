"""Tests for app.modules.vehiculos.models (C-02 task 2.3)."""

from sqlalchemy import inspect
from sqlmodel import SQLModel

import app.modules.vehiculos.models as vehiculos_models


def test_vehiculos_module_imports_without_errors():
    """The vehiculos models module must import cleanly (task 2.3 acceptance)."""
    assert vehiculos_models is not None


def test_vehiculo_model_has_expected_columns_and_fk():
    """vehiculo: id, patente, cliente_id FK, fecha_alta, fecha_baja."""
    inspector = inspect(SQLModel.metadata.tables["vehiculo"])
    columns = {c.name for c in inspector.columns}
    for col in ("id", "patente", "cliente_id", "fecha_alta", "fecha_baja"):
        assert col in columns, f"vehiculo missing column: {col}"

    fk_targets = {str(fk) for fk in inspector.foreign_keys}
    assert any("cliente" in t for t in fk_targets), "vehiculo.cliente_id must FK to cliente.id"


def test_vehiculo_patente_partial_unique_index():
    """vehiculo.patente has a partial unique index where fecha_baja IS NULL."""
    indexes = SQLModel.metadata.tables["vehiculo"].indexes
    names = {ix.name for ix in indexes}
    assert "ix_vehiculo_patente_uc" in names
    ix = next(i for i in indexes if i.name == "ix_vehiculo_patente_uc")
    assert ix.unique is True
    where = ix.dialect_options.get("postgresql", {}).get("where")
    assert where is not None, "partial unique index must have postgresql_where"


def test_vehiculo_cliente_id_not_nullable():
    """vehiculo.cliente_id is not nullable (every vehicle belongs to a client)."""
    col = SQLModel.metadata.tables["vehiculo"].c.cliente_id
    assert col.nullable is False
