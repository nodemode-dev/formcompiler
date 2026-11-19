import json
from pathlib import Path

APPS = Path(__file__).resolve().parent.parent / "apps"


def test_every_app_with_a_mac_build_is_notarized():
    for path in sorted(APPS.glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        if any(p.startswith("macos") for p in entry.get("platforms", [])):
            assert entry["signing"]["macos"] == "apple", path.name
