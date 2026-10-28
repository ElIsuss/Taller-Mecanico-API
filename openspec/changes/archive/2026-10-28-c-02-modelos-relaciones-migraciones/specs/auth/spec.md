# Spec Delta

## Purpose

Gestiona la identidad de usuarios, las asignaciones de rol con vigencia, los intentos de acceso y la bitácora de eventos de seguridad.

## ADDED Requirements

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
