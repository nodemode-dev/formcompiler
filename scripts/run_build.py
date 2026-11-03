import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tauri_config import build_config, write_config, write_platform_configs
from windows_signing import tauri_dirs

SECRET_GROUPS = [
    ("APPLE_CERTIFICATE", "APPLE_CERTIFICATE_PASSWORD"),
    ("APPLE_SIGNING_IDENTITY",),
    ("APPLE_ID", "APPLE_PASSWORD", "APPLE_TEAM_ID"),
    ("TAURI_SIGNING_PRIVATE_KEY", "TAURI_SIGNING_PRIVATE_KEY_PASSWORD"),
    ("WINDOWS_CERT_THUMBPRINT",),
    ("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"),
]


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def flag(value):
    return str(value).strip().lower() in ("1", "true", "yes")


def clean_secrets(env):
    for group in SECRET_GROUPS:
        if not env.get(group[0], "").strip():
            for name in group:
                env.pop(name, None)
        else:
            for name in group[1:]:
                if not env.get(name, "").strip():
                    env.pop(name, None)
    return env


def without_empty_tauri_config(env):
    if not env.get("TAURI_CONFIG", "").strip():
        env.pop("TAURI_CONFIG", None)
    return env


def default_lines(shell, cli, install, install_args, install_desktop, config_arg="", target_args=""):
    run = f"call {cli}.bat" if shell == "cmd" else f"./{cli}"
    lines = []
    if install:
        lines.append(f"{run} install {install_args}".rstrip())
    if install_desktop:
        lines.append(f"{run} install-desktop")
    if config_arg:
        config_arg = config_arg if shell == "cmd" else f"--config '{config_arg.removeprefix('--config ')}'"
    if not re.fullmatch(r"(--target [A-Za-z0-9_-]+)?", target_args.strip()):
        fail(f"target arguments {target_args!r} must be --target <triple>")
    lines.append(" ".join(part for part in (f"{run} desktop build", config_arg, target_args.strip()) if part))
    return lines


def platform_env(env):
    import json
    try:
        extra = json.loads(env.get("FORMCOMPILER_PLATFORM_ENV", "") or "{}")
    except json.JSONDecodeError:
        fail("FORMCOMPILER_PLATFORM_ENV is not JSON")
    for key, value in extra.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            fail(f"platform environment name {key!r} is not allowed")
        env[key] = str(value)
    return env


def minimum_macos(conf="src-tauri/tauri.conf.json"):
    path = Path(conf)
    if not path.is_file():
        return ""
    import json
    macos = json.loads(path.read_text(encoding="utf-8")).get("bundle", {}).get("macOS", {}) or {}
    return str(macos.get("minimumSystemVersion", "") or "")


def windows_bash(path_value, is_file=os.path.isfile):
    for directory in path_value.split(";"):
        directory = directory.strip().strip('"').rstrip("\\")
        lowered = directory.lower()
        if not directory or lowered.endswith("\\system32") or lowered.endswith("\\windowsapps"):
            continue
        candidate = f"{directory}\\bash.exe"
        if is_file(candidate):
            return candidate
    return None


MSVC_TRIPLES = {"x64": "X86_64", "arm64": "AARCH64", "x86": "I686"}


def msvc_linkers(path_value, is_file=os.path.isfile):
    for directory in path_value.split(";"):
        match = re.fullmatch(r"(.*\\VC\\Tools\\MSVC\\[^\\]+\\bin\\Host(?:x64|arm64|x86))\\(?:x64|arm64|x86)\\?",
                             directory.strip().strip('"'), re.IGNORECASE)
        if not match:
            continue
        links = {f"CARGO_TARGET_{triple}_PC_WINDOWS_MSVC_LINKER": f"{match.group(1)}\\{arch}\\link.exe"
                 for arch, triple in MSVC_TRIPLES.items()}
        return {name: link for name, link in links.items() if is_file(link)}
    return {}


