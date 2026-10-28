# Spec Delta

## Purpose

Administra órdenes de trabajo, ítems de repuesto, estados de orden e historial de cambios de estado.

## ADDED Requirements

### Requirement: Orden nace PENDIENTE con al menos un ítem
El sistema SHALL crear órdenes de trabajo en estado PENDIENTE y exigir al menos un ítem de repuesto.

#### Scenario: Orden creada en PENDIENTE
- **WHEN** se crea una orden de trabajo
- **THEN** su estado inicial es PENDIENTE

#### Scenario: Orden sin ítems rechazada
- **WHEN** se intenta crear una orden sin ítems de repuesto
- **THEN** el sistema rechaza la operación

### Requirement: Ítems sin repuestos repetidos en una orden
El sistema SHALL prohibir que una orden contenga el mismo repuesto más de una vez.

#### Scenario: Repuesto duplicado en ítems rechazado
- **WHEN** una orden intenta incluir dos ítems con el mismo repuesto
- **THEN** el sistema rechaza la operación

### Requirement: Precio de ítem copiado del repuesto
El sistema SHALL copiar el precio del repuesto al precio_unitario de cada ítem al crear la orden.

#### Scenario: Precio unitario copia del repuesto
- **WHEN** se crea un ítem de orden para un repuesto dado
- **THEN** el precio_unitario del ítem iguala el precio vigente del repuesto en ese momento

### Requirement: Total calculado por el servidor
El sistema SHALL calcular el total de la orden como suma de cantidad × precio_unitario de sus ítems.

#### Scenario: Total es suma de ítems
- **WHEN** una orden tiene ítems con cantidades y precios unitarios
- **THEN** el total de la orden equivale a la suma de cantidad × precio_unitario de cada ítem

### Requirement: Transiciones de estado de orden
El sistema SHALL permitir solo transiciones PENDIENTE → EN_REPARACION, EN_REPARACION → TERMINADA y PENDIENTE → CANCELADA.

#### Scenario: Transición PENDIENTE a EN_REPARACION permitida
- **WHEN** una orden en PENDIENTE recibe transición a EN_REPARACION
- **THEN** el sistema acepta el cambio de estado

#### Scenario: Transición EN_REPARACION a TERMINADA permitida
- **WHEN** una orden en EN_REPARACION recibe transición a TERMINADA
- **THEN** el sistema acepta el cambio de estado

#### Scenario: Transición PENDIENTE a CANCELADA permitida
- **WHEN** una orden en PENDIENTE recibe transición a CANCELADA
- **THEN** el sistema acepta el cambio de estado

#### Scenario: Transición inválida rechazada
- **WHEN** se intenta una transición no permitida (por ejemplo, TERMINADA → EN_REPARACION)
- **THEN** el sistema rechaza el cambio de estado

### Requirement: Tablas de solo agregado protegidas
El sistema SHALL prohibir modificar o borrar filas en historial_estado_orden, movimiento_stock e historial_precio_repuesto.

#### Scenario: UPDATE rechazado en tabla de solo agregado
- **WHEN** se intenta actualizar una fila en historial_estado_orden, movimiento_stock o historial_precio_repuesto
- **THEN** el sistema rechaza la operación

#### Scenario: DELETE rechazado en tabla de solo agregado
- **WHEN** se intenta borrar una fila en historial_estado_orden, movimiento_stock o historial_precio_repuesto
- **THEN** el sistema rechaza la operación
