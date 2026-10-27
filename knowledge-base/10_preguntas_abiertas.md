# Preguntas Abiertas

## Inconsistencias detectadas

No se detectaron inconsistencias entre los documentos fuente (el informe de discovery y la sección `discovery` de nivel superior de `.active-orchestrator-state.json` coinciden en alcance, roles, reglas de negocio y stack).

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|-----------|----------|---------|---------|
| Alta | ¿Soporte para múltiples mecánicos por orden, o siempre uno asignado? | Sprint 1 (asignación de mecánicos en órdenes) | Product Owner |
| Media | ¿Los avisos por `BackgroundTasks` son suficientes o se necesitarán colas Redis en el futuro? | Sprint 3 (notificaciones al cliente) | Equipo técnico |
| Baja | ¿El alcance es un solo taller o una cadena de talleres (multi-tenant)? | Lanzamiento (aislamiento de datos) | Tech Lead |

## [DISCOVERY] Campos inferidos con baja confianza

Ninguno. Todos los seis campos de `kb.discovery` pudieron inferirse con confianza desde los documentos fuente y la sección `discovery` de nivel superior del estado del orchestrador.
