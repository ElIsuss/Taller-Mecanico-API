# auth Specification

## Purpose

Gestiona la identidad de usuarios, las asignaciones de rol con vigencia, los intentos de acceso y la bitácora de eventos de seguridad.

## Requirements

### Requirement: Email único de usuario
El sistema SHALL garantizar que el email de un usuario sea único y obligatorio (columna `usuario.email` con UNIQUE).

#### Scenario: Email duplicado rechazado
- **WHEN** se intenta crear un usuario con un email que ya existe
- **THEN** el sistema rechaza la operación con error de unicidad

### Requirement: Roles como valores controlados
El sistema SHALL aceptar únicamente los roles ADMIN, RECEPCION, MECANICO y CLIENTE, validados por un CHECK en `asignacion_rol.rol`.

#### Scenario: Rol válido aceptado
- **WHEN** se crea una asignación de rol con valor ADMIN, RECEPCION, MECANICO o CLIENTE
- **THEN** el sistema acepta la asignación

#### Scenario: Rol inválido rechazado
- **WHEN** se intenta asignar un rol fuera de ese conjunto
- **THEN** la base de datos rechaza la operación

### Requirement: Una asignación vigente por rol por usuario
El sistema SHALL permitir a lo sumo una asignación no revocada (`revocada_en IS NULL`) por par `(usuario_id, rol)`, garantizado por un índice único parcial.

#### Scenario: Asignación vigente duplicada rechazada
- **WHEN** un usuario ya tiene una asignación no revocada para un rol
- **THEN** el sistema rechaza crear una segunda asignación vigente para ese mismo rol

#### Scenario: Asignación revocada permite nueva apertura
- **WHEN** la asignación previa tiene `revocada_en` establecido
- **THEN** el sistema permite crear una nueva asignación para ese mismo rol

### Requirement: Vigencia y otorgante de la asignación
El sistema SHALL registrar `desde`, `vence_en` (opcional), `revocada_en` (opcional) y `otorgada_por` (usuario que otorgó el rol, opcional) en cada asignación.

#### Scenario: Asignación con vigencia
- **WHEN** se crea una asignación con `vence_en` futuro
- **THEN** la asignación se considera vigente hasta esa fecha salvo revocación

### Requirement: password_cambiada_en con precisión de subsegundo
El sistema SHALL almacenar `password_cambiada_en` como `timestamptz` nullable para comparar con el `iat` del token sin truncar.

#### Scenario: Comparación de iat sin truncar a segundos
- **WHEN** se compara el `iat` del token contra `password_cambiada_en`
- **THEN** la comparación usa la marca de tiempo completa con zona horaria

### Requirement: Registro de intentos de acceso
El sistema SHALL registrar cada intento de login en `intento_acceso` (`cuando`, `email`, `ip`, `exito`) con un índice `(email, ip, cuando)` para soportar el límite de intentos fallidos.

#### Scenario: Intento fallido registrado
- **WHEN** un login falla
- **THEN** se inserta una fila en `intento_acceso` con `exito = false`

### Requirement: Bitácora de eventos de seguridad
El sistema SHALL registrar eventos de seguridad en `evento_seguridad` (`cuando`, `actor`, `accion`).

#### Scenario: Evento de seguridad registrado
- **WHEN** ocurre una acción auditable (alta de usuario, cambio de rol, revocación)
- **THEN** se inserta una fila en `evento_seguridad` con actor y acción

### Requirement: Validación de credenciales de login
The system SHALL allow users to authenticate with email and password.

#### Scenario: Login exitoso con credenciales válidas
- **WHEN** the user sends a POST request to `/auth/login` with valid email and password
- **THEN** the system returns 200 OK with a JWT token in an `access_token` cookie
- **AND** the response body contains user information without `password_hash`

#### Scenario: Login fallido con credenciales inválidas
- **WHEN** the user sends a POST request to `/auth/login` with invalid email or password
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Invalid credentials"}`

#### Scenario: Login con cuenta desactivada
- **WHEN** the user tries to login with a disabled account
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Account disabled"}`

### Requirement: Cumplimiento RN-09 (tiempo y respuesta constantes)
The system SHALL return the same response whether the email exists or not, to prevent email enumeration attacks.

