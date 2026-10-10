# ADR-0013: Deep link y endpoint de detalle de alerta

- **Estado:** Aceptado
- **Fecha:** 2026-10-09
- **Iteración ADD:** Iteración 3 (Usabilidad)
- **Trazabilidad:** DD-14, DD-15 (DC-18, DC-19) · Drivers: QA-03, US33, AC-03

## Contexto
El encargado sin perfil técnico debe llegar a la alerta y entender su contexto sin navegar.

## Decisión
Toda notificación incluye `{WEB_BASE_URL}/alerts/{incidentId}`. `GET /api/v1/alerts/{id}/detail` devuelve en una sola respuesta activo, lectura, rango, estado, acciones permitidas según el rol y `suggestedAssignee` (usuario que reconoció la incidencia más reciente del mismo activo en 30 días; si no existe, el usuario autenticado). Si no hay sesión, el login redirige de vuelta al deep link.

## Consecuencias
Endpoint específico de lectura. Táctica: maintain task model / maintain user model.

## Alternativas descartadas
—
