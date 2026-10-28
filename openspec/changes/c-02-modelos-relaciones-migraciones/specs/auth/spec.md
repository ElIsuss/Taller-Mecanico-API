# Spec Delta

## Purpose

Gestiona la identidad de usuarios, roles y asignaciones de rol con vigencia para controlar el acceso al sistema.

## ADDED Requirements

### Requirement: Usuario con email único entre vigentes
El sistema SHALL garantizar que el email de un usuario sea único solo entre los usuarios no dados de baja.

#### Scenario: Email único entre usuarios vigentes
- **WHEN** se intenta crear un usuario con un email que ya pertenece a un usuario vigente
- **THEN** el sistema rechaza la operación con error de unicidad

#### Scenario: Email reutilizable tras baja lógica
- **WHEN** un usuario fue dado de baja (fecha_baja no nula)
- **THEN** otro usuario puede registrarse con el mismo email

### Requirement: Rol del catálogo de roles
El sistema SHALL permitir solo roles del catálogo predefinido: RECEPCION, MECANICO, ADMIN, CLIENTE.

#### Scenario: Rol válido del catálogo
- **WHEN** se crea una asignación de rol con nombre RECEPCION, MECANICO, ADMIN o CLIENTE
- **THEN** el sistema acepta la asignación

#### Scenario: Rol inválido rechazado
- **WHEN** se intenta asignar un rol que no existe en el catálogo
- **THEN** el sistema rechaza la operación

### Requirement: Una asignación abierta por rol por usuario
El sistema SHALL permitir a lo sumo una asignación de rol vigente (sin fecha_hasta) por usuario y rol.

#### Scenario: Asignación abierta duplicada rechazada
- **WHEN** un usuario ya tiene una asignación vigente para un rol
- **THEN** el sistema rechaza crear una segunda asignación abierta para ese mismo rol

#### Scenario: Asignación cerrada permite nueva apertura
- **WHEN** una asignación previa tiene fecha_hasta establecida
- **THEN** el sistema permite crear una nueva asignación abierta para ese mismo rol

### Requirement: password_cambiada_en con precisión de subsegundo
El sistema SHALL almacenar password_cambiada_en con precisión de zona horaria y subsegundos para comparar iat del token sin truncar.

#### Scenario: Comparación de iat sin truncar a segundos
- **WHEN** se compara iat del token contra password_cambiada_en
- **THEN** la comparación usa la marca de tiempo completa sin truncar a segundos
