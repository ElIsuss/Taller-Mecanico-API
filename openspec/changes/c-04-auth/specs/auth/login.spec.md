## Purpose
Especificación del endpoint de inicio de sesión para la API del taller mecánico.

## ADDED Requirements

### Requirement: Validación de credenciales de login
The system SHALL allow users to authenticate with email and password.

#### Scenario: Login exitoso con credenciales válidas
- **WHEN** the user sends a POST request to `/auth/login` with valid email and password
- **THEN** the system returns 200 OK with a JWT token in a `access_token` cookie
- **AND** the response body contains `{"detail": "Logged in successfully"}`

#### Scenario: Login fallido con credenciales inválidas
- **WHEN** the user sends a POST request to `/auth/login` with invalid email or password
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Invalid credentials"}`

#### Scenario: Login con cuenta desactivada
- **WHEN** the user tries to login with a disabled account
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Account disabled"}`

### Requirement: Cumplimiento RN-09 (misma respuesta exista o no el correo)
The system SHALL return the same response whether the email exists or not, to prevent email enumeration attacks.

#### Scenario: Email inexistente retorna mismo error que email incorrecto
- **WHEN** the user sends a POST request to `/auth/login` with a non-registered email
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Invalid credentials"}`

#### Scenario: Email incorrecto retorna mismo error que email inexistente
- **WHEN** the user sends a POST request to `/auth/login` with an incorrect password for a registered email
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Invalid credentials"}`