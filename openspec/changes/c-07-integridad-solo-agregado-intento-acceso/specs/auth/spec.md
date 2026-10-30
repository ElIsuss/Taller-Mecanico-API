# Spec Delta: auth

## MODIFIED Requirements

### Requirement: Registro de intentos de acceso
El sistema SHALL registrar cada intento de login en `intento_acceso` (`cuando`, `email`, `ip`, `exito`) con un índice `(email, ip, cuando)` en una sesión y transacción independientes que ejecuten commit inmediato para asegurar que el registro persista aun si la transacción principal falla o sufre un rollback.

#### Scenario: Intento fallido registrado
- **WHEN** un login falla
- **THEN** se inserta y confirma de forma inmediata una fila en `intento_acceso` con `exito = false`

#### Scenario: Persistencia ante rollback de la sesión principal
- **WHEN** ocurre una excepción o rollback en el flujo principal de autenticación
- **THEN** la fila en `intento_acceso` persiste en la base de datos debido a su transacción independiente
