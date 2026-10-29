## Purpose
Especificación del JSON Web Token y claims de autorización.

## ADDED Requirements

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
- **THEN** the claim `roles` contains the list of roles vigentes (activos en la base de datos) para ese usuario, consultados en cada petición (RN-04)

### Requirement: RN-07 - Comparación de iat sin truncar
The system SHALL compare `iat` against `password_cambiada_en` without truncating to seconds (RN-07).

#### Scenario: Validación de iat contra password_cambiada_en sin truncar
- **WHEN** a user changes their password and attempts to use a pre-existing token
- **THEN** the system validates iat by comparing the full timestamp against password_cambiada_en
- **AND** a token with iat within the same second as password_cambio is invalidated
- **AND** the system does NOT truncate iat to seconds before comparison