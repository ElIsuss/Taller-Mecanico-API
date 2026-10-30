"""Validation of Alembic migrations against a real PostgreSQL database (C-02 tasks 4.1-4.4).

Requires a reachable PostgreSQL and the env var TEST_DATABASE_URL, e.g.:
  TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/taller_mecanico_test
"""

import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DB_URL:
    pytest.skip(
        "TEST_DATABASE_URL no está definida; se omiten las validaciones contra PostgreSQL",
        allow_module_level=True,
    )
ASYNC_DB_URL = TEST_DB_URL.replace("postgresql+asyncpg://", "postgresql://")

EXPECTED_TABLES = {
    "usuario", "asignacion_rol", "intento_acceso", "evento_seguridad",
    "cliente", "vehiculo", "repuesto",
    "estado_orden", "orden_trabajo", "item_orden",
    "historial_estado_orden", "movimiento_stock", "historial_precio_repuesto",
}

PARTIAL_UNIQUE_INDEXES = {
    "ix_vehiculo_patente_uc": "BORRADO_EN IS NULL",
    "ix_repuesto_codigo_uc": "BORRADO_EN IS NULL",
    "ix_asignacion_rol_usuario_rol_uc": "REVOCADA_EN IS NULL",
}

PROTECTED_TABLES = (
    "historial_estado_orden",
    "movimiento_stock",
    "historial_precio_repuesto",
)


def _run_alembic(args):
    env = dict(os.environ)
    env["DATABASE_URL"] = TEST_DB_URL
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "alembic"] + args,
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True, env=env,
    )


def _ensure_clean():
    """Leave the test database at the 'base' state (no tables from C-02)."""
    _run_alembic(["downgrade", "base"])


@pytest.fixture(autouse=True)
def clean_db():
    _ensure_clean()
    yield
    _ensure_clean()


async def _pg():
    return await asyncpg.connect(ASYNC_DB_URL)


async def _table_names(conn):
    rows = await conn.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    return {r["table_name"] for r in rows}


async def _index_names(conn):
    rows = await conn.fetch(
        "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'"
    )
    return {r["indexname"]: r["indexdef"] for r in rows}


async def _triggers_exist(conn):
    rows = await conn.fetch(
        "SELECT tgname, tgrelid::regclass::text AS tabla FROM pg_trigger t "
        "JOIN pg_class c ON c.oid = t.tgrelid "
        "WHERE c.relnamespace = 'public'::regnamespace AND NOT t.tgisinternal"
    )
    return {r["tabla"]: r["tgname"] for r in rows}


@pytest.mark.asyncio
async def test_4_1_upgrade_head_creates_all_tables():
    """4.1: `alembic upgrade head` creates all C-02 tables."""
    result = _run_alembic(["upgrade", "head"])
    assert result.returncode == 0, f"upgrade head failed: {result.stderr}"

    conn = await _pg()
    try:
        tables = await _table_names(conn)
    finally:
        await conn.close()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"Tables missing after upgrade head: {sorted(missing)}"


@pytest.mark.asyncio
async def test_4_2_downgrade_base_drops_all_tables():
    """4.2: `alembic downgrade base` drops all tables in correct order."""
    _run_alembic(["upgrade", "head"])
    result = _run_alembic(["downgrade", "base"])
    assert result.returncode == 0, f"downgrade base failed: {result.stderr}"

    conn = await _pg()
    try:
        tables = await _table_names(conn)
    finally:
        await conn.close()

    leftover = EXPECTED_TABLES & tables
    assert not leftover, f"Tables still present after downgrade base: {sorted(leftover)}"


@pytest.mark.asyncio
async def test_4_3_partial_unique_indexes_exist():
    """4.3: los indices unicos parciales del TP existen con su predicado."""
    _run_alembic(["upgrade", "head"])

    conn = await _pg()
    try:
        indexes = await _index_names(conn)
    finally:
        await conn.close()

    for index_name, predicate in PARTIAL_UNIQUE_INDEXES.items():
        assert index_name in indexes, f"Missing partial unique index {index_name}"
        assert predicate in indexes[index_name].upper(), (
            f"Index {index_name} no es parcial: {indexes[index_name]}"
        )


@pytest.mark.asyncio
async def test_4_4_trigger_exists_on_protected_tables():
    """4.4a: RN-15 trigger exists on each protected (solo-agregado) table."""
    _run_alembic(["upgrade", "head"])

    conn = await _pg()
    try:
        triggers = await _triggers_exist(conn)
    finally:
        await conn.close()

    for table in PROTECTED_TABLES:
        assert table in triggers, f"Missing trigger on protected table {table}"


