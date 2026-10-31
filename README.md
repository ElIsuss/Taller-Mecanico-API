# Taller Mecánico API

API REST desarrollada con **FastAPI y PostgreSQL** para gestionar las operaciones de un taller mecánico: clientes, vehículos, repuestos, órdenes de trabajo, usuarios y permisos.

Este proyecto forma parte de un trabajo práctico académico de Programación III. Su objetivo es aplicar arquitectura en capas, programación asíncrona, autenticación, autorización, persistencia relacional y manejo seguro de transacciones.

## Objetivos del proyecto

- Centralizar la gestión de clientes y vehículos.
- Registrar y administrar órdenes de trabajo.
- Gestionar el catálogo de repuestos y sus existencias.
- Controlar el acceso según los roles de los usuarios.
- Garantizar la integridad de los datos mediante transacciones y restricciones de base de datos.
- Aplicar buenas prácticas de desarrollo de APIs REST.

## Tecnologías

- **Python 3.12**
- **FastAPI 0.111**
- **SQLModel 0.0.24**
- **SQLAlchemy 2.0** con soporte asíncrono
- **PostgreSQL 16**
- **asyncpg**
- **Alembic** para migraciones
- **Pydantic V2** y `pydantic-settings`
- **bcrypt** para el hash de contraseñas
- **PyJWT** para la gestión de tokens
- **Uvicorn** como servidor ASGI


## Funcionalidades principales

### Usuarios y seguridad

- Registro público de clientes.
- Inicio y cierre de sesión.
- Cambio de contraseña.
- Autenticación mediante JWT en cookies `HttpOnly`.
- Autorización según los roles vigentes en la base de datos.
- Control de intentos fallidos de inicio de sesión.
- Administración de usuarios y roles.
- Registro y consulta de eventos de seguridad según los permisos correspondientes.

### Clientes y vehículos

- Alta y consulta de clientes.
- Registro y consulta de vehículos.
- Asociación de vehículos con sus propietarios.
- Baja lógica de vehículos.
- Restricción del acceso a los datos según los permisos y la propiedad del recurso.

### Repuestos

- Administración del catálogo de repuestos.
- Consulta de existencias.
- Reposición de stock.
- Registro de movimientos de inventario.
- Baja lógica de repuestos.

### Órdenes de trabajo

- Creación de órdenes con fallas e ítems de repuestos.
- Asignación de órdenes a mecánicos.
- Inicio y finalización de reparaciones.
- Cancelación de órdenes cuando se cumplen las reglas de negocio.
- Descuento de existencias al finalizar una reparación, dentro de una transacción.
- Consulta del estado de las órdenes.

Los estados contemplados son:

- `PENDIENTE`
- `EN_REPARACION`
- `TERMINADA`
- `CANCELADA`

## Roles del sistema

| Rol | Responsabilidades principales |
|---|---|
| `RECEPCION` | Registrar clientes y vehículos, abrir órdenes y cancelar órdenes permitidas. |
| `MECANICO` | Iniciar y finalizar las órdenes que tiene asignadas. |
| `ADMIN` | Administrar repuestos, reponer stock, gestionar roles y consultar eventos de seguridad. |
| `CLIENTE` | Registrarse y consultar sus propios vehículos y órdenes. |

Los permisos se verifican con los roles vigentes en la base de datos. La aplicación debe distinguir entre falta de autenticación (`401 Unauthorized`) y falta de autorización (`403 Forbidden`).

## Arquitectura

El proyecto utiliza una arquitectura en capas:

`Router → Service → Unit of Work → Repository → Model`

- **Router:** define los endpoints HTTP, recibe solicitudes y devuelve respuestas.
- **Service:** implementa los casos de uso y las reglas de negocio.
- **Unit of Work (UoW):** coordina las operaciones transaccionales, los commits y los rollbacks.
- **Repository:** encapsula el acceso a los datos.
- **Model:** representa las entidades persistidas en PostgreSQL.

La lógica de negocio no debe concentrarse en los routers y los repositorios no deben confirmar transacciones por su cuenta.

## Base de datos y migraciones

La persistencia se realiza en PostgreSQL y la estructura de la base de datos se administra mediante Alembic.

- Las modificaciones del esquema deben realizarse mediante migraciones.
- No se utiliza `create_all()` para crear las tablas.
- Las operaciones relacionadas que requieren atomicidad deben ejecutarse dentro de una misma transacción.
- Los registros históricos protegidos deben respet
