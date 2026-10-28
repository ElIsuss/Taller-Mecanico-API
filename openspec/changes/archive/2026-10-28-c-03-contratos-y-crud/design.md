# Design

## Context

C-02 dejó los modelos SQLModel y el esquema Alembic, pero `app/modules/*` solo tiene `models.py`: no existen schemas, routers, servicios ni excepción centralizada. `app/main.py` solo expone salud y `app/core/database.py` ya provee `get_session` y el motor en `lifespan`.

Ver proposal.md para la motivación. La arquitectura objetivo es Router → Service → Unit of Work → Repository → Model, pero los repositorios y la UoW llegan en C-06; C-03 debe poder implementarse sin adelantarlos.

## Goals / Non-Goals

**Goals:**
- Contratos Pydantic V2 estrictos y respuestas públicas estables para los cinco recursos.
- CRUD completo de clientes, vehículos y repuestos, más búsqueda, reposición y cambio de precio.
- Órdenes con ítems, total en servidor, ciclo de vida y descuento de stock atómico.
- Paginación y manejo de errores uniformes.
- Servicios por módulo que concentren reglas y dejen a los routers delgados.

**Non-Goals:**
- Autenticación, cookies, JWT y autorización por rol (C-04/C-05). En C-03 el actor viaja como `usuario_id` en el cuerpo.
- Repositorios genéricos, `UnitOfWork` y precarga sistemática (C-06/C-08).
- Migraciones nuevas: C-03 no cambia el esquema.
- Avisos al cliente (C-08) e idempotencia de reintentos.

## Decisions

### 1. Servicios con sesión, sin repositorios todavía
Cada módulo agrega `schemas.py`, `service.py` y `router.py`. El router valida y delega; el servicio recibe `AsyncSession` y ejecuta consultas SQLAlchemy/SQLModel. La transacción se abre en el servicio con `async with session.begin()` para las operaciones de escritura múltiple (terminar orden, cambio de precio, reposición).

**Alternativa considerada:** introducir ya `BaseRepository`/`UnitOfWork`.
**Razón para no elegirla:** es el objeto de C-06; adelantarlo duplica trabajo y rompe el orden del roadmap. La firma de los servicios se mantiene compatible para que C-06 sustituya la sesión por la UoW.

### 2. Actor transitorio en el cuerpo
`POST /ordenes`, `iniciar`, `terminar`, `cancelar`, reposiciones y cambio de precio reciben `usuario_id` obligatorio. El servicio valida que exista y lo usa para `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto`. C-04/C-05 reemplazarán ese campo por el usuario de la sesión y lo quitarán de los contratos.

**Alternativa considerada:** dejar `usuario_id` nulo hasta C-04.
**Razón para no elegirla:** el esquema exige el actor en las tablas de auditoría y posponerlo dejaría el ciclo de vida incompleto.

### 3. Rutas en la raíz
Los routers se montan sin prefijo (`/clientes`, `/vehiculos`, `/repuestos`, `/ordenes`, `/estados-orden`) para coincidir con la KB y los flujos (`POST /ordenes`, `GET /auth/yo`). `API_V1_STR` queda reservado para el OpenAPI.

### 4. Paginación genérica
`app/core/pagination.py` define `Pagina[T]` (`items`, `total`, `page`, `size`, `pages`) y `PaginaParams` como dependencia (`page` ≥ 1, `size` 1–100, default 20). Los servicios devuelven `(items, total)` y el router arma `pages = ceil(total / size)`. Si `page > max(pages, 1)` se responde 422.

**Alternativa considerada:** devolver listas planas.
**Razón para no elegirla:** US-015 y CHANGES exigen el envoltorio uniforme.

