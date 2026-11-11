import copy
import json

import pytest

from conftest import REPO, entries, script
from registry import validate


def test_every_registry_entry_validates_against_the_contract():
    out = script("registry.py", "check")
    assert out.returncode == 0, out.stdout + out.stderr
    count = len(list((REPO / "apps").glob("*.json")))
    assert f"registry: {count} entries, {count} valid" in out.stdout


@pytest.mark.parametrize("path", sorted((REPO / "apps").glob("*.json")), ids=lambda p: p.stem)
def test_entry_has_no_problems(path):
    assert validate(json.loads(path.read_text(encoding="utf-8")), path) == []


def test_catalogue_ids_are_unique():
    ids = [e["catalog"]["id"] for e in entries()]
    assert len(ids) == len(set(ids))


def mutated(change):
    entry = copy.deepcopy(next(e for e in entries() if e["app"] == "formportal"))
    change(entry)
    return validate(entry, REPO / "apps" / f"{entry['app']}.json")


@pytest.mark.parametrize("change", [
    lambda e: e.pop("repository"),
    lambda e: e.update(repository="someone-else/formportal"),
    lambda e: e.update(enabled="yes"),
    lambda e: e.update(enabled=False, disabled_reason=""),
    lambda e: e.update(release="ship-it"),
    lambda e: e["version"].update(file="VERSION", pattern=""),
    lambda e: e["version"].update(pattern="^no group$"),
    lambda e: e["version"].update(pattern="(unclosed"),
    lambda e: e.update(checks=[]),
    lambda e: e.update(checks=["../evil.yml"]),
    lambda e: e.update(platforms=["amiga-68k"]),
    lambda e: e.update(app="Other Name"),
], ids=["no-repository", "foreign-owner", "enabled-not-bool", "disabled-without-reason", "unknown-release", "plain-file-without-pattern", "pattern-without-group", "pattern-not-compiling", "no-checks", "check-path", "unknown-platform", "name-mismatch"])
def test_a_bad_entry_is_refused(change):
    assert mutated(change)


@pytest.mark.parametrize("bad", ["{not json", '{"app": "half"}'])
def test_the_check_fails_on_a_broken_registry(tmp_path, monkeypatch, capsys, bad):
    import registry

    for path in (REPO / "apps").glob("*.json"):
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "half.json").write_text(bad, encoding="utf-8")
    monkeypatch.setattr(registry, "APPS", tmp_path)
    monkeypatch.setattr("sys.argv", ["registry.py", "check"])
    with pytest.raises(SystemExit) as done:
        registry.main()
    assert done.value.code == 1
    assert "half.json" in capsys.readouterr().out


