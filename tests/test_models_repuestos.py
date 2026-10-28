"""Tests for app.modules.repuestos.models (C-02 task 2.4)."""

from sqlalchemy import inspect
from sqlmodel import SQLModel

import app.modules.repuestos.models as repuestos_models


def test_repuestos_module_imports_without_errors():
    """The repuestos models module must import cleanly (task 2.4 acceptance)."""
    assert repuestos_models is not None


def test_repuesto_model_has_expected_columns():
    """repuesto: id, codigo, nombre, precio, stock, fecha_alta, fecha_baja."""
    table = SQLModel.metadata.tables["repuesto"]
    for col in ("id", "codigo", "nombre", "precio", "stock", "fecha_alta", "fecha_baja"):
        assert col in table.c, f"repuesto missing column: {col}"


def test_repuesto_codigo_partial_unique_index():
    """repuesto.codigo has a partial unique index where fecha_baja IS NULL."""
    indexes = SQLModel.metadata.tables["repuesto"].indexes
    names = {ix.name for ix in indexes}
    assert "ix_repuesto_codigo_uc" in names
    ix = next(i for i in indexes if i.name == "ix_repuesto_codigo_uc")
    assert ix.unique is True
    where = ix.dialect_options.get("postgresql", {}).get("where")
    assert where is not None, "partial unique index must have postgresql_where"


def test_repuesto_stock_has_default():
    """repuesto.stock has a default value (0)."""
    col = SQLModel.metadata.tables["repuesto"].c.stock
    assert col.default is not None