def run_bash(lines, env, runner_os):
    script = "\n".join(lines)
    bash = "bash"
    if runner_os == "windows":
        bash = windows_bash(env.get("PATH", "")) or fail("Git Bash is not on PATH; a bare bash would start the WSL launcher")
    return subprocess.run([bash, "-eo", "pipefail", "-c", script], env=env).returncode


def run_cmd(lines, env):
    names = sorted((k for k in env if k.startswith("FORMCOMPILER_")), key=len, reverse=True)
    for name in names:
        lines = [line.replace(f"%{name}%", env[name]) for line in lines]
    body = "@echo off\r\n" + "".join(f"{line}\r\nif errorlevel 1 exit /b 1\r\n" for line in lines)
    with tempfile.NamedTemporaryFile("w", suffix=".cmd", delete=False, dir=env.get("RUNNER_TEMP")) as handle:
        handle.write(body)
        path = handle.name
    return subprocess.run(["cmd", "/d", "/c", path], env=env).returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--os", required=True, choices=["macos", "linux", "windows"])
    parser.add_argument("--cli", required=True)
    parser.add_argument("--install", default="true")
    parser.add_argument("--install-args", default="")
    parser.add_argument("--install-desktop", default="true")
    parser.add_argument("--windows-shell", default="cmd", choices=["cmd", "bash"])
    parser.add_argument("--command", default="")
    parser.add_argument("--extra-config", default="")
    parser.add_argument("--adhoc-macos", default="true")
    parser.add_argument("--phase", default="build", choices=["build", "post-build"])
    args = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.cli):
        fail(f"cli {args.cli!r} must be a plain file name")
    if not re.fullmatch(r"[A-Za-z0-9 ._=/-]*", args.install_args):
        fail(f"install-args {args.install_args!r} may hold only letters, digits, spaces and . _ = / -")

    env = without_empty_tauri_config(platform_env(clean_secrets(dict(os.environ))))
    env.setdefault("FORMCOMPILER_TARGET_ARGS", "")
    config = build_config(args.os, args.extra_config, flag(args.adhoc_macos), env)
    config_path = write_config(config, Path(env.get("RUNNER_TEMP", tempfile.gettempdir())) / "formcompiler.tauri.json")
    if args.phase == "build" and config:
        for path in write_platform_configs(tauri_dirs(Path.cwd()), args.os, config):
            print(f"formcompiler: tauri config merged into {path}")
    env["FORMCOMPILER_TAURI_CONFIG"] = config_path
    env["FORMCOMPILER_CONFIG_ARG"] = f"--config {config_path}" if config_path else ""
    if args.os == "windows":
        for name, link in msvc_linkers(env.get("PATH", "")).items():
            env.setdefault(name, link)
    if args.os == "macos" and not env.get("MACOSX_DEPLOYMENT_TARGET"):
        minimum = minimum_macos()
        if minimum:
            env["MACOSX_DEPLOYMENT_TARGET"] = minimum

    shell = args.windows_shell if args.os == "windows" else "bash"
    lines = [line.rstrip() for line in args.command.splitlines() if line.strip()]
    if args.phase == "post-build":
        shell = "bash"
        if not lines:
            print("formcompiler: no post-build commands")
            return
    elif not lines:
        lines = default_lines(shell, args.cli, flag(args.install), args.install_args, flag(args.install_desktop),
                              env["FORMCOMPILER_CONFIG_ARG"], env.get("FORMCOMPILER_TARGET_ARGS", ""))

    print(f"formcompiler: {args.os} build in {shell}, tauri config: {config_path or 'none'}")
    for line in lines:
        print(f"  {line}")
    sys.stdout.flush()
    code = run_cmd(lines, env) if shell == "cmd" else run_bash(lines, env, args.os)
    if code:
        fail(f"the build exited {code}")


if __name__ == "__main__":
    main()
