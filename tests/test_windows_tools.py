"""Which bash and which linker a Windows build gets, from the PATH the Git Bash step hands run_build.py."""
import re
from pathlib import Path

from run_build import msvc_linkers, windows_bash

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "desktop-release.yml"
MSVC = r"C:\Program Files\Microsoft Visual Studio\18\Enterprise\VC\Tools\MSVC\14.51.36231\bin"
GIT_BASH = r"C:\Program Files\Git\usr\bin\bash.exe"
WSL = r"C:\Windows\system32\bash.exe"


def present(*paths):
    return lambda candidate: candidate in paths


def test_a_bare_bash_is_never_the_wsl_launcher_even_when_system32_comes_first():
    path = r"C:\Windows\system32;C:\Program Files\Git\usr\bin;C:\Windows"
    assert windows_bash(path, present(WSL, GIT_BASH)) == GIT_BASH


def test_windows_bash_skips_the_store_alias_and_quoted_entries_still_match():
    alias = r"C:\Users\runneradmin\AppData\Local\Microsoft\WindowsApps\bash.exe"
    path = r'C:\Users\runneradmin\AppData\Local\Microsoft\WindowsApps;"C:\Program Files\Git\usr\bin"'
    assert windows_bash(path, present(alias, GIT_BASH)) == GIT_BASH


def test_windows_bash_is_none_when_only_wsl_is_there():
    assert windows_bash(r"C:\Windows\system32", present(WSL)) is None


def test_the_msvc_linker_is_named_for_each_target_so_git_link_exe_cannot_win():
    path = rf"C:\Program Files\Git\usr\bin;{MSVC}\HostX64\x64;C:\Windows\system32"
    links = [rf"{MSVC}\HostX64\x64\link.exe", rf"{MSVC}\HostX64\arm64\link.exe"]
    assert msvc_linkers(path, present(*links)) == {
        "CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER": links[0],
        "CARGO_TARGET_AARCH64_PC_WINDOWS_MSVC_LINKER": links[1],
    }


def test_an_arm64_host_names_its_own_linkers():
    path = rf"{MSVC}\HostARM64\arm64"
    link = rf"{MSVC}\HostARM64\arm64\link.exe"
    assert msvc_linkers(path, present(link)) == {"CARGO_TARGET_AARCH64_PC_WINDOWS_MSVC_LINKER": link}


def test_no_msvc_on_path_names_no_linker():
    assert msvc_linkers(r"C:\Program Files\Git\usr\bin;C:\Windows\system32", present()) == {}


def test_stapling_is_retried_after_a_dropped_connection():
    text = WORKFLOW.read_text()
    step = text.split("- name: Notarize the macOS disk images", 1)[1].split("\n      - name:", 1)[0]
    assert re.search(r"for attempt in 1 2 3 4 5; do\s+if xcrun stapler staple \"\$dmg\" && xcrun stapler validate \"\$dmg\"", step)
    assert not re.search(r"(?m)^\s+xcrun stapler staple \"\$dmg\"$", step)
