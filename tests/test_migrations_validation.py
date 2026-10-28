"""Validation of Alembic migrations against a real PostgreSQL database (C-02 tasks 4.1-4.4)."""

import os
import subprocess
from pathlib import Path

import asyncpg
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DB_URL = "postgresql+asyncpg://postgres:isussmegapro1010@localhost:5432/taller_mecanico_test"
SYNC_DB_URL = "postgresql+psycopg2://postgres:isussmegapro1010@localhost:5432/taller_mecanico_test"

EXPECTED_TABLES = {
    "cliente", "estado_orden", "repuesto", "rol",
    "historial_precio_repuesto", "movimiento_stock",
    "usuario", "vehiculo", "orden_trabajo", "rol_asignacion",
    "historial_estado_orden", "orden_item",
}

PARTIAL_UNIQUE_INDEXES = {
    "cliente": "ix_cliente_documento_uc",
    "repuesto": "ix_repuesto_codigo_uc",
    "usuario": "ix_usuario_email_uc",
    "vehiculo": "ix_vehiculo_patente_uc",
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
        [str(PROJECT_ROOT / ".venv" / "Scripts" / "alembic.exe")] + args,
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
    return await asyncpg.connect(
        "postgresql://postgres:isussmegapro1010@localhost:5432/taller_mecanico_test"
    )


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
    """4.3: partial unique indexes (postgresql_where fecha_baja IS NULL) exist."""
    _run_alembic(["upgrade", "head"])

    conn = await _pg()
    try:
        indexes = await _index_names(conn)
    finally:
        await conn.close()

    for table, index_name in PARTIAL_UNIQUE_INDEXES.items():
        assert index_name in indexes, f"Missing partial unique index {index_name} on {table}"
        indexdef = indexes[index_name]
        assert "WHERE fecha_baja IS NULL" in indexdef.upper(), (
            f"Index {index_name} is not a partial unique index (no WHERE fecha_baja IS NULL)"
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
    """4.4b: RN-15 rejects UPDATE and DELETE (allows INSERT) on a protected table."""
    _run_alembic(["upgrade", "head"])

    conn = await _pg()
    try:
        # Insert parent repuesto, then a movimiento_stock row (INSERT is allowed).
        await conn.execute(
            "INSERT INTO repuesto (id, codigo, nombre, precio, stock) VALUES (1, 'REP-001', 'Test', 10.0, 5)"
        )
        await conn.execute(
            "INSERT INTO movimiento_stock (id, repuesto_id, tipo, cantidad) VALUES (1, 1, 'alta', 10)"
        )

        # UPDATE must be rejected.
        with pytest.raises(asyncpg.PostgresError):
            await conn.execute("UPDATE movimiento_stock SET cantidad = 99 WHERE id = 1")

        # DELETE must be rejected.
        with pytest.raises(asyncpg.PostgresError):
            await conn.execute("DELETE FROM movimiento_stock WHERE id = 1")
    finally:
        await conn.close()
