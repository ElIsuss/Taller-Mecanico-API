# Spec Delta: integridad-solo-agregado

## Purpose

Asegura la inmutabilidad física y persistencia histórica de las tablas de solo agregado (historial_estado_orden, movimiento_stock e historial_precio_repuesto) mediante disparadores de base de datos en PostgreSQL (RN-15).

## ADDED Requirements

### Requirement: Protección de tablas de solo agregado mediante disparador
El sistema SHALL rechazar cualquier operación de `UPDATE` o `DELETE` sobre las tablas `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto` en PostgreSQL mediante una función y disparadores `BEFORE UPDATE OR DELETE FOR EACH ROW` (RN-15), permitiendo únicamente operaciones `INSERT`.

#### Scenario: Inserción permitida en tablas de solo agregado
- **WHEN** se ejecuta un `INSERT` válido sobre cualquiera de las tablas de solo agregado (`historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto`)
- **THEN** el registro se almacena exitosamente

#### Scenario: Modificación rechazada por disparador
- **WHEN** se intenta ejecutar un `UPDATE` sobre cualquier registro de `historial_estado_orden`, `movimiento_stock` o `historial_precio_repuesto`
- **THEN** el disparador de PostgreSQL aborta la operación emitiendo una excepción que señala la regla RN-15

#### Scenario: Eliminación rechazada por disparador
- **WHEN** se intenta ejecutar un `DELETE` sobre cualquier registro de `historial_estado_orden`, `movimiento_stock` o `historial_precio_repuesto`
- **THEN** el disparador de PostgreSQL aborta la operación emitiendo una excepción que señala la regla RN-15
