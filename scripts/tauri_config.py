import argparse
import json
import os
import re
import sys
from pathlib import Path

from public_urls import base_url, quoted


PLATFORM_FILES = {"macos": "tauri.macos.conf.json", "linux": "tauri.linux.conf.json", "windows": "tauri.windows.conf.json"}


def merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def load_extra(extra):
    extra = (extra or "").strip()
    if not extra:
        return {}
    if extra.startswith("{"):
        return json.loads(extra)
    path = Path(extra)
    if not path.is_file():
        sys.exit(f"::error::extra Tauri config {extra} is neither JSON nor a file")
    return json.loads(path.read_text(encoding="utf-8"))


def updater_endpoint(env):
    """The app's update feed in the download store, which the publishing pipeline writes on every stable release. The app's own
    tauri.conf.json may name a GitHub URL on this private repository, which the public cannot read."""
    app = env.get("FORMCOMPILER_APP", "").strip()
    try:
        base = base_url(env.get("FORMCOMPILER_PUBLIC_BASE", ""))
    except ValueError as error:
        sys.exit(f"::error::{error}")
    return f"{base}/{quoted(app, 'updates', 'latest.json')}" if base and app else ""


def msi_version(version):
    core, _, pre = version.partition("+")[0].partition("-")
    if not pre:
        return ""
    number = re.search(r"(\d+)$", pre)
    return f"{core}.{min(int(number.group(1)) if number else 0, 65535)}"


def build_config(runner_os, extra="", adhoc_macos=True, env=os.environ):
    config = {}
    uses_updater = env.get("FORMCOMPILER_UPDATER_TAURI", "true").strip().lower() not in ("false", "0", "no")
    if uses_updater and env.get("TAURI_SIGNING_PRIVATE_KEY", "").strip():
        merge(config, {"bundle": {"createUpdaterArtifacts": True}})
        if env.get("TAURI_UPDATER_PUBKEY", "").strip():
            merge(config, {"plugins": {"updater": {"pubkey": env["TAURI_UPDATER_PUBKEY"].strip()}}})
        endpoint = updater_endpoint(env)
        if endpoint:
            merge(config, {"plugins": {"updater": {"endpoints": [endpoint]}}})
    if runner_os == "windows" and env.get("WINDOWS_CERT_THUMBPRINT", "").strip():
        merge(config, {"bundle": {"windows": {
            "certificateThumbprint": env["WINDOWS_CERT_THUMBPRINT"].strip(),
            "digestAlgorithm": "sha256",
            "timestampUrl": "http://timestamp.digicert.com",
        }}})
    if runner_os == "windows":
        wix = msi_version(env.get("FORMCOMPILER_VERSION", "").strip())
        if wix:
            merge(config, {"bundle": {"windows": {"wix": {"version": wix}}}})
    if runner_os == "macos" and adhoc_macos and not env.get("APPLE_CERTIFICATE", "").strip() \
            and not env.get("APPLE_SIGNING_IDENTITY", "").strip():
        merge(config, {"bundle": {"macOS": {"signingIdentity": "-"}}})
    return merge(config, load_extra(extra))


def write_platform_configs(directories, runner_os, config):
    name = PLATFORM_FILES[runner_os]
    written = []
    for directory in directories:
        if (directory / f"{name}5").is_file() or (directory / f"Tauri.{runner_os}.toml").is_file():
            print(f"::warning::{directory} keeps its own {runner_os} config in TOML or JSON5; formcompiler's settings reach it only through --config")
            continue
        path = directory / name
        current = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        path.write_text(json.dumps(merge(current, json.loads(json.dumps(config))), indent=2), encoding="utf-8")
        written.append(path)
    return written


def write_config(config, out):
    if not config:
        return ""
    path = Path(out).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path.as_posix()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--os", required=True, choices=["macos", "linux", "windows"])
    parser.add_argument("--extra", default="")
    parser.add_argument("--no-adhoc", action="store_true")
    parser.add_argument("--out", default=str(Path(os.environ.get("RUNNER_TEMP", ".")) / "formcompiler.tauri.json"))
    args = parser.parse_args()
    config = build_config(args.os, args.extra, not args.no_adhoc)
    print(json.dumps(config, indent=2))
    print(write_config(config, args.out) or "no --config needed")


if __name__ == "__main__":
    main()
