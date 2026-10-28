# Modelo de Datos

> Esquema alineado al enunciado del TP (Cap1a6): los nombres de tablas y columnas son obligatorios. Se pueden agregar columnas, pero no quitar ni renombrar las definidas.

## Dominios

- **Seguridad / identidad**: usuarios, asignaciones de rol con vigencia, intentos de acceso, eventos de seguridad.
- **Clientes y vehículos**: fichas de cliente, vehículos vinculados a cliente.
- **Catálogo de repuestos y stock**: repuestos, precios, movimientos de stock, historial de precios.
- **Órdenes de trabajo**: órdenes, ítems de repuesto, estados de orden (catálogo), historial de cambios de estado.

## ERD (Entity Relationship Diagram)

```
usuario 1:N asignacion_rol         (un usuario tiene asignaciones de rol)
cliente 1:1 usuario                (cliente.usuario_id, opcional y único)
cliente 1:N vehiculo               (un cliente tiene varios vehículos)
vehiculo 1:N orden_trabajo         (un vehículo tiene varias órdenes)
usuario 1:N orden_trabajo          (mecánico asignado, opcional)
estado_orden 1:N orden_trabajo     (estado actual, FK a estado_orden.codigo)
orden_trabajo 1:N item_orden       (una orden tiene varios ítems)
repuesto 1:N item_orden            (un repuesto aparece en varios ítems)
repuesto 1:N movimiento_stock      (alta, reposición, terminación)
repuesto 1:N historial_precio_repuesto (cambios de precio)
orden_trabajo 1:N historial_estado_orden (cambios de estado de la orden)
estado_orden 1:N historial_estado_orden  (desde_estado y hasta_estado)
usuario 1:N intento_acceso / evento_seguridad / historiales
```

## Entidades

Convenciones: fechas `timestamptz`; dinero `NUMERIC` mapeado a `Decimal` (nunca `float`); cada FK con índice.

### usuario
- Atributos: id (PK), email (UNIQUE, obligatorio), nombre, password_hash, activo, debe_cambiar_password, password_cambiada_en (timestamptz nullable)
- Constraints: email único (RN-02)
- Relaciones: 1:N `asignacion_rol`, 1:1 opcional con `cliente`, 1:N órdenes asignadas e historiales

### asignacion_rol
- Atributos: id (PK), usuario_id (FK), rol (CHECK: ADMIN, RECEPCION, MECANICO, CLIENTE), desde, vence_en (nullable), revocada_en (nullable), otorgada_por (FK usuario, nullable)
- Constraints: un usuario tiene a lo sumo una asignación no revocada por rol (RN-03)
- Índices: `ix_asignacion_rol_usuario_rol_uc` único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`; índices sobre `usuario_id` y `otorgada_por`

### intento_acceso
- Atributos: id (PK), cuando, email, ip, exito
- Índices: `ix_intento_acceso_email_ip_cuando (email, ip, cuando)` para el límite de intentos (RN-08)

### evento_seguridad
- Atributos: id (PK), cuando, actor, accion
- Uso: bitácora de auditoría de acciones sensibles

### cliente
- Atributos: id (PK), usuario_id (FK nullable, UNIQUE), nombre, documento (UNIQUE), telefono
- Constraints: documento único; un usuario se vincula a lo sumo a un cliente
- Sin borrado lógico

### vehiculo
- Atributos: id (PK), cliente_id (FK), patente, marca, modelo, anio, borrado_en (timestamptz nullable)
- Constraints: `1950 <= anio <= 2100`; patente única entre vigentes (RN-01); un vehículo con órdenes abiertas no se da de baja (RN-16, capa de servicio)
- Índices: `ix_vehiculo_patente_uc` único parcial `WHERE borrado_en IS NULL`; índice sobre `cliente_id`

### repuesto
- Atributos: id (PK), codigo, descripcion, precio `NUMERIC(10,2)`, stock, borrado_en (timestamptz nullable)
- Constraints: `precio > 0`; `stock >= 0`; código único entre vigentes (RN-01); el stock solo cambia por movimientos (RN-14)
- Índices: `ix_repuesto_codigo_uc` único parcial `WHERE borrado_en IS NULL`

### estado_orden (catálogo de estados)
- Atributos: codigo (PK), descripcion, posicion (UNIQUE), es_final
- Valores esperados: PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA
- Constraints: solo lectura desde la API (RN-19); posiciones únicas

### orden_trabajo
- Atributos: id (PK), vehiculo_id (FK), mecanico_id (FK usuario, nullable), estado (FK `estado_orden.codigo`), falla, creada_en, total `NUMERIC(12,2)`
- Constraints: `total >= 0`; nace en el estado inicial con al menos un ítem (RN-10); transiciones PENDIENTE → EN_REPARACION → TERMINADA y PENDIENTE → CANCELADA (RN-11)
- Índices: `vehiculo_id`, `mecanico_id`, `estado`

### item_orden
- Atributos: id (PK), orden_id (FK), repuesto_id (FK), cantidad, precio_unitario `NUMERIC(10,2)`
- Constraints: `cantidad > 0`; `precio_unitario > 0`; UNIQUE `(orden_id, repuesto_id)` (RN-10); el precio se copia del repuesto al crear
- Índices: `orden_id`, `repuesto_id`

### historial_estado_orden (solo agregado)
- Atributos: id (PK), orden_id (FK), desde_estado (FK nullable), hasta_estado (FK), usuario_id (FK), cuando
- Constraints: solo agregado (RN-15), protegido por disparador; `desde_estado` nulo en la creación
- Índices: todas las FKs

### movimiento_stock (solo agregado)
- Atributos: id (PK), repuesto_id (FK), orden_id (FK nullable), usuario_id (FK), cantidad, motivo, cuando
- Constraints: `cantidad <> 0`; solo agregado (RN-15); el stock solo cambia por movimientos (RN-14)
- Índices: todas las FKs

### historial_precio_repuesto (solo agregado)
- Atributos: id (PK), repuesto_id (FK), usuario_id (FK), precio_anterior `NUMERIC(10,2)`, precio_nuevo `NUMERIC(10,2)`, cuando
- Constraints: `precio_nuevo > 0`; `precio_nuevo <> precio_anterior`; solo agregado (RN-15, RN-20)
- Índices: `repuesto_id`, `usuario_id`

## Protección de tablas de solo agregado (RN-15)

Migración escrita a mano: función `fn_rechazar_update_delete_solo_agregado()` y un trigger `BEFORE UPDATE OR DELETE` por tabla (`historial_estado_orden`, `movimiento_stock`, `historial_precio_repuesto`). `INSERT` está permitido. Los statements no llevan `;` final porque asyncpg rechaza el terminador.

## Seed data inicial

- Estados de orden obligatorios: PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA (catálogo `estado_orden`)
- Roles válidos: ADMIN, RECEPCION, MECANICO, CLIENTE (CHECK, no tabla)
- Usuario administrador inicial (credenciales via variables de entorno, nunca en código)
- Repuestos de ejemplo del catálogo inicial
