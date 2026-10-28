# Design: C-01 proyecto-configuracion-ciclo-vida

## Architecture & Patterns
- **Patrón de capas**: Router → Service → UoW → Repository → Model (preparado con `app/modules/`).
- **Ciclo de vida asíncrono**: `asynccontextmanager lifespan` en `app/main.py` inicializa el motor SQLAlchemy y la factoría de sesiones (`async_sessionmaker`), almacenándolos en `app.state.db_engine` y `app.state.async_session_maker`. Al apagar, ejecuta `await app.state.db_engine.dispose()`.
- **Configuración centralizada**: `app/core/config.py` usa `pydantic-settings` con `model_config = SettingsConfigDict(env_file=".env", extra="forbid")` y `@computed_field` para calcular dinámicamente `SQLALCHEMY_DATABASE_URI`.
- **Gestión de sesiones**: `app/core/database.py` expunde `get_session` extrayendo la factoría desde `app.state.async_session_maker` con `expire_on_commit=False`.
- **Seguridad (RN-09)**: `app/core/security.py` maneja hashing con bcrypt fuera del bucle de eventos (`to_thread` / `run_in_executor`) y verificación en tiempo constante (`constant_time_verify`) para evitar enumeración de usuarios.
