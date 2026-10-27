# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **Taller Mecanico — API**.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar el change a implementar (siguiente en orden sugerido o desbloqueado por un GATE).
2. Leer los punteros "Leer antes" de la knowledge-base indicados en cada change.
3. Ejecutar `/opsx:propose C-NN-nombre` para generar los artifacts del change.
4. Implementar el scope definido, respetando dependencias, gobernanza y las reglas de la KB.
5. Ejecutar `/opsx:archive C-NN-nombre` y marcar el checkbox `[x]` del change.

---

## Árbol de dependencias

```
C-01 proyecto-configuracion-ciclo-vida
└── C-02 modelos-relaciones-migraciones
    ├── C-03 contratos-y-crud ──┐
    │                             └── C-08 lecturas-sin-n1-y-asincronia (también depende de C-06)
    ├── C-04 autenticacion
    │   └── C-05 autorizacion
    └── C-06 repositorios-y-unit-of-work ──┤
        ├── C-07 integridad-solo-agregado-intento-acceso (también depende de C-02)
        └── C-08 lecturas-sin-n1-y-asincronia (también depende de C-03)
```

Notas de dependencia cruzada:
- `C-08` depende además de `C-03` (endpoints) y de `C-06` (repositorios con carga anticipada).
- `C-07` depende además de `C-02` (modelos de tablas solo-agregado), ya satisfecho por la cadena principal.

---

## Paralelismo por fase

```
GATE 0: (inicio)
  → C-01 proyecto-configuracion-ciclo-vida             [Agente A — Backend Core]

GATE 1: C-01 ✓
  → C-02 modelos-relaciones-migraciones                [Agente A — Backend Core]

GATE 2: C-02 ✓     ← PRIMER FORK (modelos listos)
  → C-03 contratos-y-crud                              [Agente A — Backend Core]
  → C-04 autenticacion                                 [Agente B — Backend Auth/Seguridad]

GATE 3: C-03 ✓ y C-04 ✓     ← FORK
  → C-05 autorizacion                                  [Agente B — Backend Auth/Seguridad]
  → C-06 repositorios-y-unit-of-work                   [Agente C — Backend Datos/Integridad]

GATE 4: C-06 ✓ (y C-03 ya listo)   ← FORK
  → C-07 integridad-solo-agregado-intento-acceso       [Agente C — Backend Datos/Integridad]
  → C-08 lecturas-sin-n1-y-asincronia                  [Agente A — Backend Core]
```

---

## Camino crítico (5 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-06 → C-08 *
                                           ↘ C-07 *
```

La cadena lineal más corta desde `C-01` hasta producción requiere los 5 changes arriba. `C-07` (integridad/solo-agregado) y `C-08` (lecturas optimizadas) son ambos cambios finales válidos del camino crítico (marcados con `*`); `C-05` (autorización) se ejecuta en paralelo por la rama de seguridad y no alarga el camino crítico mínimo.

---

## Plan óptimo con 3 agentes

| Paso | Agente A (Backend Core) | Agente B (Backend Auth/Seguridad) | Agente C (Backend Datos/Integridad) |
|------|-------------------------|-----------------------------------|-------------------------------------|
| 1 | C-01 proyecto-configuracion-ciclo-vida | — | — |
| 2 | C-02 modelos-relaciones-migraciones | — | — |
| 3 | C-03 contratos-y-crud | C-04 autenticacion | — |
| 4 | — | C-05 autorizacion | C-06 repositorios-y-unit-of-work |
| 5 | C-08 lecturas-sin-n1-y-asincronia | — | C-07 integridad-solo-agregado-intento-acceso |

Carga de puntos por agente: **A = 40 pts**, **B = 30 pts**, **C = 30 pts** (total 100 pts).

---

## FASE 1 — Fundación e infraestructura

> Nota: `C-01` y `C-02` son estrictamente secuenciales; no hay paralelismo dentro de la fase.

### [C-01] `proyecto-configuracion-ciclo-vida`
- **Estado**: `[ ]` pendiente
- **Puntos**: 8 | **Orden sugerido**: 1
- **Scope**:
  - Estructura de carpetas obligatoria: `app/core/` y `app/modules/<modulo>/` (auth, clientes, vehiculos, repuestos, ordenes, roles)
  - Settings con `pydantic-settings` y `@computed_field`: dirección de base asíncrona y tamaño de pool de conexiones
  - Motor SQLAlchemy async y fábrica de sesiones (`async_sessionmaker`) creados en `lifespan` y guardados en `app.state`
  - `get_session` con `expire_on_commit=False`
  - Hash fictício del login (placeholder para cumplir RN-09: responde igual exista o no el correo)
  - `dispose()` del motor al apagar (shutdown de `lifespan`)
  - Endpoints de salud: `GET /health/live` y `GET /health/ready`
- **Dependencias**: ninguna
- **Governance**: MEDIO (infraestructura crítica: motor de BD, ciclo de vida, salud)
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` (§Seguridad, §Variables de entorno, §Estructura de directorios)
  - `knowledge-base/02_descripcion_general.md` (§Stack tecnológico, §Arquitectura general)
  - `knowledge-base/04_modelo_de_datos.md` (§Dominios)

