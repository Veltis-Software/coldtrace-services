# ADR-0001: Microservicios por Bounded Context

- **Estado:** Aceptado
- **Fecha:** 2026-10-09
- **Iteración ADD:** Iteración 0
- **Trazabilidad:** DD-02 (DC-02) · Drivers: CON-02, CON-03

## Contexto
El backend de referencia es un monolito modular Spring Boot organizado en 8 Bounded Contexts. El curso exige microservicios con DDD (CON-02) y se debe reutilizar el código existente (CON-03).

## Decisión
Se crea **un microservicio por Bounded Context** (8 servicios): identity, asset, monitoring, alert, report, maintenance, ai-assistance y subscription. Cada uno conserva la estructura hexagonal `domain / application / infrastructure / interfaces.rest` y su propio repositorio.

## Consecuencias
Alta cohesión semántica y reutilización directa del código. Más servicios que operar y desplegar.

## Alternativas descartadas
Tres servicios gruesos (operación, negocio, soporte): descartado porque mezcla contextos con ritmos de cambio distintos.
