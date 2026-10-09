"""Prepare independently buildable repositories and inspectable local evidence."""
from pathlib import Path
import json
import shutil
import subprocess
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SHARED_REV = "08ab5ee5321e3d7e5e4ec0b3c454a5f5da9bfcc3"
MODULES = ("coldtrace-monitoring-service", "coldtrace-alert-service", "coldtrace-api-gateway")
WORKFLOW = """name: Verify independent service
on: [push, pull_request, workflow_dispatch]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {path: service}
      - uses: actions/checkout@v4
        with:
          repository: Veltis-Software/coldtrace-shared
          ref: SHARED_REV
          path: shared
      - uses: actions/setup-java@v4
        with: {distribution: temurin, java-version: '21', cache: maven, cache-dependency-path: '**/pom.xml'}
      - run: mvn -B -f shared/pom.xml install
      - run: mvn -B -f service/pom.xml verify
      - run: docker build --build-context shared=./shared -t SERVICE:ci ./service
      - uses: actions/upload-artifact@v4
        if: always()
        with: {name: test-results, path: service/target/surefire-reports}
"""
DOCKERFILE = """# syntax=docker/dockerfile:1.7
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY --from=shared . /shared/
RUN mvn -B -f /shared/pom.xml -DskipTests install
COPY pom.xml ./
COPY src/ ./src/
RUN mvn -B -DskipTests package
RUN cp target/SERVICE-0.1.0-SNAPSHOT.jar /app.jar
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN useradd --system --uid 10001 coldtrace
COPY --from=build --chown=10001:10001 /app.jar ./app.jar
USER 10001
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=70.0"
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
"""

