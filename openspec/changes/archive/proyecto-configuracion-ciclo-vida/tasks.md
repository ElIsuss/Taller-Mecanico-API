# Tasks: C-01 proyecto-configuracion-ciclo-vida

- [x] Crear estructura de directorios `app/core/` y `app/modules/{auth,clientes,vehiculos,repuestos,ordenes,roles}/`
- [x] Configurar variables de entorno y `pydantic-settings` con `@computed_field` y `extra="forbid"` (`app/core/config.py`)
- [x] Implementar conexión asíncrona SQLAlchemy, `async_sessionmaker` y `get_session` (`app/core/database.py`)
- [x] Implementar gestión de ciclo de vida (`lifespan`) en `app/main.py` con `app.state` y `dispose()`
- [x] Implementar endpoints de salud `GET /health/live` y `GET /health/ready`
- [x] Implementar utilidades de seguridad con bcrypt y verificación en tiempo constante (RN-09) (`app/core/security.py`)
- [x] Escribir y verificar tests unitarios e de integración para health checks y seguridad (`tests/`)
- [x] Crear plantillas de entorno (`.env.example`) y exclusiones (`.gitignore`)
