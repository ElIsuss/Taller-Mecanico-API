## 1. Configuración y estructura

- [x] 1.1 Crear `app/modules/auth/schemas.py` con `Login`, `Register`, `Me` schemas y `extra="forbid"`
- [x] 1.2 Crear `app/modules/auth/models.py` con el modelo `Usuario` extendido si es necesario
- [x] 1.3 Agregar router de auth en `app/main.py` incluyendo `router_auth`

## 2. bcrypt fuera del event loop

- [x] 2.1 Implementar función `hash_password` usando `run_in_executor` (to_thread) con semáforo global
- [x] 2.2 Implementar función `verify_password` usando `run_in_executor` para comparar hash
- [x] 2.3 Configurar `BCRYPT_ROUNDS` en `app/core/config.py` con valor por defecto 12
- [x] 2.4 Agregar validación de límite de 72 bytes para entrada de bcrypt

## 3. JWT y tokens

- [x] 3.1 Implementar `create_access_token` generando JWT con claims `sub`, `iat`, `exp`, `roles`
- [x] 3.2 Implementar `decode_access_token` validando y extrayendo claims del token en cookie
- [x] 3.3 Configurar `SECRET_KEY` y `ALGORITHM` en settings (ya definidos en config.py)
- [x] 3.4 Establecer `ACCESS_TOKEN_EXPIRE_MINUTES` = 30

## 4. Endpoint de login

- [x] 4.1 Crear `POST /auth/login` en `app/modules/auth/router.py`
- [x] 4.2 Validar credenciales contra base de datos
- [x] 4.3 Aplicar RN-09: respuesta igual exista o no el correo (siempre 401 "Invalid credentials")
- [x] 4.4 Aplicar RN-08: contador de intentos fallidos, a 5 → 429 con Retry-After
- [x] 4.5 Generar token JWT y establecer cookie `access_token` con HttpOnly, SameSite=Lax, Max-Age
- [x] 4.6 Probar casos: login exitoso, credenciales inválidas, cuenta desactivada

## 5. Endpoint de registro

- [x] 5.1 Crear `POST /auth/register` en `app/modules/auth/router.py`
- [x] 5.2 Implementar registro atómico: usuario + rol CLIENTE + ficha cliente (RN-02/US-002)
- [x] 5.3 Hashear contraseña antes de guardar (bcrypt fuera del evento)
- [x] 5.4 Retornar 201 Created con datos básicos (sin password_hash)
- [x] 5.5 Probar: registro exitoso, email duplicado, documento duplicado

## 6. Endpoint de logout

- [x] 6.1 Crear `POST /auth/logout` en `app/modules/auth/router.py`
- [x] 6.2 Invalidar la cookie `access_token` (Set-Cookie con Max-Age=0)
- [x] 6.3 Retornar 204 No Content
- [x] 6.4 Probar: logout con sesión activa, logout sin sesión (idempotente)

## 7. Endpoint de perfil (GET /auth/yo)

- [x] 7.1 Crear `GET /auth/yo` en `app/modules/auth/router.py`
- [x] 7.2 Verificar cookie `access_token` y obtener usuario actual
- [x] 7.3 Retornar datos del usuario sin password_hash
- [x] 7.4 Incluir roles vigentes consultados en base (RN-04)
- [x] 7.5 Retornar 401 si no hay sesión válida
- [x] 7.6 Probar: perfil devuelto, 401 sin token