### [C-02] `modelos-relaciones-migraciones`
- **Estado**: `[ ]` pendiente
- **Puntos**: 14 | **Orden sugerido**: 2
- **Scope**:
  - Modelos SQLModel: `usuario`, `rol`, `rol_asignacion`, `cliente`, `vehiculo`, `repuesto`, `estado_orden`, `orden_trabajo`, `orden_item`
  - Tablas de solo-agregado: `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto`
  - Índices únicos parciales (`postgresql_where`) sobre los campos de unicidad vigentes: email de usuario, documento de cliente, patente de vehículo y código de repuesto (RN-01)
  - FK `orden_trabajo.estado_orden_id` al catálogo `estado_orden` (sin CHECK constraint, RN-19)
  - Navegación en ambos extremos de las relaciones; `Usuario.cliente` devuelve objeto (1:1), no lista
  - Esquema creado exclusivamente con Alembic (sin `create_all`)
  - 2 migraciones: una autogenerate y una escrita a mano (disparador solo-agregado para RN-15)
  - `seed.py` carga los 4 estados del catálogo `estado_orden`, los 4 roles y el administrador inicial
- **Dependencias**: `C-01`
- **Governance**: CRITICO (modelos core que todo lo demás referencia)
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (§Entidades, §Seed data)
  - `knowledge-base/05_reglas_de_negocio.md` (§RN-01, §RN-15, §RN-19)
  - `knowledge-base/08_arquitectura_propuesta.md` (tabla de patrones aplicados)

---

## FASE 2 — Endpoints, autenticación y autorización

> Nota: `C-03` y `C-04` pueden ejecutarse en paralelo tras `C-02` (GATE 2). `C-05` requiere `C-04`.

### [C-03] `contratos-y-crud`
- **Estado**: `[ ]` pendiente
- **Puntos**: 10 | **Orden sugerido**: 3
- **Scope**:
  - Schemas de contrato separados de los modelos (Pydantic) con `extra="forbid"`
  - Respuestas sin exponer `password_hash`
  - PATCH parcial con `exclude_unset`
  - Códigos de respuesta: 201, 204, 404, 409, 422
  - Paginación con envoltorio `{items, total, page, size, pages}` (page desde 1, size 1-100 default 20; página más allá del total → 422)
  - Endpoints CRUD: clientes, vehículos, repuestos, órdenes de trabajo y catálogo `estado_orden` (solo lectura)
  - Búsqueda de repuestos por descripción con parámetros ligados (bound parameters)
- **Dependencias**: `C-02`
- **Governance**: BAJO (CRUD simple, contratos de entrada/salida)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` (US-004 a US-012)
  - `knowledge-base/07_flujos_principales.md` (Flujo 3, 4, 5, 6)
  - `knowledge-base/04_modelo_de_datos.md` (§Entidades)

### [C-04] `autenticacion`
- **Estado**: `[ ]` pendiente
- **Puntos**: 16 | **Orden sugerido**: 4
- **Scope**:
  - bcrypt con costo configurable (`BCRYPT_ROUNDS`), fuera del bucle de eventos (`to_thread` + semáforo)
  - Hash de contraseña calculado antes de iniciar la transacción
  - Límite de 72 bytes de entrada de bcrypt
  - Login: límite de intentos fallidos (RN-08 → 429 con Retry-After), verificación contra hash real o fictício (RN-09), respuesta igual exista o no el correo
  - JWT con claims `sub`, `iat`, `exp`, `roles`
  - Cookie `access_token`: `HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure`
  - Registro automático atómico (usuario + rol CLIENTE + ficha cliente, US-002 / RN-02)
  - Logout (borrado de cookie)
  - `GET /auth/yo` (perfil del usuario autenticado)
- **Dependencias**: `C-01`, `C-02`
- **Governance**: CRITICO (sistema de autenticación)
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` (§Rutas públicas)
  - `knowledge-base/05_reglas_de_negocio.md` (§RN-06 a RN-09)
  - `knowledge-base/08_arquitectura_propuesta.md` (§Seguridad)

### [C-05] `autorizacion`
- **Estado**: `[ ]` pendiente
- **Puntos**: 14 | **Orden sugerido**: 5
- **Scope**:
  - `get_usuario_actual` → 401 si no hay sesión válida
  - `requiere_rol` → 403, consultando roles vigentes en la base en cada petición (RN-04; los roles del token son informativos)
  - Autoprotección ADMIN: un administrador no puede revocarse su propio ADMIN (RN-05)
  - Cambio obligatorio de contraseña: 2 grupos de rutas en `main.py` (rutas `/auth` y salud vs. el resto; RN-06)
  - Tabla de historial de seguridad con actor `SISTEMA`
  - Comparación de `iat` sin truncar a segundos frente a `password_cambiada_en` (RN-07)
