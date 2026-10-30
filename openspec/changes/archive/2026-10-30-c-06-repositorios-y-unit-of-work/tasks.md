# Tasks: C-06 Repositorios y Unit of Work

## 1. Base de repositorios

- [x] 1.1 Crear `BaseRepository` con sesión inyectada y operaciones CRUD básicas para entidades del dominio.
- [x] 1.2 Implementar `flush()` y validación explícita cuando la sesión no existe.
- [x] 1.3 Crear `SoftDeleteRepository` para entidades con borrado lógico (`borrado_en`).
- [x] 1.4 Definir `UnitOfWork` con commit/rollback, manejo de sesión y cierre seguro.
- [x] 1.5 Exponer `get_uow()` desde `app/core/database.py` para crear blocks transaccionales desde infraestructura.

## 2. Repositorios por módulo

- [x] 2.1 Crear repositorios para `usuarios` (`UsuarioRepository`, `AsignacionRolRepository`).
- [x] 2.2 Crear repositorios para `clientes` (`ClienteRepository`, `VehiculoRepository`).
- [x] 2.3 Crear repositorios para `repuestos` (`RepuestoRepository`, `MovimientoStockRepository`, `HistorialPrecioRepuestoRepository`).
- [x] 2.4 Crear repositorios para `ordenes` (`EstadoOrdenRepository`, `OrdenTrabajoRepository`, `ItemOrdenRepository`, `HistorialEstadoOrdenRepository`).

## 3. Unit of Work por dominio

- [x] 3.1 Crear `UsuarioUnitOfWork` con repositorios asociados a la sesión registrada.
- [x] 3.2 Crear `ClienteUnitOfWork` con repositorios asociados a la sesión registrada.
- [x] 3.3 Crear `RepuestoUnitOfWork` con repositorios asociados a la sesión registrada.
- [x] 3.4 Crear `OrdenUnitOfWork` con repositorios asociados a la sesión registrada.
- [x] 3.5 Asegurar que los repositorios enlazados al UoW compartan la misma transacción y se limpien al cerrar.

## 4. Verificación del patrón

- [x] 4.1 Ejecutar la suite de tests del proyecto para validar que no haya regresión.
- [x] 4.2 Ejecutar `openspec validate c-06-repositorios-y-unit-of-work`.
- [x] 4.3 Confirmar que el repositorio no hace commits y que la transacción queda en la capa UoW.
