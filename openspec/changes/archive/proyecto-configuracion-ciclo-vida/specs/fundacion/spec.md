# Spec Delta: fundacion (C-01 Proyecto, Configuración y Ciclo de Vida)

## Purpose
Establecer la estructura base del proyecto, la configuración centralizada con Pydantic Settings, el ciclo de vida (`lifespan`) para el motor y fábrica de sesiones asíncronas, y los endpoints de salud.

## ADDED Requirements

### Requirement: Configuración centralizada con Pydantic Settings
El sistema SHALL leer la configuración mediante `pydantic-settings` y construir la URL de conexión a la base de datos de forma asíncrona mediante un `@computed_field`.

#### Scenario: Configuración de base de datos asíncrona
- **WHEN** la aplicación arranca y lee las variables de entorno
- **THEN** se configura correctamente el driver asincrónico y el tamaño del pool de conexiones

### Requirement: Inicialización y cierre en el ciclo de vida (Lifespan)
El sistema SHALL inicializar el motor SQLAlchemy asíncrono y la fábrica de sesiones (`async_session_maker`) durante el evento de inicio en el `lifespan`, almacenándolos en `app.state`, y ejecutar `dispose()` del motor al apagar la aplicación.

#### Scenario: Recursos en app.state
- **WHEN** la aplicación inicia exitosamente
- **THEN** `app.state.db_engine` y `app.state.async_session_maker` se encuentran disponibles y configurados con `expire_on_commit=False`

#### Scenario: Cierre limpio de recursos
- **WHEN** la aplicación recibe señal de apagado
- **THEN** se libera el motor de base de datos con `dispose()`

### Requirement: Endpoints de salud (Liveness y Readiness)
El sistema SHALL exponer `GET /health/live` (que no toca la base de datos) y `GET /health/ready` (que ejecuta `SELECT 1` y responde 503 si la base no contesta).

#### Scenario: Verificación de disponibilidad (Live)
- **WHEN** se consulta `GET /health/live`
- **THEN** responde 200 OK indicando que el proceso está vivo

#### Scenario: Verificación de preparación (Ready)
- **WHEN** se consulta `GET /health/ready` y la base de datos responde
- **THEN** responde 200 OK; si la base falla, responde 503
