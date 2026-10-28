# vehiculos Specification

## Purpose

Gestiona vehículos vinculados a un cliente, con patente única entre vigentes y protección contra la baja si tienen órdenes abiertas.

## Requirements

### Requirement: Patente única entre vehículos vigentes
El sistema SHALL garantizar que la patente sea única solo entre los vehículos no borrados (`borrado_en IS NULL`), mediante un índice único parcial.

#### Scenario: Patente duplicada entre vigentes rechazada
- **WHEN** se intenta crear un vehículo con una patente que ya pertenece a un vehículo vigente
- **THEN** el sistema rechaza la operación con error de unicidad

#### Scenario: Patente reutilizable tras baja lógica
- **WHEN** un vehículo fue borrado (`borrado_en` no nulo)
- **THEN** otro vehículo puede registrarse con la misma patente

### Requirement: Vehículo pertenece a un cliente
El sistema SHALL exigir `vehiculo.cliente_id` no nulo con FK a `cliente.id` e índice sobre la FK.

#### Scenario: Vehículo sin cliente rechazado
- **WHEN** se intenta crear un vehículo sin `cliente_id`
- **THEN** la base de datos rechaza la operación

### Requirement: Año del vehículo en rango válido
El sistema SHALL validar `1950 <= anio <= 2100` mediante CHECK.

#### Scenario: Año fuera de rango rechazado
- **WHEN** se intenta registrar un vehículo con año 1949 o 2101
- **THEN** la base de datos rechaza la operación

### Requirement: Vehículo con órdenes abiertas no se da de baja
El sistema SHALL impedir el borrado lógico de un vehículo que tenga órdenes de trabajo abiertas (regla de servicio).

#### Scenario: Baja bloqueada si tiene órdenes abiertas
- **WHEN** un vehículo tiene al menos una orden no terminada ni cancelada
- **THEN** el sistema rechaza dar de baja al vehículo

#### Scenario: Baja permitida sin órdenes abiertas
- **WHEN** un vehículo no tiene órdenes abiertas
- **THEN** el sistema permite dar de baja al vehículo
