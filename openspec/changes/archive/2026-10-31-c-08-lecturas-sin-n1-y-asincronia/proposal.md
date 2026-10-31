# Proposal: Lecturas sin N+1 y Asincronía (C-08)

## Why

El sistema requiere consultas de detalle de órdenes con un número fijo y predecible de accesos a la base de datos (sin N+1), handlers completamente asíncronos sin llamadas bloqueantes en el hilo de eventos, y avisos al cliente ejecutados en segundo plano tras terminar o cancelar una orden (RN-04/RN-05).

## What Changes

- **Precarga sistemática en repositorios**: El `OrdenRepository` ya utiliza `selectinload` para `items`, `items.repuesto`, `vehiculo.cliente` e `historial_estados`, garantizando que `GET /ordenes/{id}` ejecute el mismo número de consultas independientemente de la cantidad de ítems.
- **Handlers `async def`**: Todos los endpoints de órdenes (`router.py`) son `async def` y delegan operaciones de I/O a servicios/repository asíncronos; no hay llamadas bloqueantes.
- **BackgroundTasks para avisos**: Al terminar (`POST /ordenes/{id}/terminar`) y cancelar (`POST /ordenes/{id}/cancelar`) una orden, se programa un `BackgroundTask` que registra en el log (`taller.avisos`) el aviso al cliente con el ID de orden, nombre del cliente y nuevo estado, sin bloquear la respuesta HTTP.
- **Pruebas de evidencia**: 
  - Test de conteo de consultas (`test/test_c08_lecturas.py`) que verifica que `GET /ordenes/{id}` con 2 ítems y con 4 ítems genera el mismo número de `SELECT` (8 en ambos casos).
  - Test de `BackgroundTasks` que valida que el aviso se programa y ejecuta tras `terminar` y `cancelar`.
  - Evidencia en consola con `SQL_ECHO=true` y archivo `.http` ejecutable (`test/c-12-15-avisos-n1.http`) para los casos C-12 (reponer + terminar) y C-15 (detalle 2 vs 4 ítems) del PDF.

## Capabilities

### New Capabilities
- `notificaciones-orden`: Aviso asíncrono al cliente vía log tras cambio de estado a TERMINADA o CANCELADA (RN-04/RN-05).

### Modified Capabilities
- `ordenes`: Lectura de detalle con consultas constantes (sin N+1) y avisos en segundo plano.

## Impact

- **Módulo órdenes**: Nuevo archivo `app/modules/ordenes/notificaciones.py`; router actualizado con `BackgroundTasks` en `terminar_orden` y `cancelar_orden`.
- **Tests**: `test/test_c08_lecturas.py` (3 tests) y `test/c-12-15-avisos-n1.http`.
- **Evidencia**: Carpeta `/tmp/opencode/auditoria-c08/` con logs, JSONs y resúmenes de C-12/C-15.