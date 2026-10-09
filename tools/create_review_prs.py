"""Create draft review PRs with exact local validation and bounded scope."""
import json
import subprocess
import tempfile
from pathlib import Path

assert subprocess.check_output(["gh", "api", "user", "--jq", ".login"], text=True).strip() == "David-std2"
items = {
    "coldtrace-shared": ("Versioned events and safe correlation primitives for Sprint 1", "Introduces the common version-1 event envelope and correlation sanitization/filter infrastructure. No business entities or shared persistence are included. Consumers pin shared revision 08ab5ee5321e3d7e5e4ec0b3c454a5f5da9bfcc3 (tag v0.1.0-sprint1).", "Two tests passed with Java 21. ADR-0010; T-01."),
    "coldtrace-monitoring-service": ("Idempotent telemetry ingestion and organization-scoped current states", "Implements batches/heartbeats, atomic readings + projections + outbox, gap detection, and current-state queries. Replaying an older reading does not regress current state. IAM resolves the organization from the existing authenticated session; demo fixtures are explicit and local only. Pub/Sub publication currently targets the emulator.", "23 Java 21 tests passed, including five Cucumber scenarios and architecture checks. Local MySQL/Compose execution and 50-sensor recovery were exercised. ADR-0006, ADR-0007, ADR-0010, ADR-0011; T-10/T-11/T-12/T-20/T-21 (partial)."),
    "coldtrace-alert-service": ("Idempotent alert consumer with durable in-app notifications", "Consumes threshold and gap events transactionally. Duplicate delivery creates one incident/notification; notification failure rolls back the processed marker. An old gap-close cannot resolve a newer gap. Organization-scoped list/detail supports verifying alerts. The push receiver is opt-in for the local emulator; cloud OIDC, acknowledge/assign, SSE and email/SMS remain outside this increment.", "Five Java 21 tests passed. The local end-to-end flow created and queried a durable IN_APP notification. ADR-0010/ADR-0013 (partial); T-20/T-23 (partial)."),
    "coldtrace-api-gateway": ("Route the Sprint 1 increment while preserving brownfield APIs", "Routes telemetry/current-state requests to Monitoring and implemented alert list/detail to Alert; other APIs retain the existing backend. Propagates bearer authentication and sanitized correlation IDs. Shared dependency is pinned to the prepared library revision.", "Three Java 21 routing tests passed; real local smoke requests passed. Standalone Docker image built using the sibling shared build context. ADR-0002; T-02."),
    "coldtrace-edge-gateway": ("Persist unconfirmed IoT readings and stable retry batches", "Adds SQLite WAL store-and-forward with persistent sequences and stable batch IDs/payloads. Deletes readings only after complete accepted/duplicated confirmation. Simulator supports a bounded network cut; MQTT adapter is optional and has not been field tested.", "Six tests passed inside the Python 3.12 Docker image. A 50-sensor run withheld sends for 300 seconds, accepted all 1,650 readings and emptied the backlog in 3.234 seconds, with no pending or duplicate readings. This is a local result. ADR-0005; T-13."),
    "coldtrace-infrastructure": ("Prepare reproducible local MySQL and Pub/Sub orchestration", "Adds Compose for the consolidated source and sibling repositories, isolated MySQL schemas/users, idempotent emulator bootstrap and explicit demo override. Local Monitoring/Alert/Gateway health was verified. Cloud names/cost constraints are documented as preparation; no Google Cloud resources were created.", "Compose configuration and actual local Docker execution passed. Emulator interruption retained and subsequently published an outbox event. Cloud authenticated push/publication remain pending. ADR-0003/ADR-0009; T-03."),
    "coldtrace-services": ("Deliver the TP1 telemetry-to-alert increment and observed evidence", "Extracts Monitoring and a bounded Alert consumer behind a Strangler gateway, with shared contracts and an Edge store-and-forward agent. Adds only an authenticated session-context endpoint to the brownfield IAM. Includes the architecture review, standalone repository exports, workflows, Postman collection and observed local deployment evidence. TP1 / Sprint 1 only; frontend work, full eight-service migration, cloud deployment, video and team/board evidence remain pending. See evidence/HANDOFF_PARA_CLAUDE.md.", "33 tests passed with Java 21, six Python 3.12 tests, and two targeted legacy IAM tests with JDK 26. Newman: eight requests/nine assertions passed. Docker/MySQL/PubSub local flow, broker interruption, tenant isolation and 300-second Edge network-withholding recovery were exercised. ADR-0002/0005/0006/0007/0010/0011; T-01/T-02/T-03/T-11/T-12/T-13 and bounded parts of T-20/T-23. GitHub CI must be checked separately."),
}
results = []
for name, (title, change, validation) in items.items():
    branch = "codex/tp1-architecture-implementation" if name == "coldtrace-services" else "codex/tp1-import"
    existing = subprocess.check_output(["gh", "pr", "list", "--repo", f"Veltis-Software/{name}", "--head", branch, "--state", "open", "--json", "url"], text=True)
    existing = json.loads(existing)
    if existing:
        results.append({"repository": name, "url": existing[0]["url"]})
        continue
    with tempfile.TemporaryDirectory(prefix="coldtrace-pr-") as folder:
        body = Path(folder) / "body.md"
        body.write_text(change + "\n\nValidation: " + validation + "\n\nImplementation assisted by Codex in David's workspace; no contributions by other team members are asserted.\n", encoding="utf-8")
        result = subprocess.run(["gh", "pr", "create", "--repo", f"Veltis-Software/{name}", "--draft", "--base", "main", "--head", branch, "--title", title, "--body-file", str(body)], capture_output=True, text=True)
        result.check_returncode()
        results.append({"repository": name, "url": result.stdout.strip()})
print(json.dumps(results))
