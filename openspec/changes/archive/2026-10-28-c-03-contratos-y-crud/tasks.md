# Tasks

## 1. Base transversal

- [x] 1.1 Crear `app/core/pagination.py` con `Pagina[T]`, `PaginaParams` y el cálculo de `pages`, y verificar con tests unitarios los límites (`page=0`, `size=101`, lista vacía → `pages=0`) y el cálculo de páginas
- [x] 1.2 Crear `app/core/exceptions.py` con `NoEncontrado`, `Conflicto`, `Invalido` y los handlers de `IntegrityError`, registrarlos en `app/main.py` y verificar con tests que 404/409/422/500 devuelven `{"detail": ...}` sin SQL interno
- [x] 1.3 Crear `tests/conftest.py` con fixtures de PostgreSQL de test (Alembic `upgrade head`), `AsyncClient` sobre ASGITransport y helpers de siembra (usuarios, estados, clientes, vehículos, repuestos), y verificar que un test smoke de `GET /docs` pasa

## 2. Clientes

- [x] 2.1 Crear `app/modules/clientes/schemas.py` (`ClienteCreate`, `ClienteUpdate`, `ClienteRead`) con `extra="forbid"` y verificar con tests de Pydantic que campos desconocidos fallan y que el PATCH usa `exclude_unset`
- [x] 2.2 Implementar `app/modules/clientes/service.py` con alta, consulta, listado paginado, actualización y baja con validación de vehículos, y verificar con tests de integración los casos 201/200/204/404/409
- [x] 2.3 Crear `app/modules/clientes/router.py`, montarlo en `app/main.py` y verificar con tests de integración las rutas `/clientes` y su documentación en `/openapi.json`

## 3. Vehículos

- [x] 3.1 Crear `app/modules/vehiculos/schemas.py` (`VehiculoCreate`, `VehiculoUpdate`, `VehiculoRead`) con validación de año y sin exponer `borrado_en`, y verificarlo con tests de Pydantic
- [x] 3.2 Implementar `app/modules/vehiculos/service.py` con alta, consulta y listado filtrado por `cliente_id`, excluyendo borrados, y verificar con tests de integración los casos 201/200/404/409/422
- [x] 3.3 Implementar la baja lógica y el bloqueo por órdenes abiertas en el servicio, y verificar con tests que responde 204 sin órdenes abiertas y 409 con al menos una orden no final
- [x] 3.4 Crear `app/modules/vehiculos/router.py`, montarlo en `app/main.py` y verificar con tests de integración la reutilización de patente tras la baja y la documentación en `/openapi.json`

## 4. Repuestos

- [x] 4.1 Crear `app/modules/repuestos/schemas.py` (`RepuestoCreate`, `RepuestoUpdate` con `usuario_id` condicional, `RepuestoRead`, `MovimientoStockRead`, `HistorialPrecioRead`) y verificar con tests que `stock` en PATCH y precio sin actor fallan con 422
- [x] 4.2 Implementar `app/modules/repuestos/service.py` con alta, consulta, listado paginado, búsqueda escapada y baja lógica, y verificar con tests de integración los casos 201/200/404/409/422
- [x] 4.3 Implementar el cambio de precio transaccional con inserción de `historial_precio_repuesto` solo si el precio cambia, y verificar con tests que el historial se crea, se omite cuando el precio es igual y es consultable con `GET /repuestos/{id}/historial-precios`
- [x] 4.4 Implementar `POST /repuestos/{id}/reposiciones` con `movimiento_stock` positivo y actualización de stock, y verificar con tests que cantidad ≤ 0 responde 422, repuesto borrado 404 y una reposición válida crea el movimiento
- [x] 4.5 Crear `app/modules/repuestos/router.py`, montarlo en `app/main.py` y verificar con tests de integración la búsqueda con `%`/`_`, el envoltorio de paginación y la documentación en `/openapi.json`

## 5. Catálogo de estados

- [x] 5.1 Crear `app/modules/ordenes/schemas.py` con `EstadoOrdenRead` y `app/modules/ordenes/service.py` con consulta del catálogo ordenada por `posicion`, y verificarlo con tests de integración
- [x] 5.2 Exponer `GET /estados-orden` y `GET /estados-orden/{codigo}` en `app/modules/ordenes/router.py`, y verificar con tests que 404 aplica al código inexistente y que POST/PATCH/DELETE responden 405

## 6. Órdenes y ciclo de vida

- [x] 6.1 Crear en `app/modules/ordenes/schemas.py` los contratos de orden (`OrdenCreate` con ítems, `OrdenUpdate`, `OrdenRead` con ítems, acciones con `usuario_id`) y verificar con tests de Pydantic que `items` vacío, repetidos y `total` en PATCH fallan con 422
- [x] 6.2 Implementar la apertura de orden en el servicio con copia de precios, total en servidor, estado PENDIENTE e historial inicial, y verificar con tests los casos 201, vehículo/repuesto inexistente (404), borrado (409) y total calculado
- [x] 6.3 Implementar consulta por id con ítems y listado paginado con filtros `estado` y `vehiculo_id`, y verificarlo con tests de integración
- [x] 6.4 Implementar `PATCH /ordenes/{id}` limitado a `falla` y `mecanico_id` en PENDIENTE, y verificar con tests que 409 aplica a estados no PENDIENTE y 422 a campos no permitidos
- [x] 6.5 Implementar `iniciar` y `cancelar` con validación de estado e historial, y verificar con tests las transiciones PENDIENTE → EN_REPARACION y PENDIENTE → CANCELADA, más los 409 en estados inválidos
- [x] 6.6 Implementar `terminar` en una transacción con `SELECT ... FOR UPDATE`, verificación de stock, descuento, movimientos negativos e historial, y verificar con tests el caso feliz y que stock insuficiente responde 409 sin dejar escrituras
- [x] 6.7 Montar las rutas de órdenes en `app/main.py` y verificar con tests de integración los códigos 201/200/404/409/422 y la documentación en `/openapi.json`

## 7. Integración y cierre

- [x] 7.1 Ejecutar la suite completa con PostgreSQL (`TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/taller_mecanico_test`) y sin base (skips esperados), y verificar que no hay regresiones en los 66 tests de C-02
- [x] 7.2 Ejecutar `python -m compileall -q app alembic tests` y `openspec validate c-03-contratos-y-crud --strict`, y corregir cualquier error reportado
- [x] 7.3 Revisar que `knowledge-base/05_reglas_de_negocio.md` y `07_flujos_principales.md` coincidan con las transiciones y el descuento de stock implementados, y actualizar `CHANGES.md` con el estado de C-03
