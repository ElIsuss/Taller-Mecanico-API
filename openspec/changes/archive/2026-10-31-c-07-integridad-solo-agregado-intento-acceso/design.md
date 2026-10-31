# Design: Integridad Solo Agregado e Intento de Acceso (C-07)

## Context

El proyecto requiere salvaguardar registros inmutables de auditoría y movimientos de stock (RN-15) y mantener una bitácora infalible de intentos de login para prevención de ataques de fuerza bruta (RN-08).

Actualmente:
- Existen los modelos y migraciones en Alembic, incluyendo `migrations/versions/6b6c35076332_rn15_solo_agregado_trigger.py` que crea la función `fn_rechazar_update_delete_solo_agregado` y los 3 triggers en PostgreSQL.
- En `app/modules/usuarios/service.py`, `registrar_intento_acceso` registra intentos pero requiere validación formal de que su commit sea autónomo y sobreviva a fallos o rollbacks de la sesión principal en todas las condiciones de ejecución.
- En `test/solo_agregado.sql` y `test/test_migrations_validation.py`, se dispone de scripts y pruebas contra PostgreSQL que deben ser consolidados y ampliados para verificar ambos requerimientos.

## Goals / Non-Goals

**Goals:**
- Asegurar la inmutabilidad física en PostgreSQL mediante triggers `BEFORE UPDATE OR DELETE` sobre las tablas `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto` (RN-15).
- Asegurar que `registrar_intento_acceso` persista en base de datos mediante una sesión/transacción independiente con commit inmediato, sobreviviendo a fallos de autenticación (401/429) y a rollbacks en la sesión principal.
- Proporcionar pruebas automatizadas tanto a nivel de aislamiento transaccional (`intento_acceso`) como a nivel de integridad de esquema en PostgreSQL.

**Non-Goals:**
- No implementar emulación de triggers PL/pgSQL en SQLite (el entorno canónico de integridad y producción es PostgreSQL 16).
- No modificar endpoints de la API ni esquemas de entrada/salida (la firma de contratos ya está fijada en C-03).
- No abarcar optimizaciones de N+1 de lectura (alcance exclusivo de C-08).

## Decisions

### Decisión 1: Función única PL/pgSQL para disparadores de solo-agregado (RN-15)
- **Elección**: Definir una única función `fn_rechazar_update_delete_solo_agregado()` en PostgreSQL que inspecciona `TG_OP` y lanza una excepción si se intenta `UPDATE` o `DELETE`. Se asocia a 3 disparadores `BEFORE UPDATE OR DELETE ON <table> FOR EACH ROW`.
- **Razón**: Centraliza la regla de negocio RN-15 en una única rutina de base de datos, facilitando el mantenimiento y garantizando mensajes de error consistentes.
- **Alternativa descartada**: Triggers independientes con funciones separadas por tabla (duplicación innecesaria de código PL/pgSQL).

### Decisión 2: Sesión y transacción autónoma para `intento_acceso` (RN-08)
- **Elección**: `registrar_intento_acceso` opera con una sesión dedicada independiente de la transacción principal del request. Si el bind de la sesión principal o el `async_sessionmaker` está disponible, se abre una nueva sesión `async with AsyncSession(bind) as sep_session:` y se realiza un `commit()` explícito.
- **Razón**: Durante un login fallido o ante una excepción de negocio, FastAPI o el middleware pueden descartar o hacer rollback de la transacción principal. La auditoría de seguridad y el conteo de intentos de fuerza bruta deben persistir obligatoriamente para cumplir RN-08.
- **Alternativa descartada**: Enlazar `intento_acceso` a la misma transacción que el resto de las operaciones (se perdería el registro al producirse un rollback).

### Decisión 3: Verificación dual de integridad (SQL y pruebas de integración)
- **Elección**: Mantener el script ejecutable `test/solo_agregado.sql` para pruebas manuales con `psql` y añadir/consolidar pruebas automatizadas en `test/test_migrations_validation.py` y `test/test_auth.py` para asegurar que ningún cambio futuro degrade las restricciones.
- **Razón**: Permite validar tanto el comportamiento nativo de la base de datos como la integración desde la capa de servicios de Python.

## Risks / Trade-offs

- **[Riesgo: Manejo de terminadores de sentencia en asyncpg]**: asyncpg no soporta múltiples sentencias separadas por punto y coma en una sola llamada de statement preparado.
  - *Mitigación*: Cada statement DDL (`CREATE OR REPLACE FUNCTION`, `CREATE TRIGGER`) se ejecuta en su propio `op.execute(sa.text(...))` sin punto y coma final en la migración de Alembic.
- **[Riesgo: Agotamiento de conexiones por sesión independiente de intento de acceso]**:
  - *Mitigación*: La sesión autónoma tiene un ciclo de vida milimétrico: inserta el registro, hace commit y se cierra de inmediato en el bloque `async with`.

## Migration Plan

1. La migración `6b6c35076332_rn15_solo_agregado_trigger.py` se aplica secuencialmente tras `92c8c4836886_initial_models.py` con `alembic upgrade head`.
2. El rollback se realiza limpiamente con `alembic downgrade -1`, eliminando primero los triggers y luego la función.
