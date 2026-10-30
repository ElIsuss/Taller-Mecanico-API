# Design: C-05 Autorización y Control de Acceso (RBAC)

## Context
Ver `proposal.md` y `specs/autorizacion/spec.md`.
El sistema cuenta con autenticación JWT mediante cookie `access_token` (C-04). Las tablas `asignacion_rol` y `evento_seguridad` ya forman parte del esquema de base de datos desde C-02. Ahora se deben conectar los mecanismos de autorización y protección de rutas.

## Goals / Non-Goals

**Goals:**
- Implementar la dependencia factoría `requiere_rol(*roles)` compatible con FastAPI.
- Consultar roles activos en base de datos en cada petición (**RN-04**).
- Restringir navegación para usuarios con cambio de clave pendiente (**RN-06**).
- Implementar autoprotección de administradores (**RN-05**).
- Crear endpoints de administración de roles con auditoría en `evento_seguridad`.
- Proteger las rutas de negocio según la matriz RBAC de `03_actores_y_roles.md`.

**Non-Goals:**
- Permisos granulares a nivel de campo (Attribute-Based Access Control). Se utiliza RBAC clásico según la matriz de 4 roles: ADMIN, RECEPCION, MECANICO, CLIENTE.
- Implementación del Unit of Work transaccional para repuestos/stock (eso pertenece a C-06).

## Decisions

### 1. Dependencia factoría `requiere_rol(*roles_permitidos)`
- **Diseño**: Una función que retorna una dependencia async inyectable en routers o endpoints específicos:
  ```python
  def requiere_rol(*roles_permitidos: str):
      async def role_checker(
          request: Request,
          usuario: Usuario = Depends(get_current_user),
          session: AsyncSession = Depends(get_session),
      ) -> Usuario: ...
      return role_checker
  ```
- **Lógica**:
  1. Obtiene el usuario autenticado (retorna 401 si no hay sesión válida).
  2. Verifica RN-06: si `usuario.debe_cambiar_password` es `True` y la ruta solicitada no pertenece a `/auth` ni `/health`, levanta 403 Forbidden.
  3. Consulta `asignacion_rol` para `usuario.id` donde `revocada_en IS NULL` y (`vence_en IS NULL` o `vence_en > now()`).
  4. Si ninguno de los roles vigentes coincide con `roles_permitidos`, levanta 403 Forbidden (`detail="Permisos insuficientes"`).
  5. Retorna la instancia de `usuario` para ser consumida en el handler.

### 2. Autoprotección ADMIN (RN-05)
- En el endpoint y servicio de revocación de roles (`POST /auth/roles/revocar` o `DELETE /usuarios/{id}/roles/{rol}`):
  - Si el usuario objetivo es el mismo que el usuario autenticado y el rol es `ADMIN`: responde 409 Conflict (`"No puedes revocar tu propio rol ADMIN"`).
  - Antes de revocar, se consulta el total de administradores vigentes en la base. Si es igual o menor a 1: responde 409 Conflict (`"El sistema no puede quedar sin administradores"`).

### 3. Registro en `evento_seguridad`
- Función auxiliar `registrar_evento_seguridad(session, actor, accion)` que añade un registro a la tabla `evento_seguridad`.
- Se invoca en asignaciones y revocaciones de roles, registrando el ID del administrador ejecutor o `"SISTEMA"`.

### 4. Protección de Routers existentes
- **Clientes**: CRUD restringido a RECEPCION y ADMIN; CLIENTE solo puede ver su propia ficha.
- **Vehículos**: RECEPCION y ADMIN CRUD; CLIENTE solo consulta sus propios vehículos.
- **Repuestos**: Lectura para todos los roles autenticados; creación, modificación de precio/catálogo restringido a ADMIN.
- **Órdenes**: RECEPCION, ADMIN y CLIENTE (sus órdenes); MECANICO iniciar y terminar órdenes asignadas.

## Risks / Trade-offs

- [Risk: Consulta a base de datos en cada petición para RN-04] → Mitigation: La tabla `asignacion_rol` cuenta con índice único parcial `ix_asignacion_rol_usuario_rol_uc (usuario_id, rol) WHERE revocada_en IS NULL`, haciendo la consulta por `usuario_id` extremadamente rápida (< 1ms).
- [Risk: Interferencia con rutas públicas] → Mitigation: Las rutas públicas (`/auth/login`, `/auth/register`, `/health/*`) no utilizan `requiere_rol`.
