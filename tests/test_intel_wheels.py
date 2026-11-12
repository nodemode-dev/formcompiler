import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-release.yml"
MANIFEST = ROOT / "deps-macos-x64.json"


def steps(text: str) -> list[str]:
    build_job = re.search(r"(?ms)^  build:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", text).group(1)
    return re.split(r"(?m)^      - ", build_job)[1:]


def intel_step() -> tuple[list[str], str]:
    found = steps(WORKFLOW.read_text(encoding="utf-8"))
    names = [s.splitlines()[0] for s in found]
    return names, found[names.index("name: Intel Mac wheels")]


def test_intel_mac_builds_get_their_wheels_before_the_app_set_up_and_only_on_intel():
    names, body = intel_step()
    assert names.index("name: Intel Mac wheels") < names.index("name: App set-up")
    assert "if: matrix.platform == 'macos-x64'" in body


def test_the_wheels_are_checked_against_the_committed_hashes_before_pip_sees_them():
    _, body = intel_step()
    assert "working-directory: .formcompiler" in body
    assert body.index("shasum -a 256 -c SHA256SUMS") < body.index("PIP_FIND_LINKS=")
    assert 'PIP_FIND_LINKS=$dest' in body and 'UV_FIND_LINKS=$dest' in body
    assert "https://" not in body.split("PIP_FIND_LINKS=")[1]


def test_the_manifest_names_each_wheel_with_a_sha256_and_an_https_index():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["index"].startswith("https://dl.formai.studio/") and data["index"].endswith("/")
    assert data["wheels"]
    for name, digest in data["wheels"].items():
        assert re.fullmatch(r"[A-Za-z0-9_.-]+-macosx_\d+_0_x86_64\.whl", name), name
        assert re.fullmatch(r"[0-9a-f]{64}", digest), name