### 5. Búsqueda con parámetros ligados y escape
`GET /repuestos?busqueda=` usa `ilike` con `%...%`, escapando `%`, `_` y `\` y pasando `escape="\\"`. Nunca se interpola el texto en SQL.

### 6. Baja lógica y borrado físico
- `vehiculo` y `repuesto`: `DELETE` setea `borrado_en = now()`; los listados y consultas por id filtran `borrado_en IS NULL`.
- `vehiculo` con órdenes abiertas (unión con `estado_orden.es_final = false`) → 409.
- `cliente`: sin borrado lógico; `DELETE` físico solo si no tiene filas en `vehiculo` (incluidas las borradas); si tiene → 409.

### 7. Contratos de entrada/salida
- Entradas: `ConfigDict(extra="forbid")`; PATCH usa `model_dump(exclude_unset=True)`.
- Salidas: `ConfigDict(from_attributes=True)` con campos públicos; se excluyen `borrado_en` y cualquier detalle interno.
- `RepuestoUpdate` declara `usuario_id` opcional; un validador exige `usuario_id` cuando viene `precio` (422 si falta) y el servicio no inserta historial si el precio no cambió.
- `VehiculoUpdate` no permite `borrado_en`; la baja solo ocurre por `DELETE`.

### 8. Órdenes: creación y transiciones
- Crear: validar vehículo/repuestos vigentes, mínimo un ítem, sin repetidos, cantidades > 0; copiar `precio` a `precio_unitario`; `total = Σ cantidad × precio_unitario`; estado PENDIENTE; historial inicial (`desde_estado = NULL`, `hasta_estado = PENDIENTE`).
- `PATCH`: solo `falla` y `mecanico_id`, solo en PENDIENTE (409 en otro estado).
- `iniciar`: PENDIENTE → EN_REPARACION; si `mecanico_id` es nulo se asigna el actor; historial.
- `terminar`: EN_REPARACION → TERMINADA; dentro de una transacción, bloquear los repuestos con `SELECT ... FOR UPDATE`, verificar stock, descontar, crear un `movimiento_stock` con cantidad negativa y motivo `terminación`, y el historial. Si falta stock → 409 sin escrituras.
- `cancelar`: PENDIENTE → CANCELADA; historial. La autorización por rol/propiedad llega en C-05.

**Alternativa considerada:** descontar stock al crear la orden.
**Razón para no elegirla:** RN-13 y el Flujo 4 descuentan al terminar; descontar antes bloquearía stock de órdenes que nunca se ejecutan.

### 9. Errores
`app/core/exceptions.py` define errores de aplicación (`NoEncontrado`, `Conflicto`, `Invalido`) y handlers que devuelven `{"detail": "..."}`. Un handler de `IntegrityError` traduce violaciones de unicidad/FK a 409 y cualquier otro error de base a 500 con mensaje genérico (RN-18). Los routers no arman mensajes de SQL.

### 10. Estado del catálogo
`estado_orden` se expone con `GET /estados-orden` y `GET /estados-orden/{codigo}` (404 si no existe); no se declaran rutas de escritura, por lo que FastAPI responde 405 a POST/PATCH/DELETE.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| C-04/C-05 deben quitar `usuario_id` de los contratos | Dejarlo aislado en schemas de acciones y documentarlo como transitorio; los servicios ya reciben el id como parámetro |
| C-06 reemplaza la apertura de transacción de los servicios | Mantener las escrituras múltiples en un único método de servicio para que el cambio sea localizado |
| Condiciones de carrera de stock entre terminaciones simultáneas | `SELECT ... FOR UPDATE` sobre los repuestos dentro de la transacción |
| Tests necesitan catálogo `estado_orden` y usuarios | Fixture de integración que ejecuta Alembic y siembra estados/usuarios mínimos |
| Respuestas 405 del catálogo dependen del framework | Verificar con tests que no existan rutas de escritura |

## Migration Plan

1. Crear `app/core/pagination.py` y `app/core/exceptions.py`; registrar handlers en `app/main.py`.
2. Agregar `schemas.py`, `service.py` y `router.py` por módulo; montar routers.
3. Implementar CRUD y luego órdenes/ciclo de vida.
4. Tests de integración con PostgreSQL: contratos, paginación, errores, baja lógica, totales, stock y transiciones.
5. No hay migraciones ni rollback de esquema.

## Open Questions

- ¿El `usuario_id` transitorio se elimina en C-04 o se mantiene hasta C-05? — se decide al implementar C-04; no cambia el diseño de C-03.
