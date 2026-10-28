# Tasks

## 1. Infraestructura de Alembic

- [x] 1.1 Crear `alembic.ini` y `alembic/env.py` configurados para leer `SQLModel.metadata` de los modelos del proyecto y verificar que `alembic current` corre sin errores
- [x] 1.2 Ajustar `app/core/database.py` para exportar el metadata de SQLModel hacia Alembic y verificar que `alembic revision --autogenerate` detecta las tablas

## 2. Modelos SQLModel por módulo

- [x] 2.1 Crear `app/modules/auth/models.py` con `usuario`, `rol`, `rol_asignacion` incluyendo relaciones, FKs, `fecha_alta`/`fecha_baja`, `password_cambiada_en` como `DateTime(timezone=True)`, y `usuario.cliente_id` → `cliente.id`; verificar que los modelos importan sin errores
- [x] 2.2 Crear `app/modules/clientes/models.py` con `cliente` (documento único parcial, `fecha_alta`/`fecha_baja`) y verificar importación
- [x] 2.3 Crear `app/modules/vehiculos/models.py` con `vehiculo` (patente única parcial, `cliente_id` FK, `fecha_alta`/`fecha_baja`) y verificar importación
- [x] 2.4 Crear `app/modules/repuestos/models.py` con `repuesto` (código único parcial, `fecha_alta`/`fecha_baja`) y verificar importación
- [x] 2.5 Crear `app/modules/ordenes/models.py` con `estado_orden`, `orden_trabajo`, `orden_item`, `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto` incluyendo FKs y `fecha_alta`/`fecha_baja` donde aplique; verificar importación

## 3. Migraciones Alembic

- [x] 3.1 Generar migración autogenerate inicial (`alembic revision --autogenerate -m "initial models"`) con todas las tablas, FKs e índices; revisar el archivo generado y verificar que cubre todas las entidades del modelo
- [x] 3.2 Crear migración escrita a mano con función y disparador de PostgreSQL que rechace `UPDATE`/`DELETE` en `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto` (RN-15); verificar que el archivo de migración contiene el disparador

## 4. Validación de migraciones

- [ ] 4.1 Ejecutar `alembic upgrade head` contra una base de datos PostgreSQL de prueba y verificar que todas las tablas se crean
- [ ] 4.2 Ejecutar `alembic downgrade base` y verificar que las tablas se eliminan en orden correcto
- [ ] 4.3 Verificar en la base de datos que existen los índices únicos parciales (`postgresql_where fecha_baja IS NULL`) sobre email, documento, patente y código
- [ ] 4.4 Verificar en la base de datos que el disparador de solo agregado existe y rechaza `UPDATE`/`DELETE` en las tres tablas protegidas

## Workflow follow-up

- Tras completar C-02, el siguiente change desbloqueado es C-03 (contratos-y-crud) y C-04 (autenticacion) en paralelo (GATE 2).
