# Design: C-06 Repositorios y Unit of Work

## Context
Ver `proposal.md` y `specs/repositorios-unit-of-work/spec.md`.
El proyecto ya define una arquitectura por capas y la base de modelos de dominio, pero aún no está implementada una capa de acceso a datos consistente. La intención de este cambio es centralizar la sesión, el acceso a datos y la transacción para que los servicios puedan operar sin depender directamente de la sesión global.

## Goals / Non-Goals

**Goals:**
- Centralizar CRUD y consultas complejas en repositorios por dominio.
- Garantizar transacciones sobre una sesión compartida por módulo.
- Reutilizar la semántica de borrado lógico cuando el modelo lo requiere.
- Mantener la regla de que los repositorios usen `flush()` y no `commit()`.

**Non-Goals:**
- Rediseñar toda la lógica de negocios de los servicios.
- Cambiar la base tecnológica ni el esquema de BD.
- Introducir una capa de cache u optimizaciones de consultas fuera del alcance del patrón UoW.

## Decisions

### 1. BaseRepository como capa común
- El repositorio base recibe la sesión del UoW y expone `add`, `save`, `get_by_id`, `get_one`, `list`, `remove`, `flush`.
- Si la sesión no existe, falla con un error explícito para evitar accesos sin transacción.

### 2. SoftDeleteRepository para entidades con borrado lógico
- Los modelos con `borrado_en` heredan de `SoftDeleteRepository`.
- `list_active` y `get_active_by_id` filtran por `borrado_en IS NULL`.
- `soft_delete()` actualiza la fecha bastando con `flush()` lateral; la confirmación va al UoW.

### 3. UnitOfWork como transacción de dominio
- `UnitOfWork` crea y sostiene la sesión de SQLAlchemy.
- Se responsabiliza por `commit()`, `rollback()`, `flush()` y cierre de sesión.
- Cada repositorio del dominio se asocia a la misma sesión y se registra en la instancia del UoW.

### 4. Domain-specific UoW wrappers
- `UsuarioUnitOfWork`, `ClienteUnitOfWork`, `RepuestoUnitOfWork` y `OrdenUnitOfWork` exponen los repositorios del dominio con una sesión compartida.
- Esto reduce la duplicación de acceso a `session` y fija un punto único de transacción para cada módulo.

### 5. `get_uow()` en la capa de infraestructura
- `app/core/database.py` ofrece un factory de `UnitOfWork` para que servicios o dependencias puedan crear un bloque transaccional sin manipular el engine directamente.

## Risks / Trade-offs
- [Risk: Cambio de servicio directo a UoW en varios módulos] → Mitigation: el cambio se mantiene en la capa base y módulo, sin reescribir toda la lógica de negocio a la vez.
- [Risk: errores de sesión sin UoW] → Mitigation: `BaseRepository` valida la sesión activa y falla con un mensaje claro.
- [Risk: commit accidental en repositorio] → Mitigation: límites explícitos y convención documentada en la capa base.
