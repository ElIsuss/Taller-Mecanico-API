# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — API solo backend (sin frontend propio)
**Decisión**: El sistema es una API REST pura; no se incluye frontend.
**Contexto**: El TP pide una API para el taller; los clientes se registran "en la web" pero esa web es ajena al alcance del TP.
**Alternativas consideradas**: Incluir un frontend sencillo (React, etc.).
**Justificación**: El alcance y las restricciones del TP se centran en la API (capas, autenticación, RBAC, transacciones, catálogos, trigger).
**Trade-offs aceptados**: No se documentan pantallas ni navegación de UI.

### DD-02 — JWT en cookie HttpOnly (no en header Authorization)
**Decisión**: Los tokens JWT viajan exclusivamente en cookie `access_token` con `HttpOnly`, `SameSite=Lax`.
**Contexto**: Restricción no negociable del TP.
**Alternativas consideradas**: Bearer token en header `Authorization`.
**Justificación**: Cumple la restricción del enunciado y reduce exposición a XSS.
**Trade-offs aceptados**: Requiere manejo de cookies en el cliente; no se usa el encabezado `Authorization`.

### DD-03 — SQLModel + SQLAlchemy 2.0 async con asyncpg
**Decisión**: ORM SQLModel sobre SQLAlchemy 2.0 async, driver asyncpg, PostgreSQL 16.
**Contexto**: Stack obligado por el TP.
**Alternativas consideradas**: SQLAlchemy sync, otro driver, otra base de datos.
**Justificación**: Es el stack obligado; soporta operaciones asíncronas requeridas por el curso.
**Trade-offs aceptados**: Complejidad de `async/await` en todo el stack de datos.

### DD-04 — Alembic para el esquema (no create_all)
**Decisión**: El esquema se crea exclusivamente con `alembic upgrade head`; no se usa `create_all`.
**Contexto**: Restricción no negociable; los casos de prueba y la corrección usan nombres de tablas y columnas obligatorios.
**Alternativas consideradas**: `Base.metadata.create_all` al arrancar.
**Justificación**: Cumple la restricción y permite migraciones versionadas (una autogenerate + una escrita a mano para el disparador de solo agregado).
**Trade-offs aceptados**: Requiere ejecutar migraciones antes de usar la base; el disparador de solo agregado debe escribirse a mano.

### DD-05 — Borrado lógico para vehículos y repuestos
**Decisión**: Vehículos y repuestos se dan de baja lógicamente (`borrado_en`), no se borran físicamente.
**Contexto**: RN-16 exige conservar datos aunque dejen de aparecer; el TP nombra la columna `borrado_en`.
**Alternativas consideradas**: Borrado físico (`DELETE`).
**Justificación**: Cumple RN-16 y permite índices únicos parciales sobre los vigentes (RN-01).
**Trade-offs aceptados**: Todas las consultas deben filtrar por vigentes; más complejidad en consultas.

## Supuestos inferidos

### SU-01 — Un mecánico asignado por orden (no múltiples)
**Supuesto**: Cada orden de trabajo tiene un solo mecánico asignado (campo `mechanico_asignado_id`, relación 1:1 opcional).
**Origen**: Pregunta abierta del informe de discovery ("¿Soporte para múltiples mecánicos por orden, o siempre uno asignado?"); se asume uno asignado por simplicidad y por el enunciado del TP.
**Riesgo si es falso**: Si se requieren múltiples mecánicos, habría que cambiar a una relación N:M (tabla intermedia).
**Cómo validar**: Confirmar con el product owner antes de implementar la asignación de mecánicos.

### SU-02 — BackgroundTasks suficientes para avisos (no colas Redis)
**Supuesto**: Los avisos al cliente se resuelven con `BackgroundTasks` de FastAPI; no se necesitan colas Redis.
**Origen**: Pregunta abierta del informe de discovery; funcionalidad opcional "Colas Redis (capítulo 8) — no se evalúa".
**Riesgo si es falso**: Si se necesitan avisos confiables o reintentos, habría que agregar Redis + colas.
**Cómo validar**: Confirmar si los requisitos de notificación exigen colas en una versión futura.

### SU-03 — Escala "team" (un taller, equipo pequeño)
**Supuesto**: El sistema opera a escala de un solo taller con un equipo pequeño (< 50 personas).
**Origen**: Inferido de los 4 roles (RECEPCION, MECANICO, ADMIN, CLIENTE) y el dominio de un taller mecánico local.
**Riesgo si es falso**: Si el sistema debe soportar múltiples talleres (multi-tenant), cambiaría el modelo de datos y el aislamiento de datos.
**Cómo validar**: Confirmar si el alcance es un solo taller o una cadena de talleres.

### SU-04 — Un administrador inicial creado por seed.py
**Supuesto**: `seed.py` crea un usuario administrador inicial cuyas credenciales vienen de variables de entorno.
**Origen**: RN-05 ("el sistema nunca queda sin administradores vigentes") y la funcionalidad necesaria "seed.py con datos iniciales obligatorios".
**Riesgo si es falso**: Sin admin inicial no se podría asignar roles ni gestionar personal.
**Cómo validar**: Revisar que `seed.py` incluya el admin inicial con credenciales de `.env`.
