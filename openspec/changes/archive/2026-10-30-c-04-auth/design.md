## Context

Sistema de autenticación para API FastAPI con SQLModel/SQLAlchemy 2.0 async. Los endpoints CRUD (C-03) ya están implementados y requieren autenticación vigente. No se usarán create_all, solo Alembic para el esquema. bcrypt corre fuera del bucle de eventos con to_thread + semáforo. Los tokens JWT viajan solo en la cookie `access_token` con HttpOnly, SameSite=Lax.

## Goals / Non-Goals

**Goals:**
- Implementar login/registro con bcrypt hash fuera del evento
- Generar JWT con claims sub, iat, exp, roles
- Almacenar token en cookie HttpOnly SameSite=Lax
- Validar RN-08 (5 intentos → 429 con Retry-After) y RN-09 (misma respuesta exista/no exista)
- Soporte para logout y GET /auth/yo

**Non-Goals:**
- Renovar tokens (refresh tokens) - fuera de alcance actual
- Autenticación mediante header Authorization - usar solo cookie
- Renovación de sesión automática

## Decisions

1. **bcrypt fuera del bucle**: Usar `run_in_executor` (to_thread) con semáforo global para evitar bloqueo del event loop. El hash se calcula antes de iniciar la transacción de base de datos.

2. **Cookie vs Header**: El token JWT viaja exclusivamente en la cookie `access_token` con atributos `HttpOnly`, `SameSite=Lax`, `Max-Age` y `Secure` (en producción). Nunca se lee del encabezado `Authorization`.

3. **Login igual exista o no el correo (RN-09)**: El endpoint de login retorna siempre 401 con el mismo mensaje `{"detail": "Invalid credentials"}` ya sea el email no exista o la contraseña sea incorrecta, para prevenir enumeración de emails.

4. **Límite de intentos RN-08**: Contador de intentos fallidos por IP o correo en memoria (semáforo + diccionario). A los 5 fallos, responder 429 con `Retry-After` header. El contador se reinicia después de un período de tiempo configurado.

5. **JWT claims**: Incluir `sub` (user ID), `iat` (timestamp sin truncar), `exp` (expiración), y `roles` (roles vigentes consultados en base por RN-04).

6. **Registro automático (RN-02/US-002)**: Al registrar un nuevo cliente, se crea atomicamente: usuario con password_hash encriptado + asignacion_rol con rol CLIENTE + ficha cliente vinculada al usuario_id.

7. **Validación de contraseña**: Límite de 72 bytes para entrada de bcrypt. Contraseñas menores a longitud mínima son rechazadas con 422.

## Risks / Trade-offs

- [Risk: bcrypt fuera del event loop] → Mitigation: Usar `to_thread` con semáforo; el overhead es mínimo comparado con el bloqueo del event loop.
- [Risk: Comparación iat vs password_cambiada_en (RN-07)] → Mitigation: Comparar timestamps completos sin truncar a segundos; guardar password_cambiada_en como timestamptz.
- [Risk: Cookie SameSite=Lax en contexto cross-site] → Mitigation: El diseño actual usa Lax que es seguro para navegación normal; considerar Strict si es necesario.
- [Risk: Estado de sesión en memoria para RN-08] → Mitigation: El contador de intentos puede perderse en reinicios; considerar persistencia en Redis o base de datos para producción.

## Migration Plan

1. Agregar router `auth` en `app/main.py`
2. Crear schemas en `app/modules/auth/schemas.py`
3. Implementar service en `app/modules/auth/service.py`
4. Implementar router en `app/modules/auth/router.py`
5. Probar suite de tests con PostgreSQL

## Open Questions

- ¿Se soportarán múltiples mecánicos por orden en el futuro? (Pregunta abierta de prioridad alta, no bloquea este change)
- ¿Los avisos por BackgroundTasks son suficientes o se necesitarán colas Redis en el futuro? (Pregunta media, no bloquea)