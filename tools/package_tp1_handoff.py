"""Package committed source and observed evidence without local credentials."""
import subprocess
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path.home() / "Downloads/coldtrace-tp1-implementation-handoff-20261009.zip"
BUNDLE = Path.home() / "Downloads/coldtrace-tp1-local-20261009.bundle"
subprocess.run(["git", "bundle", "create", str(BUNDLE),
                "codex/tp1-architecture-implementation", "codex/export-shared",
                "^db07b299a4b808fa49b9ed3bd7b134d61f47a523"], cwd=ROOT, check=True)
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
exports = ROOT.parent / "coldtrace-sprint1-repositories"
with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
    for relative in filter(None, tracked):
        archive.write(ROOT / relative, "coldtrace-services/" + relative)
    for file in exports.rglob("*"):
        if not file.is_file() or any(part in (".git", "target", "__pycache__") for part in file.relative_to(exports).parts):
            continue
        if file.name == ".env" or file.suffix == ".log" or ".sqlite" in file.name:
            continue
        archive.write(file, "prepared-repositories/" + file.relative_to(exports).as_posix())
    for file in (ROOT / "docs/architecture/diagrams/rendered").glob("*.png"):
        archive.write(file, "original-design-diagrams/" + file.name)
    archive.write(BUNDLE, "git-history/" + BUNDLE.name)
    archive.writestr("LEEME.txt", """ColdTrace TP1 / Sprint 1 — implementación y evidencias locales

Empieza por coldtrace-services/evidence/HANDOFF_PARA_CLAUDE.md.
prepared-repositories contiene seis directorios para los repositorios nuevos.
El paquete incluye código base, extracciones, pruebas y configuración.
No incluye .env, tokens JWT, bases de datos locales ni binarios de compilación.
original-design-diagrams contiene DIAGRAMAS DEL PACK, no capturas de despliegue.
git-history conserva los commits nuevos; el bundle requiere el baseline público
db07b299a4b808fa49b9ed3bd7b134d61f47a523 de coldtrace-services.
La publicación remota y ejecución de CI deben confirmarse en GitHub.
""")
with ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
print(f"{OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
