# ColdTrace Shared

Small technical library: EventEnvelope version 1, validated correlation IDs,
and a servlet correlation filter with MDC cleanup. It contains no entities,
repositories or shared database access. Monitoring and the API Gateway consume
the library; bounded-context domain models stay owned by their services.

Build/install using JDK 21 and Maven: `mvn -B verify install`.
Coordinates: `com.acme.coldtrace:coldtrace-shared:0.1.0-SNAPSHOT`.
