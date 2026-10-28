# Proposal

## Why

C-02 dejó el esquema y los modelos listos, pero la API todavía no expone ningún recurso: no hay contratos Pydantic, routers ni endpoints CRUD. C-03 convierte ese modelo de datos en una API REST usable (clientes, vehículos, repuestos, órdenes y catálogo de estados) con contratos estrictos, paginación y códigos de error consistentes, para que C-04/C-05 puedan agregar autenticación y autorización sobre endpoints ya existentes.

## What Changes

- Schemas Pydantic V2 de entrada/salida separados de los modelos SQLModel, con `extra="forbid"` en entradas y sin exponer `password_hash` ni campos internos.
- PATCH parcial con `exclude_unset` (solo se actualiza lo enviado).
- Paginación uniforme `{items, total, page, size, pages}` (page ≥ 1, size 1–100, default 20; página fuera de rango → 422).
- CRUD de clientes (sin borrado lógico; DELETE solo si no tiene vehículos).
- CRUD de vehículos con baja lógica (`borrado_en`) y bloqueo de baja si tiene órdenes abiertas.
- CRUD de repuestos con baja lógica, búsqueda por descripción con parámetros ligados, reposición de stock vía `movimiento_stock` y cambio de precio con línea en `historial_precio_repuesto`.
- Órdenes de trabajo: crear (mínimo un ítem, sin repuestos repetidos, precio copiado y total calculado en servidor), listar, consultar, actualizar datos básicos y ejecutar el ciclo de vida (`iniciar`, `terminar`, `cancelar`) con descuento de stock e historial de estado.
- `GET /estados-orden` de solo lectura sobre el catálogo `estado_orden`.
- Mapeo de errores: 201/204, 404, 409 (duplicados, conflictos de estado, stock insuficiente), 422 (validación/página fuera de rango), sin filtrar detalles internos de base (RN-18).
- Acciones que escriben historiales reciben `usuario_id` (actor) en la petición; C-04/C-05 lo reemplazarán por el usuario de la sesión autenticada.

## Capabilities

### New Capabilities

- `contratos-api`: reglas transversales de contratos HTTP (entradas estrictas, PATCH parcial, envoltorio de paginación, códigos de error y sanitización de respuestas).
- `clientes-crud`: alta, listado paginado, consulta, actualización parcial y baja de clientes.
- `vehiculos-crud`: alta, listado paginado, consulta, actualización parcial y baja lógica de vehículos.
- `repuestos-crud`: CRUD de repuestos, búsqueda por descripción, reposición de stock y cambio de precio con historial.
- `ordenes-crud`: creación, consulta, actualización básica y ciclo de vida de órdenes de trabajo.
- `estado-orden-consulta`: consulta de solo lectura del catálogo de estados de orden.

### Modified Capabilities

(Ninguna — todavía no hay specs principales archivadas; las specs de dominio de C-02 siguen en su change.)

## Impact

- Código nuevo: `app/modules/{clientes,vehiculos,repuestos,ordenes,estados_orden}/schemas.py`, `router.py`; servicios mínimos por módulo; `app/core/exceptions.py` y registro de routers en `app/main.py`.
- Sin migraciones nuevas: C-03 usa el esquema de C-02.
- Dependencias: FastAPI/Pydantic ya presentes; no se agregan librerías.
- C-04 (autenticación), C-05 (autorización), C-06 (repositorios/UoW) y C-08 (lecturas sin N+1) se apoyan en estos endpoints.
