# Visión y Objetivos

## Propósito del sistema

Proveer una API REST asíncrona que un taller mecánico use para gestionar su operación diaria: la recepción da de alta clientes y vehículos, abre una orden de trabajo por cada ingreso con la falla que describe el cliente y los repuestos a usar; un mecánico toma la orden, la repara y la da por terminada (descuentando del stock cada repuesto usado); el administrador mantiene el catálogo de repuestos, repone el stock y administra al personal y sus roles; los clientes se registran solos en la web y consultan el estado de sus vehículos.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|-------|-------------------|----------------------|
| Recepción (RECEPCION) | Gestionar el ingreso de clientes, vehículos y aperturas de orden de trabajo | Dar de alta clientes y vehículos; cancelar órdenes de trabajo |
| Mecánico (MECANICO) | Iniciar y terminar órdenes de trabajo asignadas | Descontar el stock de cada repuesto usado al terminar una orden |
| Administrador (ADMIN) | Mantener el catálogo de repuestos, repone stock y administra personal y roles | Asignar y revocar roles del personal; consultar eventos de seguridad |
| Cliente (CLIENTE) | Registrarse solo y consultar el estado de sus vehículos y órdenes | Ver sus propios vehículos y las órdenes de esos vehículos solamente |

## Alcance v1.0

- API asíncrona en capas: Router → Service → UoW → Repository → Model
- Autenticación con contraseñas guardadas con bcrypt y token JWT en cookie HttpOnly
- Autorización basada en roles vigentes en la base de datos en cada petición (401 vs 403)
- CRUD de clientes, vehículos, repuestos y órdenes de trabajo
- Catálogo de estados de orden (PENDIENTE, EN_REPARACION, TERMINADA, CANCELADA)
- Transacciones Unit of Work para operaciones de escritura múltiple (auto-registro, terminación de orden, cambio de precio de repuesto)
- Tablas de solo agregado protegidas por disparador de base de datos
- Borrado lógico para vehículos y repuestos, con índices únicos parciales sobre los vigentes
- Paginación con envoltorio {items, total, page, size, pages}
- Migraciones con Alembic (una generada con autogenerate, una escrita a mano para el disparador de solo agregado)
- seed.py con datos iniciales obligatorios para poner el proyecto en marcha

## Fuera de alcance

- Interfaz de usuario propia (frontend): el sistema es solo API/backend
- Pagos, WhatsApp, calendarios ni APIs de terceros obligatorias
- Colas de tareas con Redis (los avisos al cliente se resuelven con BackgroundTasks)
- Concurrencia avanzada (capítulo 7 — no se evalúa en este TP)

## Métricas de éxito

- El esquema se crea exclusivamente con `alembic upgrade head` sobre una base vacía
- Ninguna entrada inválida termina en un 500; ningún error devuelve texto interno de la base al cliente
- seed.py carga los datos iniciales obligatorios (roles, estados de orden, administrador inicial)
