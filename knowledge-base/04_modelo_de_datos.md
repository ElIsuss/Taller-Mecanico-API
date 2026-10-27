# Modelo de Datos

## Dominios

- **Seguridad / identidad**: usuarios, roles, asignaciones de rol con vigencia, sesiones (JWT en cookie), intentos fallidos de login.
- **Clientes y vehículos**: fichas de cliente, vehículos vinculados a cliente.
- **Catálogo de repuestos y stock**: repuestos, precios, movimientos de stock, historial de precios.
- **Órdenes de trabajo**: órdenes, ítems de repuesto, estados de orden (catálogo), historial de cambios de estado.

## ERD (Entity Relationship Diagram)

```
usuario 1:N rol_asignacion     (un usuario tiene asignaciones de rol)
rol 1:N rol_asignacion         (un rol puede asignarse a varios usuarios)
cliente 1:N vehiculo           (un cliente tiene varios vehículos)
vehiculo 1:N orden_trabajo     (un vehículo tiene varias órdenes)
orden_trabajo 1:1 estado_orden (estado actual, vía catálogo estado_orden)
orden_trabajo 1:N orden_item   (una orden tiene varios ítems)
repuesto 1:N orden_item        (un repuesto aparece en varios ítems)
repuesto 1:N movimiento_stock  (alta, reposición, terminación)
repuesto 1:N historial_precio_repuesto (cambios de precio)
orden_trabajo 1:N historial_estado_orden (cambios de estado de la orden)
```

## Entidades

### usuario
- Atributos: id (PK), email (único vigente), documento, password_hash, password_cambiada_en, fecha_alta, fecha_baja
- Relaciones: 1:N rol_asignacion
- Constraints: email único entre los vigentes (RN-01)
- Índices: único parcial sobre email vigente

### rol
- Atributos: id (PK), nombre (RECEPCION, MECANICO, ADMIN, CLIENTE)
- Relaciones: 1:N rol_asignacion

### rol_asignacion (asignación de rol con vigencia)
- Atributos: id (PK), usuario_id (FK), rol_id (FK), vigente_desde, vigente_hasta (NULL = vigente)
- Constraints: un usuario tiene a lo sumo una asignación abierta por rol (RN-03)

### cliente
- Atributos: id (PK), documento (único vigente), nombre, apellido, fecha_alta, fecha_baja
- Constraints: documento único entre los vigentes (RN-01)

### vehiculo
- Atributos: id (PK), cliente_id (FK), patente (única vigente), marca, modelo, anio, fecha_alta, fecha_baja
- Constraints: patente única entre los vigentes (RN-01); un vehículo con órdenes abiertas no se da de baja (RN-16)
- Índices: único parcial sobre patente vigente

### repuesto
- Atributos: id (PK), codigo (único vigente), nombre, descripcion, precio, stock, fecha_alta, fecha_baja
- Constraints: código único entre los vigentes (RN-01); el stock solo cambia por movimientos (RN-14)
- Índices: único parcial sobre código vigente

### estado_orden (catálogo de estados)
- Atributos: id (PK), nombre (PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA)
- Constraints: solo lectura desde la API; no se edita desde ella (RN-19)

### orden_trabajo
- Atributos: id (PK), vehiculo_id (FK), estado_orden_id (FK), mechanico_asignado_id (FK opcional), total, fecha_apertura, fecha_inicio, fecha_terminacion, fecha_cancelacion
- Constraints: nace PENDIENTE con al menos un ítem (RN-10); transiciones PENDIENTE → EN_REPARACION → TERMINADA, PENDIENTE → CANCELADA (RN-11)

### orden_item
- Atributos: id (PK), orden_id (FK), repuesto_id (FK), cantidad, precio_unitario (copia del repuesto al crear)
- Constraints: no repuestos repetidos en una orden (RN-10); el precio de cada ítem se copia del repuesto (RN-10)

### historial_estado_orden (solo agregado)
- Atributos: id (PK), orden_id (FK), estado_orden_id (FK), fecha_cambio, usuario_id
- Constraints: solo agregado, nadie modifica ni borra filas (RN-15); protegido por disparador de base de datos

### movimiento_stock (solo agregado)
- Atributos: id (PK), repuesto_id (FK), tipo (alta / reposición / terminación), cantidad, fecha, orden_id (FK opcional)
- Constraints: solo agregado (RN-15); el stock solo cambia por movimientos (RN-14)

### historial_precio_repuesto (solo agregado)
- Atributos: id (PK), repuesto_id (FK), precio_anterior, precio_nuevo, fecha_cambio
- Constraints: solo agregado (RN-15, RN-20); deja línea en cada cambio de precio (RN-20); un PATCH que no cambia el precio no deja línea

## Seed data inicial

- Roles obligatorios: RECEPCION, MECANICO, ADMIN, CLIENTE
- Estados de orden obligatorios: PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA
- Usuario administrador inicial (credenciales via variables de entorno, nunca en código)
- Repuestos de ejemplo del catálogo inicial
