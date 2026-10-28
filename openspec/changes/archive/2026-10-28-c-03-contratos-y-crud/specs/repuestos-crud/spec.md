# Spec Delta

## Purpose

Expone el catálogo de repuestos, su búsqueda, la reposición de stock mediante movimientos y el cambio de precio con historial.

## ADDED Requirements

### Requirement: Alta de repuesto
El sistema SHALL crear un repuesto con `codigo`, `descripcion` y `precio` obligatorios, `stock` inicial opcional (0 por defecto) y código único entre los repuestos vigentes.

#### Scenario: Alta válida
- **WHEN** se envía `POST /repuestos` con código nuevo, descripción y precio
- **THEN** la API responde 201 con el repuesto creado

#### Scenario: Código duplicado entre vigentes
- **WHEN** se envía un código que ya pertenece a un repuesto no borrado
- **THEN** la API responde 409

#### Scenario: Precio no positivo
- **WHEN** se envía un precio menor o igual a 0
- **THEN** la API responde 422

### Requirement: Consulta y búsqueda paginada
El sistema SHALL listar solo repuestos vigentes, de forma paginada, y SHALL permitir buscar por coincidencia parcial e insensible a mayúsculas en `descripcion` usando parámetros ligados.

#### Scenario: Búsqueda por descripción
- **WHEN** se consulta `GET /repuestos?busqueda=filtro`
- **THEN** la respuesta solo incluye repuestos cuya descripción contiene "filtro"

#### Scenario: Búsqueda sin resultados
- **WHEN** la búsqueda no coincide con ningún repuesto
- **THEN** la API responde 200 con `items = []`, `total = 0` y `pages = 0`

#### Scenario: Caracteres especiales en la búsqueda
- **WHEN** la búsqueda incluye `%` o `_`
- **THEN** se tratan como texto literal y no como comodines

#### Scenario: Repuesto borrado excluido
- **WHEN** se lista el catálogo
- **THEN** los repuestos con `borrado_en` establecido no aparecen

### Requirement: Actualización parcial de repuesto
El sistema SHALL actualizar solo los campos enviados (`codigo`, `descripcion`, `precio`) y SHALL rechazar cualquier intento de modificar `stock` directamente con 422.

#### Scenario: Cambio de descripción
- **WHEN** se envía `PATCH /repuestos/{id}` con una nueva descripción
- **THEN** la API responde 200 y solo cambia ese campo

#### Scenario: Intento de modificar stock
- **WHEN** se envía `stock` en el cuerpo del PATCH
- **THEN** la API responde 422 y no modifica el repuesto

### Requirement: Cambio de precio con historial
El sistema SHALL registrar una fila en `historial_precio_repuesto` cada vez que cambia el precio, con `precio_anterior`, `precio_nuevo`, `usuario_id` y `cuando`; si el precio no cambia SHALL no registrar historial.

#### Scenario: Cambio efectivo de precio
- **WHEN** se envía `PATCH /repuestos/{id}` con `precio` distinto y `usuario_id`
- **THEN** la API actualiza el precio e inserta una fila de historial

#### Scenario: PATCH de precio sin actor
- **WHEN** se envía `PATCH /repuestos/{id}` con `precio` pero sin `usuario_id`
- **THEN** la API responde 422 y no modifica el precio

#### Scenario: Precio igual al actual
- **WHEN** se envía el mismo precio que ya tiene el repuesto
- **THEN** la API responde 200 y no inserta fila de historial

### Requirement: Reposición de stock
El sistema SHALL reponer stock únicamente mediante `POST /repuestos/{id}/reposiciones`, creando un `movimiento_stock` con `cantidad` positiva, `motivo`, `usuario_id` y actualizando el stock en la misma operación.

#### Scenario: Reposición válida
- **WHEN** se envía `POST /repuestos/{id}/reposiciones` con cantidad positiva, motivo y usuario existente
- **THEN** la API responde 201, crea el movimiento y aumenta el stock

#### Scenario: Cantidad no positiva
- **WHEN** se envía una cantidad menor o igual a 0
- **THEN** la API responde 422 y no crea el movimiento

#### Scenario: Repuesto borrado
- **WHEN** se intenta reponer stock de un repuesto dado de baja
- **THEN** la API responde 404

### Requirement: Baja lógica de repuesto
El sistema SHALL dar de baja un repuesto estableciendo `borrado_en`, sin borrar sus datos, y SHALL impedir su uso en órdenes nuevas.

#### Scenario: Baja de repuesto
- **WHEN** se envía `DELETE /repuestos/{id}` de un repuesto vigente
- **THEN** la API responde 204 y el repuesto deja de aparecer en listados

#### Scenario: Repuesto borrado en una orden nueva
- **WHEN** se intenta crear una orden con un repuesto dado de baja
- **THEN** la API responde 404 o 409 y no crea la orden

### Requirement: Consulta del historial de precios
El sistema SHALL permitir consultar el historial de precios de un repuesto de forma paginada, ordenado por `cuando` descendente.

#### Scenario: Historial de un repuesto
- **WHEN** se consulta `GET /repuestos/{id}/historial-precios`
- **THEN** la API responde 200 con el envoltorio de paginación y las líneas del repuesto
