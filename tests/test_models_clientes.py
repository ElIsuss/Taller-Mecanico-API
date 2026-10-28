"""Tests for app.modules.clientes.models (C-02 task 2.2)."""

from sqlalchemy import inspect
from sqlmodel import SQLModel

import app.modules.clientes.models as clientes_models


def test_clientes_module_imports_without_errors():
    """The clientes models module must import cleanly (task 2.2 acceptance)."""
    assert clientes_models is not None


def test_cliente_model_has_expected_columns():
    """cliente: id, documento, nombre, fecha_alta, fecha_baja."""
    table = SQLModel.metadata.tables["cliente"]
    for col in ("id", "documento", "nombre", "fecha_alta", "fecha_baja"):
        assert col in table.c, f"cliente missing column: {col}"


def test_cliente_documento_partial_unique_index():
    """cliente.documento has a partial unique index where fecha_baja IS NULL."""
    indexes = SQLModel.metadata.tables["cliente"].indexes
    names = {ix.name for ix in indexes}
    assert "ix_cliente_documento_uc" in names
    ix = next(i for i in indexes if i.name == "ix_cliente_documento_uc")
    assert ix.unique is True
    where = ix.dialect_options.get("postgresql", {}).get("where")
    assert where is not None, "partial unique index must have postgresql_where"


def test_cliente_fecha_alta_fecha_baja_timezone():
    """cliente fecha_alta/fecha_baja are DateTime(timezone=True)."""
    table = SQLModel.metadata.tables["cliente"]
    assert table.c.fecha_alta.type.timezone is True
    assert table.c.fecha_baja.type.timezone is True


def test_cliente_no_cross_module_imports_needed():
    """cliente model does not import from other modules (no circular import risk)."""
    import inspect as py_inspect
    source = py_inspect.getsource(clientes_models)
    assert "from app.modules" not in source, "cliente.models must not import from other app modules"
