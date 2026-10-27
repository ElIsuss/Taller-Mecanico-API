# Discovery — Taller Mecánico: API con FastAPI y PostgreSQL

**Fecha**: 2026-10-27  
**Fuentes investigadas**: documento `TP_Cap1a6_Consigna.pdf` (22 páginas, sin scraping web)

## 1. Problema que resuelve

Un taller mecánico necesita una API para gestionar su trabajo diario. La recepción da de alta a los clientes y a sus vehículos, y abre una orden de trabajo por cada ingreso, con la falla que describe el cliente y los repuestos que se van a usar. Un mecánico toma la orden, la repara y la da por terminada: en ese momento se descuenta del stock cada repuesto usado. El administrador mantiene el catálogo de repuestos, repone el stock y administra al personal y sus roles. Los clientes se registran solos en la web y consultan el estado de sus vehículos.

El dominio está elegido para que cada capítulo del curso tenga un lugar concreto donde aparecer (composición, uno a uno opcional, borrado lógico, roles con vigencia, transacciones, catálogo de estados, tablas de sólo agregado).

## 2. Usuarios / roles

- **Recepción (RECEPCION)**: da de alta clientes y vehículos, abre órdenes de trabajo, cancela órdenes.
- **Mecánico (MECANICO)**: inicia y termina órdenes de trabajo asignadas.
- **Administrador (ADMIN)**: gestiona el catálogo de repuestos, repone stock, asigna y revoca roles del personal, consulta eventos de seguridad.
- **Cliente (CLIENTE)**: se registra solo en la web, consulta sus vehículos y el estado de sus órdenes.

## 3. Casos de uso principales

1. Como recepcionista, quiero dar de alta clientes y vehículos y abrir órdenes de trabajo con ítems de repuestos.
2. Como mecánico, quiero iniciar y terminar órdenes de trabajo (descuentando el stock de cada repuesto usado).
3. Como administrador, quiero mantener el catálogo de repuestos, reponer stock y asignar/revocar roles del personal.
4. Como cliente, quiero registrarme y consultar el estado de mis vehículos y órdenes.
5. Como recepcionista, administrador o dueño del vehículo, quiero cancelar una orden de trabajo.

## 4. Competidores / soluciones existentes

No hay competidores comerciales mencionados en el documento (se trata de un Trabajo Práctico académico). La solución actual sería procesos manuales o planillas.

## 5. Funcionalidades necesarias (MVP)

- API asíncrona en capas: Router → Service → UoW → Repository → Model.
- Autenticación con contraseñas guardadas con bcrypt y token JWT en cookie HttpOnly.
- Autorización basada en roles vigentes en la base de datos en cada petición, distinguiendo 401 y 403.
- CRUD de clientes, vehículos, repuestos y órdenes de trabajo.
- Catálogo de estados de orden (PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA).
- Transacciones Unit of Work para operaciones de escritura múltiple (auto-registro, terminación de orden, cambio de precio de repuesto).
- Tablas de sólo agregado protegidas por disparador de base de datos.
- Borrado lógico para vehículos y repuestos, con índices únicos parciales sobre los vigentes.
- Paginación con envoltorio `{items, total, page, size, pages}`.
- Migraciones con Alembic (una generada con autogenerate, una escrita a mano para el disparador de sólo agregado).
- `seed.py` con datos iniciales obligatorios para poner el proyecto en marcha.

## 6. Funcionalidades opcionales / fuera de scope

- Concurrencia (capítulo 7) — no se evalúa en este TP.
- Colas de tareas con Redis (capítulo 8) — los avisos al cliente se resuelven con `BackgroundTasks`.

## 7. Reglas de negocio (RN-01 a RN-20)

