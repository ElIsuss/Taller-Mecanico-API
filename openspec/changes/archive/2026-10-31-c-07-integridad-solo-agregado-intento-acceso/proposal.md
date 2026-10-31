# Proposal: Integridad Solo Agregado e Intento de Acceso (C-07)

## Why

El sistema de taller mecánico maneja auditoría crítica, trazabilidad de stock, historial de precios y control de fuerza bruta (RN-08 y RN-15). Para garantizar que los registros históricos nunca sean alterados o eliminados (incluso ante errores de aplicación o accesos indebidos) y que los intentos de autenticación queden registrados de manera indeleble aun cuando el login falle o la transacción principal sufra un rollback, es indispensable consolidar los mecanismos de integridad física en base de datos (disparadores PostgreSQL) y la persistencia en transacciones autónomas para `intento_acceso`.

## What Changes

- **Inmutabilidad en base de datos (RN-15)**: Asegurar y validar la protección activa mediante trigger PostgreSQL (`fn_rechazar_update_delete_solo_agregado`) sobre las tablas `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto`, impidiendo cualquier operación `UPDATE` o `DELETE`.
- **Migración versionada y reproducible en Alembic**: Consolidar la migración manual en `migrations/versions/` que define la función y disparadores en PostgreSQL y contempla el correspondiente `downgrade`.
- **Persistencia autónoma de intentos de acceso (RN-08)**: Robustecer el registro de `intento_acceso` para que utilice una sesión y transacción aisladas e independientes del flujo principal de request/UoW, garantizando `commit` inmediato y persistencia efectiva sin depender de la transacción del usuario.
- **Suite de pruebas de integridad y asilamiento transaccional**: Batería de pruebas automatizadas que verifiquen el rechazo de `UPDATE`/`DELETE` en PostgreSQL y la persistencia de `intento_acceso` en escenarios de fallo/rollback.

## Capabilities

### New Capabilities
- `integridad-solo-agregado`: Inmutabilidad física en PostgreSQL mediante triggers `BEFORE UPDATE OR DELETE` para las tablas `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto` (RN-15).

### Modified Capabilities
- `auth`: El registro de `intento_acceso` debe realizarse en una sesión y transacción independientes con commit inmediato y persistente, garantizando que los intentos fallidos sobrevivan a cualquier rollback de la sesión principal.

## Impact

- **Base de datos**: Disparadores activos en PostgreSQL en tablas de historial y movimientos; migración Alembic manual.
- **Servicio de Autenticación (`app/modules/usuarios/service.py`)**: `registrar_intento_acceso` garantiza commit autónomo utilizando `session_maker` / engine bind independiente sin verse afectado por la sesión de FastAPI / UoW.
- **Tests**: Pruebas de integración contra base de datos (validación de triggers y aislamiento transaccional).
