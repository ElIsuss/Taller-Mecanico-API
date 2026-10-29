## Purpose
Especificación del registro automático de usuario con rol CLIENTE y ficha cliente.

## ADDED Requirements

### Requirement: Registro atómico de usuario con rol y ficha
The system SHALL perform atomic registration creating a user, a CLIENTE role assignment, and a client record.

#### Scenario: Registro exitoso con creación de usuario, rol y ficha
- **WHEN** the user sends a POST request to `/auth/register` with valid client data
- **THEN** the system returns 201 Created
- **AND** a new user record is created with status ACTIVE
- **AND** a new asignacion_rol record links the user to role CLIENTE
- **AND** a new cliente record is created with the user_id reference

#### Scenario: Fallo si el email ya está registrado
- **WHEN** the user sends a POST request to `/auth/register` with an email already in use
- **THEN** the system returns 409 Conflict
- **AND** the response body contains `{"detail": "Email already registered"}`

#### Scenario: Fallo si el documento ya está registrado
- **WHEN** the user sends a POST request to `/auth/register` with a document already in use
- **THEN** the system returns 409 Conflict
- **AND** the response body contains `{"detail": "Document already registered"}`