# Spec Delta

## Purpose

Administra el catálogo de repuestos, sus precios y el stock; el stock solo cambia mediante movimientos y cada cambio de precio deja historial.

## ADDED Requirements

### Requirement: Código único entre repuestos vigentes
El sistema SHALL garantizar que el código sea único solo entre los repuestos no borrados (`borrado_en IS NULL`), mediante un índice único parcial.

#### Scenario: Código duplicado entre vigentes rechazado
- **WHEN** se intenta crear un repuesto con un código que ya pertenece a un repuesto vigente
- **THEN** el sistema rechaza la operación con error de unicidad

### Requirement: Dinero con precisión decimal
El sistema SHALL almacenar `precio` como `NUMERIC(10,2)` y `precio_unitario` de los ítems como `NUMERIC(10,2)`, mapeados a `Decimal` (nunca `float`).

#### Scenario: Precio con dos decimales
- **WHEN** se guarda un precio de 1234.56
- **THEN** la base de datos conserva exactamente 1234.56

### Requirement: Validaciones de repuesto
El sistema SHALL validar `precio > 0` y `stock >= 0` mediante CHECK.

#### Scenario: Precio no positivo rechazado
- **WHEN** se intenta guardar un repuesto con precio 0 o negativo
- **THEN** la base de datos rechaza la operación

#### Scenario: Stock negativo rechazado
- **WHEN** se intenta dejar el stock por debajo de 0
- **THEN** la base de datos rechaza la operación

### Requirement: Stock solo modificable mediante movimientos
El sistema SHALL permitir cambios de stock únicamente a través de registros en `movimiento_stock`; `cantidad` no puede ser cero y cada movimiento guarda `motivo`, `usuario_id` y opcionalmente `orden_id`.

#### Scenario: Stock no editable directamente por PATCH
- **WHEN** se intenta modificar el campo stock mediante PATCH
- **THEN** el sistema rechaza la operación

#### Scenario: Movimiento de cantidad cero rechazado
- **WHEN** se registra un movimiento con `cantidad = 0`
- **THEN** la base de datos rechaza la operación

### Requirement: Historial de precios en cada cambio
El sistema SHALL insertar una fila en `historial_precio_repuesto` (`precio_anterior`, `precio_nuevo`, `usuario_id`, `cuando`) cada vez que cambia el precio, en la misma transacción, con `precio_nuevo > 0` y `precio_nuevo <> precio_anterior`.

#### Scenario: Línea de historial al cambiar precio
- **WHEN** el precio de un repuesto se modifica
- **THEN** se inserta una fila en `historial_precio_repuesto`

#### Scenario: Sin línea si el precio no cambia
- **WHEN** un PATCH no modifica el precio
- **THEN** no se inserta ninguna fila en `historial_precio_repuesto`