def prepare_modules():
    for module in MODULES:
        folder = ROOT / "sprint1" / module
        (folder / ".github/workflows").mkdir(parents=True, exist_ok=True)
        (folder / ".github/workflows/ci.yml").write_text(WORKFLOW.replace("SHARED_REV", SHARED_REV).replace("SERVICE", module), encoding="utf-8")
        (folder / "Dockerfile").write_text(DOCKERFILE.replace("SERVICE", module), encoding="utf-8")
        (folder / ".gitignore").write_text("target/\n.idea/\n*.log\n.env\n", encoding="utf-8")
        (folder / ".dockerignore").write_text("target\n.git\n.env\n*.log\n", encoding="utf-8")
        readme = folder / "README.md"
        existing = readme.read_text(encoding="utf-8") if readme.exists() else f"# {module}\n"
        marker = "\n## Independent repository build\n"
        existing = existing.split(marker)[0]
        readme.write_text(existing + marker + f"""
Use Java 21 and Maven. Install the sibling `coldtrace-shared` revision
`{SHARED_REV}` first: `mvn -f ../coldtrace-shared/pom.xml install`.
Then run `mvn verify` in this repository.

Build its standalone image with
`docker build --build-context shared=../coldtrace-shared -t {module}:tp1 .`.
The workflow checks out the same shared revision and publishes test artifacts.
Remote execution requires publishing the prepared repositories first.
The source and architecture audit are in `Veltis-Software/coldtrace-services`.
""", encoding="utf-8")
    edge = ROOT / "sprint1/coldtrace-edge-gateway"
    (edge / "README.md").write_text("""# ColdTrace Edge Gateway — Sprint 1

Python 3.12; SQLite WAL retains unconfirmed readings and stable batch identities
across restarts. `python -m unittest discover -v` runs the buffer tests.
Set API_BASE_URL, GATEWAY_UUID, DEVICE_UUID and GATEWAY_API_KEY explicitly.
`python edge_agent.py --help` describes the simulator and network-cut options.
MQTT uses optional paho-mqtt 2.1; the real MQTT adapter has not been field tested.
The Docker image runs as a non-root user. Mount a writable volume for SQLite.
""", encoding="utf-8")
    (edge / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (edge / ".github/workflows/ci.yml").write_text("""name: Verify edge
on: [push, pull_request, workflow_dispatch]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: python -m unittest discover -v
      - run: docker build -t coldtrace-edge-gateway:ci .
""", encoding="utf-8")
    (edge / ".gitignore").write_text("__pycache__/\n*.sqlite*\n.env\n*.log\n", encoding="utf-8")

def capture_evidence():
    evidence = ROOT / "evidence"
    results = []
    for xml in sorted((ROOT / "sprint1").glob("*/target/surefire-reports/TEST-*.xml")):
        tree = ET.parse(xml).getroot()
        results.append({"suite": tree.attrib["name"], **{k: int(tree.attrib.get(k, "0")) for k in ("tests", "failures", "errors", "skipped")}})
    (evidence / "java21-test-results.json").write_text(json.dumps({"runtime": "Docker maven:3.9.9-eclipse-temurin-21", "suites": results}, indent=2), encoding="utf-8")
    for module, port in (("monitoring", 18083), ("alert", 18084)):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v3/api-docs") as response:
            document = json.load(response)
        (evidence / f"openapi-{module}.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    log = (ROOT / "sprint1-jdk21-build.log").read_text(encoding="utf-8", errors="replace")
    (evidence / "java21-build-summary.txt").write_text(log[log.rfind("[INFO] Reactor Summary"):], encoding="utf-8")
    health = {}
    for service, port in (("monitoring", 18083), ("alert", 18084), ("gateway", 18080)):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/actuator/health") as response:
            health[service] = {"url": f"http://127.0.0.1:{port}/actuator/health", "response": json.load(response)}
    (evidence / "docker-health.json").write_text(json.dumps({"observedAt": datetime.now(timezone.utc).isoformat(), "services": health}, indent=2), encoding="utf-8")
    for filename in ("alert-java21-final.log", "cucumber-java21-final.log"):
        log = (ROOT / filename).read_text(encoding="utf-8", errors="replace")
        (evidence / filename.replace(".log", "-summary.txt")).write_text(log[log.rfind("[INFO] Results:"):], encoding="utf-8")
    commits = subprocess.check_output(["git", "log", "--format=%h | %aI | %s", "db07b299a4b808fa49b9ed3bd7b134d61f47a523..HEAD"], cwd=ROOT).decode()
    (evidence / "local-development-commits.txt").write_text(commits, encoding="utf-8")
    legacy = ROOT / "target/surefire-reports/TEST-com.acme.coldtrace.platform.iam.interfaces.rest.SessionContextControllerTest.xml"
    tree = ET.parse(legacy).getroot()
    (evidence / "legacy-iam-test-results.json").write_text(json.dumps({"runtime": "host JDK 26", "suite": tree.attrib["name"], **{k: int(tree.attrib[k]) for k in ("tests", "errors", "failures", "skipped")}}, indent=2), encoding="utf-8")

def prepare_repository_exports():
    infra = ROOT / "sprint1/coldtrace-infrastructure"
    compose = (infra / "compose.yaml").read_text(encoding="utf-8")
    for module in MODULES:
        original = f"context: ../..\n      dockerfile: sprint1/docker/Dockerfile\n      args: {{MODULE: {module}}}"
        replacement = f"context: ../{module}\n      dockerfile: Dockerfile\n      additional_contexts:\n        shared: ../coldtrace-shared"
        compose = compose.replace(original, replacement)
    (infra / "compose.repositories.yaml").write_text(compose, encoding="utf-8")
    (infra / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (infra / ".github/workflows/ci.yml").write_text("""name: Validate orchestration
on: [push, pull_request, workflow_dispatch]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose --env-file .env.example -f compose.repositories.yaml config --quiet
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: python -m py_compile pubsub_init.py
      - run: bash -n mysql-init.sh
""", encoding="utf-8")
    (infra / ".gitignore").write_text(".env\n__pycache__/\n*.log\n", encoding="utf-8")
    destination = ROOT.parent / "coldtrace-sprint1-repositories"
    destination.mkdir(exist_ok=True)
    for folder in sorted((ROOT / "sprint1").glob("coldtrace-*")):
        shutil.copytree(folder, destination / folder.name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("target", "__pycache__", ".git", ".env", "*.log", "*.sqlite*"))
    (destination / "README.md").write_text("""# ColdTrace TP1 prepared repository exports

Six local repository directories are prepared for Veltis-Software. Remote
publication is pending: the authenticated David-std account has read-only
access to coldtrace-services and cannot create repositories in the organization.

Install coldtrace-shared before Maven consumer builds. Standalone Docker builds
use the sibling shared directory as a named BuildKit context.
In coldtrace-infrastructure run:
`docker compose --env-file .env.example -f compose.repositories.yaml -f compose.demo.yaml --profile apps up --build -d`.
These are explicit local synthetic fixtures. IAM also requires the brownfield
application from coldtrace-services on host port 8090 with its separate DB.
Never use demo keys or the emulator receiver for a cloud deployment.

The consolidated source, report of actual tests and architecture review remain
in ../coldtrace-services. A workflow file is preparation, not a completed CI run.
""", encoding="utf-8")

if __name__ == "__main__":
    prepare_modules()
    capture_evidence()
    prepare_repository_exports()
