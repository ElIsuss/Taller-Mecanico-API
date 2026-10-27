# Flujos Principales

Cada flujo se documenta extremo a extremo, mostrando interacciones entre componentes.

## Flujo 1: Auto-registro de cliente

**Disparador**: Cliente nuevo se registra en la web  
**Actor**: Cliente

**Pasos**:
1. Cliente envía `POST /auth/registro` con datos de usuario, documento y ficha de cliente
2. Router valida la entrada (pydantic) y deriva al Service de autenticación
3. Service verifica que el documento no pertenezca ya a un cliente del taller (409 si es así)
4. UoW abre transacción: crea usuario, asigna rol CLIENTE, crea ficha de cliente
5. Si todo OK, confirma la transacción; si falla algo, revierte todo (RN-02)

**Diagrama de secuencia**:
```
Cliente → API (/auth/registro) → Service → UoW → Repository → DB
                                    ← transacción atómica ←
```

**Casos de error**:
- Documento ya es de un cliente del taller → 409, no se apropia de la ficha (RN-02)

---

## Flujo 2: Login y autenticación

**Disparador**: Usuario intenta iniciar sesión  
**Actor**: Cualquier usuario registrado

**Pasos**:
1. Usuario envía `POST /auth/login` con correo y contraseña
2. Service verifica intentos fallidos (mismo correo, misma IP, 60 s): si ≥ 5, responde 429 sin verificar la contraseña (RN-08)
3. Service responde igual exista o no el correo, y tarda igual (RN-09)
4. Si las credenciales son válidas, genera JWT y lo establece en cookie `access_token` (`HttpOnly`, `SameSite=Lax`)
5. Un login correcto reinicia la cuenta de intentos fallidos

**Casos de error**:
- 5 intentos fallidos → 429 con Retry-After (RN-08)
- Credenciales inválidas → 401 genérico (no revela si el correo existe, RN-09)

---

## Flujo 3: Apertura de orden de trabajo

**Disparador**: Recepción recibe un vehículo para reparación  
**Actor**: Recepción (RECEPCION)

**Pasos**:
1. Recepción da de alta (o consulta) cliente y vehículo
2. Recepción envía `POST /ordenes` con la falla del cliente y los ítems de repuestos (al menos uno)
3. Router valida que haya ítem mínimo y sin repuestos repetidos (RN-10)
4. Service copia el precio de cada repuesto al ítem y calcula el total en el servidor (RN-10)
5. La orden nace en estado PENDIENTE (catálogo `estado_orden`, RN-19)

**Casos de error**:
- Orden sin ítems o con repuestos repetidos → 400 (RN-10)

---

## Flujo 4: Inicio y terminación de orden de trabajo

**Disparador**: Mecánico comienza y termina una reparación  
**Actor**: Mecánico (MECANICO) o Administrador (ADMIN)

**Pasos (inicio)**:
1. Mecánico envía `POST /ordenes/{id}/iniciar`
2. Service verifica que el mecánico tenga la orden asignada y estado PENDIENTE
3. Transición PENDIENTE → EN_REPARACION; el mecánico queda asignado (RN-11)

**Pasos (terminación)**:
1. Mecánico asignado o administrador envía `POST /ordenes/{id}/terminar`
2. UoW abre transacción única:
   a. Descuenta el stock de cada ítem de la orden
   b. Crea un `movimiento_stock` por cada salida
   c. Crea una línea de `historial_estado_orden`
3. Transición EN_REPARACION → TERMINADA (RN-11)
4. Si un repuesto no alcanza, se revierte toda la transacción (ninguna escritura queda, RN-13)

**Casos de error**:
- Stock insuficiente → transacción revertida, error 409 (RN-13)
- Orden no está EN_REPARACION o el mecánico no es el asignado → 403 / 409

---

## Flujo 5: Cancelación de orden de trabajo

**Disparador**: Recepción, administrador o dueño del vehículo cancela una orden  
**Actor**: Recepción / Administrador / Cliente (dueño)

**Pasos**:
1. Actor envía `POST /ordenes/{id}/cancelar`
2. Service evalúa primero quién es y qué relación tiene con la orden (permiso, 403 si no corresponde)
3. Service evalúa luego si el estado permite cancelar (solo PENDIENTE; terminada → 409)
4. Transición PENDIENTE → CANCELADA (RN-11)

**Casos de error**:
- No tiene permiso sobre la orden → 403 (RN-12)
- Orden ya terminada → 409 (RN-12)
- El permiso se evalúa antes que el estado (RN-12)

---

## Flujo 6: Cambio de precio de repuesto y reposición de stock

**Disparador**: Administrador actualiza precio o repone stock  
**Actor**: Administrador (ADMIN)

**Pasos (precio)**:
1. Administrador envía `PATCH /repuestos/{id}` con nuevo precio
2. Si el precio cambió, UoW abre transacción: actualiza precio + crea línea en `historial_precio_repuesto` (RN-20)
3. Si el precio no cambió, no se deja línea (RN-20)

**Pasos (stock)**:
1. Administrador registra una reposición (movimiento_stock de tipo reposición)
2. El stock solo cambia por movimientos, nunca por PATCH directo (RN-14)

**Casos de error**:
- Repuesto dado de baja no se usa en órdenes nuevas (RN-16)
