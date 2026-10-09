"""Emit UTF-8 Git tree changes for connector publication without credentials."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "db07b299a4b808fa49b9ed3bd7b134d61f47a523"

def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT)

paths = git("diff", "--name-only", BASE, "HEAD").decode().splitlines()
chunk = int(sys.argv[1]) if len(sys.argv) > 1 else 0
entries = []
for path in paths[chunk * 15:(chunk + 1) * 15]:
    content = git("show", f"HEAD:{path}").decode("utf-8")
    entries.append({"path": path, "mode": "100644", "type": "blob", "content": content})
print(json.dumps({"total": len(paths), "entries": entries}, ensure_ascii=True))
