"""Tests for app.modules.ordenes.models (C-02 task 2.5)."""

from sqlalchemy import Numeric, UniqueConstraint
from sqlmodel import SQLModel

import app.modules.ordenes.models as ordenes_models


def test_ordenes_module_imports_without_errors():
    """The ordenes models module must import cleanly (task 2.5 acceptance)."""
    assert ordenes_models is not None


def test_estado_orden_pk_is_codigo():
    """estado_orden usa codigo como PK, con posicion unica y es_final."""
    table = SQLModel.metadata.tables["estado_orden"]
    assert {"codigo", "descripcion", "posicion", "es_final"} <= set(table.c.keys())
    assert [c.name for c in table.primary_key.columns] == ["codigo"]
    assert table.c.posicion.unique is True
    assert "codigo" in table.c and "id" not in table.c


def test_orden_trabajo_has_all_fks_and_indexes():
    """orden_trabajo: vehiculo_id, mecanico_id (nullable) y estado FK."""
    table = SQLModel.metadata.tables["orden_trabajo"]
    targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "vehiculo.id" in targets
    assert "usuario.id" in targets
    assert "estado_orden.codigo" in targets
    assert table.c.mecanico_id.nullable is True

    indexed_columns = {tuple(col.name for col in ix.columns) for ix in table.indexes}
    for col in ("vehiculo_id", "mecanico_id", "estado"):
        assert (col,) in indexed_columns, f"orden_trabajo.{col} debe tener indice"


def test_orden_trabajo_total_es_numeric_12_2():
    """total se modela como NUMERIC(12,2) y arranca en 0."""
    col = SQLModel.metadata.tables["orden_trabajo"].c.total
    assert isinstance(col.type, Numeric)
    assert col.type.precision == 12
    assert col.type.scale == 2
    assert col.default is not None


def test_orden_trabajo_check_total_no_negativo():
    """total >= 0."""
    checks = {
        c.name: str(c.sqltext).lower()
        for c in SQLModel.metadata.tables["orden_trabajo"].constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert checks.get("ck_orden_trabajo_total_no_negativo") == "total >= 0"


def test_item_orden_columns_fks_and_unique():
    """item_orden: orden_id, repuesto_id, cantidad, precio_unitario y UNIQUE compuesta."""
    table = SQLModel.metadata.tables["item_orden"]
    assert {"id", "orden_id", "repuesto_id", "cantidad", "precio_unitario"} <= set(table.c.keys())
    targets = {fk.target_fullname for fk in table.foreign_keys}
    assert "orden_trabajo.id" in targets
    assert "repuesto.id" in targets

    uniques = {
        tuple(col.name for col in c.columns)
        for c in table.constraints
        if isinstance(c, UniqueConstraint)
    }
    assert ("orden_id", "repuesto_id") in uniques

    precio_col = table.c.precio_unitario
    assert isinstance(precio_col.type, Numeric)
    assert (precio_col.type.precision, precio_col.type.scale) == (10, 2)


def test_item_orden_check_constraints():
    """cantidad > 0 y precio_unitario > 0."""
    checks = {
        c.name: str(c.sqltext).lower()
        for c in SQLModel.metadata.tables["item_orden"].constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert checks.get("ck_item_orden_cantidad_positiva") == "cantidad > 0"
    assert checks.get("ck_item_orden_precio_unitario_positivo") == "precio_unitario > 0"


def test_append_only_tables_have_expected_columns():
    """Tablas de solo agregado no tienen borrado logico y guardan quien/cuando."""
    expected = {
        "historial_estado_orden": {
            "id", "orden_id", "desde_estado", "hasta_estado", "usuario_id", "cuando",
        },
        "movimiento_stock": {
            "id", "repuesto_id", "orden_id", "usuario_id", "cantidad", "motivo", "cuando",
        },
        "historial_precio_repuesto": {
            "id", "repuesto_id", "usuario_id", "precio_anterior", "precio_nuevo", "cuando",
        },
    }
    for table_name, columns in expected.items():
        table = SQLModel.metadata.tables[table_name]
        assert columns <= set(table.c.keys()), f"{table_name} incompleta"
        assert "borrado_en" not in table.c
        assert "fecha_baja" not in table.c
        assert table.c.cuando.type.timezone is True


def test_historial_estado_orden_dos_fks_a_estado_orden():
    """desde_estado (nullable) y hasta_estado referencian estado_orden.codigo."""
    table = SQLModel.metadata.tables["historial_estado_orden"]
    targets = [fk.target_fullname for fk in table.foreign_keys]
    assert targets.count("estado_orden.codigo") == 2
    assert table.c.desde_estado.nullable is True
    assert table.c.hasta_estado.nullable is False


def test_movimiento_stock_check_cantidad_no_cero():
    """cantidad <> 0 (RN-14)."""
    checks = {
        c.name: str(c.sqltext).lower()
        for c in SQLModel.metadata.tables["movimiento_stock"].constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert checks.get("ck_movimiento_stock_cantidad_no_cero") == "cantidad <> 0"


def test_historial_precio_repuesto_checks():
    """precio_nuevo > 0 y distinto de precio_anterior (RN-20)."""
    checks = {
        c.name: str(c.sqltext).lower()
        for c in SQLModel.metadata.tables["historial_precio_repuesto"].constraints
        if c.__class__.__name__ == "CheckConstraint"
    }
    assert checks.get("ck_historial_precio_nuevo_positivo") == "precio_nuevo > 0"
    assert checks.get("ck_historial_precio_cambio") == "precio_nuevo <> precio_anterior"


def test_todas_las_fks_de_ordenes_tienen_indice():
    """Cada FK de las tablas de ordenes tiene indice (regla del proyecto)."""
    para_revisar = {
        "orden_trabajo": ("vehiculo_id", "mecanico_id", "estado"),
        "item_orden": ("orden_id", "repuesto_id"),
        "historial_estado_orden": ("orden_id", "desde_estado", "hasta_estado", "usuario_id"),
        "movimiento_stock": ("repuesto_id", "orden_id", "usuario_id"),
        "historial_precio_repuesto": ("repuesto_id", "usuario_id"),
    }
    for table_name, columnas in para_revisar.items():
        table = SQLModel.metadata.tables[table_name]
        indexed_columns = {tuple(col.name for col in ix.columns) for ix in table.indexes}
        for col in columnas:
            assert (col,) in indexed_columns, f"{table_name}.{col} sin indice"


def test_ordenes_relationships_declared():
    """OrdenTrabajo navega a vehiculo, mecanico, estado, items e historiales."""
    OrdenTrabajo = ordenes_models.OrdenTrabajo
    for attr in (
        "vehiculo",
        "mecanico",
        "estado_actual",
        "items",
        "historial_estados",
        "movimientos_stock",
    ):
        assert hasattr(OrdenTrabajo, attr), f"OrdenTrabajo missing relationship: {attr}"