- RN-01: El correo de un usuario y el documento de un cliente son únicos. La patente de un vehículo y el código de un repuesto son únicos entre los que no están dados de baja.
- RN-02: El auto-registro crea el usuario, su rol CLIENTE y su ficha de cliente: o quedan las tres filas, o ninguna. Si el documento ya es de un cliente del taller, el registro da 409 y no se apropia de esa ficha.
- RN-03: Un usuario tiene a lo sumo una asignación abierta por rol.
- RN-04: Los permisos se deciden con los roles vigentes en la base, en cada petición. Los roles que trae el token son informativos.
- RN-05: Un administrador no puede revocarse su propio rol ADMIN, y el sistema nunca queda sin administradores vigentes.
- RN-06: Mientras un usuario tenga el cambio de contraseña pendiente, sólo puede usar las rutas de `/auth` y las de salud.
- RN-07: Al cambiar la contraseña, las sesiones emitidas antes dejan de valer, aunque sean del mismo segundo que el cambio; la que devuelve el propio cambio, no.
- RN-08: Después de 5 intentos fallidos con el mismo correo desde la misma IP en 60 segundos, el login responde 429 sin verificar la contraseña. Un login correcto reinicia la cuenta.
- RN-09: El login responde lo mismo, y tarda lo mismo, exista o no el correo.
- RN-10: Una orden nace PENDIENTE con al menos un ítem y sin repuestos repetidos. El precio de cada ítem se copia del repuesto, y el total lo calcula el servidor.
- RN-11: Las transiciones de una orden son PENDIENTE → EN_REPARACION (la inicia un mecánico, que queda asignado), EN_REPARACION → TERMINADA (la termina el mecánico asignado o un administrador) y PENDIENTE → CANCELADA.
- RN-12: Cancelan una orden la recepción, el administrador o el dueño del vehículo. El permiso se evalúa antes que el estado.
- RN-13: Terminar una orden descuenta el stock de cada ítem, deja un movimiento por cada salida y una línea de historial. Si un repuesto no alcanza, no queda ninguna de esas escrituras.
- RN-14: El stock de un repuesto sólo cambia a través de movimientos: el alta con stock inicial, la reposición y la terminación de órdenes. No se edita por PATCH.
- RN-15: `historial_estado_orden`, `movimiento_stock` y `historial_precio_repuesto` son de sólo agregado: nadie puede modificar ni borrar sus filas.
- RN-16: Un vehículo o un repuesto dado de baja deja de aparecer y no se puede usar en órdenes nuevas, pero sus datos se conservan. Un vehículo con órdenes abiertas no se da de baja.
- RN-17: Lo propio sólo pide estar autenticado: un cliente ve sus vehículos y las órdenes de sus vehículos, y ninguna otra.
- RN-18: Ningún error devuelve al cliente texto interno de la base. Ninguna entrada inválida termina en un 500.
- RN-19: Los estados posibles de una orden son las filas del catálogo `estado_orden`. El catálogo se consulta desde la API y no se edita desde ella.
- RN-20: Cada cambio del precio de un repuesto deja una línea en `historial_precio_repuesto`, en la misma transacción que el cambio. Un PATCH que no cambia el precio no deja línea.

### Detalle de reglas específicas

**Auto-protección de ADMIN**: Un administrador no puede revocarse su propio rol ADMIN (responde 409), y el sistema nunca queda sin administradores vigentes.

**Cancelación de orden**: Puede ser cancelada por recepción, administrador o el dueño del vehículo. El permiso se evalúa antes que el estado. La ruta de cancelar no lleva `requiere_rol` — el servicio decide primero quién es y qué relación tiene con la orden (403), y recién después si el estado permite cancelarla (409). Una orden ya terminada no se puede cancelar (409).

**Invalidación de sesiones al cambiar contraseña**: Al cambiar la contraseña, las sesiones emitidas antes dejan de valer, aunque sean del mismo segundo que el cambio; la sesión que entrega el propio cambio sí vale. La comparación de `iat` (issued at) del token vs `password_cambiada_en` se hace sin truncar a segundos.

## 8. Integraciones

No hay integraciones externas obligatorias. PostgreSQL como base de datos. No hay pagos, WhatsApp, calendarios ni APIs de terceros.

## 9. Restricciones (no negociables)

- Python 3.12, FastAPI 0.111, SQLModel 0.0.24, SQLAlchemy 2.0 asíncrono, asyncpg, PostgreSQL 16, Alembic 1.13, pydantic-settings 2.0, bcrypt 4.0, PyJWT 2.8, uvicorn.
- Estructura de carpetas obligatoria (`app/core/`, `app/modules/<módulo>/` con modelos, schemas, repositorio, unit_of_work, service, router).
- Nombres de tablas y columnas obligatorios (los casos de prueba y la corrección los usan).
- No usar `create_all`; el esquema se crea exclusivamente con Alembic.
- Ningún repositorio confirma (`commit`); sólo `flush`.
- Carga perezosa prohibida: toda relación que se lee se precarga en el repositorio.
- Tokens sólo en cookie `access_token` con `HttpOnly`, `SameSite=Lax`; nunca en el cuerpo ni leído del encabezado `Authorization`.
- `.env` no se versiona; `env.example` sin secretos. Credenciales y clave de firma nunca en el código.

## 10. Riesgos

- El TP tiene criterios de evaluación estrictos (8 ejercicios con porcentajes).
- Un proyecto que no levanta, que no crea su esquema con `alembic upgrade head` sobre una base vacía o que contiene credenciales reales en el repositorio no se corrige hasta que se subsane.
- El disparador de sólo agregado debe escribirse a mano (Alembic autogenerate no ve funciones ni disparadores).
- `bcrypt` debe correr fuera del bucle de eventos (`to_thread` + semáforo).
- Comparación de `iat` vs `password_cambiada_en` sin truncar a segundos.

## 11. Preguntas abiertas

- ¿Soporte para múltiples mecánicos por orden, o siempre uno asignado?
- ¿Los avisos por `BackgroundTasks` son suficientes o se necesitarán colas Redis en el futuro?
