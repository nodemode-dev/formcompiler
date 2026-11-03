"""The Tauri config formcompiler adds at build time: the updater's key and, with the download store set, its address."""
import json
import re
from pathlib import Path

import pytest

from run_build import without_empty_tauri_config
from tauri_config import build_config, msi_version, write_platform_configs

SIGNED = {"TAURI_SIGNING_PRIVATE_KEY": "k", "TAURI_UPDATER_PUBKEY": "pub"}


def updater(config):
    return config.get("plugins", {}).get("updater", {})


def test_a_signed_build_with_the_store_set_reads_its_updates_from_the_store():
    env = {**SIGNED, "FORMCOMPILER_PUBLIC_BASE": "https://dl.formai.studio/", "FORMCOMPILER_APP": "formvis"}
    assert updater(build_config("linux", env=env)) == {"pubkey": "pub", "endpoints": ["https://dl.formai.studio/formvis/updates/latest.json"]}


def test_the_app_name_is_quoted_in_the_address():
    env = {**SIGNED, "FORMCOMPILER_PUBLIC_BASE": "https://dl.formai.studio", "FORMCOMPILER_APP": "form.md"}
    assert updater(build_config("linux", env=env))["endpoints"] == ["https://dl.formai.studio/form.md/updates/latest.json"]


@pytest.mark.parametrize("missing", ["FORMCOMPILER_PUBLIC_BASE", "FORMCOMPILER_APP"])
def test_without_the_store_or_the_app_the_apps_own_endpoints_stay(missing):
    env = {**SIGNED, "FORMCOMPILER_PUBLIC_BASE": "https://dl.formai.studio", "FORMCOMPILER_APP": "formvis"}
    env.pop(missing)
    assert "endpoints" not in updater(build_config("linux", env=env))


def test_an_unsigned_build_gets_no_updater_settings():
    env = {"FORMCOMPILER_PUBLIC_BASE": "https://dl.formai.studio", "FORMCOMPILER_APP": "formvis"}
    assert updater(build_config("linux", env=env)) == {}


def test_an_app_without_the_updater_gets_no_updater_settings_even_when_signed():
    env = {**SIGNED, "FORMCOMPILER_PUBLIC_BASE": "https://dl.formai.studio", "FORMCOMPILER_APP": "formwav",
           "FORMCOMPILER_UPDATER_TAURI": "false"}
    config = build_config("linux", env=env)
    assert updater(config) == {}
    assert "createUpdaterArtifacts" not in config.get("bundle", {})


def test_a_bad_store_address_stops_the_build():
    env = {**SIGNED, "FORMCOMPILER_PUBLIC_BASE": "http://dl.formai.studio", "FORMCOMPILER_APP": "formvis"}
    with pytest.raises(SystemExit):
        build_config("linux", env=env)


@pytest.mark.parametrize("version, wix", [
    ("0.9.8-beta.1", "0.9.8.1"),
    ("1.97.0-rc.12", "1.97.0.12"),
    ("2.0.0-beta", "2.0.0.0"),
    ("1.0.0-beta.70000", "1.0.0.65535"),
    ("1.2.3", ""),
    ("1.2.3+build.7", ""),
])
def test_a_prerelease_gets_an_msi_version_windows_installer_accepts(version, wix):
    assert msi_version(version) == wix


def test_a_windows_beta_build_sets_the_msi_version():
    config = build_config("windows", env={"FORMCOMPILER_VERSION": "0.9.8-beta.1"})
    assert config["bundle"]["windows"]["wix"] == {"version": "0.9.8.1"}


@pytest.mark.parametrize("runner_os, version", [("windows", "0.9.8"), ("linux", "0.9.8-beta.1"), ("macos", "0.9.8-beta.1")])
def test_a_stable_or_non_windows_build_keeps_the_apps_msi_version(runner_os, version):
    config = build_config(runner_os, adhoc_macos=False, env={"FORMCOMPILER_VERSION": version})
    assert "wix" not in config.get("bundle", {}).get("windows", {})


def test_the_platform_config_reaches_a_build_the_app_runs_itself(tmp_path):
    app = tmp_path / "src-tauri"
    app.mkdir()
    (app / "tauri.windows.conf.json").write_text(json.dumps({"bundle": {"windows": {"signCommand": "sign %1"}}}))
    written = write_platform_configs([app], "windows", {"bundle": {"windows": {"wix": {"version": "0.9.8.1"}}}})
    assert written == [app / "tauri.windows.conf.json"]
    assert json.loads(written[0].read_text()) == {"bundle": {"windows": {"signCommand": "sign %1", "wix": {"version": "0.9.8.1"}}}}


def test_a_platform_config_kept_in_toml_is_left_alone(tmp_path):
    (tmp_path / "Tauri.linux.toml").write_text("")
    assert write_platform_configs([tmp_path], "linux", {"bundle": {"createUpdaterArtifacts": True}}) == []
    assert not (tmp_path / "tauri.linux.conf.json").exists()


def test_the_build_step_never_sets_the_variable_tauri_build_parses():
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "desktop-release.yml").read_text()
    assert not re.search(r"^\s+TAURI_CONFIG:", workflow, re.M)


@pytest.mark.parametrize("value", ["", "  "])
def test_an_empty_tauri_config_is_dropped_before_the_app_builds(value):
    assert "TAURI_CONFIG" not in without_empty_tauri_config({"TAURI_CONFIG": value, "PATH": "/bin"})


def test_a_real_tauri_config_is_kept():
    assert without_empty_tauri_config({"TAURI_CONFIG": "{}"})["TAURI_CONFIG"] == "{}"
