# Entrega de implementación TP1 / Sprint 1

El alcance es un incremento funcional de Monitoring + Alert, agente Edge y
API Gateway. Las demás capacidades permanecen en el sistema base. No afirmar
que se implementaron los ocho microservicios, cuatro sprints ni el despliegue
integral 5.4. El documento Word original no fue modificado durante este cierre.

## Qué se puede documentar

| Sección | Material verificable |
|---|---|
| 5.1 | Pruebas Java 21, escenarios Cucumber ejecutados, seis pruebas Python, ArchUnit; biblioteca compartida sin entidades de negocio; refactor parcial de SensorReading; Strangler, outbox, consumidor idempotente y store-and-forward. |
| 5.2 | Rama `codex/tp1-architecture-implementation`, commits reales, Maven por servicio, Java 21/Boot 3.3.13 para extracciones, Java 26/Boot 4 para el base, Docker sin root, esquemas y usuarios separados, workflows preparados. La ejecución remota de CI debe corroborarse en GitHub antes de presentarla como aprobada. |
| 5.3.1.1 Sprint Backlog | US47 recuperación/idempotencia, US46 brechas, US04 estado actual, US16 consulta consolidada de backend, US06 notificación interna durable. Son capacidades implementadas parcialmente; no se realizó interfaz de usuario. El equipo debe confirmar asignaciones, horas y alcance de cada US en Trello. |
| 5.3.1.2 Development | Historial local real, fuentes y cambios a IAM; no atribuir implementación a Alessandro o Renso sin sus commits. |
| 5.3.1.3 Testing | `java21-test-results.json`, reportes de Maven, feature `telemetry.feature`, `python312-docker-tests.txt`, prueba de rollback/idempotencia y evento de cierre desordenado de Alert. |
| 5.3.1.4 Execution | `local-smoke.json`, colección Postman y ejecución `postman-newman.txt`, `edge-recovery.json`, consultas reales de MySQL y recuperación del broker. Video pendiente. |
| 5.3.1.5 Documentation | `openapi-monitoring.json`, `openapi-alert.json`; Swagger local en puertos 18083 y 18084. Los contratos objetivo del pack de Claude incluyen operaciones aún no implementadas y no deben reemplazar estos OpenAPI ejecutables. |
| 5.3.1.6 Deployment | Servicios Docker + MySQL 8 + emulador Pub/Sub realmente ejecutados; `docker-health.json` y configuración Compose. Captura de Google Cloud pendiente. |
| 5.3.1.7 Collaboration | Commits y PR cuando se publique. No hay evidencia validada de contribuciones de otros integrantes en este incremento. |
| 5.3.1.8 Kanban | Tablero indicado por el usuario: https://trello.com/b/6a963a0f21f9470e710e1f76 . Falta acceso/captura; se omite el token privado de invitación. |

## Resultados observados

La prueba local Edge usó 50 sensores con intervalo de 10 segundos y retuvo
envíos durante 300 segundos. Acumuló 1.500 lecturas pendientes; el búfer se
vació 3,234 segundos después de permitir los envíos. A los 330,046 segundos
se habían generado y aceptado 1.650 lecturas, con cero duplicados y pendientes.
La consulta de MySQL, incluyendo siete lecturas de otras pruebas, registró
1.657 filas y 50 dispositivos, cero claves duplicadas y cero eventos pendientes.
Esto demuestra esa ejecución local, no una garantía de SLA cloud.

La interrupción real del emulador permitió aceptar ingesta con HTTP 202,
retener el evento en outbox y publicarlo al recuperar el broker. El consumidor
generó una incidencia para ese evento. El emulador es efímero: hubo que recrear
sus tópicos tras reiniciarlo.

Postman/Newman ejecutó ocho peticiones y nueve aserciones sin fallos. El tiempo
medio de esas solicitudes no equivale al benchmark sostenido de QA02.

## Diferencias y pendientes arquitectónicos

- La desviación actual es instantánea y WARNING; aún falta acordar y aplicar
  la política de duración/tolerancia y severidad completa.
- La notificación es IN_APP/AVAILABLE persistida; no se enviaron emails/SMS.
- No están implementados acknowledge/assign, undo ni SSE del contrato objetivo.
- `incident.opened` se guarda en outbox de Alert, pero todavía no se publica.
- Réplicas de dispositivos y rangos son fixtures locales explícitos; no existe
  todavía el consumidor de `asset.settings-changed`.
- El publicador y receptor actuales funcionan con el emulador local. Para cloud
  faltan autenticación del publicador y validación OIDC del push.
- QA02 (1.000 sensores y percentiles) y QA03 (estudio con participantes) pendientes.
- No se migró el historial de datos del curso anterior a los nuevos esquemas.
- Los PNG del handoff original son diagramas de diseño, no capturas de despliegue;
  permanecen en el ZIP original y en la copia local, no se versionan otra vez.

Consultar `docs/architecture/SPRINT1_REVIEW.md` para las correcciones justificadas
al pack y `sprint1/coldtrace-infrastructure/CLOUD_PREPARATION.md` para nombres
propuestos, cuotas gratuitas y límites. No se creó ningún recurso facturable.

Los seis directorios preparados para repositorios independientes están en
`C:/Users/david/IdeaProjects/coldtrace-sprint1-repositories`. Los seis componentes
ya están publicados en Veltis-Software desde David-std2, en la rama
`codex/tp1-import`, con PR #1 de cada repositorio. El repositorio consolidado
también tiene PR #1, rama `codex/tp1-architecture-implementation`. Los PRs están
en borrador y no se fusionaron. El tag `v0.1.0-sprint1` de coldtrace-shared
conserva la revisión exacta fijada por los consumidores. Para ejecutar antes
de fusionar, clonar expresamente las ramas indicadas. Consultar
`repository-publication.json` y las ejecuciones de GitHub para el estado de CI.
