## Purpose
Especificación del endpoint de cierre de sesión.

## ADDED Requirements

### Requirement: Logout con invalidación de cookie
The system SHALL invalidate the `access_token` cookie upon logout.

#### Scenario: Logout exitoso borra la cookie access_token
- **WHEN** the user sends a POST request to `/auth/logout` with an valid authentication cookie
- **THEN** the system returns 204 No Content
- **AND** the `access_token` cookie is cleared (Max-Age=0 or Expires=past)
- **AND** the `Set-Cookie` header is included to delete the cookie

#### Scenario: Logout sin sesión activa
- **WHEN** the user sends a POST request to `/auth/logout` without an active session
- **THEN** the system returns 204 No Content
- **AND** the cookie is still cleared (idempotent operation)