import copy
import re

import pytest

from conftest import REPO, entries, script
from registry import config, validate

DESKTOP = (REPO / ".github" / "workflows" / "desktop-release.yml").read_text(encoding="utf-8")
RELEASE = (REPO / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
LGPL_APPS = {"formcut", "format"}
FFMPEG = "backend/.lgpl-ffmpeg"


def entry(app):
    return next(e for e in entries() if e["app"] == app)


def step(name):
    match = re.search(rf"(?ms)^      - name: {re.escape(name)}\n(.*?)(?=^      - |\Z)", DESKTOP)
    assert match, name
    return match.group(1)


def order(name):
    return DESKTOP.index(f"      - name: {name}\n")


def test_only_the_lgpl_ffmpeg_apps_cache_a_build_folder():
    caching = {e["app"] for e in entries() if "build_cache" in e["toolchain"]}
    assert caching == LGPL_APPS


@pytest.mark.parametrize("app", sorted(LGPL_APPS))
def test_the_lgpl_apps_cache_their_ffmpeg_keyed_on_the_scripts_that_build_it(app):
    cache = entry(app)["toolchain"]["build_cache"]
    assert cache["paths"] == [FFMPEG]
    assert {"setup/build_lgpl_av", "setup/build_lgpl_av.bat"} <= set(cache["key_files"])
    values = config(entry(app))
    assert values["build_cache_paths"] == FFMPEG
    assert values["build_cache_key_files"].splitlines() == cache["key_files"]


def test_an_app_without_a_build_cache_passes_nothing():
    values = config(entry("formportal"))
    assert values["build_cache_paths"] == "" and values["build_cache_key_files"] == ""


def test_formcut_keeps_its_macos_wheels():
    assert entry("formcut")["toolchain"]["pip_cache_macos"] is True


@pytest.mark.parametrize("cache", [
    {"paths": [FFMPEG]},
    {"paths": [FFMPEG], "key_files": []},
    {"paths": [], "key_files": ["setup/build_lgpl_av"]},
    {"paths": ["/Users/runner/ffmpeg"], "key_files": ["setup/build_lgpl_av"]},
    {"paths": ["backend/../../elsewhere"], "key_files": ["setup/build_lgpl_av"]},
    {"paths": ["backend/*"], "key_files": ["setup/build_lgpl_av"]},
    {"paths": ["."], "key_files": ["setup/build_lgpl_av"]},
    {"paths": [FFMPEG], "key_files": ["$HOME/x"]},
    "backend/.lgpl-ffmpeg",
], ids=["no-key-files", "empty-key-files", "no-paths", "absolute", "parent", "glob", "checkout", "variable", "not-object"])
def test_a_bad_build_cache_is_refused(cache):
    changed = copy.deepcopy(entry("formcut"))
    changed["toolchain"]["build_cache"] = cache
    assert validate(changed, REPO / "apps" / "formcut.json")


def test_release_passes_the_build_cache_to_the_desktop_build():
    assert "build-cache-paths: ${{ fromJSON(needs.gate.outputs.config).build_cache_paths }}" in RELEASE
    assert "build-cache-key-files: ${{ fromJSON(needs.gate.outputs.config).build_cache_key_files }}" in RELEASE


def test_the_build_cache_is_restored_before_the_build_on_an_exact_key_only():
    key = step("build cache key")
    assert "if: inputs.build-cache-paths != ''" in key
    for part in ("APP: ${{ inputs.app-name }}", "PLATFORM: ${{ matrix.platform }}", "RUNNER_LABEL: ${{ matrix.runner }}", "KEY_FILES: ${{ inputs.build-cache-key-files }}"):
        assert part in key
    restore = step("build cache")
    assert "actions/cache/restore@" in restore
    assert "path: ${{ inputs.build-cache-paths }}" in restore
    assert "key: ${{ steps.buildkey.outputs.key }}" in restore
    assert "restore-keys" not in restore
    assert order("build cache key") < order("build cache") < order("Build")


def test_the_build_cache_is_saved_even_when_the_build_fails_or_times_out():
    save = step("Save the build cache")
    assert "actions/cache/save@" in save
    assert "if: always() && inputs.build-cache-paths != ''" in save
    assert "steps.buildcache.outputs.cache-hit != 'true'" in save
    assert "key: ${{ steps.buildkey.outputs.key }}" in save
    assert order("Build") < order("Save the build cache") < order("Post-build")


def test_the_pip_wheels_follow_the_build_cache_key_without_moving_other_apps_keys():
    pip = step("pip wheel cache key")
    assert "BUILD_HASH: ${{ steps.buildkey.outputs.hash }}" in pip
    assert "$setup${BUILD_HASH:+-$BUILD_HASH}-" in pip
    assert order("build cache key") < order("pip wheel cache key")


def outputs(result):
    assert result.returncode == 0, result.stdout + result.stderr
    return dict(line.split("=", 1) for line in result.stdout.splitlines())


def make_app(tmp_path, body="FFMPEG_VERSION=8.0.3\n"):
    (tmp_path / "setup").mkdir(exist_ok=True)
    (tmp_path / "setup" / "build_lgpl_av").write_text(body, encoding="utf-8")
    (tmp_path / "setup" / "build_lgpl_av.bat").write_text("set FFMPEG_VERSION=8.0.3\n", encoding="utf-8")
    return tmp_path


def key_for(root, app="formcut", platform="macos-x64", runner="macos-15-intel"):
    return outputs(script("build_cache.py", f"--app={app}", f"--platform={platform}", f"--runner={runner}",
                          "--key-files=setup/build_lgpl_av\nsetup/build_lgpl_av.bat", f"--root={root}"))


def test_the_key_names_the_app_platform_and_runner(tmp_path):
    found = key_for(make_app(tmp_path))
    assert re.fullmatch(r"formcompiler-build-formcut-macos-x64-macos-15-intel-[0-9a-f]{16}", found["key"])
    assert found["key"].endswith(found["hash"])


def test_another_app_or_platform_never_shares_the_key(tmp_path):
    root = make_app(tmp_path)
    keys = {key_for(root)["key"], key_for(root, app="format")["key"], key_for(root, platform="macos-arm64", runner="macos-latest")["key"]}
    assert len(keys) == 3


def test_a_new_ffmpeg_version_changes_the_key(tmp_path):
    before = key_for(make_app(tmp_path))
    after = key_for(make_app(tmp_path, "FFMPEG_VERSION=8.0.4\n"))
    assert before["hash"] != after["hash"]


@pytest.mark.parametrize("files", ["", "setup/missing", "../outside", "/etc/passwd"])
def test_a_key_file_that_is_missing_or_outside_the_app_stops_the_build(tmp_path, files):
    result = script("build_cache.py", "--app=formcut", "--platform=macos-x64", "--runner=macos-15-intel",
                    f"--key-files={files}", f"--root={make_app(tmp_path)}")
    assert result.returncode == 1
    assert "::error::" in result.stdout
