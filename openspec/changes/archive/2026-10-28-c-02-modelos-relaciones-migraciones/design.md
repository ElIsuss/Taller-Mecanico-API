# Design

## Context

C-01 dejó lista la aplicación (config, database, lifespan, health checks) pero sin modelo de datos ni migraciones. El esquema debe respetar los nombres de tablas y columnas del TP Cap1a6, que son obligatorios. El stack es Python 3.12, FastAPI 0.111, SQLModel/SQLAlchemy 2.0 async, asyncpg, PostgreSQL 16, Alembic 1.13.

Ver proposal.md para motivación completa.

## Goals / Non-Goals

**Goals:**
- Definir las 13 tablas del dominio y sus relaciones en SQLModel
- Crear tablas de solo agregado protegidas por disparador de base (RN-15)
- Índices únicos parciales solo donde el TP los define (patente, código, asignación vigente)
- Inicializar Alembic con 2 migraciones (autogenerate + hand-written para el disparador)
- `password_cambiada_en` como `timestamptz` para RN-07
- Relación `cliente.usuario_id` → `usuario.id` (1:1 opcional)
- `mecanico_id` acepta cualquier usuario (no solo MECANICO)
- Soft-delete explícito con `borrado_en` solo en `vehiculo` y `repuesto`
- Dinero en `Numeric`/`Decimal`

**Non-Goals:**
- Seed data (admin, estados) — queda para C-04
- Routers, schemas Pydantic, servicios, repositorios, Unit of Work — C-03 a C-06
- Autenticación, JWT, bcrypt en endpoints — C-04
- Triggers de negocio distintos de RN-15 (transiciones, total, stock) — capa de servicio

## Decisions

### 1. Estructura de archivos por módulo + agregador central
Cada módulo (`auth`, `clientes`, `vehiculos`, `repuestos`, `ordenes`) tiene su `models.py`. Las relaciones cruzan módulos mediante FKs y forward references (`TYPE_CHECKING`). `app/core/models.py` importa todos los módulos y se usa en `alembic/env.py` y `app/main.py` para poblar `SQLModel.metadata` y configurar los mappers una sola vez.

**Alternativa considerada:** todos los modelos en `app/core/models.py`.
**Razón para no elegirla:** la arquitectura organiza por módulos y C-03+ espera módulos independientes.

### 2. cliente → usuario (1:1 opcional)
`cliente.usuario_id` es FK nullable y UNIQUE a `usuario.id`. El TP ubica la FK en `cliente`.

### 3. Soft-delete acotado
Solo `vehiculo` y `repuesto` tienen `borrado_en` (`timestamptz` nullable), porque el TP solo pide unicidad entre vigentes para patente y código. `usuario` usa `activo`; `cliente` no tiene baja lógica. No se usa mixin compartido.

### 4. Roles y estados
No hay tabla `rol`: `asignacion_rol.rol` es texto con CHECK `IN ('ADMIN','RECEPCION','MECANICO','CLIENTE')`. `estado_orden` sí es catálogo, con `codigo` como PK (usada por `orden_trabajo.estado` y por ambas columnas de `historial_estado_orden`).

### 5. Índices únicos parciales
- `vehiculo.patente` WHERE `borrado_en IS NULL`
- `repuesto.codigo` WHERE `borrado_en IS NULL`
- `asignacion_rol (usuario_id, rol)` WHERE `revocada_en IS NULL`

`usuario.email` y `cliente.documento` usan UNIQUE simple.

### 6. Disparador RN-15
Migración Alembic hecha a mano porque autogenerate no detecta funciones ni disparadores. Rechaza `UPDATE` y `DELETE` en las tres tablas de solo agregado; permite `INSERT`. Sin `;` final en los statements (asyncpg rechaza el terminador) y con `EXECUTE FUNCTION ...()`.

### 7. Dos migraciones
- Migración 1 (autogenerate): tablas, FKs, CHECKs, índices
- Migración 2 (hand-written): función + disparadores de solo agregado

### 8. Tipos
Fechas `DateTime(timezone=True)` con `server_default now()` donde corresponde. Dinero `Numeric(10,2)` (ítems/precios) y `Numeric(12,2)` (total de orden), anotados como `Decimal`. Cada FK con índice.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Nombres del TP son obligatorios y limitan el diseño | Los tests de modelos y `compare_metadata` verifican el esquema; se agregan columnas solo cuando el TP las define |
| `lazy="raise"` (carga perezosa prohibida) afecta C-06 | Diseñar relaciones pensando en carga anticipada desde ahora |
| Disparador manual puede desincronizarse con autogenerate | `test_4_5_autogenerate_sin_diferencias` + upgrade/downgrade contra PostgreSQL real |
| FKs cruzando módulos pueden crear importaciones circulares | Forward references con `TYPE_CHECKING` y agregador `app/core/models.py` |
| `compare_metadata` marca drift por CHECKs/índices | Revisar migración generada y ajustar el test al predicado normalizado por PostgreSQL |

## Migration Plan

1. `alembic init alembic` (o crear `alembic.ini` y `alembic/env.py` manualmente)
2. Configurar `env.py` para importar `app.core.models`
3. `alembic revision --autogenerate -m "initial models"` → revisar y ajustar (import de `sqlmodel`)
4. Crear migración hand-written para el disparador RN-15
5. `alembic upgrade head` en PostgreSQL de prueba
6. `alembic downgrade base` para verificar reversibilidad

## Open Questions

- ¿El seed de `estado_orden` va en la migración inicial o en `seed.py`? — fuera de este change; RN-19 exige el catálogo cargado para operar.
