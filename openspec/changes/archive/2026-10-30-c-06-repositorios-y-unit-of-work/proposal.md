# Proposal: C-06 Repositorios y Unit of Work

## Why
La arquitectura funcional del proyecto ya establece el flujo Router → Service → UoW → Repository → Model, pero la capa de acceso a datos aún no está implementada de forma consistente. El sistema tiene servicios con acceso directo a `AsyncSession`, lo que dificulta la transacción centralizada, la reutilización por dominio y la separación de responsabilidades que exige el roadmap.

## What Changes
- Crear una capa base de repositorios con sesión inyectada, consultas CRUD tipadas y `flush()` como única operación de persistencia.
- Implementar `UnitOfWork` transaccional para manejar `commit()`, `rollback()`, cierre y unión de repositorios por dominio.
- Agregar repositorios para los módulos de `usuarios`, `clientes`, `repuestos` y `ordenes`, incluyendo soporte de borrado lógico para entidades con `borrado_en`.
- Definir wrapper de UoW por dominio para que las operaciones de negocio se ejecuten dentro de la misma sesión y transacción.
- Inyectar los UoW desde los routers y migrar las operaciones transaccionales de los servicios a los repositorios.
- Centralizar los cambios de stock en la creación de movimientos, incluida la terminación de órdenes.
- Mantener la regla no negociable: los repositorios nunca hacen `commit`, y el `Unit of Work` confirma al cerrar el bloque.

## Capabilities

### New Capabilities
- `repositorios-uow`: abstracción de acceso a datos y transacciones para cada módulo del taller.

### Modified Capabilities
- `app/core/`: base de transacciones y repositories comunes.
- `app/modules/*/repository.py`: repositorios concretos por dominio.
- `app/modules/*/unit_of_work.py`: nuestros wrappers de dominio.

## Impact
- `app/core/repository.py`
- `app/core/unit_of_work.py`
- `app/core/database.py`
- `app/modules/usuarios/repository.py`
- `app/modules/clientes/repository.py`
- `app/modules/repuestos/repository.py`
- `app/modules/ordenes/repository.py`
- `app/modules/*/unit_of_work.py`
- Servicios y routers de los módulos `usuarios`, `clientes`, `repuestos` y `ordenes`.
