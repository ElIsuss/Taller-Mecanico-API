# Tasks: Lecturas sin N+1 y Asincronía (C-08)

## 1. Precarga en repositorio para eliminar N+1

- [x] 1.1 Verificar que `OrdenRepository.get_loaded` usa `selectinload` para `items.repuesto`, `vehiculo.cliente` e `historial_estados` (ya implementado en `app/modules/ordenes/repository.py:35-41`).
- [x] 1.2 Confirmar que `service._a_read` accede solo a relaciones precargadas sin disparar consultas adicionales.

## 2. Handlers asíncronos sin bloqueos

- [x] 2.1 Validar que todos los endpoints de `app/modules/ordenes/router.py` son `async def`.
- [x] 2.2 Verificar que no hay llamadas bloqueantes (`time.sleep`, `bcrypt` directo, etc.) en routers ni servicios de órdenes; bcrypt delegado a `asyncio.to_thread` desde `C-04`.

## 3. BackgroundTasks para avisos al cliente (RN-04/RN-05)

- [x] 3.1 Crear `app/modules/ordenes/notificaciones.py` con `enviar_aviso_cliente(orden_id, cliente, estado)` que loguea a `taller.avisos` (nivel WARNING para visibilidad en uvicorn).
- [x] 3.2 Modificar `terminar_orden` en `router.py` para aceptar `BackgroundTasks` y programar el aviso tras `service.terminar_orden`.
- [x] 3.3 Modificar `cancelar_orden` análogamente.
- [x] 3.4 Verificar que el aviso incluye `orden_id`, `cliente` (nombre) y `estado` (TERMINADA/CANCELADA).

## 4. Suite de pruebas C-08

- [x] 4.1 Escribir `test/test_c08_lecturas.py`:
  - Fixture `auth_admin` (usuario ADMIN con hash real).
  - Helper `_crear_orden` (2 y 4 ítems).
  - Test `test_detalle_orden_consultas_constantes` con contador de `SELECT` vía `sqlalchemy.event`.
  - Test `test_aviso_al_terminar` con monkeypatch del aviso.
  - Test `test_aviso_al_cancelar` con monkeypatch del aviso.
- [x] 4.2 Ejecutar tests con `TEST_DATABASE_URL` → 3 passed, 8 vs 8 consultas.
- [x] 4.3 Generar evidencia de consola con `SQL_ECHO=true` → `uvicorn-c08.log`.

## 5. Archivo `.http` ejecutable para casos C-12 y C-15 del PDF

- [x] 5.1 Crear `test/c-12-15-avisos-n1.http` con:
  - Login admin (`admin@example.com` / `Secreta123!`).
  - C-12: Reponer repuesto 3 (+10), terminar orden 2, detalle orden 2 (historial y stock).
  - C-15: Crear orden 2 ítems, crear orden 4 ítems, detalle de ambas con variable `{{ordenDos.response.body.$.id}}`.

## 6. Verificación integral y regresión

- [x] 6.1 Ejecutar baseline: `alembic upgrade head`, `seed.py`, smoke test (LIVE/READY/LOGIN/ORDENES 200).
- [x] 6.2 Confirmar que los tests existentes de órdenes (`test/test_api_ordenes.py`) no se rompen (aunque requieren auth).
- [x] 6.3 Documentar evidencia en `/tmp/opencode/auditoria-c08/`:
  - `c15-pytest.txt` (tests pasan, 8 vs 8).
  - `c15-console.txt` (8 SELECT para 2 y 4 ítems).
  - `c12-resumen.txt` (stock 2→12→8, historial, movimientos, aviso en log).
  - `uvicorn-c08.log` (SQL + aviso).
  - JSONs de cada petición.

## Workflow follow-up

- Ejecutar `/opsx:apply c-08-lecturas-sin-n1-y-asincronia` para confirmar implementación.
- Ejecutar `/opsx:archive c-08-lecturas-sin-n1-y-asincronia` tras completar y verificar las tareas.