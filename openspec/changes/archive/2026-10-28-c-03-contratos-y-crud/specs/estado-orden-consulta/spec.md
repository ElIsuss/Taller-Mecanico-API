# Spec Delta

## Purpose

Expone la consulta de solo lectura del catálogo de estados de orden para que los clientes de la API conozcan los estados válidos y su orden.

## ADDED Requirements

### Requirement: Consulta del catálogo de estados
El sistema SHALL exponer `GET /estados-orden` con los estados del catálogo ordenados por `posicion`, de forma paginada, sin permitir altas, modificaciones ni borrados desde la API.

#### Scenario: Listado de estados
- **WHEN** se consulta `GET /estados-orden`
- **THEN** la API responde 200 con los estados ordenados por `posicion` e incluye `codigo`, `descripcion`, `posicion` y `es_final`

#### Scenario: Alta no permitida
- **WHEN** se envía `POST /estados-orden`
- **THEN** la API responde 405

#### Scenario: Modificación no permitida
- **WHEN** se envía `PATCH` o `DELETE` sobre `/estados-orden/{codigo}`
- **THEN** la API responde 405

#### Scenario: Estado inexistente
- **WHEN** se consulta `GET /estados-orden/NO_EXISTE`
- **THEN** la API responde 404 si se expone la consulta por código
