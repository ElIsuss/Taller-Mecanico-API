# Spec Delta

## Purpose

Expone la apertura, consulta, actualización básica y el ciclo de vida de las órdenes de trabajo, incluyendo ítems, total calculado, historial de estados y descuento de stock al terminar.

## ADDED Requirements

### Requirement: Apertura de orden con ítems
El sistema SHALL crear una orden en estado PENDIENTE con `vehiculo_id`, `falla`, al menos un ítem y `usuario_id` (actor), copiando el precio vigente de cada repuesto y calculando el total en el servidor.

#### Scenario: Alta válida
- **WHEN** se envía `POST /ordenes` con un vehículo vigente, falla, un ítem y un usuario existente
- **THEN** la API responde 201 con la orden en PENDIENTE, el `total` calculado y una línea de historial inicial

#### Scenario: Orden sin ítems
- **WHEN** se envía una orden con la lista de ítems vacía
- **THEN** la API responde 422 y no crea la orden

#### Scenario: Repuesto repetido
- **WHEN** se envían dos ítems con el mismo `repuesto_id`
- **THEN** la API responde 422 y no crea la orden

#### Scenario: Vehículo o repuesto inexistente
- **WHEN** el `vehiculo_id` o algún `repuesto_id` no existe
- **THEN** la API responde 404 y no crea la orden

#### Scenario: Vehículo o repuesto borrado
- **WHEN** el vehículo o algún repuesto está dado de baja
- **THEN** la API responde 409 y no crea la orden

#### Scenario: Total calculado por el servidor
- **WHEN** la orden tiene 2 ítems de 3 y 2 unidades con precios 10.00 y 5.50
- **THEN** el `total` devuelto es 41.00, sin confiar en un total enviado por el cliente

### Requirement: Consulta y listado de órdenes
El sistema SHALL permitir consultar una orden por id (con sus ítems) y listar órdenes de forma paginada, opcionalmente filtradas por `estado` y `vehiculo_id`.

#### Scenario: Detalle de orden
- **WHEN** se consulta `GET /ordenes/{id}`
- **THEN** la API responde 200 con la orden, su estado, su total y sus ítems

#### Scenario: Filtro por estado
- **WHEN** se consulta `GET /ordenes?estado=PENDIENTE`
- **THEN** la respuesta solo incluye órdenes en ese estado

#### Scenario: Orden inexistente
- **WHEN** se consulta un id que no existe
- **THEN** la API responde 404

### Requirement: Actualización básica de orden
El sistema SHALL permitir modificar `falla` y `mecanico_id` solo mientras la orden está en PENDIENTE; los ítems y el total no se editan por PATCH.

#### Scenario: Cambio de falla en PENDIENTE
- **WHEN** se envía `PATCH /ordenes/{id}` con una nueva falla y la orden está PENDIENTE
- **THEN** la API responde 200 y actualiza la falla

#### Scenario: Cambio en orden ya iniciada
- **WHEN** se intenta PATCH sobre una orden EN_REPARACION, TERMINADA o CANCELADA
- **THEN** la API responde 409

#### Scenario: Intento de cambiar ítems o total
- **WHEN** el cuerpo del PATCH incluye `items` o `total`
- **THEN** la API responde 422

### Requirement: Inicio de orden
El sistema SHALL permitir iniciar solo una orden PENDIENTE, pasándola a EN_REPARACION, asignando `mecanico_id` si estaba vacío y registrando historial con el actor.

#### Scenario: Inicio válido
- **WHEN** se envía `POST /ordenes/{id}/iniciar` con `usuario_id` sobre una orden PENDIENTE
- **THEN** la API responde 200 con estado EN_REPARACION y una línea de historial

#### Scenario: Orden no PENDIENTE
- **WHEN** se intenta iniciar una orden ya iniciada, terminada o cancelada
- **THEN** la API responde 409 y no cambia el estado

### Requirement: Terminación de orden con descuento de stock
El sistema SHALL terminar solo una orden EN_REPARACION; en una única operación SHALL verificar stock suficiente, descontar el stock de cada ítem, crear un `movimiento_stock` negativo por ítem, pasar la orden a TERMINADA y registrar el historial.

#### Scenario: Terminación válida
- **WHEN** hay stock suficiente y se envía `POST /ordenes/{id}/terminar` con `usuario_id`
- **THEN** la API responde 200, descuenta el stock, crea los movimientos y deja la orden TERMINADA

#### Scenario: Stock insuficiente
- **WHEN** algún repuesto no alcanza para la cantidad del ítem
- **THEN** la API responde 409 y no deja ninguna escritura (ni stock, ni movimientos, ni historial)

#### Scenario: Orden no EN_REPARACION
- **WHEN** se intenta terminar una orden en otro estado
- **THEN** la API responde 409 y no modifica nada

### Requirement: Cancelación de orden
El sistema SHALL permitir cancelar solo una orden PENDIENTE, pasándola a CANCELADA y registrando el historial con el actor.

#### Scenario: Cancelación válida
- **WHEN** se envía `POST /ordenes/{id}/cancelar` con `usuario_id` sobre una orden PENDIENTE
- **THEN** la API responde 200 con estado CANCELADA y una línea de historial

#### Scenario: Orden terminada no se cancela
- **WHEN** se intenta cancelar una orden TERMINADA
- **THEN** la API responde 409 y no cambia el estado

#### Scenario: Orden ya cancelada
- **WHEN** se intenta cancelar una orden CANCELADA
- **THEN** la API responde 409
