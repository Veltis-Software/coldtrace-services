# Alert Service — TP1 increment

Consumes threshold.breached and source.gap through a Pub/Sub emulator push
subscription. A transaction stores the processed event marker, incident,
durable in-app notification and incident.opened outbox event. Repeated eventId
does not create a second incident. Gap CLOSED resolves open NO_DATA incidents
for the same organization and asset.

GET /api/v1/alerts and /api/v1/alerts/{id} validate the legacy JWT by asking
the owning IAM context; queries always filter by organization. The legacy
organization-scoped incident routes remain in the brownfield application.

Local-only push receiver must explicitly be enabled:
`--coldtrace.pubsub.local-push-enabled=true`. It is disabled by default.
Cloud OIDC push authentication, external notifications, acknowledgement,
assignment, SSE, and incident.opened publishing are not implemented here.
The notification deep link is evidence of durable availability, not of a
completed frontend route or email delivery.

Build with JDK 21. Install coldtrace-shared in the local Maven repository
before building this repository independently, or use the parent workspace
reactor. Runtime variables: DB_URL, DB_USER, DB_PASSWORD, IDENTITY_URL, PORT.

The new threshold type THRESHOLD_BREACHED is explicit for this increment;
the original backend accepts free-text incident types and WARNING/CRITICAL
severity. Detailed alert-service.yaml from the handoff describes a later
usability increment and is not claimed as fulfilled by these query endpoints.

## Independent repository build

Use Java 21 and Maven. Install the sibling `coldtrace-shared` revision
`08ab5ee5321e3d7e5e4ec0b3c454a5f5da9bfcc3` first: `mvn -f ../coldtrace-shared/pom.xml install`.
Then run `mvn verify` in this repository.

Build its standalone image with
`docker build --build-context shared=../coldtrace-shared -t coldtrace-alert-service:tp1 .`.
The workflow checks out the same shared revision and publishes test artifacts.
Remote execution requires publishing the prepared repositories first.
The source and architecture audit are in `Veltis-Software/coldtrace-services`.
