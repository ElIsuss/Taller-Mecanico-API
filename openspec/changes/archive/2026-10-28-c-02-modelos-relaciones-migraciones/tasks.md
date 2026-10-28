# Tasks

## 1. Infraestructura de Alembic

- [x] 1.1 Crear `alembic.ini` y `alembic/env.py` configurados para leer `SQLModel.metadata` de los modelos del proyecto y verificar que `alembic current` corre sin errores
- [x] 1.2 Ajustar `app/core/database.py` para exportar el metadata de SQLModel hacia Alembic y verificar que `alembic revision --autogenerate` detecta las tablas

## 2. Modelos SQLModel por módulo (esquema del TP Cap1a6)

- [x] 2.1 Crear `app/modules/auth/models.py` con `usuario` (email UNIQUE, nombre, password_hash, activo, debe_cambiar_password, password_cambiada_en `timestamptz`), `asignacion_rol` (rol con CHECK ADMIN/RECEPCION/MECANICO/CLIENTE, desde, vence_en, revocada_en, otorgada_por, índice único parcial por `(usuario_id, rol)` donde `revocada_en IS NULL`), `intento_acceso` (índice `(email, ip, cuando)`) y `evento_seguridad`; verificar importación
- [x] 2.2 Crear `app/modules/clientes/models.py` con `cliente`: `usuario_id` nullable UNIQUE FK a `usuario.id`, `nombre`, `documento` UNIQUE, `telefono`; verificar importación
- [x] 2.3 Crear `app/modules/vehiculos/models.py` con `vehiculo`: `cliente_id` FK indexada, patente única parcial donde `borrado_en IS NULL`, `marca`, `modelo`, `anio` con CHECK 1950–2100; verificar importación
- [x] 2.4 Crear `app/modules/repuestos/models.py` con `repuesto`: código único parcial donde `borrado_en IS NULL`, `descripcion`, `precio NUMERIC(10,2)`, `stock` con CHECK `>= 0`, `borrado_en`; verificar importación
- [x] 2.5 Crear `app/modules/ordenes/models.py` con `estado_orden` (PK `codigo`, `posicion` UNIQUE, `es_final`), `orden_trabajo` (vehiculo_id, mecanico_id opcional, estado FK, falla, creada_en, total `NUMERIC(12,2)`), `item_orden` (UNIQUE `(orden_id, repuesto_id)`), `historial_estado_orden`, `movimiento_stock` y `historial_precio_repuesto`; verificar importación
- [x] 2.6 Crear `app/core/models.py` que importe todos los módulos para poblar `SQLModel.metadata` y resolver las relaciones con forward references; usarlo en `alembic/env.py` y `app/main.py`

## 3. Migraciones Alembic

- [x] 3.1 Generar migración autogenerate inicial (`alembic revision --autogenerate -m "initial models"`) con todas las tablas, FKs, CHECKs e índices; revisar el archivo generado (import de `sqlmodel`) y verificar que cubre todas las entidades del modelo
- [x] 3.2 Crear migración escrita a mano con función y disparador de PostgreSQL que rechace `UPDATE`/`DELETE` en `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto` (RN-15); verificar que el archivo de migración contiene el disparador

## 4. Validación de migraciones

- [x] 4.1 Ejecutar `alembic upgrade head` contra una base de datos PostgreSQL de prueba y verificar que todas las tablas se crean
- [x] 4.2 Ejecutar `alembic downgrade base` y verificar que las tablas se eliminan en orden correcto
- [x] 4.3 Verificar en la base de datos los índices únicos parciales (`vehiculo.patente` y `repuesto.codigo` con `borrado_en IS NULL`; `asignacion_rol (usuario_id, rol)` con `revocada_en IS NULL`)
- [x] 4.4 Verificar en la base de datos que el disparador de solo agregado existe y rechaza `UPDATE`/`DELETE` en las tres tablas protegidas
- [x] 4.5 Verificar con `compare_metadata` que los modelos y el esquema migrado no divergen (sin drift al autogenerar)

## 5. Documentación del change

- [x] 5.1 Actualizar `proposal.md`, `design.md` y los specs de `auth`, `clientes`, `vehiculos`, `repuestos` y `ordenes` al esquema del TP Cap1a6

## Workflow follow-up

- Tras completar C-02, el siguiente change desbloqueado es C-03 (contratos-y-crud) y C-04 (autenticacion) en paralelo (GATE 2).
