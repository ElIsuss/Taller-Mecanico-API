# autorizacion Specification

## Purpose
Define el control de acceso basado en roles (RBAC), la verificación de permisos en base de datos en cada petición, la restricción de rutas para usuarios con cambio de contraseña pendiente y la protección de cuentas administrativas.

## Requirements

### Requirement: Verificación de sesión activa
El sistema SHALL requerir una sesión válida mediante la cookie `access_token` para acceder a recursos protegidos, respondiendo 401 si la sesión falta o es inválida.

#### Scenario: Acceso a ruta protegida sin sesión
- **WHEN** un cliente envía una petición a un endpoint protegido sin la cookie `access_token`
- **THEN** el sistema responde con código HTTP 401 Unauthorized
- **AND** el cuerpo de la respuesta contiene `{"detail": "Not authenticated"}`

#### Scenario: Acceso a ruta protegida con token expirado
- **WHEN** un cliente envía una petición con un token cuya expiración (`exp`) es anterior al momento actual
- **THEN** el sistema responde con código HTTP 401 Unauthorized

### Requirement: Consulta de roles vigentes en base de datos (RN-04)
El sistema SHALL consultar los roles vigentes (`revocada_en IS NULL` y `vence_en IS NULL OR vence_en > now()`) directamente en la base de datos en cada petición, considerando los roles del JWT únicamente como informativos.

#### Scenario: Permiso concedido por rol vigente en base
- **WHEN** un usuario posee una asignación de rol activa en la base de datos que coincide con los roles requeridos
- **THEN** el sistema permite la ejecución del endpoint solicitado

#### Scenario: Permiso denegado si el rol fue revocado en base aunque figure en token
- **WHEN** un token JWT contiene un rol que fue revocado en la base de datos (`revocada_en IS NOT NULL`)
- **THEN** el sistema deniega el acceso con 403 Forbidden

### Requirement: Restricción de acceso por rol con 403 Forbidden
El sistema SHALL responder 403 Forbidden cuando un usuario autenticado no posee ninguno de los roles necesarios para operar el endpoint.

#### Scenario: Usuario sin rol requerido
- **WHEN** un usuario autenticado con rol CLIENTE intenta acceder a un endpoint restringido a RECEPCION o ADMIN
- **THEN** el sistema responde 403 Forbidden
- **AND** el cuerpo contiene el mensaje de permisos insuficientes

### Requirement: Restricción de cambio obligatorio de contraseña (RN-06)
El sistema SHALL restringir el acceso a usuarios que tengan `debe_cambiar_password = True` únicamente a las rutas bajo `/auth` y rutas de salud.

#### Scenario: Usuario con cambio pendiente accede a ruta de negocio
- **WHEN** un usuario con `debe_cambiar_password = True` intenta acceder a una ruta de negocio (clientes, vehículos, repuestos, órdenes)
- **THEN** el sistema deniega el acceso con 403 Forbidden
- **AND** el cuerpo informa que debe cambiar su contraseña antes de continuar

#### Scenario: Usuario con cambio pendiente accede a ruta de auth o salud
- **WHEN** un usuario con `debe_cambiar_password = True` accede a `/auth/yo`, `/auth/logout`, `/auth/cambiar-password` o `/health/*`
- **THEN** el sistema permite la petición normalmente

### Requirement: Autoprotección de administradores (RN-05)
El sistema SHALL impedir que un administrador se revoque su propio rol ADMIN y garantizar que el sistema nunca quede sin administradores vigentes.

#### Scenario: Administrador intenta revocar su propio rol ADMIN
- **WHEN** un administrador intenta revocar su propia asignación de rol ADMIN
- **THEN** el sistema rechaza la operación con código 409 Conflict
- **AND** la asignación permanece activa

#### Scenario: Intento de revocar al último administrador del sistema
- **WHEN** se intenta revocar el rol ADMIN al único usuario con rol ADMIN activo en el sistema
- **THEN** el sistema rechaza la operación con código 409 Conflict

### Requirement: Auditoría en bitácora de eventos de seguridad
El sistema SHALL registrar en la tabla `evento_seguridad` (`cuando`, `actor`, `accion`) cada modificación de roles o eventos críticos del sistema, usando el identificador del usuario o `SISTEMA`.

#### Scenario: Asignación o revocación de rol registrada
- **WHEN** un administrador otorga o revoca un rol a un usuario
- **THEN** se crea una fila en `evento_seguridad` con el actor que ejecutó la acción y la descripción correspondiente
