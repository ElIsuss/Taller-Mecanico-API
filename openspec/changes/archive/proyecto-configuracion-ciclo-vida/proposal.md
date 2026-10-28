# Proposal: C-01 proyecto-configuracion-ciclo-vida

## What
Configuración inicial del proyecto Taller Mecánico API (Fase 1 / GATE 0), estableciendo la estructura en capas obligatoria (`app/core/`, `app/modules/`), configuración con `pydantic-settings`, ciclo de vida con motor y sesión de SQLAlchemy asíncronos, endpoints de salud y stubs de seguridad (RN-09).

## Why
Es el cimiento técnico obligatorio del proyecto definido en el roadmap (`CHANGES.md`) y la base de conocimiento, permitiendo el acceso asíncrono a la base de datos y preparando la infraestructura para los siguientes changes de modelos y CRUD.

## Capabilities / Scope
- Estructura de carpetas: `app/core/`, `app/modules/{auth,clientes,vehiculos,repuestos,ordenes,roles}/`
- Configuración con `pydantic-settings` (`Settings` con `extra="forbid"` y `@computed_field` para `SQLALCHEMY_DATABASE_URI`)
- Ciclo de vida (`lifespan`) para inicializar motor async y `async_sessionmaker`, guardándolos en `app.state` y haciendo `dispose()` al apagar
- Dependencia `get_session` con `expire_on_commit=False`
- Endpoints de salud: `GET /health/live` y `GET /health/ready`
- Utilidades de seguridad con bcrypt y verificación en tiempo constante (RN-09)
