# Tasks: C-05 Autorización y Control de Acceso (RBAC)

## 1. Dependencias de Autorización y Control de Sesión

- [x] 1.1 Implementar `get_current_user` con validación de sesión activa (401 si no hay token o es inválido) y verificación de `password_cambiada_en` vs `iat` (RN-07)
- [x] 1.2 Implementar factoría `requiere_rol(*roles)` en `app/core/dependencies.py` que consulte roles vigentes en base de datos (`revocada_en IS NULL`) en cada petición (RN-04)
- [x] 1.3 Implementar verificación de cambio obligatorio de contraseña (RN-06): denegar acceso con 403 Forbidden a rutas fuera de `/auth` y `/health` si `debe_cambiar_password = True`
- [x] 1.4 Crear tests unitarios en `test/test_dependencies_auth.py` para `requiere_rol`, 401 sin sesión, 403 con rol incorrecto y RN-06

## 2. Gestión de Roles y Autoprotección ADMIN (RN-05)

- [x] 2.1 Crear schemas para asignación y revocación de roles (`AsignarRol`, `RevocarRol`) con `extra="forbid"`
- [x] 2.2 Implementar en `service.py` la lógica de asignación de roles con validación de roles válidos y unicidad de asignación vigente (RN-03)
- [x] 2.3 Implementar en `service.py` la lógica de revocación de roles con autoprotección ADMIN (RN-05): impedir auto-revocación de ADMIN (409) y evitar dejar al sistema sin administradores (409)
- [x] 2.4 Implementar función `registrar_evento_seguridad` para auditar asignaciones y revocaciones en `evento_seguridad`
- [x] 2.5 Crear endpoints en el router de usuarios/auth (`POST /auth/roles/asignar` y `POST /auth/roles/revocar`) protegidos con `requiere_rol("ADMIN")`
- [x] 2.6 Crear tests unitarios y de integración para la autoprotección ADMIN y asignación/revocación de roles

## 3. Protección de Routers Existentes (Matriz RBAC)

- [x] 3.1 Proteger endpoints de clientes en `app/modules/clientes/router.py`: CRUD restringido a `RECEPCION` y `ADMIN`
- [x] 3.2 Proteger endpoints de vehículos en `app/modules/clientes/router.py` (`router_vehiculos`): `RECEPCION` y `ADMIN`
- [x] 3.3 Proteger endpoints de repuestos en `app/modules/repuestos/router.py`: lectura autenticada; creación y actualización restringidas a `ADMIN`
- [x] 3.4 Proteger endpoints de órdenes en `app/modules/ordenes/router.py`: creación `RECEPCION`/`ADMIN`, cancelación `RECEPCION`/`ADMIN`/`CLIENTE`, iniciar/terminar `MECANICO`/`ADMIN`
- [x] 3.5 Crear endpoint de auditoría `GET /auth/eventos-seguridad` restringido a `ADMIN`

## 4. Verificación Integral

- [x] 4.1 Ejecutar suite completa de tests (`pytest`) y verificar que todos los casos de autorización pasen en verde
- [x] 4.2 Validar el change con `openspec validate c-05-autorizacion`
