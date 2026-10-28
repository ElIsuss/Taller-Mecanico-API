# Spec Delta

## Purpose

Gestiona vehículos vinculados a cliente, con patente única entre vigentes y protección contra baja si tiene órdenes abiertas.

## ADDED Requirements

### Requirement: Patente única entre vehículos vigentes
El sistema SHALL garantizar que la patente de un vehículo sea única solo entre los vehículos no dados de baja.

#### Scenario: Patente única entre vehículos vigentes
- **WHEN** se intenta crear un vehículo con una patente que ya pertenece a un vehículo vigente
- **THEN** el sistema rechaza la operación con error de unicidad

#### Scenario: Patente reutilizable tras baja lógica
- **WHEN** un vehículo fue dado de baja (fecha_baja no nula)
- **THEN** otro vehículo puede registrarse con la misma patente

### Requirement: Vehículo con órdenes abiertas no se da de baja
El sistema SHALL impedir el borrado lógico de un vehículo que tenga órdenes de trabajo abiertas.

#### Scenario: Baja bloqueada si tiene órdenes abiertas
- **WHEN** un vehículo tiene al menos una orden de trabajo no terminada ni cancelada
- **THEN** el sistema rechaza dar de baja al vehículo

#### Scenario: Baja permitida si no tiene órdenes abiertas
- **WHEN** un vehículo no tiene órdenes abiertas (todas terminadas o canceladas, o ninguna)
- **THEN** el sistema permite dar de baja al vehículo
