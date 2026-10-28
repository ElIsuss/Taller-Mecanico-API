"""Tests for Alembic infrastructure (C-02 tasks 1.1, 1.2)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Import every model module so SQLModel.metadata is fully populated (mirrors migrations/env.py).
import app.modules.clientes.models  # noqa: F401
import app.modules.ordenes.models  # noqa: F401
import app.modules.repuestos.models  # noqa: F401
import app.modules.usuarios.models  # noqa: F401


def test_alembic_ini_exists():
    """alembic.ini must exist at project root."""
    assert (PROJECT_ROOT / "alembic.ini").is_file()


def test_alembic_env_exists():
    """migrations/env.py must exist."""
    assert (PROJECT_ROOT / "migrations" / "env.py").is_file()


def _database_url():
    """Lee la URL de prueba del entorno; nunca hardcodear credenciales."""
    return os.environ.get("TEST_DATABASE_URL")


def test_alembic_current_runs_without_errors():
    """`alembic current` must exit 0 (env.py imports cleanly, target_metadata loads)."""
    url = _database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL no está definida")
    env = dict(os.environ)
    env["DATABASE_URL"] = url
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"alembic current failed: {result.stderr}"


def test_target_metadata_registers_expected_tables():
    """SQLModel.metadata must register all C-02 entities."""
    table_names = set(SQLModel.metadata.tables.keys())
    expected = {
        "usuario", "asignacion_rol", "intento_acceso", "evento_seguridad",
        "cliente",
        "vehiculo",
        "repuesto",
        "estado_orden", "orden_trabajo", "item_orden",
        "historial_estado_orden", "movimiento_stock", "historial_precio_repuesto",
    }
    missing = expected - table_names
    assert not missing, f"Tables missing from SQLModel.metadata: {sorted(missing)}"


def test_rol_no_es_una_tabla_segun_el_tp():
    """El TP modela el rol como CHECK en asignacion_rol, no como tabla."""
    assert "rol" not in SQLModel.metadata.tables
    assert "rol_asignacion" not in SQLModel.metadata.tables


def test_password_cambiada_en_is_timezone_aware():
    """password_cambiada_en must be DateTime(timezone=True)."""
    col = SQLModel.metadata.tables["usuario"].c.password_cambiada_en
    assert col.type.timezone is True


def test_partial_unique_indexes_defined_in_models():
    """Models declare the TP partial unique indexes (WHERE ... IS NULL)."""
    expected = {
        "vehiculo": ("ix_vehiculo_patente_uc", "borrado_en IS NULL"),
        "repuesto": ("ix_repuesto_codigo_uc", "borrado_en IS NULL"),
        "asignacion_rol": ("ix_asignacion_rol_usuario_rol_uc", "revocada_en IS NULL"),
    }
    for table_name, (index_name, predicate) in expected.items():
        indexes = SQLModel.metadata.tables[table_name].indexes
        names = {ix.name for ix in indexes}
        assert index_name in names, f"{table_name} missing partial unique index {index_name}"
        index = next(ix for ix in indexes if ix.name == index_name)
        where = index.dialect_options["postgresql"].get("where")
        assert where is not None
        assert predicate.upper() in str(where).upper()


def test_database_exports_sqlmodel_metadata():
    """app.core.database must export SQLModel.metadata toward Alembic (task 1.2)."""
    from app.core.database import SQLModel_metadata

    assert SQLModel_metadata is SQLModel.metadata
    assert len(SQLModel_metadata.tables) > 0


async def test_autogenerate_detects_tables():
    """`alembic revision --autogenerate` must detect all model tables (tasks 1.2 / 3.1)."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    url = _database_url()
    if not url:
        pytest.skip("TEST_DATABASE_URL no está definida")
    connectable = create_async_engine(url)

    def _compare(sync_conn):
        context = MigrationContext.configure(sync_conn)
        compare_metadata(context, SQLModel.metadata)
        return True

    try:
        async with connectable.connect() as conn:
            assert await conn.run_sync(_compare)
    finally:
        await connectable.dispose()