#### Scenario: Email inexistente retorna mismo error y tarda lo mismo
- **WHEN** the user sends a POST request to `/auth/login` with a non-registered email
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Invalid credentials"}`

#### Scenario: Email incorrecto retorna mismo error
- **WHEN** the user sends a POST request to `/auth/login` with an incorrect password for a registered email
- **THEN** the system returns 401 Unauthorized
- **AND** the response body contains `{"detail": "Invalid credentials"}`

### Requirement: Cumplimiento RN-08 (límite de 5 intentos fallidos en 60s)
The system SHALL block login attempts from an email and IP pair after 5 failed attempts within 60 seconds.

#### Scenario: 5 intentos fallidos activan bloqueo 429
- **WHEN** 5 failed login attempts occur from the same email and IP within 60 seconds
- **THEN** subsequent login attempts return 429 Too Many Requests
- **AND** include a `Retry-After` header without checking the password

#### Scenario: Login exitoso reinicia el conteo de fallos
- **WHEN** a successful login occurs
- **THEN** the failure count for that email and IP is reset

### Requirement: JWT con claims obligatorios
The system SHALL generate a JWT token with the claims `sub`, `iat`, `exp`, and `roles` upon successful authentication.

#### Scenario: Token incluye claim sub con el user ID
- **WHEN** a user authenticates successfully
- **THEN** the generated JWT includes the claim `sub` matching the user's ID

#### Scenario: Token incluye claim iat (issued at timestamp)
- **WHEN** a JWT is generated
- **THEN** the claim `iat` is included as a Unix timestamp without truncation to seconds (RN-07)

#### Scenario: Token incluye claim exp (expiration time)
- **WHEN** a JWT is generated with the configured ACCESS_TOKEN_EXPIRE_MINUTES
- **THEN** the claim `exp` is set to the expiration time calculated from iat + expire minutes

#### Scenario: Token incluye claim roles con roles vigentes de la base
- **WHEN** a user authenticates
- **THEN** the claim `roles` contains the list of roles vigentes para ese usuario consultados en la base (RN-04)

### Requirement: RN-07 - Comparación de iat sin truncar
The system SHALL compare `iat` against `password_cambiada_en` without truncating to seconds.

#### Scenario: Validación de iat contra password_cambiada_en sin truncar
- **WHEN** a user changes their password and attempts to use a pre-existing token
- **THEN** the system validates iat by comparing the full timestamp against password_cambiada_en
- **AND** a token with iat earlier than password_cambiada_en is invalidated

### Requirement: Logout con invalidación de cookie
The system SHALL invalidate the `access_token` cookie upon logout.

#### Scenario: Logout exitoso borra la cookie access_token
- **WHEN** the user sends a POST request to `/auth/logout`
- **THEN** the system returns 204 No Content
- **AND** the `access_token` cookie is cleared (Max-Age=0)

### Requirement: Obtención de perfil del usuario autenticado
The system SHALL return the authenticated user's profile when accessing `GET /auth/yo`.

#### Scenario: Perfil devuelto con datos básicos del usuario
- **WHEN** the user sends a GET request to `/auth/yo` with a valid `access_token` cookie
- **THEN** the system returns 200 OK
- **AND** the response body contains user information: `id`, `email`, `nombre`, `rol`, `iat`
- **AND** `password_hash` is NOT included

#### Scenario: 401 si no hay sesión válida
- **WHEN** the user sends a GET request to `/auth/yo` without a valid `access_token` cookie
- **THEN** the system returns 401 Unauthorized

### Requirement: Registro atómico de usuario con rol y ficha (RN-02 / US-002)
The system SHALL perform atomic registration creating a user, a CLIENTE role assignment, and a client record.

#### Scenario: Registro exitoso
- **WHEN** the user sends a POST request to `/auth/register` with valid client data
- **THEN** the system returns 201 Created
- **AND** creates atomic user + role CLIENTE + client record
- **AND** sets the `access_token` cookie

#### Scenario: Fallo si el email o documento ya está registrado
- **WHEN** the user sends a POST request to `/auth/register` with duplicated email or document
- **THEN** the system returns 409 Conflict
