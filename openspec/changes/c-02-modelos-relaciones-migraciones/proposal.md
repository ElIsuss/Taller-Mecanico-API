# Proposal

## Why

C-01 estableció configuración, ciclo de vida de la aplicación y salud, pero no existe modelo de datos ni infraestructura de migraciones. C-02 define las entidades del dominio, sus relaciones y la base de migraciones Alembic para que los cambios posteriores (contratos/CRUD, autenticación, repositorios) tengan algo que persistir.

## What Changes

- Inicializar infraestructura de Alembic (`alembic.ini`, `alembic/env.py`, `alembic/versions/`)
- Modelos SQLModel: `usuario`, `rol`, `rol_asignacion`, `cliente`, `vehiculo`, `repuesto`, `estado_orden`, `orden_trabajo`, `orden_item`
- Tablas de solo agregado: `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto`
- Índices únicos parciales (`postgresql_where`, solo vigentes) para unicidad de email, documento, patente y código (RN-01)
- Disparador de base de datos que protege las tablas de solo agregado contra `UPDATE`/`DELETE` (RN-15), en migración escrita a mano
- Dos migraciones Alembic: una autogenerate y una escrita a mano para el disparador
- Relación `usuario.cliente_id` → `cliente.id` (1:1); `orden_trabajo.mecanico_asignado_id` acepta cualquier usuario
- `fecha_baja`/`fecha_alta` declaradas por modelo (sin mixin compartido); `password_cambiada_en` como `DateTime(timezone=True)`

## Capabilities

### New Capabilities

- `auth`: identidad del sistema — usuarios, roles y asignaciones de rol con vigencia
- `clientes`: fichas de cliente con borrado lógico y unicidad de documento entre vigentes
- `vehiculos`: vehículos vinculados a cliente, con patente única entre vigentes y bloqueo de baja si tiene órdenes abiertas
- `repuestos`: catálogo de repuestos, movimientos de stock e historial de precios; stock solo modificable vía movimientos
- `ordenes`: órdenes de trabajo, ítems de repuesto, catálogo de estados de orden e historial de cambios de estado

### Modified Capabilities

(Ninguna — no hay specs preexistentes en el proyecto)

## Impact

- Código nuevo: `app/modules/auth/models.py`, `app/modules/clientes/models.py`, `app/modules/vehiculos/models.py`, `app/modules/repuestos/models.py`, `app/modules/ordenes/models.py`, `app/modules/roles/models.py`
- Directorio nuevo: `alembic/` con configuración y versiones de migración
- `app/core/database.py`: posible ajuste para importar `Base.metadata` de SQLModel hacia Alembic
- Los cambios C-03 a C-08 dependen de este modelo de datos
