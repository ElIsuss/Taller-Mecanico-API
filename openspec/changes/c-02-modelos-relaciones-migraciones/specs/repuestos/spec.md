# Spec Delta

## Purpose

Administra catálogo de repuestos, movimientos de stock e historial de precios; el stock solo cambia mediante movimientos.

## ADDED Requirements

### Requirement: Código único entre repuestos vigentes
El sistema SHALL garantizar que el código de un repuesto sea único solo entre los repuestos no dados de baja.

#### Scenario: Código único entre repuestos vigentes
- **WHEN** se intenta crear un repuesto con un código que ya pertenece a un repuesto vigente
- **THEN** el sistema rechaza la operación con error de unicidad

### Requirement: Stock solo modificable mediante movimientos
El sistema SHALL permitir cambios de stock únicamente a través de registros en movimiento_stock (alta, reposición, terminación).

#### Scenario: Stock no editable directamente por PATCH
- **WHEN** se intenta modificar el campo stock de un repuesto mediante PATCH
- **THEN** el sistema rechaza la operación

#### Scenario: Stock cambia vía movimiento de alta
- **WHEN** se registra un movimiento de tipo alta con cantidad positiva para un repuesto
- **THEN** el stock del repuesto aumenta en esa cantidad

#### Scenario: Stock cambia vía movimiento de reposición
- **WHEN** se registra un movimiento de tipo reposición con cantidad positiva para un repuesto
- **THEN** el stock del repuesto aumenta en esa cantidad

#### Scenario: Stock cambia vía movimiento de terminación
- **WHEN** se registra un movimiento de tipo terminación con cantidad positiva para un repuesto
- **THEN** el stock del repuesto disminuye en esa cantidad

### Requirement: Historial de precios en cada cambio
El sistema SHALL dejar una línea en historial_precio_repuesto cada vez que cambia el precio de un repuesto, en la misma transacción.

#### Scenario: Línea de historial al cambiar precio
- **WHEN** el precio de un repuesto se modifica
- **THEN** se inserta una fila en historial_precio_repuesto con precio_anterior, precio_nuevo y fecha_cambio

#### Scenario: Sin línea de historial si el precio no cambia
- **WHEN** se hace un PATCH a un repuesto que no modifica su precio
- **THEN** no se inserta ninguna fila en historial_precio_repuesto
