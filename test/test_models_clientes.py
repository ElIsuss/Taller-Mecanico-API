"""Tests for app.modules.clientes.models (C-02 task 2.2)."""

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel

import app.modules.clientes.models as clientes_models


def test_clientes_module_imports_without_errors():
    """The clientes models module must import cleanly (task 2.2 acceptance)."""
    assert clientes_models is not None


def test_cliente_model_has_expected_columns():
    """cliente: id, usuario_id, nombre, documento, telefono."""
    table = SQLModel.metadata.tables["cliente"]
    expected = {"id", "usuario_id", "nombre", "documento", "telefono"}
    assert expected <= set(table.c.keys()), f"cliente missing: {sorted(expected - set(table.c.keys()))}"


def test_cliente_usuario_id_is_nullable_unique_fk():
    """cliente.usuario_id es opcional, unico y apunta a usuario.id."""
    table = SQLModel.metadata.tables["cliente"]
    col = table.c.usuario_id
    assert col.nullable is True
    assert col.unique is True
    targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "usuario.id" in targets


def test_cliente_documento_is_unique_and_not_nullable():
    """cliente.documento es unico y obligatorio."""
    col = SQLModel.metadata.tables["cliente"].c.documento
    assert col.unique is True
    assert col.nullable is False


def test_cliente_has_no_soft_delete_columns():
    """El TP no define borrado logico para cliente (solo vehiculo y repuesto)."""
    columns = set(SQLModel.metadata.tables["cliente"].c.keys())
    assert "fecha_alta" not in columns
    assert "fecha_baja" not in columns
    assert "borrado_en" not in columns


def test_cliente_usuario_id_has_index():
    """La FK cliente.usuario_id esta cubierta por un indice o unique (regla del proyecto)."""
    table = SQLModel.metadata.tables["cliente"]
    indexed_columns = {tuple(col.name for col in ix.columns) for ix in table.indexes}
    unique_columns = {
        tuple(col.name for col in c.columns)
        for c in table.constraints
        if isinstance(c, UniqueConstraint)
    }
    assert ("usuario_id",) in indexed_columns or ("usuario_id",) in unique_columns


def test_cliente_no_cross_module_imports_needed():
    """cliente model no importa modulos en runtime (solo TYPE_CHECKING)."""
    import inspect as py_inspect

    source = py_inspect.getsource(clientes_models)
    runtime_imports = [
        line
        for line in source.splitlines()
        if line.startswith("from app.modules") or line.startswith("import app.modules")
    ]
    assert runtime_imports == []
