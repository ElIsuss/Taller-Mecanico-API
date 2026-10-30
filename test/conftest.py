"""Fixtures de integración para los endpoints (C-03)."""

import itertools
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

if TEST_DATABASE_URL:
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "taller_mecanico")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "test-admin-password")

from sqlmodel import SQLModel  # noqa: E402

from app.main import app  # noqa: E402
from app.modules.clientes.models import Cliente, Vehiculo  # noqa: E402
from app.modules.ordenes.models import EstadoOrden  # noqa: E402
from app.modules.repuestos.models import Repuesto  # noqa: E402
from app.modules.usuarios.models import Usuario  # noqa: E402

ESTADOS = (
    ("PENDIENTE", "Pendiente", 1, False),
    ("EN_REPARACION", "En reparación", 2, False),
    ("TERMINADA", "Terminada", 3, True),
    ("CANCELADA", "Cancelada", 4, True),
)


def _dsn() -> str:
    return TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


def _alembic(args: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
async def db_ready():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL no está definida")

    result = _alembic(["upgrade", "head"])
    assert result.returncode == 0, f"alembic upgrade head falló: {result.stderr}"

    conn = await asyncpg.connect(_dsn())
    try:
        tablas = ", ".join(f'"{t}"' for t in SQLModel.metadata.tables)
        await conn.execute(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE")
        for codigo, descripcion, posicion, es_final in ESTADOS:
            await conn.execute(
                "INSERT INTO estado_orden (codigo, descripcion, posicion, es_final) "
                "VALUES ($1, $2, $3, $4)",
                codigo,
                descripcion,
                posicion,
                es_final,
            )
    finally:
        await conn.close()
    yield


@pytest.fixture
async def client(db_ready):
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class Seed:
    def __init__(self, session_maker) -> None:
        self._session_maker = session_maker
        self._contador = itertools.count(1)

    async def _guardar(self, obj):
        async with self._session_maker() as session:
            async with session.begin():
                session.add(obj)
                await session.flush()
        return obj

    async def usuario(
        self,
        email: str | None = None,
        nombre: str = "Usuario Test",
        activo: bool = True,
    ) -> Usuario:
        n = next(self._contador)
        return await self._guardar(
            Usuario(
                email=email or f"usuario{n}@test.com",
                nombre=nombre,
                password_hash="hash",
                activo=activo,
                debe_cambiar_password=False,
            )
        )

    async def cliente(
        self,
        nombre: str = "Cliente Test",
        documento: str | None = None,
        telefono: str = "555-0000",
        usuario_id: int | None = None,
    ) -> Cliente:
        n = next(self._contador)
        return await self._guardar(
            Cliente(
                nombre=nombre,
                documento=documento or f"DOC-{n:05d}",
                telefono=telefono,
                usuario_id=usuario_id,
            )
        )

    async def vehiculo(
        self,
        cliente_id: int,
        patente: str | None = None,
        marca: str = "Marca",
        modelo: str = "Modelo",
        anio: int = 2020,
    ) -> Vehiculo:
        n = next(self._contador)
        return await self._guardar(
            Vehiculo(
                cliente_id=cliente_id,
                patente=patente or f"AAA{n:03d}",
                marca=marca,
                modelo=modelo,
                anio=anio,
            )
        )

    async def repuesto(
        self,
        codigo: str | None = None,
        descripcion: str = "Repuesto Test",
        precio: str = "10.00",
        stock: int = 10,
    ) -> Repuesto:
        from decimal import Decimal

        n = next(self._contador)
        return await self._guardar(
            Repuesto(
                codigo=codigo or f"REP-{n:03d}",
                descripcion=descripcion,
                precio=Decimal(precio),
                stock=stock,
            )
        )


@pytest.fixture
async def seed(client) -> Seed:
    return Seed(app.state.async_session_maker)
