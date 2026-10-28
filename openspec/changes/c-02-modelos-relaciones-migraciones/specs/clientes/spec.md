# Spec Delta

## Purpose

Administra fichas de cliente con borrado lógico y unicidad de documento entre los vigentes.

## ADDED Requirements

### Requirement: Documento único entre clientes vigentes
El sistema SHALL garantizar que el documento de un cliente sea único solo entre los clientes no dados de baja.

#### Scenario: Documento único entre clientes vigentes
- **WHEN** se intenta crear un cliente con un documento que ya pertenece a un cliente vigente
- **THEN** el sistema rechaza la operación con error de unicidad

#### Scenario: Documento reutilizable tras baja lógica
- **WHEN** un cliente fue dado de baja (fecha_baja no nula)
- **THEN** otro cliente puede registrarse con el mismo documento

### Requirement: Baja lógica conserva datos del cliente
El sistema SHALL conservar los datos de un cliente dado de baja y no permitir usarlo en operaciones nuevas.

#### Scenario: Cliente dado de baja no aparece en operaciones nuevas
- **WHEN** un cliente tiene fecha_baja establecida
- **THEN** el cliente no se incluye en listados ni puede vincularse a vehículos u órdenes nuevas

#### Scenario: Datos conservados tras baja
- **WHEN** se consulta un cliente dado de baja por su identificador
- **THEN** el sistema devuelve sus datos con fecha_baja poblada
