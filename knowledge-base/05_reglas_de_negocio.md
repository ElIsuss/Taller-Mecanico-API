# Reglas de Negocio

Cada regla tiene un código único `RN-XX-NN` para trazabilidad.

## Dominio: Unicidad (RN-01)

- **RN-01**: Unicidad de email, documento, patente y código entre los vigentes (correo de usuario, documento de cliente, patente de vehículo y código de repuesto, solo entre los que no están dados de baja).

## Dominio: Auto-registro de clientes (RN-02)

- **RN-02**: El auto-registro crea el usuario, su rol CLIENTE y su ficha de cliente: o quedan las tres filas, o ninguna. Si el documento ya es de un cliente del taller, el registro da 409 y no se apropia de esa ficha.

## Dominio: Usuarios, roles y autorización (RN-03 a RN-05)

- **RN-03**: Un usuario tiene a lo sumo una asignación abierta por rol.
- **RN-04**: Los permisos se deciden con los roles vigentes en la base, en cada petición. Los roles que trae el token son informativos. (401 vs 403)
- **RN-05**: Un administrador no puede revocarse su propio rol ADMIN (responde 409), y el sistema nunca queda sin administradores vigentes.

## Dominio: Cambio de contraseña y sesiones (RN-06 a RN-09)

- **RN-06**: Mientras un usuario tenga el cambio de contraseña pendiente, solo puede usar las rutas de `/auth` y las de salud.
- **RN-07**: Al cambiar la contraseña, las sesiones emitidas antes dejan de valer, aunque sean del mismo segundo que el cambio; la sesión que entrega el propio cambio sí vale. La comparación de `iat` (issued at) del token vs `password_cambiada_en` se hace sin truncar a segundos.
- **RN-08**: Después de 5 intentos fallidos con el mismo correo desde la misma IP en 60 segundos, el login responde 429 sin verificar la contraseña. Un login correcto reinicia la cuenta.
- **RN-09**: El login responde igual, y tarda lo mismo, exista o no el correo.

## Dominio: Órdenes de trabajo (RN-10 a RN-13)

- **RN-10**: Una orden nace PENDIENTE con al menos un ítem y sin repuestos repetidos. El precio de cada ítem se copia del repuesto, y el total lo calcula el servidor.
- **RN-11**: Las transiciones de una orden son PENDIENTE → EN_REPARACION (la inicia un mecánico, que queda asignado), EN_REPARACION → TERMINADA (la termina el mecánico asignado o un administrador) y PENDIENTE → CANCELADA.
- **RN-12**: Cancelan una orden la recepción, el administrador o el dueño del vehículo. El permiso se evalúa antes que el estado. Una orden ya terminada no se puede cancelar (409).
- **RN-13**: Terminar una orden descuenta el stock de cada ítem, deja un movimiento por cada salida y una línea de historial. Si un repuesto no alcanza, no queda ninguna de esas escrituras (transacción única).

## Dominio: Stock y repuestos (RN-14, RN-20)

- **RN-14**: El stock de un repuesto solo cambia a través de movimientos: el alta con stock inicial, la reposición y la terminación de órdenes. No se edita por PATCH.
- **RN-20**: Cada cambio del precio de un repuesto deja una línea en `historial_precio_repuesto`, en la misma transacción que el cambio. Un PATCH que no cambia el precio no deja línea.

## Dominio: Solo agregado y borrado lógico (RN-15, RN-16)

- **RN-15**: `historial_estado_orden`, `movimiento_stock` y `historial_precio_repuesto` son de solo agregado: nadie puede modificar ni borrar sus filas. Protegido por disparador de base de datos.
- **RN-16**: Un vehículo o un repuesto dado de baja deja de aparecer y no se puede usar en órdenes nuevas, pero sus datos se conservan. Un vehículo con órdenes abiertas no se da de baja.

## Dominio: Acceso propio y seguridad global (RN-17, RN-18)

- **RN-17**: Lo propio solo pide autenticación: un cliente ve sus vehículos y las órdenes de sus vehículos, y ninguna otra.
- **RN-18**: Ningún error devuelve al cliente texto interno de la base. Ninguna entrada inválida termina en un 500.

## Dominio: Catálogo de estados de orden (RN-19)

- **RN-19**: Los estados posibles de una orden son las filas del catálogo `estado_orden`. El catálogo se consulta desde la API y no se edita desde ella.
