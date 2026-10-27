# Funcionalidades

Organizadas por **épica** y luego por **historia de usuario** (formato US-NNN).

## Épica 1: Seguridad y autenticación

### US-001 — Auto-registro de cliente
**Como** cliente nuevo  
**Quiero** registrarme en la web  
**Para** crear mi usuario, mi rol CLIENTE y mi ficha de cliente de forma atómica

**Criterios de aceptación**:
- [ ] CA-1: Se crean usuario + rol CLIENTE + ficha cliente en una sola transacción
- [ ] CA-2: Si el documento ya pertenece a un cliente del taller, responde 409 y no se apropia de la ficha
- [ ] CA-3: El usuario queda con rol CLIENTE asignado y vigente

**Reglas relacionadas**: RN-02, RN-01

### US-002 — Login con JWT en cookie HttpOnly
**Como** usuario registrado  
**Quiero** iniciar sesión y recibir un token JWT en cookie HttpOnly  
**Para** autenticarme en las peticiones siguientes

**Criterios de aceptación**:
- [ ] CA-1: El token viaja solo en cookie `access_token` con `HttpOnly`, `SameSite=Lax`
- [ ] CA-2: El login responde igual exista o no el correo (RN-09)
- [ ] CA-3: Después de 5 intentos fallidos (mismo correo, misma IP, 60s) responde 429 (RN-08)

**Reglas relacionadas**: RN-08, RN-09

### US-003 — Cambio de contraseña e invalidación de sesiones
**Como** usuario autenticado  
**Quiero** cambiar mi contraseña  
**Para** que las sesiones previas dejen de ser válidas

**Criterios de aceptación**:
- [ ] CA-1: Mientras el cambio esté pendiente, solo rutas `/auth` y salud (RN-06)
- [ ] CA-2: Las sesiones previas (incluso del mismo segundo) dejan de valer; la del cambio sí (RN-07)

**Reglas relacionadas**: RN-06, RN-07

## Épica 2: Gestión de clientes y vehículos (Recepción)

### US-004 — Alta de cliente
**Como** recepcionista  
**Quiero** dar de alta un cliente  
**Para** registrarlo en el sistema

**Criterios de aceptación**:
- [ ] CA-1: Documento único entre vigentes (RN-01)
- [ ] CA-2: Solo recepcionista o administrador pueden crear clientes

**Reglas relacionadas**: RN-01

### US-005 — Alta de vehículo
**Como** recepcionista  
**Quiero** dar de alta un vehículo vinculado a un cliente  
**Para** asociarlo a su dueño

**Criterios de aceptación**:
- [ ] CA-1: Patente única entre vigentes (RN-01)
- [ ] CA-2: Debe existir un cliente vinculado

**Reglas relacionadas**: RN-01

### US-006 — Borrado lógico de vehículo o repuesto
**Como** administrador o recepcionista  
**Quiero** dar de baja un vehículo o un repuesto  
**Para** que deje de aparecer sin perder su historial

**Criterios de aceptación**:
- [ ] CA-1: Un vehículo con órdenes abiertas no se da de baja (RN-16)
- [ ] CA-2: Dado de baja, no se usa en órdenes nuevas; los datos se conservan

**Reglas relacionadas**: RN-16

## Épica 3: Catálogo de repuestos y stock (Administrador)

### US-007 — CRUD de repuestos
**Como** administrador  
**Quiero** mantener el catálogo de repuestos  
**Para** tener los repuestos disponibles para las órdenes

**Criterios de aceptación**:
- [ ] CA-1: Código único entre vigentes (RN-01)
- [ ] CA-2: Cambio de precio deja línea en `historial_precio_repuesto` (RN-20)
- [ ] CA-3: El stock solo cambia por movimientos, no por PATCH (RN-14)

**Reglas relacionadas**: RN-01, RN-14, RN-20

### US-008 — Reposición de stock
**Como** administrador  
**Quiero** reponer el stock de un repuesto  
**Para** mantener disponibilidad

**Criterios de aceptación**:
- [ ] CA-1: Queda un `movimiento_stock` de tipo reposición (RN-14)

