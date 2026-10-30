# Proposal: C-05 Autorización y Control de Acceso (RBAC)

## Why
El sistema ya cuenta con autenticación basada en JWT en cookies (C-04), pero actualmente no restringe el acceso a los endpoints según los roles del usuario ni valida los permisos en base de datos. Se requiere implementar la capa de autorización RBAC conforme a la matriz de permisos, garantizando que los permisos se verifiquen contra roles vigentes en la base en cada petición (RN-04), impidiendo la auto-revocación del rol ADMIN (RN-05), restringiendo a usuarios con cambio de contraseña pendiente (RN-06) y registrando eventos de seguridad en auditoría.

## What Changes
- Implementación de la dependencia `requiere_rol(*roles_permitidos)` que consulta los roles vigentes en la base de datos (`revocada_en IS NULL` y `vence_en > now()` o null) en cada petición (RN-04).
- Si no hay sesión válida o token expirado/inválido: responder 401 Unauthorized.
- Si el usuario está autenticado pero no tiene ninguno de los roles requeridos: responder 403 Forbidden con `{"detail": "Permisos insuficientes"}`.
- Validación de RN-06: usuarios con `debe_cambiar_password = True` solo pueden consumir endpoints bajo `/auth` o `/health`; cualquier otra petición responde 403 Forbidden con detalle de cambio de contraseña requerido.
- Protección ADMIN (RN-05): endpoint para gestión de roles que prohíbe que un administrador se revoque su propio rol ADMIN (409 Conflict) y que impida dejar al sistema sin administradores vigentes.
- Registro de auditoría en la tabla `evento_seguridad` para acciones sensibles (asignación y revocación de roles, intentos anómalos) con actor correspondiente o `SISTEMA`.
- Protección de los routers existentes (`clientes`, `vehiculos`, `repuestos`, `ordenes`) aplicando la matriz de permisos RBAC de `03_actores_y_roles.md`.

## Capabilities

### New Capabilities
- `autorizacion`: Control de acceso basado en roles (RBAC) con consulta en base de datos en cada petición, restricción RN-06 y protección ADMIN RN-05.

### Modified Capabilities
<!-- Ninguna especificación existente cambia sus requisitos -->

## Impact
- Dependencias en `app/core/dependencies.py` (`requiere_rol`, middleware/verificación RN-06).
- Módulo de roles y usuarios (`app/modules/usuarios/`): endpoints para asignación y revocación de roles con validación de autoprotección ADMIN (RN-05) y registro en `evento_seguridad`.
- Routers de negocio (`clientes`, `ordenes`, `repuestos`): aplicación de dependencias `Depends(requiere_rol(...))` según la matriz RBAC.
