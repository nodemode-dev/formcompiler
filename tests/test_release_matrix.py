import json
import shutil
import subprocess
import sys

import pytest

from conftest import REPO, entries, script
from plan import parse_version, plan_matrix

PATTERN_LINES = {
    "form.md": "VERSION := v{v}\nLDFLAGS := -s -w\n",
    "formNET": "VERSION := v{v}\nLDFLAGS := -s -w\n",
    "formcut": 'from app import x\n\nAPP_VERSION = "{v}"\napp = FastAPI(version=APP_VERSION)\n',
}

DISABLED = [e["app"] for e in entries() if not e["enabled"]]
ENABLED = [e["app"] for e in entries() if e["enabled"]]


def fixture_text(entry, version):
    source = entry["version"]
    if source.get("pattern"):
        return PATTERN_LINES[entry["app"]].format(v=version)
    if source["file"].endswith(".json"):
        return json.dumps({"productName": entry["app"], "version": version}, indent=2)
    if source["file"].endswith(".toml"):
        return f'[package]\nname = "{entry["app"]}"\nversion = "{version}"\n'
    return f"{version}\n"


def test_every_pattern_source_has_a_fixture_line():
    assert {e["app"] for e in entries() if e["version"].get("pattern")} == set(PATTERN_LINES)


@pytest.mark.parametrize("entry", entries(), ids=lambda e: e["app"])
def test_the_declared_version_source_resolves_in_a_fixture_repo(tmp_path, entry):
    target = tmp_path / entry["version"]["file"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(fixture_text(entry, "3.4.5"), encoding="utf-8")
    assert parse_version(target.read_text(encoding="utf-8"), str(target), entry["version"].get("pattern")) == "3.4.5"


def test_a_pattern_that_matches_nothing_stops_the_release(tmp_path):
    target = tmp_path / "Makefile"
    target.write_text("NAME := form.md\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        parse_version(target.read_text(), str(target), r"^VERSION := v(\S+)")


@pytest.fixture
def held_back(tmp_path):
    shutil.copytree(REPO / "scripts", tmp_path / "scripts")
    shutil.copytree(REPO / "apps", tmp_path / "apps")
    app = ENABLED[0]
    path = tmp_path / "apps" / f"{app}.json"
    entry = json.loads(path.read_text(encoding="utf-8"))
    entry.update(enabled=False, disabled_reason="held back by the test")
    path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return tmp_path, app


def held_script(root, *args):
    return subprocess.run([sys.executable, "-I", str(root / "scripts" / "registry.py"), *args], cwd=root, capture_output=True, text=True, timeout=120)


def test_disabled_apps_are_not_listed_for_release():
    out = script("registry.py", "list", "--enabled")
    assert out.returncode == 0, out.stderr
    listed = json.loads(out.stdout)
    assert sorted(listed) == sorted(ENABLED)
    assert not set(listed) & set(DISABLED)


def test_a_held_back_app_is_not_listed_for_release(held_back):
    root, app = held_back
    out = held_script(root, "list", "--enabled")
    assert out.returncode == 0, out.stderr
    assert app not in json.loads(out.stdout)


def test_a_held_back_app_cannot_be_configured_for_a_build(held_back):
    root, app = held_back
    out = held_script(root, "config", "--app", app)
    assert out.returncode != 0
    assert "is disabled in the registry" in out.stdout + out.stderr


@pytest.mark.parametrize("app", DISABLED)
def test_a_disabled_app_cannot_be_configured_for_a_build(app):
    out = script("registry.py", "config", "--app", app)
    assert out.returncode != 0
    assert "is disabled in the registry" in out.stdout + out.stderr


@pytest.mark.parametrize("app", ENABLED)
def test_an_enabled_app_configures_with_a_platform_matrix(app, tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    out = script("registry.py", "config", "--app", app, cwd=tmp_path)
    assert out.returncode == 0, out.stdout + out.stderr
    values = json.loads(out.stdout)
    assert values["config"]


def test_the_plan_refuses_an_unknown_or_repeated_platform():
    assert plan_matrix("linux-x64,windows-x64")["include"]
    for spec in ("amiga-68k", "linux-x64,linux-x64", ""):
        with pytest.raises(SystemExit):
            plan_matrix(spec)


def test_an_experimental_platform_is_marked_and_kept():
    rows = {r["platform"]: r for r in plan_matrix("macos-arm64,windows-x86?")["include"]}
    assert rows["windows-x86"]["experimental"] is True
    assert rows["macos-arm64"]["experimental"] is False
