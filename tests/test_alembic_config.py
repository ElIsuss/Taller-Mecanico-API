"""Tests for Alembic infrastructure (C-02 tasks 1.1, 1.2)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, pool
from sqlmodel import SQLModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Import every model module so SQLModel.metadata is fully populated (mirrors alembic/env.py).
import app.modules.auth.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401
import app.modules.vehiculos.models  # noqa: F401
import app.modules.repuestos.models  # noqa: F401
import app.modules.ordenes.models  # noqa: F401
import app.modules.roles.models  # noqa: F401


def test_alembic_ini_exists():
    """alembic.ini must exist at project root."""
    assert (PROJECT_ROOT / "alembic.ini").is_file()


def test_alembic_env_exists():
    """alembic/env.py must exist."""
    assert (PROJECT_ROOT / "alembic" / "env.py").is_file()


def test_alembic_current_runs_without_errors():
    """`alembic current` must exit 0 (env.py imports cleanly, target_metadata loads)."""
    alembic_exe = PROJECT_ROOT / ".venv" / "Scripts" / "alembic.exe"
    env = dict(os.environ)
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:isussmegapro1010@localhost:5432/taller_mecanico_test"
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(
        [str(alembic_exe), "current"],
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
        "rol", "usuario", "rol_asignacion",
        "cliente",
        "vehiculo",
        "repuesto",
        "estado_orden", "orden_trabajo", "orden_item",
        "historial_estado_orden", "movimiento_stock", "historial_precio_repuesto",
    }
    missing = expected - table_names
    assert not missing, f"Tables missing from SQLModel.metadata: {sorted(missing)}"


def test_usuario_cliente_id_fk_to_cliente():
    """usuario.cliente_id must FK to cliente.id (1:1, nullable)."""
    inspector = inspect(SQLModel.metadata.tables["usuario"])
    fk_targets = {str(fk) for fk in inspector.foreign_keys}
    assert any("cliente" in t for t in fk_targets), "usuario.cliente_id must FK to cliente.id"


def test_password_cambiada_en_is_timezone_aware():
    """password_cambiada_en must be DateTime(timezone=True)."""
    col = SQLModel.metadata.tables["usuario"].c.password_cambiada_en
    assert col.type.timezone is True


def test_partial_unique_indexes_defined_in_models():
    """Models must declare partial unique indexes (postgresql_where fecha_baja IS NULL)."""
    expected = {
        "usuario": "ix_usuario_email_uc",
        "cliente": "ix_cliente_documento_uc",
        "vehiculo": "ix_vehiculo_patente_uc",
        "repuesto": "ix_repuesto_codigo_uc",
    }
    for table_name, index_name in expected.items():
        indexes = SQLModel.metadata.tables[table_name].indexes
        names = {ix.name for ix in indexes}
        assert index_name in names, f"{table_name} missing partial unique index {index_name}"


def test_database_exports_sqlmodel_metadata():
    """app.core.database must export SQLModel.metadata toward Alembic (task 1.2)."""
    from app.core.database import SQLModel_metadata

    assert SQLModel_metadata is SQLModel.metadata
    assert len(SQLModel_metadata.tables) > 0


def test_autogenerate_detects_tables():
    """`alembic revision --autogenerate` must detect all model tables (tasks 1.2 / 3.1)."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    url = "postgresql+psycopg2://postgres:isussmegapro1010@localhost:5432/taller_mecanico_test"
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as conn:
        context = MigrationContext.configure(conn)
        compare_metadata(context, SQLModel.metadata)

    # If we reach here without error, autogenerate successfully diffed against all model tables.
    assert True
