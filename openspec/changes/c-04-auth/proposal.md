## Why

Implementación del sistema de autenticación para la API del taller mecánico. Se requiere asegurar los endpoints CRUD ya implementados y cumplir con las reglas de negocio RN-08 (límite de intentos fallidos → 429 con Retry-After) y RN-09 (login responde igual exista o no el correo). Además, se necesita soportar la autenticación con JWT en cookie HttpOnly para todas las operaciones posteriores.

## What Changes

Implementación completa del flujo de autenticación:

- **bcrypt** con costo configurable (`BCRYPT_ROUNDS`), fuera del bucle de eventos usando `to_thread` + semáforo
- **Hash de contraseña** calculado antes de iniciar la transacción
- **Límite de 72 bytes** de entrada de bcrypt
- **Login**: límite de intentos fallidos (RN-08 → 429 con Retry-After), verificación contra hash real o fictício (RN-09), respuesta igual exista o no el correo
- **JWT** con claims `sub`, `iat`, `exp`, `roles`
- **Cookie `access_token`**: `HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure`
- **Registro automático atómico** (usuario + rol CLIENTE + ficha cliente, RN-02 / US-002)
- **Logout** (borrado de cookie)
- **GET /auth/yo** (perfil del usuario autenticado)

## Capabilities

### New Capabilities

- `auth/login`: Endpoint de inicio de sesión con validación de credenciales y generación de token
- `auth/register`: Registro automático atómico (usuario + rol CLIENTE + ficha cliente)
- `auth/jwt`: Generación y validación de JWT con claims de rol
- `auth/logout`: Borrado de la cookie `access_token`
- `auth/me`: Endpoint `GET /auth/yo` para obtener el perfil del usuario

### Modified Capabilities

- Ninguna (no hay modificaciones de requisitos en specs existentes)

## Impact

- Endpoints: `POST /auth/login`, `POST /auth/register`, `POST /auth/logout`, `GET /auth/yo`
- Middleware de protección en rutas privadas usando `requiere_rol`
- Integración con `app/main.py` para incluir el router de auth
- Dependencias: C-01 (configuración ciclo vida) y C-02 (modelos y migraciones) ya completados
- Governance: CRITICO - sistema de autenticación es crítico para la seguridad del sistema