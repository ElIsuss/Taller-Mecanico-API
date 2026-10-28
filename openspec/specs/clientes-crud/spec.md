# clientes-crud Specification

## Purpose

Expone el ciclo de vida de las fichas de cliente mediante endpoints REST de alta, consulta, actualización parcial, listado paginado y baja.

## Requirements

### Requirement: Alta de cliente
El sistema SHALL crear un cliente con `nombre`, `documento` y `telefono` obligatorios, y `usuario_id` opcional, devolviendo 201 con el cliente creado.

#### Scenario: Alta válida
- **WHEN** se envía `POST /clientes` con nombre, documento y teléfono
- **THEN** la API responde 201 con el cliente y su `id`

#### Scenario: Documento duplicado
- **WHEN** se envía un documento que ya pertenece a otro cliente
- **THEN** la API responde 409 y no crea el cliente

#### Scenario: Usuario ya vinculado
- **WHEN** se envía un `usuario_id` que ya está vinculado a otro cliente
- **THEN** la API responde 409

### Requirement: Consulta y listado de clientes
El sistema SHALL permitir consultar un cliente por id y listar clientes de forma paginada.

#### Scenario: Cliente existente
- **WHEN** se consulta `GET /clientes/{id}` de un cliente existente
- **THEN** la API responde 200 con sus datos públicos

#### Scenario: Cliente inexistente
- **WHEN** se consulta `GET /clientes/{id}` de un id que no existe
- **THEN** la API responde 404

#### Scenario: Listado paginado
- **WHEN** se consulta `GET /clientes?page=1&size=10`
- **THEN** la API responde 200 con el envoltorio de paginación

### Requirement: Actualización parcial de cliente
El sistema SHALL actualizar solo los campos enviados (`nombre`, `documento`, `telefono`, `usuario_id`) y validar la unicidad de documento y usuario.

#### Scenario: Cambio de teléfono
- **WHEN** se envía `PATCH /clientes/{id}` con un nuevo teléfono
- **THEN** la API responde 200 y solo cambia ese campo

#### Scenario: Documento de otro cliente
- **WHEN** se intenta cambiar el documento a uno ya usado por otro cliente
- **THEN** la API responde 409

### Requirement: Baja de cliente sin vehículos
El sistema SHALL borrar físicamente un cliente solo si no tiene vehículos asociados; en caso contrario SHALL responder 409.

#### Scenario: Cliente sin vehículos
- **WHEN** se envía `DELETE /clientes/{id}` de un cliente sin vehículos
- **THEN** la API responde 204 y el cliente deja de existir

#### Scenario: Cliente con vehículos
- **WHEN** el cliente tiene al menos un vehículo (vigente o dado de baja)
- **THEN** la API responde 409 y no borra el cliente

#### Scenario: Cliente inexistente
- **WHEN** se intenta borrar un cliente que no existe
- **THEN** la API responde 404
