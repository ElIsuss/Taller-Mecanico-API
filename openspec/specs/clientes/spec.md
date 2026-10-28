# clientes Specification

## Purpose

Administra las fichas de cliente y su vínculo opcional con un usuario del sistema.

## Requirements

### Requirement: Documento único de cliente
El sistema SHALL garantizar que el documento de un cliente sea único y obligatorio (columna `cliente.documento` con UNIQUE).

#### Scenario: Documento duplicado rechazado
- **WHEN** se intenta crear un cliente con un documento que ya existe
- **THEN** el sistema rechaza la operación con error de unicidad

### Requirement: Cliente vinculado opcionalmente a un usuario
El sistema SHALL permitir que un cliente esté asociado a lo sumo a un usuario mediante `cliente.usuario_id` (nullable, UNIQUE, FK a `usuario.id`).

#### Scenario: Cliente sin usuario
- **WHEN** se crea un cliente sin cuenta de acceso
- **THEN** `usuario_id` queda nulo y el cliente existe igualmente

#### Scenario: Segundo vínculo al mismo usuario rechazado
- **WHEN** se intenta asociar un usuario ya vinculado a otro cliente
- **THEN** el sistema rechaza la operación por unicidad de `usuario_id`

### Requirement: Datos de contacto del cliente
El sistema SHALL almacenar `nombre` y `telefono` obligatorios para cada cliente.

#### Scenario: Alta de cliente con contacto
- **WHEN** se crea un cliente con nombre y teléfono
- **THEN** el cliente queda registrado con ambos datos
