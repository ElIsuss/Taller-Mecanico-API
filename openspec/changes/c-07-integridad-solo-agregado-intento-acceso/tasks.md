# Tasks: Integridad Solo Agregado e Intento de Acceso (C-07)

## 1. Integridad física de tablas de solo agregado (RN-15)

- [x] 1.1 Revisar y afinar la migración manual en `migrations/versions/6b6c35076332_rn15_solo_agregado_trigger.py` garantizando compatibilidad con asyncpg (statements DDL separados sin punto y coma final) y simetría en `downgrade()` eliminando triggers y función.
- [x] 1.2 Extender y ejecutar las pruebas en `test/test_migrations_validation.py` verificando que los disparadores `trg_*_solo_agregado` existen en PostgreSQL y rechazan formalmente `UPDATE` y `DELETE` en las 3 tablas (`historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto`) permitiendo operaciones `INSERT`.
- [x] 1.3 Verificar la coherencia del script de auditoría manual `test/solo_agregado.sql` frente al catálogo y disparadores de la base de datos.

## 2. Aislamiento y persistencia autónoma de intento_acceso (RN-08)

- [x] 2.1 Refactorizar `registrar_intento_acceso` en `app/modules/usuarios/service.py` para asegurar que utiliza una sesión dedicada y transacción autónoma con commit inmediato, garantizando que el registro persista aun cuando la sesión o UoW principal sufra un rollback o lance excepciones HTTP.
- [x] 2.2 Escribir prueba en `test/test_auth.py` que simule una excepción/rollback forzado en la sesión principal durante el intento de login y verifique que la fila en `intento_acceso` se mantiene persistida en la base de datos.
- [x] 2.3 Validar que el flujo completo de protección contra fuerza bruta (RN-08: bloqueo con 429 y cabecera Retry-After tras 5 intentos fallidos, y reinicio tras login exitoso) opere consistentemente con las transacciones autónomas.

## 3. Verificación integral y regresión

- [x] 3.1 Ejecutar la suite de pruebas del módulo de usuarios y seguridad (`test/test_unit_auth.py`, `test/test_auth.py`, `test/test_models_usuarios.py`) y constatar que todos los casos pasan sin fallos.

## Workflow follow-up

- Ejecutar `/opsx:apply c-07-integridad-solo-agregado-intento-acceso` para iniciar la implementación con Strict TDD.
- Ejecutar `/opsx:archive c-07-integridad-solo-agregado-intento-acceso` tras completar y verificar las tareas.
