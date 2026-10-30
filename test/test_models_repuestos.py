"""Tests for app.modules.repuestos.models (C-02 task 2.4)."""

from decimal import Decimal

from sqlalchemy import Numeric, inspect
from sqlmodel import SQLModel

import app.modules.repuestos.models as repuestos_models


def test_repuestos_module_imports_without_errors():
    """The repuestos models module must import cleanly (task 2.4 acceptance)."""
    assert repuestos_models is not None


def test_repuesto_model_has_expected_columns():
    """repuesto: id, codigo, descripcion, precio, stock, borrado_en."""
    table = SQLModel.metadata.tables["repuesto"]
    expected = {"id", "codigo", "descripcion", "precio", "stock", "borrado_en"}
    assert expected <= set(table.c.keys())


def test_repuesto_codigo_partial_unique_index():
    """repuesto.codigo es unico solo entre los vigentes (borrado_en IS NULL)."""
    index = next(
        ix
        for ix in SQLModel.metadata.tables["repuesto"].indexes
        if ix.name == "ix_repuesto_codigo_uc"
    )
    assert index.unique is True
    where = index.dialect_options["postgresql"].get("where")
    assert where is not None
    assert "BORRADO_EN IS NULL" in str(where).upper()


def test_repuesto_precio_es_numeric_no_float():
    """El dinero nunca se modela como float: NUMERIC(10,2) y Decimal."""
    col = SQLModel.metadata.tables["repuesto"].c.precio
    assert isinstance(col.type, Numeric)
    assert col.type.precision == 10
    assert col.type.scale == 2
    assert repuestos_models.Repuesto.__annotations__["precio"] is Decimal


def test_repuesto_check_constraints():
    """precio > 0 y stock >= 0."""
    checks = {
        c.name: str(c.sqltext).lower()
        for c in SQLModel.metadata.tables["repuesto"].constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert checks.get("ck_repuesto_precio_positivo") == "precio > 0"
    assert checks.get("ck_repuesto_stock_no_negativo") == "stock >= 0"


def test_repuesto_stock_has_default():
    """repuesto.stock arranca en 0."""
    col = SQLModel.metadata.tables["repuesto"].c.stock
    assert col.default is not None
    assert col.default.arg == 0


def test_repuesto_relationships_declared():
    """Repuesto navega a items y a los historiales agregados."""
    Repuesto = repuestos_models.Repuesto
    assert hasattr(Repuesto, "items_orden")
    assert hasattr(Repuesto, "movimientos_stock")
    assert hasattr(Repuesto, "historiales_precio")


def test_repuesto_borrado_en_is_timezone_aware():
    """borrado_en es timestamptz y nullable."""
    col = SQLModel.metadata.tables["repuesto"].c.borrado_en
    assert col.type.timezone is True
    assert col.nullable is True
