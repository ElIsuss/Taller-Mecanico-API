# repositorios-unit-of-work Specification

## Purpose
Definir la capa de repositorios y Unit of Work del proyecto para encapsular el acceso a datos, centralizar transacciones y mantener la regla de negocio de que los repositorios no hagan commits.

## Requirements

### Requirement: Repositorio genérico con sesión inyectada
El sistema SHALL exponer una clase base `BaseRepository` que reciba la sesión de SQLAlchemy y permita CRUD básico con `flush()` como persistencia intermedia.

#### Scenario: Repositorio sin sesión activa
- **WHEN** un repositorio intenta ejecutar una operación sin una sesión vinculada
- **THEN** el sistema lanza una excepción explícita indicando que la sesión no está disponible

#### Scenario: Persistencia intermedia
- **WHEN** un servicio agrega una entidad a través del repositorio
- **THEN** la entidad queda asociada a la sesión y solo se persiste con `flush()` antes del commit del UoW

### Requirement: Soporte de borrado lógico en repositorios
El sistema SHALL ofrecer `SoftDeleteRepository` para entidades con `borrado_en`, ocultando por defecto las filas eliminadas lógicamente y permitiendo `soft_delete()` sin commit.

#### Scenario: Registro activo consultado por ID
- **WHEN** un modelo soporta borrado lógico y se consulta por ID
- **THEN** solo se devuelve la fila activa si `borrado_en` es `NULL`

#### Scenario: Eliminación lógica
- **WHEN** una entidad activa se marca como borrada
- **THEN** el campo `borrado_en` se actualiza y la operación queda sujeta al `commit()` del UoW

### Requirement: Unit of Work transaccional por dominio
El sistema SHALL proporcionar un `UnitOfWork` que maneje la sesión, el commit y el rollback, y que asocie los repositorios del dominio a la sesión activa del bloque transaccional.

#### Scenario: Operación exitosa
- **WHEN** una transacción termina sin errores
- **THEN** el `UnitOfWork` ejecuta `commit()` y deja la sesión en estado consistente

#### Scenario: Operación fallida
- **WHEN** una operación dentro del bloque genera una excepción
- **THEN** el `UnitOfWork` ejecuta `rollback()` y elimina la transacción parcialmente aplicada

### Requirement: Repositorios por módulo
El sistema SHALL tener un repositorio concreto por dominio (`usuarios`, `clientes`, `repuestos`, `ordenes`) y un wrapper de `UnitOfWork` por módulo para encapsular la sesión compartida.

#### Scenario: Dominio con repositorios registrados
- **WHEN** un servicio del módulo usuarios, clientes, repuestos u órdenes crea su `UnitOfWork`
- **THEN** el UoW expone los repositorios del dominio asociados a la misma sesión

### Requirement: Regla de no commit en repositorios
El sistema SHALL garantizar que ningún repositorio haga `commit()` por sí mismo y que toda confirmación dependa del `UnitOfWork` que contiene la sesión.

#### Scenario: Transacción multi-acción
- **WHEN** una operación necesita guardar varias entidades en una misma unidad transaccional
- **THEN** la persistencia se resuelve con `flush()` local y la confirmación final ocurre al cerrar el UoW

### Requirement: Servicios transaccionales integrados con repositorios y UoW
El sistema SHALL inyectar un UoW del dominio desde el router, y los servicios SHALL abrirlo con `async with` y realizar el acceso transaccional a datos mediante los repositorios del UoW.

#### Scenario: Operación de negocio exitosa
- **WHEN** un servicio ejecuta una operación transaccional mediante repositorios del UoW
- **THEN** todos los cambios se confirman juntos al salir correctamente del contexto

#### Scenario: Operación de negocio fallida
- **WHEN** una operación de servicio falla antes de completar sus cambios
- **THEN** el UoW revierte toda la transacción y no quedan escrituras parciales

#### Scenario: Modificación de stock
- **WHEN** una operación de negocio aumenta o disminuye el stock
- **THEN** el cambio se realiza a través del registro de un movimiento dentro del mismo UoW
