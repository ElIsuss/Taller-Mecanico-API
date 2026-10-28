# Proposal

## Why

C-01 estableció configuración, ciclo de vida de la aplicación y salud, pero no existe modelo de datos ni infraestructura de migraciones. C-02 define las entidades del dominio, sus relaciones y la base de migraciones Alembic para que los cambios posteriores (contratos/CRUD, autenticación, repositorios) tengan algo que persistir.

El esquema sigue el enunciado del TP (Cap1a6), donde los nombres de tablas y columnas son obligatorios: se pueden agregar columnas, pero no quitar ni renombrar las definidas.

## What Changes

- Inicializar infraestructura de Alembic (`alembic.ini`, `alembic/env.py`, `alembic/versions/`)
- Modelos SQLModel: `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`, `cliente`, `vehiculo`, `repuesto`, `estado_orden`, `orden_trabajo`, `item_orden`
- Tablas de solo agregado: `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto`
- Roles como CHECK en `asignacion_rol.rol` (no hay tabla `rol`); estados como catálogo `estado_orden` con PK `codigo`
- Índices únicos parciales: `vehiculo.patente` y `repuesto.codigo` donde `borrado_en IS NULL`; `asignacion_rol (usuario_id, rol)` donde `revocada_en IS NULL`
- `usuario.email` y `cliente.documento` con UNIQUE simple
- Dinero con `NUMERIC(10,2)` / `NUMERIC(12,2)` y `Decimal` (nunca `float`)
- Disparador de base de datos que protege las tablas de solo agregado contra `UPDATE`/`DELETE` (RN-15), en migración escrita a mano
- Dos migraciones Alembic: una autogenerate y una escrita a mano para el disparador
- Relación `cliente.usuario_id` → `usuario.id` (1:1 opcional); `orden_trabajo.mecanico_id` acepta cualquier usuario
- `app/core/models.py` importa todos los modelos para poblar `SQLModel.metadata` y resolver forward references

## Capabilities

### New Capabilities

- `auth`: identidad del sistema — usuarios, asignaciones de rol con vigencia, intentos de acceso y eventos de seguridad
- `clientes`: fichas de cliente, unicidad de documento y vínculo opcional con un usuario
- `vehiculos`: vehículos vinculados a cliente, patente única entre vigentes y bloqueo de baja si tiene órdenes abiertas
- `repuestos`: catálogo de repuestos, movimientos de stock e historial de precios; stock solo modificable vía movimientos
- `ordenes`: órdenes de trabajo, ítems de repuesto, catálogo de estados e historial de cambios de estado

### Modified Capabilities

(Ninguna — no hay specs preexistentes en el proyecto)

## Impact

- Código nuevo: `app/modules/auth/models.py`, `app/modules/clientes/models.py`, `app/modules/vehiculos/models.py`, `app/modules/repuestos/models.py`, `app/modules/ordenes/models.py`, `app/core/models.py`
- Directorio nuevo: `alembic/` con configuración y versiones de migración
- `alembic/env.py` y `app/main.py` importan `app/core/models.py` para registrar las tablas
- Los cambios C-03 a C-08 dependen de este modelo de datos
- `app/modules/roles/models.py` queda reservado sin entidades (el rol es un CHECK, no una tabla)
