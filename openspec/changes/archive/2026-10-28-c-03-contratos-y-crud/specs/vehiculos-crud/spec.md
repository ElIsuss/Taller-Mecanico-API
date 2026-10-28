# Spec Delta

## Purpose

Expone el alta, consulta, listado paginado, actualización parcial y baja lógica de vehículos vinculados a un cliente.

## ADDED Requirements

### Requirement: Alta de vehículo
El sistema SHALL crear un vehículo con `cliente_id`, `patente`, `marca`, `modelo` y `anio`, exigiendo que el cliente exista y que la patente sea única entre los vehículos vigentes.

#### Scenario: Alta válida
- **WHEN** se envía `POST /vehiculos` con un cliente existente y una patente nueva
- **THEN** la API responde 201 con el vehículo creado

#### Scenario: Cliente inexistente
- **WHEN** se envía un `cliente_id` que no existe
- **THEN** la API responde 404

#### Scenario: Patente duplicada entre vigentes
- **WHEN** se envía una patente que ya pertenece a un vehículo no borrado
- **THEN** la API responde 409

#### Scenario: Año fuera de rango
- **WHEN** se envía un `anio` menor a 1950 o mayor a 2100
- **THEN** la API responde 422

### Requirement: Consulta y listado de vehículos vigentes
El sistema SHALL permitir consultar un vehículo vigente por id y listar solo los vehículos no borrados, de forma paginada y opcionalmente filtrados por `cliente_id`.

#### Scenario: Listado excluye borrados
- **WHEN** se consulta `GET /vehiculos`
- **THEN** la respuesta no incluye vehículos con `borrado_en` establecido

#### Scenario: Filtro por cliente
- **WHEN** se consulta `GET /vehiculos?cliente_id=3`
- **THEN** la respuesta solo incluye vehículos de ese cliente

#### Scenario: Vehículo borrado consultado por id
- **WHEN** se consulta `GET /vehiculos/{id}` de un vehículo dado de baja
- **THEN** la API responde 404

### Requirement: Actualización parcial de vehículo
El sistema SHALL actualizar solo los campos enviados y validar la existencia del cliente y la unicidad de patente.

#### Scenario: Cambio de modelo
- **WHEN** se envía `PATCH /vehiculos/{id}` con un nuevo modelo
- **THEN** la API responde 200 y solo cambia ese campo

#### Scenario: Patente de otro vehículo vigente
- **WHEN** se intenta cambiar la patente a una ya usada por otro vehículo vigente
- **THEN** la API responde 409

### Requirement: Baja lógica de vehículo
El sistema SHALL dar de baja un vehículo estableciendo `borrado_en`, sin borrar sus datos, y SHALL rechazar la baja con 409 si tiene órdenes abiertas (estado no final).

#### Scenario: Baja permitida
- **WHEN** se envía `DELETE /vehiculos/{id}` de un vehículo sin órdenes abiertas
- **THEN** la API responde 204 y el vehículo deja de aparecer en los listados

#### Scenario: Baja bloqueada por órdenes abiertas
- **WHEN** el vehículo tiene al menos una orden cuyo estado no es final
- **THEN** la API responde 409 y no modifica `borrado_en`

#### Scenario: Patente reutilizable tras la baja
- **WHEN** un vehículo fue dado de baja y se crea otro con la misma patente
- **THEN** la API acepta el alta
