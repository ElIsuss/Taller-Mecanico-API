# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|-------|-------------|-----------------|
| Recepción (RECEPCION) | Personal de recepción del taller | Da de alta clientes y vehículos, abre órdenes de trabajo, cancela órdenes |
| Mecánico (MECANICO) | Personal de reparación | Inicia y termina órdenes de trabajo asignadas; descuenta stock al terminar |
| Administrador (ADMIN) | Responsable del taller | Gestiona catálogo de repuestos, repone stock, asigna/revoca roles, consulta eventos de seguridad |
| Cliente (CLIENTE) | Dueño de vehículo que usa el taller | Se registra solo; consulta sus vehículos y el estado de sus órdenes |

## RBAC — Matriz de permisos

| Rol | Clientes | Vehículos | Repuestos | Órdenes de trabajo | Roles / personal | Eventos de seguridad |
|-----|----------|-----------|-----------|--------------------|------------------|----------------------|
| RECEPCION | CRUD | CRUD | Lectura | Crear, cancelar | — | — |
| MECANICO | Lectura | Lectura | Lectura | Iniciar, terminar (asignadas) | — | — |
| ADMIN | CRUD | CRUD | CRUD | Todas + cancelar | Asignar / revocar | Lectura |
| CLIENTE | Propia ficha | Sus vehículos | — | Sus órdenes | — | — |

Los permisos se deciden con los roles vigentes en la base en cada petición (RN-04). Los roles que trae el token son informativos. Un administrador no puede revocarse su propio rol ADMIN (responde 409), y el sistema nunca queda sin administradores vigentes (RN-05).

## Rutas públicas

- `POST /auth/registro` — auto-registro atómico (usuario + rol CLIENTE + ficha cliente)
- `POST /auth/login` — responde igual exista o no el correo (RN-09)
- `GET /salud` — rutas de salud

Mientras un usuario tenga el cambio de contraseña pendiente, solo puede usar rutas de `/auth` y salud (RN-06). Todo lo demás requiere autenticación; un cliente solo ve sus propios vehículos y las órdenes de esos vehículos (RN-17).
