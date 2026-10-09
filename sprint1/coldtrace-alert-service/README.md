# ColdTrace Alert Service

Consumes `threshold.breached` and `source.gap` integration events. Incident,
notification, processed-event marker and outbox entry commit atomically.
Duplicate event delivery produces one incident. Gap recovery resolves only the
matching organization's asset; an older close cannot resolve a newer gap.

## API and notifications

`GET /api/v1/alerts` and `GET /api/v1/alerts/{id}` require a bearer token; IAM
resolves the organization and queries are isolated by it. The detail contains
durable `IN_APP` notifications with status `AVAILABLE` and `/alerts/{id}` links.
This increment does not send email/SMS or implement acknowledgement/assignment,
undo or SSE. `incident.opened` is persisted in the service outbox; its relay is
not yet implemented.

## Configuration

| Variable | Purpose / default |
|---|---|
| PORT | HTTP port; 8084 |
| DB_URL, DB_USER, DB_PASSWORD | MySQL connection to `ct_alert` |
| IDENTITY_URL | IAM URL; http://127.0.0.1:8090 |
| COLDTRACE_PUBSUB_LOCAL_PUSH_ENABLED | Explicit emulator receiver opt-in; false |

When enabled locally, `POST /internal/pubsub/events` accepts Pub/Sub push
envelopes. It is disabled by default and has no cloud OIDC validation; enable
it only with the local emulator. Schema changes use Flyway.

OpenAPI: `/v3/api-docs`; Swagger: `/swagger-ui.html`; health:
`/actuator/health`. Tests cover duplicate delivery, rollback on notification
failure, gap closure isolation, invalid envelopes and delayed close events.

## Build and test

Requires Java 21 and Maven. Install the shared library from tag
`v0.1.0-sprint1` (`08ab5ee5321e3d7e5e4ec0b3c454a5f5da9bfcc3`) first:

```sh
mvn -B -f ../coldtrace-shared/pom.xml install
mvn -B verify
```

Build the standalone image with the sibling library as a named build context:

```sh
docker build --build-context shared=../coldtrace-shared -t coldtrace-alert-service:dev .
```

The CI workflow installs the pinned shared source, runs tests, builds the image
and uploads test reports. Local orchestration is in `coldtrace-infrastructure`.