- **Dependencias**: `C-04`
- **Governance**: ALTO (gestión de roles y autorización)
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` (§Matriz de permisos RBAC)
  - `knowledge-base/05_reglas_de_negocio.md` (§RN-03 a RN-07)
  - `knowledge-base/04_modelo_de_datos.md` (§usuario, rol_asignacion)

---

## FASE 3 — Repositorios, Unit of Work e integridad

> Nota: `C-06` requiere `C-02` y `C-03` (GATE 3). `C-07` requiere `C-06` y `C-02` (GATE 4).

### [C-06] `repositorios-y-unit-of-work`
- **Estado**: `[ ]` pendiente
- **Puntos**: 20 | **Orden sugerido**: 6
- **Scope**:
  - `BaseRepository[T]` + `SoftDeleteRepository[T]` (solo `flush()`, nunca `commit()`)
  - Precarga (eager loading) en repositorio para evitar lecturas N+1
  - `UnitOfWork` como contexto asíncrono (`async with`)
  - El router construye la UoW y el servicio la abre con `async with`
  - Operaciones RN-02 (auto-registro atómico), RN-13 (terminar orden) y RN-20 (cambio de precio) en un solo bloque transaccional
  - Repositorio de solo lectura para el catálogo `estado_orden`
  - Punto único de escritura de stock (RN-14: el stock solo cambia por movimientos)
- **Dependencias**: `C-02`, `C-03`
- **Governance**: ALTO (transacciones atómicas y escritura única de stock)
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` (tabla de patrones: Repository, Unit of Work)
  - `knowledge-base/05_reglas_de_negocio.md` (§RN-02, §RN-13, §RN-14, §RN-20)
  - `knowledge-base/07_flujos_principales.md` (Flujo 2, 4, 6)

### [C-07] `integridad-solo-agregado-intento-acceso`
- **Estado**: `[ ]` pendiente
- **Puntos**: 10 | **Orden sugerido**: 7
- **Scope**:
  - Disparador de base de datos que rechaza `UPDATE`/`DELETE` en `historial_estado_orden`, `movimiento_stock` e `historial_precio_repuesto` (RN-15)
  - Migración escrita a mano para el disparador (Alembic autogenerate no detecta funciones ni disparadores)
  - Tabla `intento_acceso` en su propia sesión/transacción que siempre confirma (commit independiente)
- **Dependencias**: `C-02`, `C-06`
- **Governance**: CRITICO (audit trail y tablas de solo-agregado, datos de seguridad)
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (§historial_estado_orden, movimiento_stock, historial_precio_repuesto)
  - `knowledge-base/05_reglas_de_negocio.md` (§RN-15)
  - `knowledge-base/08_arquitectura_propuesta.md` (tablas de solo agregado + disparador de base)

---

## FASE 4 — Lecturas optimizadas y asincronía

> Nota: `C-08` requiere `C-03` y `C-06` (GATE 4).

### [C-08] `lecturas-sin-n1-y-asincronia`
- **Estado**: `[ ]` pendiente
- **Puntos**: 8 | **Orden sugerido**: 8
- **Scope**:
  - Carga anticipada en repositorio (`selectinload`/`joinedload`) para lecturas sin N+1
  - Detalle de orden con un número fijo y predecible de consultas a la base
  - Handlers `async def` en todos los routers
  - Sin llamadas bloqueantes en el hilo de eventos (bcrypt ya corre fuera del bucle en `C-04`)
  - `BackgroundTasks` para envío de aviso al cliente (al terminar/cancelar orden)
- **Dependencias**: `C-03`, `C-06`
- **Governance**: MEDIO (rendimiento de lecturas y asincronía)
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` (Flujo 4, 5)
  - `knowledge-base/04_modelo_de_datos.md` (§orden_trabajo)
  - `knowledge-base/08_arquitectura_propuesta.md`

---

## Tabla resumen de changes

| Código | Change | Puntos | Orden | Dependencias | Governance | Agente |
|--------|--------|--------|-------|--------------|------------|--------|
| C-01 | proyecto-configuracion-ciclo-vida | 8 | 1 | — | MEDIO | A |
| C-02 | modelos-relaciones-migraciones | 14 | 2 | C-01 | CRITICO | A |
| C-03 | contratos-y-crud | 10 | 3 | C-02 | BAJO | A |
| C-04 | autenticacion | 16 | 4 | C-01, C-02 | CRITICO | B |
| C-05 | autorizacion | 14 | 5 | C-04 | ALTO | B |
| C-06 | repositorios-y-unit-of-work | 20 | 6 | C-02, C-03 | ALTO | C |
| C-07 | integridad-solo-agregado-intento-acceso | 10 | 7 | C-02, C-06 | CRITICO | C |
| C-08 | lecturas-sin-n1-y-asincronia | 8 | 8 | C-03, C-06 | MEDIO | A |

**Total**: 100 puntos · 8 changes · 4 fases · 4 gates de paralelismo · camino crítico de 5 changes.

**Primer change recomendado**: `C-01` (`proyecto-configuracion-ciclo-vida`) — arrancar con `/opsx:propose C-01-proyecto-configuracion-ciclo-vida`.
