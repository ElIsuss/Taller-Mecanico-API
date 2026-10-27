# Descripción General

## Stack tecnológico

| Capa | Tecnologías | Versión mínima |
|------|-------------|----------------|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI | 0.111 |
| ORM / Modelo | SQLModel, SQLAlchemy 2.0 async | 0.0.24 / 2.0 |
| Controlador de base de datos | asyncpg | — |
| Base de datos | PostgreSQL | 16 |
| Migraciones | Alembic | 1.13 |
| Configuración | pydantic-settings | 2.0 |
| Hash de contraseñas | bcrypt | 4.0 |
| Tokens | PyJWT | 2.8 |
| Servidor ASGI | uvicorn | — |

## Arquitectura general

API REST monolítica en capas, sin frontend propio. Cada petición atraviesa: Router (rutas y validación de entrada) → Service (reglas de negocio y orquestación) → Unit of Work (transacciones) → Repository (acceso a datos, solo `flush`, sin `commit`) → Model (entidades SQLModel). Los tokens JWT viajan únicamente en la cookie `access_token` con `HttpOnly`, `SameSite=Lax`; nunca en el cuerpo ni leídos del encabezado `Authorization`.

## Integraciones externas

| Servicio | Propósito | Tipo |
|----------|-----------|------|
| PostgreSQL 16 | Almacenamiento principal de datos | Conexión directa (asyncpg) |
| (ninguna externa obligatoria) | — | — |

No hay pagos, WhatsApp, calendarios ni APIs de terceros obligatorias.

## API REST — endpoints principales agrupados por recurso

- **Auth**: registro (auto-registro atómico: usuario + rol CLIENTE + ficha cliente), login (cookie HttpOnly), cambio de contraseña, salud
- **Usuarios / roles**: listar, asignar rol, revocar rol (un administrador no se revoca su propio ADMIN)
- **Clientes**: CRUD de clientes (alta por recepción o auto-registro)
- **Vehículos**: CRUD de vehículos vinculados a cliente
- **Repuestos**: CRUD del catálogo de repuestos, reposición de stock, historial de precios
- **Órdenes de trabajo**: abrir, iniciar (asignar mecánico), terminar (descuenta stock), cancelar, consultar estado
- **Catálogo de estados de orden**: consulta de estados (solo lectura desde la API; no se edita desde ella)
