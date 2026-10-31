# Design: Lecturas sin N+1 y Asincronía (C-08)

## Arquitectura

El cambio se enmarca en la capa de presentación (routers) y repositorio, sin modificar el modelo de datos ni migraciones.

### 1. Precarga en `OrdenRepository` (`app/modules/ordenes/repository.py`)

```python
async def get_loaded(self, orden_id: int) -> OrdenTrabajo | None:
    return await self.session.exec(
        select(self.model)
        .where(self.model.id == orden_id)
        .options(
            selectinload(OrdenTrabajo.items).selectinload(ItemOrden.repuesto),
            selectinload(OrdenTrabajo.vehiculo).selectinload(Vehiculo.cliente),
            selectinload(OrdenTrabajo.historial_estados),
        )
    ).first()
```

Uso en servicio:
```python
async def _a_read(orden: OrdenTrabajo) -> OrdenRead:
    # Accede a orden.vehiculo.patente, orden.vehiculo.cliente.nombre,
    # item.repuesto.codigo/descripcion, orden.historial_estados
    # sin disparar consultas adicionales.
```

**Resultado**: 8 `SELECT` fijos (incluyendo auth) para cualquier cantidad de ítems.

### 2. Handlers asíncronos sin bloqueos

Todos los endpoints en `app/modules/ordenes/router.py` son `async def`:
- `listar_ordenes`, `obtener_orden`, `crear_orden`, `actualizar_orden`
- `iniciar_orden`, `terminar_orden`, `cancelar_orden`
- `listar_estados`, `obtener_estado`

Las operaciones de bcrypt (`hash_password`, `verify_password`) corren fuera del bucle con `asyncio.to_thread` + `Semaphore(4)` desde `C-04` (`app/core/security.py`). No hay otras llamadas bloqueantes.

### 3. BackgroundTasks para avisos

```python
# app/modules/ordenes/notificaciones.py
logger = logging.getLogger("taller.avisos")

def enviar_aviso_cliente(orden_id: int, cliente: str, estado: str) -> None:
    logger.warning(
        "Aviso enviado al cliente %s: orden %s %s",
        cliente,
        orden_id,
        estado,
    )
```

En router:
```python
async def terminar_orden(
    orden_id: OrdenId,
    data: OrdenAccion,
    uow: OrdenUowDep,
    background_tasks: BackgroundTasks,
) -> OrdenRead:
    orden = await service.terminar_orden(uow, orden_id, data.usuario_id)
    background_tasks.add_task(
        enviar_aviso_cliente, orden.id, orden.cliente, orden.estado
    )
    return orden
```

Mismo patrón para `cancelar_orden`.

### 4. Evidencia y verificación

- **Test de conteo** (`test/test_c08_lecturas.py::test_detalle_orden_consultas_constantes`):
  Crea órdenes con 2 y 4 ítems, usa `sqlalchemy.event` `before_cursor_execute` para contar `SELECT`, verifica igualdad.
- **Test de BackgroundTasks** (`test_aviso_al_terminar`, `test_aviso_al_cancelar`):
  Monkeypatch de `enviar_aviso_cliente`, verifica llamada con argumentos correctos.
- **Evidencia C-12/C-15** (`test/c-12-15-avisos-n1.http`): Archivo ejecutable con login, reponer, terminar, y detalle de órdenes con 2 y 4 ítems.
- **Log de consola** (`uvicorn-c08.log` con `SQL_ECHO=true`): Muestra 8 `SELECT` para `GET /ordenes/3` (2 ítems) y `GET /ordenes/4` (4 ítems), y el aviso `"Aviso enviado al cliente Jorge: orden 2 TERMINADA"` en segundo plano.