def test_a_duplicate_catalogue_id_fails_the_check(tmp_path, monkeypatch, capsys):
    import registry

    for path in (REPO / "apps").glob("*.json"):
        (tmp_path / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    twin = json.loads((REPO / "apps" / "formvis.json").read_text(encoding="utf-8"))
    twin["app"] = "formvis2"
    (tmp_path / "formvis2.json").write_text(json.dumps(twin), encoding="utf-8")
    monkeypatch.setattr(registry, "APPS", tmp_path)
    monkeypatch.setattr("sys.argv", ["registry.py", "check"])
    with pytest.raises(SystemExit) as done:
        registry.main()
    assert done.value.code == 1
    assert "is also used by" in capsys.readouterr().out


def _macos_setups():
    return [(e["app"], e.get("setup", {}).get("macos", "")) for e in entries()]


@pytest.mark.parametrize(("app", "setup"), [s for s in _macos_setups() if "PIP_NO_BINARY=opencv" in s[1]], ids=lambda v: v if isinstance(v, str) and "\n" not in v else "")
def test_opencv_built_from_source_on_macos_ignores_homebrew_and_builds_in_parallel(app, setup):
    for flag in ("-DWITH_OPENEXR=OFF", "-DWITH_VTK=OFF", "-DWITH_QT=OFF", "-DWITH_GTK=OFF", "-DWITH_EIGEN=OFF"):
        assert flag in setup, f"{app}: {flag} missing, so OpenCV links whatever the runner's Homebrew has"
    assert "CMAKE_BUILD_PARALLEL_LEVEL=" in setup, f"{app}: OpenCV compiles serially and can pass the Build step's timeout"


@pytest.mark.parametrize(("app", "setup"), [s for s in _macos_setups() if "brew install" in s[1]], ids=lambda v: v if isinstance(v, str) and "\n" not in v else "")
def test_macos_brew_installs_do_not_update_or_upgrade_the_runner(app, setup):
    assert "HOMEBREW_NO_AUTO_UPDATE=1" in setup and "HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1" in setup, app


@pytest.mark.parametrize("app", ["formlit", "formpdf", "formvis"])
def test_apps_with_a_large_python_sidecar_bundle_rpm_without_compression(app):
    entry = json.loads((REPO / "apps" / f"{app}.json").read_text(encoding="utf-8"))
    extra = json.loads(entry["build"]["tauri_config"])
    assert extra["bundle"]["linux"]["rpm"]["compression"] == {"type": "none"}


def test_formvis_stages_the_appimage_zsync_where_the_artifact_glob_finds_it(tmp_path):
    import fnmatch
    import subprocess

    entry = json.loads((REPO / "apps" / "formvis.json").read_text(encoding="utf-8"))
    assert "zsync" in entry["toolchain"]["linux_packages"].split()
    first = entry["post_build"]["linux"].splitlines()[0]
    appimage = tmp_path / "src-tauri" / "target" / "release" / "bundle" / "appimage"
    appimage.mkdir(parents=True)
    (appimage / "FormVis_1.0.0_amd64.AppImage").write_text("x")
    (tmp_path / "src-tauri" / "FormVis_1.0.0_amd64.AppImage.zsync").write_text("z")
    subprocess.run(["bash", "-c", first], cwd=tmp_path, check=True)
    staged = [str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*.zsync")]
    assert staged == ["src-tauri/target/release/bundle/appimage/FormVis_1.0.0_amd64.AppImage.zsync"]
    assert any(fnmatch.fnmatch(staged[0], pattern.replace("**/", "*/")) for pattern in entry["artifacts"])


RETIRED_RUNNERS = {"macos-12", "macos-13", "macos-14"}


def test_no_app_pins_a_retired_runner_image():
    for path in sorted((REPO / "apps").glob("*.json")):
        for platform in json.loads(path.read_text(encoding="utf-8"))["platforms"]:
            runner = str(platform).rstrip("?").partition("=")[2]
            assert runner not in RETIRED_RUNNERS, f"{path.name}: {platform} asks for a runner GitHub no longer starts"


def test_formcut_ships_for_apple_silicon_and_intel_macs():
    platforms = json.loads((REPO / "apps" / "formcut.json").read_text(encoding="utf-8"))["platforms"]
    assert {"macos-arm64", "macos-x64"} <= {str(p).rstrip("?").partition("=")[0] for p in platforms}


INTEL = "every app with a Mac build also builds for Intel Macs: list macos-x64 (required, not macos-x64?)"


@pytest.mark.parametrize("platforms", [
    ["macos-arm64", "linux-x64", "windows-x64"],
    ["macos-arm64", "macos-x64?", "linux-x64", "windows-x64"],
], ids=["no-intel", "optional-intel"])
def test_a_mac_build_without_a_required_intel_build_is_refused(platforms):
    assert INTEL in mutated(lambda e: e.update(platforms=platforms))


def test_an_entry_without_a_mac_build_needs_no_intel_build():
    assert INTEL not in mutated(lambda e: e.update(platforms=["linux-x64", "windows-x64"]))


def test_every_app_with_a_mac_build_builds_for_intel_macs_by_default():
    for entry in entries():
        names = [str(p).partition("=")[0] for p in entry["platforms"]]
        if any(n.rstrip("?").startswith("macos-") for n in names):
            assert "macos-x64" in names, entry["app"]
