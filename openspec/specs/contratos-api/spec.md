# contratos-api Specification

## Purpose

Define las reglas transversales de los contratos HTTP de la API: entradas estrictas, actualizaciones parciales, paginación uniforme, códigos de error y respuestas sin datos internos.

## Requirements

### Requirement: Entradas estrictas
El sistema SHALL rechazar con 422 cualquier campo no declarado en el contrato de entrada de un endpoint (`extra="forbid"`).

#### Scenario: Campo desconocido en el alta
- **WHEN** se envía `POST /clientes` con un campo `rol` no declarado
- **THEN** la API responde 422 y no crea el cliente

#### Scenario: Campo desconocido en una actualización
- **WHEN** se envía `PATCH /repuestos/{id}` con el campo `stock`
- **THEN** la API responde 422 y no modifica el repuesto

### Requirement: Actualización parcial
El sistema SHALL actualizar en un PATCH únicamente los campos presentes en el cuerpo (`exclude_unset`), conservando el resto de los valores.

#### Scenario: PATCH con un solo campo
- **WHEN** se envía `PATCH /clientes/{id}` con `{"telefono": "555-1234"}`
- **THEN** solo cambia el teléfono y el resto de los campos permanece igual

#### Scenario: PATCH vacío
- **WHEN** se envía `PATCH /clientes/{id}` con `{}`
- **THEN** la API responde 200 sin modificar el cliente

### Requirement: Paginación uniforme
El sistema SHALL devolver los listados con el envoltorio `{items, total, page, size, pages}`, con `page` desde 1, `size` entre 1 y 100 (default 20) y `pages = max(1, ceil(total / size))`; con `total = 0` se devuelve una página vacía (`pages = 1`).

#### Scenario: Primera página
- **WHEN** se solicita `GET /clientes?page=1&size=20` con 5 clientes
- **THEN** la respuesta incluye los 5 ítems, `total = 5`, `page = 1`, `size = 20` y `pages = 1`

#### Scenario: Listado vacío
- **WHEN** se solicita `GET /clientes?page=1&size=20` sin clientes
- **THEN** la respuesta incluye `items = []`, `total = 0` y `pages = 1`

#### Scenario: Página fuera de rango
- **WHEN** se solicita una página mayor que `pages` (o mayor que 1 con `total = 0`)
- **THEN** la API responde 422

#### Scenario: Parámetros fuera de límites
- **WHEN** se envía `page = 0` o `size = 101`
- **THEN** la API responde 422

### Requirement: Códigos de respuesta consistentes
El sistema SHALL usar 201 al crear, 204 al borrar, 404 cuando el recurso no existe, 409 ante conflictos de unicidad o de estado, y 422 ante errores de validación.

#### Scenario: Recurso inexistente
- **WHEN** se consulta `GET /vehiculos/999999`
- **THEN** la API responde 404

#### Scenario: Conflicto de unicidad
- **WHEN** se intenta crear un cliente con un documento ya existente
- **THEN** la API responde 409

#### Scenario: Creación exitosa
- **WHEN** se crea un recurso válido
- **THEN** la API responde 201 con el recurso creado

### Requirement: Respuestas sin datos internos
El sistema SHALL exponer en las respuestas solo los campos públicos definidos por cada contrato, sin `password_hash`, marcas de borrado lógico ni detalles internos de la base de datos.

#### Scenario: Error de base de datos
- **WHEN** una operación falla por una violación de restricción no mapeada
- **THEN** la API responde con un mensaje genérico sin el SQL ni el nombre interno de la restricción

#### Scenario: Representación de vehículo
- **WHEN** se consulta un vehículo vigente
- **THEN** la respuesta incluye `id`, `cliente_id`, `patente`, `marca`, `modelo` y `anio`, sin `borrado_en`
