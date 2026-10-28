# ordenes Specification

## Purpose

Administra órdenes de trabajo, ítems de repuesto, el catálogo de estados e historial de cambios de estado.

## Requirements

### Requirement: Catálogo de estados de orden
El sistema SHALL modelar `estado_orden` con `codigo` como clave primaria, `descripcion`, `posicion` única y `es_final`.

#### Scenario: Estado con posición única
- **WHEN** se intenta insertar un estado con una `posicion` ya usada
- **THEN** la base de datos rechaza la operación

### Requirement: Orden nace en el estado inicial
El sistema SHALL crear órdenes de trabajo referenciando un `estado_orden.codigo` válido y con al menos un ítem de repuesto.

#### Scenario: Orden creada en estado inicial
- **WHEN** se crea una orden de trabajo
- **THEN** su `estado` es el código inicial definido en el catálogo

#### Scenario: Orden sin ítems rechazada
- **WHEN** se intenta crear una orden sin ítems
- **THEN** el sistema rechaza la operación

### Requirement: Mecánico opcional
El sistema SHALL permitir `orden_trabajo.mecanico_id` nulo o una FK a `usuario.id`; no se restringe por rol en la base.

#### Scenario: Orden sin mecánico asignado
- **WHEN** se crea una orden sin mecánico
- **THEN** `mecanico_id` queda nulo

### Requirement: Ítems sin repuestos repetidos
El sistema SHALL prohibir el mismo repuesto dos veces en una orden mediante UNIQUE `(orden_id, repuesto_id)`.

#### Scenario: Repuesto duplicado rechazado
- **WHEN** una orden intenta incluir dos ítems con el mismo repuesto
- **THEN** la base de datos rechaza la operación

### Requirement: Precio de ítem copiado del repuesto
El sistema SHALL copiar el precio del repuesto al `precio_unitario` de cada ítem al crear la orden, con `cantidad > 0` y `precio_unitario > 0`.

#### Scenario: Precio unitario copia del repuesto
- **WHEN** se crea un ítem para un repuesto
- **THEN** su `precio_unitario` iguala el precio vigente del repuesto en ese momento

### Requirement: Total calculado por el servidor
El sistema SHALL almacenar `orden_trabajo.total` como `NUMERIC(12,2)` no negativo, calculado como suma de `cantidad × precio_unitario`.

#### Scenario: Total es suma de ítems
- **WHEN** una orden tiene ítems con cantidades y precios unitarios
- **THEN** el total equivale a la suma de `cantidad × precio_unitario`

### Requirement: Transiciones de estado de orden
El sistema SHALL permitir solo transiciones PENDIENTE → EN_REPARACION, EN_REPARACION → TERMINADA y PENDIENTE → CANCELADA.

#### Scenario: Transición permitida
- **WHEN** una orden en PENDIENTE pasa a EN_REPARACION
- **THEN** el sistema acepta el cambio de estado

#### Scenario: Transición inválida rechazada
- **WHEN** se intenta una transición no permitida (por ejemplo, TERMINADA → EN_REPARACION)
- **THEN** el sistema rechaza el cambio de estado

### Requirement: Tablas de solo agregado protegidas
El sistema SHALL prohibir `UPDATE` y `DELETE` sobre `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto` mediante un disparador de PostgreSQL (RN-15), permitiendo `INSERT`.

#### Scenario: UPDATE rechazado en tabla de solo agregado
- **WHEN** se intenta actualizar una fila en una de las tablas protegidas
- **THEN** la base de datos rechaza la operación

#### Scenario: DELETE rechazado en tabla de solo agregado
- **WHEN** se intenta borrar una fila en una de las tablas protegidas
- **THEN** la base de datos rechaza la operación
