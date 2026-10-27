# Taller Mecanico — API — Instrucciones para Agentes

## Stack Tecnológico

| Capa | Tecnologías | Versión mínima |
|------|-------------|----------------|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI | 0.111 |
| ORM / Modelo | SQLModel, SQLAlchemy 2.0 async | 0.0.24 / 2.0 |
| Controlador de base de datos | asyncpg | — |
| Base de datos | PostgreSQL | 16 |
| Migraciones | Alembic | 1.13 |
| Configuración | pydantic-settings | 2.0 |
| Hash de contraseñas | bcrypt | 4.0 |
| Tokens | PyJWT | 2.8 |
| Servidor ASGI | uvicorn | — |

Arquitectura: API REST monolítica en capas, sin frontend propio. Cada petición atraviesa: Router → Service → Unit of Work → Repository → Model. Los tokens JWT viajan únicamente en la cookie `access_token` con `HttpOnly`, `SameSite=Lax`; nunca en el cuerpo ni leídos del encabezado `Authorization`.

Reglas globales ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las hereda. Acá viven solo las reglas específicas de este proyecto + las universales que el global no cubre.

## Base de Conocimiento

| Archivo | Contenido |
|---------|-----------|
| [knowledge-base/01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance v1.0, fuera de alcance, métricas de éxito |
| [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack tecnológico, arquitectura general, integraciones externas, endpoints por recurso |
| [knowledge-base/03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Actores del sistema, matriz RBAC de permisos, rutas públicas |
| [knowledge-base/04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Dominios, ERD, entidades, atributos, constraints, índices, seed data |
| [knowledge-base/05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | RN-01 a RN-20 agrupadas por dominio |
| [knowledge-base/06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Épicas e historias de usuario (US-001 a US-016) con criterios de aceptación |
| [knowledge-base/07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos extremo a extremo: registro, login, apertura de orden, inicio/terminación, cancelación, precio/stock |
| [knowledge-base/08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones aplicados, estructura de directorios, seguridad, variables de entorno |
| [knowledge-base/09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones documentadas (DD-01 a DD-05) y supuestos inferidos (SU-01 a SU-04) |
| [knowledge-base/10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Inconsistencias, preguntas abiertas priorizadas, campos de discovery |

## Skills Disponibles

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| Backend Core | FastAPI/SQLModel/UoW | `fastapi`, `fastapi-python`, `fastapi-expert`, `sqlalchemy` |
| Backend Datos/Integridad | PostgreSQL/Alembic/migrations | `alembic`, `sqlalchemy` |
| Orquestación | OPSX/SDD | `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-registry` |

Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Rutas relativas al proyecto: `.agents/skills/fastapi`, `.agents/skills/fastapi-python`, `.agents/skills/fastapi-expert`, `.agents/skills/python-backend`, `.agents/skills/sqlalchemy`, `.agents/skills/alembic`.

## Roadmap de Changes

Proyecto: **Taller Mecanico — API**  
Total: 8 changes · 100 puntos · 4 fases · 4 gates de paralelismo · camino crítico de 5 changes.

**Camino crítico:** `C-01 → C-02 → C-03 → C-06 → C-08` (y `C-07` como alternativa final del camino crítico).

**Paralelismo por fase:**

| Gate | Changes | Agentes sugeridos |
|------|---------|-------------------|
| GATE 0 | C-01 proyecto-configuracion-ciclo-vida (8 pts) | A — Backend Core |
| GATE 1 | C-02 modelos-relaciones-migraciones (14 pts) | A — Backend Core |
| GATE 2 | C-03 contratos-y-crud (10 pts) / C-04 autenticacion (16 pts) | A / B — Backend Auth |
| GATE 3 | C-05 autorizacion (14 pts) / C-06 repositorios-y-unit-of-work (20 pts) | B / C — Backend Datos |
| GATE 4 | C-07 integridad-solo-agregado-intento-acceso (10 pts) / C-08 lecturas-sin-n1-y-asincronia (8 pts) | C / A |

**Primer change recomendado:** `C-01-proyecto-configuracion-ciclo-vida` — arrancar con `/opsx:propose C-01-proyecto-configuracion-ciclo-vida`.

Ver `CHANGES.md` en la raíz para el detalle completo de cada change, dependencias, gobernanza y punteros "Leer antes".

## Reglas Duras (específicas del proyecto)

Reglas confirmadas derivadas del stack (Python 3.12 + FastAPI 0.111):

1. **snake_case** para variables, funciones, nombres de archivos y directorios.
2. **Type hints** en todas las firmas de función (Pydantic V2, SQLAlchemy 2.x `Mapped[...]`).
3. **Pydantic `extra='forbid'`** en contratos de entrada: ningún endpoint acepta campos no declarados (evita registro con rol y edición de stock por PATCH).
4. **`async def` para operaciones de I/O**, `def` solo para código bloqueante (que corre en threadpool).
5. **Sin llamadas bloqueantes** en el hilo de eventos (bcrypt corre fuera del bucle con `to_thread` + semáforo).
6. **Carga perezosa prohibida**: toda relación que se lee se precarga en el repositorio (`lazy="raise"` para detectar olvidos).
7. **Ningún repositorio confirma (`commit`)**: solo `flush()`. El Unit of Work confirma al salir del bloque.
8. **No usar `create_all`**: el esquema se crea exclusivamente con Alembic (migraciones `autogenerate` + escritas a mano).
9. **Tokens solo en cookie `access_token`** con `HttpOnly`, `SameSite=Lax`, `Max-Age`; nunca en el cuerpo ni leídos del encabezado `Authorization`.
10. **`.env` no se versiona**: `env.example` sin secretos; credenciales y clave de firma nunca en el código.

## Flujo de Trabajo

`KB (knowledge-base/)` → `CHANGES.md` → `/opsx:propose <change>` → `/opsx:apply <change>` → `/opsx:archive <change>`

Antes de ejecutar cualquier `/opsx:propose`, leer `CHANGES.md` y los punteros "Leer antes" de la knowledge-base indicados en el change.
