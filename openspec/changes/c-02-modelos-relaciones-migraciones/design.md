# Design

## Context

C-01 dejó lista la aplicación (config, database, lifespan, health checks) pero sin modelo de datos ni migraciones. No existe `alembic/` ni ningún modelo SQLModel. Los módulos `app/modules/*` existen solo con `__init__.py`. El stack es Python 3.12, FastAPI 0.111, SQLModel/SQLAlchemy 2.0 async, asyncpg, PostgreSQL 16, Alembic 1.13.

Ver proposal.md para motivación completa.

## Goals / Non-Goals

**Goals:**
- Definir las 11 entidades del dominio y sus relaciones en SQLModel
- Crear tablas de solo agregado protegidas por disparador de base (RN-15)
- Índices únicos parciales para unicidad solo entre vigentes (RN-01)
- Inicializar Alembic con 2 migraciones (autogenerate + hand-written para el disparador)
- `password_cambiada_en` como `DateTime(timezone=True)` para RN-07
- Relación `usuario.cliente_id` → `cliente.id` (1:1, Opción A acordada)
- `mecanico_asignado_id` acepta cualquier usuario (no solo MECANICO)
- Soft-delete por modelo (`fecha_alta`/`fecha_baja` declarados en cada uno, sin mixin compartido)

**Non-Goals:**
- Seed data (admin, roles, estados) — queda para C-04/C-02 según se acuerde; el admin se deja para C-04
- Routers, schemas Pydantic, servicios, repositorios, Unit of Work — son C-03 a C-06
- Autenticación, JWT, bcrypt en endpoints — es C-04

## Decisions

### 1. Estructura de archivos por módulo
Cada módulo (`auth`, `clientes`, `vehiculos`, `repuestos`, `ordenes`, `roles`) tiene su propio `models.py` con las entidades que le pertenecen. Las relaciones cruzan módulos mediante FKs (por ejemplo, `vehiculo.cliente_id` → `cliente.id`, `orden_trabajo.vehiculo_id` → `vehiculo.id`).

**Alternativa considerada:** Todos los modelos en un solo archivo `app/core/models.py`.
**Razón para no elegirla:** La arquitectura del proyecto organiza por módulos y C-03 en adelante espera módulos independientes con sus propios modelos, schemas, routers, etc.

### 2. usuario → cliente (1:1)
`usuario.cliente_id` es FK nullable → `cliente.id`. Un usuario puede o no tener ficha de cliente.

**Alternativa considerada:** `cliente.usuario_id` → `usuario.id`.
**Razón para no elegirla:** El alcance de C-02 acordó la Opción A (usuario apunta a cliente).

### 3. Soft-delete sin mixin compartido
Cada modelo declara `fecha_alta` y `fecha_baja` por separado.

**Alternativa considerada:** Mixin `Timestamped`/`SoftDelete` heredado por todos.
**Razón para no elegirla:** El alcance acordó "cada modelo por separado".

### 4. Índices únicos parciales (RN-01)
Se crean con `postgresql_where` filtrando `fecha_baja IS NULL` sobre: `usuario.email`, `cliente.documento`, `vehiculo.patente`, `repuesto.codigo`.

### 5. Disparador RN-15
Se escribe en una migración Alembic hecha a mano porque autogenerate no detecta funciones ni disparadores de PostgreSQL. El disparador rechaza `UPDATE` y `DELETE` en `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto`. No rechaza `INSERT`.

### 6. Dos migraciones
- Migración 1 (autogenerate): todas las tablas, FKs, índices, constraints
- Migración 2 (hand-written): función + disparador de solo agregado

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Relación usuario↔cliente no definida en el ERD de la KB | Acordada como Opción A en explore; documentada aquí |
| `lazy="raise"` (carga perezosa prohibida) afecta C-06 | Diseñar relaciones pensando en carga anticipada desde ahora |
| Disparador en migración manual puede desincronizarse con autogenerate | Probar `alembic upgrade`/`downgrade` en una DB real de prueba |
| `password_cambiada_en` con precisión insuficiente rompe RN-07 | Usar `DateTime(timezone=True)` (timestamptz) |
| FKs cruzando módulos pueden crear importaciones circulares | Importar modelos solo donde se definen las relaciones; evitar importar de módulos que a su vez importen de vuelta |

## Migration Plan

1. `alembic init alembic` (o crear `alembic.ini` y `alembic/env.py` manualmente)
2. Configurar `env.py` para importar `SQLModel.metadata` desde los modelos de cada módulo
3. `alembic revision --autogenerate -m "initial models"` → revisar y ajustar
4. Crear migración hand-written para el disparador RN-15
5. `alembic upgrade head` en una base de datos de prueba PostgreSQL
6. `alembic downgrade base` para verificar reversibilidad

## Open Questions

- ¿Dónde se define `Base.metadata` de SQLModel para que Alembic lo vea (un archivo central o agregado por módulo)? — decisión de implementación, no cambia specs ni tareas.
- ¿Los estados de orden y roles se insertan en la migración inicial o en `seed.py`? — el seed queda fuera de este change; los datos catálogo podrían ir en la migración o en seed.