@pytest.mark.asyncio
async def test_4_4_trigger_rejects_update_and_delete():
    """4.4b: RN-15 rejects UPDATE and DELETE (allows INSERT) on all protected tables."""
    _run_alembic(["upgrade", "head"])

    conn = await _pg()
    try:
        # Fixtures base
        await conn.execute(
            "INSERT INTO usuario (id, email, nombre, password_hash, activo, debe_cambiar_password) "
            "VALUES (1, 'mecanico@test.com', 'Mecanico', 'hash', true, false)"
        )
        await conn.execute(
            "INSERT INTO repuesto (id, codigo, descripcion, precio, stock) "
            "VALUES (1, 'REP-001', 'Test', 10.0, 5)"
        )
        await conn.execute(
            "INSERT INTO cliente (id, nombre, documento, telefono) "
            "VALUES (1, 'Juan Perez', '12345678', '555-1234')"
        )
        await conn.execute(
            "INSERT INTO vehiculo (id, patente, marca, modelo, anio, cliente_id) "
            "VALUES (1, 'AA123BB', 'Fiat', 'Cronos', 2022, 1)"
        )
        await conn.execute(
            "INSERT INTO estado_orden (codigo, descripcion, posicion, es_final) "
            "VALUES ('PENDIENTE', 'Pendiente', 1, false)"
        )
        await conn.execute(
            "INSERT INTO orden_trabajo (id, vehiculo_id, estado, total, falla) "
            "VALUES (1, 1, 'PENDIENTE', 100.0, 'Falla en frenos')"
        )

        # 1. Probar movimiento_stock
        await conn.execute(
            "INSERT INTO movimiento_stock (id, repuesto_id, usuario_id, cantidad, motivo) "
            "VALUES (1, 1, 1, 10, 'ingreso')"
        )
        with pytest.raises(asyncpg.PostgresError) as exc_info_mov_upd:
            await conn.execute("UPDATE movimiento_stock SET cantidad = 99 WHERE id = 1")
        assert "RN-15" in str(exc_info_mov_upd.value)

        with pytest.raises(asyncpg.PostgresError) as exc_info_mov_del:
            await conn.execute("DELETE FROM movimiento_stock WHERE id = 1")
        assert "RN-15" in str(exc_info_mov_del.value)

        # 2. Probar historial_precio_repuesto
        await conn.execute(
            "INSERT INTO historial_precio_repuesto (id, repuesto_id, precio_anterior, precio_nuevo, usuario_id) "
            "VALUES (1, 1, 10.0, 15.0, 1)"
        )
        with pytest.raises(asyncpg.PostgresError) as exc_info_pre_upd:
            await conn.execute("UPDATE historial_precio_repuesto SET precio_nuevo = 20.0 WHERE id = 1")
        assert "RN-15" in str(exc_info_pre_upd.value)

        with pytest.raises(asyncpg.PostgresError) as exc_info_pre_del:
            await conn.execute("DELETE FROM historial_precio_repuesto WHERE id = 1")
        assert "RN-15" in str(exc_info_pre_del.value)

        # 3. Probar historial_estado_orden
        await conn.execute(
            "INSERT INTO historial_estado_orden (id, orden_id, desde_estado, hasta_estado, usuario_id) "
            "VALUES (1, 1, NULL, 'PENDIENTE', 1)"
        )
        with pytest.raises(asyncpg.PostgresError) as exc_info_ord_upd:
            await conn.execute("UPDATE historial_estado_orden SET hasta_estado = 'TERMINADA' WHERE id = 1")
        assert "RN-15" in str(exc_info_ord_upd.value)

        with pytest.raises(asyncpg.PostgresError) as exc_info_ord_del:
            await conn.execute("DELETE FROM historial_estado_orden WHERE id = 1")
        assert "RN-15" in str(exc_info_ord_del.value)
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_4_5_autogenerate_sin_diferencias():
    """4.5: el esquema migrado coincide con los modelos (sin drift al autogenerar)."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlmodel import SQLModel

    import app.core.models  # noqa: F401

    _run_alembic(["upgrade", "head"])
    engine = create_async_engine(TEST_DB_URL)

    def _diff(sync_conn):
        context = MigrationContext.configure(sync_conn)
        return compare_metadata(context, SQLModel.metadata)

    try:
        async with engine.connect() as conn:
            diff = await conn.run_sync(_diff)
    finally:
        await engine.dispose()

    assert diff == [], f"Modelos y migraciones divergen: {diff}"
