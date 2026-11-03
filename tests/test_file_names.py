import json

import pytest

from catalog import classify
from conftest import script
from stage import staged_name

TAURI = {
    "macos-arm64": ("macos", "aarch64", ["FormTray_0.9.8_aarch64.dmg", "FormTray.app.tar.gz", "FormTray.app.tar.gz.sig"]),
    "macos-x64": ("macos", "x86_64", ["FormTray_0.9.8_x64.dmg", "FormTray.app.tar.gz", "FormTray.app.tar.gz.sig"]),
    "macos-universal": ("macos", "universal", ["FormTray_0.9.8_universal.dmg"]),
    "linux-x64": ("linux", "x64", ["FormTray_0.9.8_amd64.AppImage", "FormTray_0.9.8_amd64.AppImage.sig", "FormTray_0.9.8_amd64.deb", "FormTray-0.9.8-1.x86_64.rpm"]),
    "linux-arm64": ("linux", "arm64", ["FormTray_0.9.8_aarch64.AppImage", "FormTray_0.9.8_arm64.deb", "FormTray-0.9.8-1.aarch64.rpm"]),
    "windows-x64": ("windows", "x64", ["FormTray_0.9.8_x64-setup.exe", "FormTray_0.9.8_x64-setup.exe.sig", "FormTray_0.9.8_x64_en-US.msi", "FormTray_0.9.8_x64_en-US.msi.sig"]),
    "windows-arm64": ("windows", "arm64", ["FormTray_0.9.8_arm64-setup.exe", "FormTray_0.9.8_arm64_en-US.msi"]),
}
CATALOG_ARCH = {"arm64": "arm64", "x64": "x86_64"}


def named(name, platform, app="formtray", version="0.9.8"):
    runner_os, arch, _ = TAURI[platform]
    return staged_name(name, runner_os, arch, "formcompiler", app, version, platform)


@pytest.mark.parametrize("platform", sorted(TAURI))
def test_every_bundle_is_named_app_version_platform(platform):
    for name in TAURI[platform][2]:
        assert named(name, platform).startswith(f"formtray-0.9.8-{platform}"), name


def test_the_names_for_one_release():
    got = {named(n, p) for p in ("macos-arm64", "linux-x64", "windows-x64") for n in TAURI[p][2]}
    assert got == {
        "formtray-0.9.8-macos-arm64.dmg",
        "formtray-0.9.8-macos-arm64.app.tar.gz",
        "formtray-0.9.8-macos-arm64.app.tar.gz.sig",
        "formtray-0.9.8-linux-x64.AppImage",
        "formtray-0.9.8-linux-x64.AppImage.sig",
        "formtray-0.9.8-linux-x64.deb",
        "formtray-0.9.8-linux-x64.rpm",
        "formtray-0.9.8-windows-x64-setup.exe",
        "formtray-0.9.8-windows-x64-setup.exe.sig",
        "formtray-0.9.8-windows-x64.msi",
        "formtray-0.9.8-windows-x64.msi.sig",
    }


@pytest.mark.parametrize("platform", sorted(TAURI))
def test_the_catalogue_reads_the_platform_from_the_new_names(platform):
    runner_os, _, names = TAURI[platform]
    arch = platform.split("-", 1)[1]
    expected = ["arm64", "x86_64"] if arch == "universal" else [CATALOG_ARCH[arch]]
    for name in names:
        new = named(name, platform)
        entries = classify(new)
        if new.endswith((".sig", ".tar.gz")):
            assert entries == []
            continue
        assert [(o, a) for o, a, _ in entries] == [(runner_os, a) for a in expected], new


def test_the_kind_survives_the_rename():
    for platform in TAURI:
        for name in TAURI[platform][2]:
            assert [k for _, _, k in classify(named(name, platform))] == [k for _, _, k in classify(name)] or not classify(name)


def test_a_beta_version_and_a_dotted_app_name():
    assert named("form.md_0.48.0-beta.1_aarch64.dmg", "macos-arm64", "form.md", "0.48.0-beta.1") == "form.md-0.48.0-beta.1-macos-arm64.dmg"


def test_zips_and_zsync_files_follow_the_rule():
    assert named("formcut-2.11.3-windows-x86_64.zip", "windows-x64", "formcut", "2.11.3") == "formcut-2.11.3-windows-x64.zip"
    assert named("formcut-2.11.3-windows-x86_64-setup.exe", "windows-x64", "formcut", "2.11.3") == "formcut-2.11.3-windows-x64-setup.exe"
    assert named("FormTray_0.9.8_amd64.AppImage.zsync", "linux-x64") == "formtray-0.9.8-linux-x64.AppImage.zsync"


def test_other_files_keep_their_names():
    for name in ("delivery-tools-macos-arm64.txt", "formdesign-core-aarch64-apple-darwin", "notes.md", "FormTray.exe"):
        assert named(name, "macos-arm64") == name


def test_app_names_keep_the_old_rule():
    assert staged_name("formvis.app.tar.gz", "macos", "aarch64", "app") == "formvis_aarch64.app.tar.gz"
    assert staged_name("formvis_1.0.0_aarch64.dmg", "macos", "aarch64", "app") == "formvis_1.0.0_aarch64.dmg"
    assert staged_name("formportal-0.53.5-linux-x86_64.zip", "linux", "x64", "app") == "formportal-0.53.5-linux-x86_64.zip"


def stage(tmp_path, *extra):
    bundle = tmp_path / "src-tauri" / "target" / "release" / "bundle"
    for folder, name in (("nsis", "FormTray_0.9.8_x64-setup.exe"), ("nsis", "FormTray_0.9.8_x64-setup.exe.sig"), ("msi", "FormTray_0.9.8_x64_en-US.msi")):
        (bundle / folder).mkdir(parents=True, exist_ok=True)
        (bundle / folder / name).write_text("signature" if name.endswith(".sig") else name, encoding="utf-8")
    return script("stage.py", "--platform=windows-x64", "--os=windows", "--arch=x64", "--updater-key=windows-x86_64", "--out=out", *extra, cwd=tmp_path)


def test_stage_writes_the_new_names_and_the_updater_follows(tmp_path):
    result = stage(tmp_path, "--app=formtray", "--version=0.9.8")
    assert result.returncode == 0, result.stdout + result.stderr
    out = tmp_path / "out"
    assert sorted(p.name for p in out.iterdir()) == [
        "formtray-0.9.8-windows-x64-setup.exe",
        "formtray-0.9.8-windows-x64-setup.exe.sig",
        "formtray-0.9.8-windows-x64.msi",
        "windows-x64.formcompiler.json",
    ]
    manifest = json.loads((out / "windows-x64.formcompiler.json").read_text(encoding="utf-8"))
    assert manifest["update"]["file"] == "formtray-0.9.8-windows-x64-setup.exe"


def test_stage_needs_the_app_and_version_for_formcompiler_names(tmp_path):
    result = stage(tmp_path)
    assert result.returncode == 1
    assert "--app and --version" in result.stdout


def test_stage_keeps_app_names_when_asked(tmp_path):
    result = stage(tmp_path, "--names=app")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FormTray_0.9.8_x64-setup.exe" in {p.name for p in (tmp_path / "out").iterdir()}
