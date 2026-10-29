## 1. Configuración y estructura

- [ ] 1.1 Crear `app/modules/auth/schemas.py` con `Login`, `Register`, `Me` schemas y `extra="forbid"`
- [ ] 1.2 Crear `app/modules/auth/models.py` con el modelo `Usuario` extendido si es necesario
- [ ] 1.3 Agregar router de auth en `app/main.py` incluyendo `router_auth`

## 2. bcrypt fuera del event loop

- [ ] 2.1 Implementar función `hash_password` usando `run_in_executor` (to_thread) con semáforo global
- [ ] 2.2 Implementar función `verify_password` usando `run_in_executor` para comparar hash
- [ ] 2.3 Configurar `BCRYPT_ROUNDS` en `app/core/config.py` con valor por defecto 12
- [ ] 2.4 Agregar validación de límite de 72 bytes para entrada de bcrypt

## 3. JWT y tokens

- [ ] 3.1 Implementar `create_access_token` generando JWT con claims `sub`, `iat`, `exp`, `roles`
- [ ] 3.2 Implementar `decode_access_token` validando y extrayendo claims del token en cookie
- [ ] 3.3 Configurar `SECRET_KEY` y `ALGORITHM` en settings (ya definidos en config.py)
- [ ] 3.4 Establecer `ACCESS_TOKEN_EXPIRE_MINUTES` = 30

## 4. Endpoint de login

- [ ] 4.1 Crear `POST /auth/login` en `app/modules/auth/router.py`
- [ ] 4.2 Validar credenciales contra base de datos
- [ ] 4.3 Aplicar RN-09: respuesta igual exista o no el correo (siempre 401 "Invalid credentials")
- [ ] 4.5 Aplicar RN-08: contador de intentos fallidos, a 5 → 429 con Retry-After
- [ ] 4.6 Generar token JWT y establecer cookie `access_token` con HttpOnly, SameSite=Lax, Max-Age
- [ ] 4.7 Probar casos: login exitoso, credenciales inválidas, cuenta desactivada

## 5. Endpoint de registro

- [ ] 5.1 Crear `POST /auth/register` en `app/modules/auth/router.py`
- [ ] 5.2 Implementar registro atómico: usuario + rol CLIENTE + ficha cliente (RN-02/US-002)
- [ ] 5.3 Hashear contraseña antes de guardar (bcrypt fuera del evento)
- [ ] 5.4 Retornar 201 Created con datos básicos (sin password_hash)
- [ ] 5.5 Probar: registro exitoso, email duplicado, documento duplicado

## 6. Endpoint de logout

- [ ] 6.1 Crear `POST /auth/logout` en `app/modules/auth/router.py`
- [ ] 6.2 Invalidar la cookie `access_token` (Set-Cookie con Max-Age=0)
- [ ] 6.3 Retornar 204 No Content
- [ ] 6.3 Probar: logout con sesión activa, logout sin sesión (idempotente)

## 7. Endpoint de perfil (GET /auth/yo)

- [ ] 7.1 Crear `GET /auth/yo` en `app/modules/auth/router.py`
- [ ] 7.2 Verificar cookie `access_token` y obtener usuario actual
- [ ] 7.3 Retornar datos del usuario sin password_hash
- [ ] 7.4 Incluir roles vigentes consultados en base (RN-04)
- [ ] 7.5 Retornar 401 si no hay sesión válida
- [ ] 7.6 Probar: perfil devuelto, 401 sin token