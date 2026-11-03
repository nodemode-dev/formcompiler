import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
VERSION_SITES = [
    ("VERSION", r"^(\S+)$"),
    ("CHANGELOG.md", r"^## v(\S+) ·"),
    ("scripts/HASHOUT_LOG.md", r"^Current build version: v(\S+)$"),
]
STRIP_EXEMPT = []

sys.path.insert(0, str(SCRIPTS))


def script(name, *args, cwd=None):
    return subprocess.run([sys.executable, "-I", str(SCRIPTS / name), *args], cwd=cwd or REPO, capture_output=True, text=True, timeout=120)


def entries():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((REPO / "apps").glob("*.json"))]


@pytest.fixture(scope="session")
def repo_versions():
    found = {}
    for rel, pattern in VERSION_SITES:
        match = re.search(pattern, (REPO / rel).read_text(encoding="utf-8"), re.MULTILINE)
        found[rel] = match.group(1) if match else None
    return found


@pytest.fixture(scope="session")
def repo_version(repo_versions):
    return next(iter(repo_versions.values()))