**Reglas relacionadas**: RN-14

## Épica 4: Órdenes de trabajo (Recepción / Mecánico / Administrador)

### US-009 — Abrir orden de trabajo
**Como** recepcionista  
**Quiero** abrir una orden de trabajo con falla e ítems de repuestos  
**Para** registrar el ingreso de un vehículo

**Criterios de aceptación**:
- [ ] CA-1: Nace PENDIENTE con al menos un ítem (RN-10)
- [ ] CA-2: Sin repuestos repetidos en la orden (RN-10)
- [ ] CA-3: Precio de cada ítem se copia del repuesto; el total lo calcula el servidor (RN-10)

**Reglas relacionadas**: RN-10

### US-010 — Iniciar orden de trabajo
**Como** mecánico  
**Quiero** iniciar una orden de trabajo asignada a mí  
**Para** comenzar la reparación

**Criterios de aceptación**:
- [ ] CA-1: Transición PENDIENTE → EN_REPARACION; el mecánico queda asignado (RN-11)

**Reglas relacionadas**: RN-11

### US-011 — Terminar orden de trabajo
**Como** mecánico asignado o administrador  
**Quiero** terminar una orden de trabajo  
**Para** darla por finalizada y descontar el stock

**Criterios de aceptación**:
- [ ] CA-1: Transición EN_REPARACION → TERMINADA (RN-11)
- [ ] CA-2: Descuenta stock de cada ítem, deja un movimiento y una línea de historial en transacción única (RN-13)
- [ ] CA-3: Si un repuesto no alcanza, no queda ninguna escritura (RN-13)

**Reglas relacionadas**: RN-11, RN-13

### US-012 — Cancelar orden de trabajo
**Como** recepcionista, administrador o dueño del vehículo  
**Quiero** cancelar una orden de trabajo  
**Para** anularla cuando corresponde

**Criterios de aceptación**:
- [ ] CA-1: Transición PENDIENTE → CANCELADA (RN-11)
- [ ] CA-2: El permiso se evalúa antes que el estado (RN-12)
- [ ] CA-3: Una orden terminada no se puede cancelar (409) (RN-12)

**Reglas relacionadas**: RN-11, RN-12

## Épica 5: Administración de personal y roles (Administrador)

### US-013 — Asignar y revocar roles
**Como** administrador  
**Quiero** asignar o revocar roles del personal  
**Para** gestionar quién tiene qué permisos

**Criterios de aceptación**:
- [ ] CA-1: Un usuario tiene a lo sumo una asignación abierta por rol (RN-03)
- [ ] CA-2: Un administrador no puede revocarse su propio ADMIN (RN-05)
- [ ] CA-3: El sistema nunca queda sin administradores vigentes (RN-05)

**Reglas relacionadas**: RN-03, RN-05

## Épica 6: Consulta propia (Cliente)

### US-014 — Consultar mis vehículos y órdenes
**Como** cliente autenticado  
**Quiero** ver mis vehículos y el estado de mis órdenes  
**Para** hacer un seguimiento de mis reparaciones

**Criterios de aceptación**:
- [ ] CA-1: Solo ve sus propios vehículos y las órdenes de esos vehículos (RN-17)
- [ ] CA-2: No ve datos de otros clientes

**Reglas relacionadas**: RN-17

## Épica 7: Operaciones transversales

### US-015 — Paginación de listados
**Como** consumidor de la API  
**Quiero** que los listados estén paginados  
**Para** navegar grandes volúmenes de datos

**Criterios de aceptación**:
- [ ] CA-1: Envoltorio `{items, total, page, size, pages}`

**Reglas relacionadas**: —

### US-016 — Migraciones y seed inicial
**Como** operador del sistema  
**Quiero** crear el esquema con Alembic y cargar datos iniciales  
**Para** poner el proyecto en marcha

**Criterios de aceptación**:
- [ ] CA-1: Esquema creado exclusivamente con `alembic upgrade head` (sin `create_all`)
- [ ] CA-2: `seed.py` carga datos iniciales obligatorios (roles, estados de orden, administrador inicial)

**Reglas relacionadas**: —
