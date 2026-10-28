"""Tests for app.modules.ordenes.models (C-02 task 2.5)."""

from sqlalchemy import inspect
from sqlmodel import SQLModel

import app.modules.ordenes.models as ordenes_models


def test_ordenes_module_imports_without_errors():
    """The ordenes models module must import cleanly (task 2.5 acceptance)."""
    assert ordenes_models is not None


def test_estado_orden_model_has_catalog_columns():
    """estado_orden: id, nombre, fecha_alta, fecha_baja."""
    table = SQLModel.metadata.tables["estado_orden"]
    for col in ("id", "nombre", "fecha_alta", "fecha_baja"):
        assert col in table.c, f"estado_orden missing column: {col}"


def test_orden_trabajo_has_all_fks():
    """orden_trabajo: cliente_id, vehiculo_id, mecanico_asignado_id, estado_id FKs."""
    inspector = inspect(SQLModel.metadata.tables["orden_trabajo"])
    fk_targets = {str(fk) for fk in inspector.foreign_keys}
    assert any("cliente" in t for t in fk_targets), "orden_trabajo.cliente_id must FK to cliente.id"
    assert any("vehiculo" in t for t in fk_targets), "orden_trabajo.vehiculo_id must FK to vehiculo.id"
    assert any("usuario" in t for t in fk_targets), "orden_trabajo.mecanico_asignado_id must FK to usuario.id"
    assert any("estado_orden" in t for t in fk_targets), "orden_trabajo.estado_id must FK to estado_orden.id"


def test_orden_trabajo_mecanico_asignado_is_nullable():
    """mecanico_asignado_id accepts any user and is nullable (not only MECANICO)."""
    col = SQLModel.metadata.tables["orden_trabajo"].c.mecanico_asignado_id
    assert col.nullable is True


def test_orden_item_has_fks():
    """orden_item: orden_trabajo_id, repuesto_id FKs, cantidad, precio_unitario."""
    inspector = inspect(SQLModel.metadata.tables["orden_item"])
    fk_targets = {str(fk) for fk in inspector.foreign_keys}
    assert any("orden_trabajo" in t for t in fk_targets), "orden_item.orden_trabajo_id must FK to orden_trabajo.id"
    assert any("repuesto" in t for t in fk_targets), "orden_item.repuesto_id must FK to repuesto.id"
    columns = {c.name for c in inspector.columns}
    assert "cantidad" in columns and "precio_unitario" in columns


def test_append_only_tables_exist():
    """historial_estado_orden, movimiento_stock, historial_precio_repuesto tables exist."""
    for table in ("historial_estado_orden", "movimiento_stock", "historial_precio_repuesto"):
        assert table in SQLModel.metadata.tables, f"Missing table: {table}"


def test_append_only_tables_have_no_fecha_baja():
    """Append-only tables do not declare fecha_baja (never soft-deleted)."""
    for table in ("historial_estado_orden", "movimiento_stock", "historial_precio_repuesto"):
        assert "fecha_baja" not in SQLModel.metadata.tables[table].c, f"{table} should not have fecha_baja"


def test_historial_precio_repuesto_columns():
    """historial_precio_repuesto: precio_anterior, precio_nuevo, fecha_cambio."""
    table = SQLModel.metadata.tables["historial_precio_repuesto"]
    for col in ("repuesto_id", "precio_anterior", "precio_nuevo", "fecha_cambio", "fecha_alta"):
        assert col in table.c, f"historial_precio_repuesto missing column: {col}"
