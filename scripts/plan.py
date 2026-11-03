import argparse
import json
import os
import re
import sys
from pathlib import Path

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$")

PLATFORMS = {
    "macos-arm64": {"runner": "macos-latest", "os": "macos", "arch": "aarch64", "updater": "darwin-aarch64", "triple": "aarch64-apple-darwin"},
    "macos-x64": {"runner": "macos-15-intel", "os": "macos", "arch": "x64", "updater": "darwin-x86_64", "triple": "x86_64-apple-darwin"},
    "macos-universal": {"runner": "macos-latest", "os": "macos", "arch": "universal", "updater": "darwin-universal", "triple": "universal-apple-darwin", "targets": "aarch64-apple-darwin,x86_64-apple-darwin", "target_args": "--target universal-apple-darwin"},
    "linux-x64": {"runner": "ubuntu-22.04", "os": "linux", "arch": "x64", "updater": "linux-x86_64", "triple": "x86_64-unknown-linux-gnu"},
    "linux-arm64": {"runner": "ubuntu-22.04-arm", "os": "linux", "arch": "aarch64", "updater": "linux-aarch64", "triple": "aarch64-unknown-linux-gnu"},
    "windows-x64": {"runner": "windows-latest", "os": "windows", "arch": "x64", "updater": "windows-x86_64", "triple": "x86_64-pc-windows-msvc"},
    "windows-arm64": {"runner": "windows-11-arm", "os": "windows", "arch": "aarch64", "updater": "windows-aarch64", "triple": "aarch64-pc-windows-msvc"},
    "windows-x86": {"runner": "windows-latest", "os": "windows", "arch": "x86", "updater": "windows-i686", "triple": "i686-pc-windows-msvc", "targets": "i686-pc-windows-msvc", "target_args": "--target i686-pc-windows-msvc", "pyarch": "x86"},
}


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def read_version(path, pattern):
    file = Path(path)
    if not file.is_file():
        fail(f"version file {path} not found")
    return parse_version(file.read_text(encoding="utf-8"), path, pattern)


def parse_version(text, path, pattern):
    file = Path(path)
    if pattern:
        found = re.search(pattern, text, re.M)
        if not found:
            fail(f"version pattern {pattern!r} matched nothing in {path}")
        return found.group(1)
    if file.suffix == ".json":
        value = json.loads(text).get("version")
        if not isinstance(value, str):
            fail(f"{path} has no string \"version\" field")
        return value
    if file.suffix == ".toml":
        import tomllib
        data = tomllib.loads(text)
        for table in (data.get("package", {}), data.get("workspace", {}).get("package", {})):
            if isinstance(table.get("version"), str):
                return table["version"]
        fail(f"{path} has no [package] or [workspace.package] version")
    return text.strip().splitlines()[0].strip() if text.strip() else fail(f"{path} is empty")


def plan_matrix(spec, platform_env=None, rust_targets=""):
    platform_env = platform_env or {}
    extra_targets = [t.strip() for t in rust_targets.split(",") if t.strip()]
    include = []
    for entry in [item.strip() for item in re.split(r"[,\s]+", spec) if item.strip()]:
        experimental = entry.endswith("?")
        name, _, runner = entry.rstrip("?").partition("=")
        if name not in PLATFORMS:
            fail(f"unknown platform {name!r}; known: {', '.join(PLATFORMS)}")
        row = {"platform": name, "targets": "", "target_args": "", "pyarch": "", **PLATFORMS[name], "experimental": experimental}
        if runner:
            row["runner"] = runner
        row["release_dir"] = f"src-tauri/target/{row['triple']}/release" if row["target_args"] else "src-tauri/target/release"
        targets = [t for t in row["targets"].split(",") if t] + extra_targets
        row["targets"] = ",".join(dict.fromkeys(targets))
        row["env"] = json.dumps(platform_env.get(name, {}), separators=(",", ":"))
        include.append(row)
    if not include:
        fail("no platforms to build")
    names = [row["platform"] for row in include]
    if len(set(names)) != len(names):
        fail(f"a platform is listed twice: {', '.join(names)}")
    return {"include": include}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version-file", default="src-tauri/tauri.conf.json")
    parser.add_argument("--version-pattern", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--platforms", default="macos-arm64,linux-x64,windows-x64")
    parser.add_argument("--ref", default=os.environ.get("GITHUB_REF", ""))
    parser.add_argument("--tag-prefix", default="v")
    parser.add_argument("--expect-version", default="")
    parser.add_argument("--platform-env", default="{}")
    parser.add_argument("--rust-targets", default="")
    args = parser.parse_args()
    try:
        platform_env = json.loads(args.platform_env or "{}")
    except json.JSONDecodeError as error:
        fail(f"--platform-env is not JSON: {error}")

    version = (args.version or read_version(args.version_file, args.version_pattern)).strip().removeprefix("v")
    if not SEMVER.match(version):
        fail(f"{version!r} is not a version like 1.2.3 or 1.2.3-rc.1")
    if args.expect_version and args.expect_version.removeprefix("v") != version:
        fail(f"the compile branch names {args.expect_version} but {args.version_file} says {version}; bump the version on main and cut the branch again")
    if not re.fullmatch(r"[A-Za-z0-9.]+-v|v", args.tag_prefix):
        fail(f"tag prefix {args.tag_prefix!r} must be v or <app>-v")
    tag = f"{args.tag_prefix}{version}"
    if args.ref.startswith("refs/tags/") and args.ref != f"refs/tags/{tag}":
        fail(f"the pushed tag {args.ref.removeprefix('refs/tags/')} does not match the app version {version}; bump the version or push {tag}")

    outputs = {
        "version": version,
        "tag": tag,
        "prerelease": "true" if "-" in version.split("+")[0] else "false",
        "matrix": json.dumps(plan_matrix(args.platforms, platform_env, args.rust_targets), separators=(",", ":")),
    }
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            for key, value in outputs.items():
                handle.write(f"{key}={value}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            rows = json.loads(outputs["matrix"])["include"]
            handle.write(f"### {tag}\n\n" + "\n".join(f"- {row['platform']} on `{row['runner']}`" for row in rows) + "\n")
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
