# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|--------|--------------|---------|
| Capas (Router → Service → UoW → Repository → Model) | Toda la API | Separación de responsabilidades; fácil de testear y mantener |
| Unit of Work | Escritura múltiple (auto-registro, terminación de orden, cambio de precio) | Transacciones atómicas: todo o nada (RN-02, RN-13, RN-20) |
| Repository (solo `flush`, sin `commit`) | Acceso a datos | El `commit` lo controla el UoW, nunca el repositorio (restricción no negociable) |
| Catálogo de estados | Tabla `estado_orden` | Estados definidos en base, no hardcodeados (RN-19) |
| Borrado lógico + índice único parcial | Vehículos, repuestos | Baja lógica sin perder historial; unicidad solo entre vigentes (RN-01, RN-16) |
| Tablas de solo agregado + disparador de base | `historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto` | Nadie modifica ni borra filas (RN-15); el disparador debe escribirse a mano (Alembic autogenerate no ve funciones ni disparadores) |

## Estructura de directorios

```
proyecto/
├── app/
│   ├── core/                          (config, seguridad, base de datos, excepciones)
│   └── modules/
│       ├── usuarios/                  (usuario, asignacion_rol, intento_acceso, evento_seguridad)
│       ├── clientes/                  (cliente y vehiculo)
│       ├── repuestos/                 (repuesto, movimiento_stock, historial_precio_repuesto)
│       ├── ordenes/                   (estado_orden, orden_trabajo, item_orden, historial_estado_orden)
│       └── health/                    (sólo router.py: /health/live y /health/ready)
├── migrations/                        (configuración de Alembic y sus versiones)
├── test/                              (archivos .http y solo_agregado.sql)
├── seed.py                            (datos iniciales obligatorios)
├── .env                               (no se versiona; credenciales nunca en código)
├── .env.example                       (sin secretos)
└── pyproject.toml / requirements.txt
```

Estructura obligatoria: `app/core/` y `app/modules/<modulo>/` (con modelos, schemas, repositorio, unit_of_work, service, router).

## Seguridad

- **Autenticación**: contraseñas hasheadas con bcrypt (fuera del bucle de eventos, `to_thread` + semáforo); token JWT en cookie `access_token` con `HttpOnly`, `SameSite=Lax`; nunca en el cuerpo ni leído del encabezado `Authorization`.
- **Autorización**: roles vigentes en la base en cada petición (401 vs 403); los roles del token son informativos (RN-04).
- **Validación de input**: schemas pydantic en el router; ninguna entrada inválida termina en 500; ningún error devuelve texto interno de base (RN-18).
- **Secrets management**: `.env` no se versiona; `env.example` sin secretos; credenciales y clave de firma nunca en el código.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|----------|-------------|---------|----------|
| DATABASE_URL | URL completa opcional; tiene prioridad sobre las variables sueltas | postgresql+asyncpg://user:pass@localhost:5432/taller | Y |
| POSTGRES_HOST | Host de PostgreSQL | localhost | N |
| POSTGRES_USER | Usuario de PostgreSQL | postgres | N |
| POSTGRES_PASSWORD | Contraseña de PostgreSQL (sin valor por defecto) | — | Y |
| POSTGRES_DB | Nombre de la base | taller_mecanico | N |
| POSTGRES_PORT | Puerto de PostgreSQL | 5432 | N |
| POOL_SIZE | Tamaño del pool del motor async | 10 | N |
| SQL_ECHO | Muestra las consultas SQL en consola para diagnóstico | false | N |
| SECRET_KEY | Clave de firma de JWT (sin valor por defecto) | (generada aleatoriamente) | Y |
| ALGORITHM | Algoritmo de JWT | HS256 | N |
| ACCESS_TOKEN_EXPIRE_MINUTES | Expiración del token | 30 | N |
| BCRYPT_ROUNDS | Factor de costo de bcrypt | 12 | N |
| FIRST_ADMIN_EMAIL | Correo del administrador inicial (seed) | admin@taller.com | Y |
| FIRST_ADMIN_PASSWORD | Contraseña del administrador inicial (seed) | — | Y |
