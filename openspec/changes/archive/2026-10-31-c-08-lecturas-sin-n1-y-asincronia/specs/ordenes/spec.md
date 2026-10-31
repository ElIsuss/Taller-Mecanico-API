# Spec Delta: ordenes (C-08 Lecturas sin N+1 y Asincronía)

## Purpose
Optimizar las lecturas del detalle de órdenes para evitar problemas N+1 mediante precarga (`selectinload`) y delegar los avisos al cliente a tareas en segundo plano (`BackgroundTasks`).

## ADDED Requirements

### Requirement: Lecturas de detalle sin N+1
El sistema SHALL precargar las relaciones de `orden_trabajo` (`items`, `items.repuesto`, `vehiculo.cliente`, `historial_estados`) utilizando `selectinload` en el repositorio para garantizar un número constante y predecible de consultas a la base de datos independientemente de la cantidad de ítems.

#### Scenario: Detalle de orden con cantidad variable de ítems
- **WHEN** se consulta el detalle de una orden de trabajo con 2 o con 4 ítems
- **THEN** la base de datos ejecuta la misma cantidad fija de consultas SQL

### Requirement: Avisos asíncronos en segundo plano
El sistema SHALL programar un aviso al cliente mediante `BackgroundTasks` al finalizar o cancelar una orden de trabajo, registrando el evento en el log (`taller.avisos`) fuera del ciclo de respuesta HTTP.

#### Scenario: Aviso al terminar o cancelar orden
- **WHEN** una orden pasa a estado `TERMINADA` o `CANCELADA`
- **THEN** se programa una tarea en segundo plano que emite el aviso correspondiente en el log sin bloquear la respuesta al usuario
