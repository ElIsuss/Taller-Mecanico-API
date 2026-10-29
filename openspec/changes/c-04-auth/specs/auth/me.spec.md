## Purpose
Especificación del endpoint de perfil de usuario autenticado.

## ADDED Requirements

### Requirement: Obtención de perfil del usuario autenticado
The system SHALL return the authenticated user's profile when accessing `GET /auth/yo`.

#### Scenario: Perfil devuelto con datos básicos del usuario
- **WHEN** the user sends a GET request to `/auth/yo` with a valid `access_token` cookie
- **THEN** the system returns 200 OK
- **AND** the response body contains user information: `{"id": ..., "email": ..., "role": ..., "iat": ...}`
- **AND** the password_hash field is NOT included in the response

#### Scenario: Perfil devuelto con roles vigentes consultados en base
- **WHEN** the user sends a GET request to `/auth/yo` with a valid `access_token` cookie
- **THEN** the response includes the `roles` field with roles vigentes consultados en la base de datos (RN-04)
- **AND** los roles del token son informativos, la fuente autoritativa es la base de datos

#### Scenario: 401 si no hay sesión válida
- **WHEN** the user sends a GET request to `/auth/yo` without a valid `access_token` cookie
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Not authenticated"}`