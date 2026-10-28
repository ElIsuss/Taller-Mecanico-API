"""Carga los datos iniciales mínimos que usan los casos de prueba.

Uso: ``python seed.py``. Vacía todas las tablas y las vuelve a poblar; requiere
que el esquema exista (``alembic upgrade head``).
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

import app.core.models  # noqa: F401  (registra todos los modelos)
from app.core.config import settings
from app.core.database import create_engine_and_session_maker
from app.modules.clientes.models import Cliente, Vehiculo
from app.modules.ordenes.models import (
    EstadoOrden,
    HistorialEstadoOrden,
    ItemOrden,
    OrdenTrabajo,
)
from app.modules.repuestos.models import (
    HistorialPrecioRepuesto,
    MovimientoStock,
    Repuesto,
)
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario

PASSWORD = "Secreta123!"
ESTADOS = (
    ("PENDIENTE", "Pendiente", 1, False),
    ("EN_REPARACION", "En reparación", 2, False),
    ("TERMINADA", "Terminada", 3, True),
    ("CANCELADA", "Cancelada", 4, True),
)


def _hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    ).decode("utf-8")


async def _vaciar(engine: AsyncEngine) -> None:
    tablas = ", ".join(f'"{tabla}"' for tabla in SQLModel.metadata.tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))


async def _cargar(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    ahora = datetime.now(timezone.utc)
    password_hash = _hash(PASSWORD)

    async with session_maker() as session:
        async with session.begin():
            for codigo, descripcion, posicion, es_final in ESTADOS:
                session.add(
                    EstadoOrden(
                        codigo=codigo,
                        descripcion=descripcion,
                        posicion=posicion,
                        es_final=es_final,
                    )
                )
            await session.flush()

            usuarios = {
                "admin": Usuario(
                    email="admin@example.com",
                    nombre="Administrador",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=False,
                ),
                "admin2": Usuario(
                    email="admin2@example.com",
                    nombre="Administrador Dos",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=False,
                ),
                "recepcion": Usuario(
                    email="recepcion@example.com",
                    nombre="Recepción",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=False,
                ),
                "mecanico": Usuario(
                    email="mecanico@example.com",
                    nombre="Mecánico",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=False,
                ),
                "mecanico2": Usuario(
                    email="mecanico2@example.com",
                    nombre="Mecánico Dos",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=False,
                ),
                "cliente": Usuario(
                    email="cliente@example.com",
                    nombre="Laura",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=False,
                ),
                "nuevo": Usuario(
                    email="nuevo@example.com",
                    nombre="Nuevo Mecánico",
                    password_hash=password_hash,
                    activo=True,
                    debe_cambiar_password=True,
                ),
            }
            session.add_all(usuarios.values())
            await session.flush()

            roles = {
                "admin": "ADMIN",
                "admin2": "ADMIN",
                "recepcion": "RECEPCION",
                "mecanico": "MECANICO",
                "mecanico2": "MECANICO",
                "cliente": "CLIENTE",
                "nuevo": "MECANICO",
            }
            for clave, rol in roles.items():
                session.add(
                    AsignacionRol(
                        usuario_id=usuarios[clave].id,
                        rol=rol,
                        desde=ahora,
                        otorgada_por=usuarios["admin"].id,
                    )
                )

            laura = Cliente(
                nombre="Laura",
                documento="DOC-LAURA",
                telefono="555-1001",
                usuario_id=usuarios["cliente"].id,
            )
            jorge = Cliente(
                nombre="Jorge",
                documento="DOC-JORGE",
                telefono="555-1002",
            )
            session.add_all([laura, jorge])
            await session.flush()

            vehiculo_laura_1 = Vehiculo(
                cliente_id=laura.id,
                patente="AB123CD",
                marca="Toyota",
                modelo="Corolla",
                anio=2020,
            )
            vehiculo_laura_2 = Vehiculo(
                cliente_id=laura.id,
                patente="EF456GH",
                marca="Ford",
                modelo="Focus",
                anio=2018,
            )
            vehiculo_jorge = Vehiculo(
                cliente_id=jorge.id,
                patente="IJ789KL",
                marca="Chevrolet",
                modelo="Onix",
                anio=2021,
            )
            session.add_all([vehiculo_laura_1, vehiculo_laura_2, vehiculo_jorge])
            await session.flush()

            filtro = Repuesto(
                codigo="REP-001",
                descripcion="Filtro de aceite",
                precio=Decimal("8500.00"),
                stock=10,
            )
            pastillas = Repuesto(
                codigo="REP-002",
                descripcion="Pastillas de freno",
                precio=Decimal("4000.00"),
                stock=4,
            )
            bujia = Repuesto(
                codigo="REP-003",
                descripcion="Bujía",
                precio=Decimal("1200.00"),
                stock=2,
            )
            aceite = Repuesto(
                codigo="REP-004",
                descripcion="Aceite por litro",
                precio=Decimal("900.00"),
                stock=20,
            )
            repuestos = [filtro, pastillas, bujia, aceite]
            session.add_all(repuestos)
            await session.flush()

            for repuesto in repuestos:
                session.add(
                    MovimientoStock(
                        repuesto_id=repuesto.id,
                        usuario_id=usuarios["admin"].id,
                        cantidad=repuesto.stock,
                        motivo="Stock inicial",
                        cuando=ahora,
                    )
                )

            orden_1 = OrdenTrabajo(
                vehiculo_id=vehiculo_laura_1.id,
                estado="PENDIENTE",
                falla="Ruido en el motor",
                creada_en=ahora,
                total=Decimal("4000.00"),
            )
            orden_2 = OrdenTrabajo(
                vehiculo_id=vehiculo_jorge.id,
                mecanico_id=usuarios["mecanico"].id,
                estado="EN_REPARACION",
                falla="Cambio de bujías",
                creada_en=ahora,
                total=Decimal("4800.00"),
            )
            session.add_all([orden_1, orden_2])
            await session.flush()

            session.add_all(
                [
                    ItemOrden(
                        orden_id=orden_1.id,
                        repuesto_id=pastillas.id,
                        cantidad=1,
                        precio_unitario=pastillas.precio,
                    ),
                    ItemOrden(
                        orden_id=orden_2.id,
                        repuesto_id=bujia.id,
                        cantidad=4,
                        precio_unitario=bujia.precio,
                    ),
                    HistorialEstadoOrden(
                        orden_id=orden_1.id,
                        desde_estado=None,
                        hasta_estado="PENDIENTE",
                        usuario_id=usuarios["admin"].id,
                        cuando=ahora,
                    ),
                    HistorialEstadoOrden(
                        orden_id=orden_2.id,
                        desde_estado=None,
                        hasta_estado="PENDIENTE",
                        usuario_id=usuarios["admin"].id,
                        cuando=ahora,
                    ),
                    HistorialEstadoOrden(
                        orden_id=orden_2.id,
                        desde_estado="PENDIENTE",
                        hasta_estado="EN_REPARACION",
                        usuario_id=usuarios["mecanico"].id,
                        cuando=ahora,
                    ),
                    HistorialPrecioRepuesto(
                        repuesto_id=filtro.id,
                        usuario_id=usuarios["admin"].id,
                        precio_anterior=Decimal("8000.00"),
                        precio_nuevo=Decimal("8500.00"),
                        cuando=ahora,
                    ),
                    EventoSeguridad(
                        actor="SISTEMA",
                        accion="Carga de los datos iniciales",
                        cuando=ahora,
                    ),
                ]
            )


async def main() -> None:
    engine, session_maker = create_engine_and_session_maker()
    try:
        await _vaciar(engine)
        await _cargar(session_maker)
    finally:
        await engine.dispose()
    print("Datos iniciales cargados.")


if __name__ == "__main__":
    asyncio.run(main())
