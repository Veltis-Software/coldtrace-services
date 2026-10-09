"""Initialize the already-created empty repositories under the selected account."""
import base64
import json
import subprocess

def gh(*args, **kwargs):
    return subprocess.run(["gh", *args], text=True, capture_output=True, **kwargs)

assert gh("api", "user", "--jq", ".login").stdout.strip() == "David-std2"
for name in ("coldtrace-shared", "coldtrace-monitoring-service", "coldtrace-alert-service",
             "coldtrace-api-gateway", "coldtrace-edge-gateway", "coldtrace-infrastructure"):
    repository = f"Veltis-Software/{name}"
    branch = gh("api", f"repos/{repository}/branches/main", "--jq", ".commit.sha")
    if branch.returncode == 0:
        print(f"{repository}: main already exists")
        continue
    metadata = gh("api", f"repos/{repository}")
    metadata.check_returncode()
    assert json.loads(metadata.stdout)["permissions"]["push"]
    commits = gh("api", f"repos/{repository}/commits", "--jq", "length")
    # GitHub returns 409 for empty repositories. Do not overwrite an existing history.
    if commits.returncode == 0:
        raise RuntimeError(f"{repository} has history without main; inspect it first")
    assert "409" in commits.stderr, commits.stderr
    payload = {"message": "docs: initialize ColdTrace repository", "branch": "main",
               "content": base64.b64encode(f"# {name}\n\nColdTrace TP1 / Sprint 1.\n".encode()).decode()}
    initialized = gh("api", "--method", "PUT", f"repos/{repository}/contents/README.md",
                     "--input", "-", "--jq", ".commit.sha", input=json.dumps(payload))
    initialized.check_returncode()
    print(f"{repository}: {initialized.stdout.strip()}")
