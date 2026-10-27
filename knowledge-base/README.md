# Taller Mecanico — API — Base de Conocimiento

Base de conocimiento generada a partir de los documentos del proyecto (`docs/discovery/informe_discovery.md` y la sección `discovery` de nivel superior de `.active-orchestrator-state.json`).

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance v1.0, fuera de alcance, métricas de éxito |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack tecnológico, arquitectura general, integraciones, endpoints principales |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, matriz RBAC de permisos, rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Dominios, ERD, entidades, atributos, constraints, índices, seed data |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-01 a RN-20 agrupadas por dominio |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas e historias de usuario (US-001 a US-016) con criterios de aceptación |
| [07_flujos_principales.md](07_flujos_principales.md) | Flujos extremo a extremo: registro, login, apertura de orden, inicio/terminación, cancelación, precio/stock |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, estructura de directorios, seguridad, variables de entorno |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones documentadas (DD-01 a DD-05) y supuestos inferidos (SU-01 a SU-04) |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias, preguntas abiertas priorizadas, campos de discovery |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

API REST asíncrona (Python 3.12, FastAPI 0.111, SQLModel/SQLAlchemy 2.0 async, PostgreSQL 16) para un taller mecánico. Gestiona clientes, vehículos, repuestos y órdenes de trabajo con autenticación bcrypt + JWT en cookie HttpOnly, autorización por roles vigentes en la base (RECEPCION, MECANICO, ADMIN, CLIENTE), transacciones Unit of Work, borrado lógico, tablas de solo agregado protegidas por disparador de base, y migraciones con Alembic. Las 20 reglas de negocio (RN-01 a RN-20) rigen todo el dominio.

## Tabla resumen de la KB generada

| Archivo | Líneas (aprox.) | Temas cubiertos |
|---------|-----------------|-----------------|
| 01_vision_y_objetivos.md | 41 | Propósito, objetivos por actor, alcance v1.0, fuera de alcance, métricas de éxito |
| 02_descripcion_general.md | 39 | Stack tecnológico, arquitectura general, integraciones externas, endpoints por recurso |
| 03_actores_y_roles.md | 29 | Actores del sistema, matriz RBAC, rutas públicas |
| 04_modelo_de_datos.md | 84 | Dominios, ERD, entidades con atributos/constraints/índices, seed data |
| 05_reglas_de_negocio.md | 50 | RN-01 a RN-20 agrupadas por dominio |
| 06_funcionalidades.md | 197 | 7 épicas, 16 historias de usuario con criterios de aceptación y reglas relacionadas |
| 07_flujos_principales.md | 121 | 6 flujos extremo a extremo con pasos, diagramas ASCII y casos de error |
| 08_arquitectura_propuesta.md | 53 | Patrones aplicados, estructura de directorios, seguridad, variables de entorno |
| 09_decisiones_y_supuestos.md | 64 | 5 decisiones documentadas (DD-01 a DD-05), 4 supuestos inferidos (SU-01 a SU-04) |
| 10_preguntas_abiertas.md | 17 | Inconsistencias, 3 preguntas abiertas priorizadas, campos de discovery |
| README.md | 47 | Índice, Quick Start, resumen ejecutivo, tabla resumen |
