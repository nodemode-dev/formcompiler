import argparse
import glob
import json
import re
import shutil
import sys
from pathlib import Path

DEFAULT_ARTIFACTS = [
    "src-tauri/target/**/bundle/dmg/*.dmg",
    "src-tauri/target/**/bundle/macos/*.app.tar.gz",
    "src-tauri/target/**/bundle/appimage/*.AppImage",
    "src-tauri/target/**/bundle/deb/*.deb",
    "src-tauri/target/**/bundle/rpm/*.rpm",
    "src-tauri/target/**/bundle/msi/*.msi",
    "src-tauri/target/**/bundle/nsis/*.exe",
    "src-tauri/target/**/bundle/*/*.sig",
]

UPDATER_PATTERNS = {
    "macos": [r"\.app\.tar\.gz$"],
    "linux": [r"\.AppImage$"],
    "windows": [r"-setup\.exe$", r"\.msi$"],
}


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


KINDS = (
    ".app.tar.gz", ".tar.gz", ".AppImage.zsync", ".AppImage", "-setup.exe", ".dmg", ".deb", ".rpm", ".msi", ".zip",
)
NAMES = ("formcompiler", "app")


def app_name(name, runner_os, arch):
    if runner_os == "macos":
        for suffix in (".app.tar.gz.sig", ".app.tar.gz"):
            stem = name[: -len(suffix)] if name.endswith(suffix) else ""
            if stem and "-" not in stem and "_" not in stem:
                return name[: -len(suffix)] + f"_{arch}" + suffix
    return name


def release_name(name, app, version, platform):
    if name.endswith(".sig"):
        return release_name(name[: -len(".sig")], app, version, platform) + ".sig"
    lower = name.lower()
    for suffix in KINDS:
        if lower.endswith(suffix.lower()):
            return f"{app}-{version}-{platform}{suffix}"
    return name


def staged_name(name, runner_os, arch, names="app", app="", version="", platform=""):
    if names == "app":
        return app_name(name, runner_os, arch)
    return release_name(name, app, version, platform)


def pick_updater(names, runner_os, out):
    for pattern in UPDATER_PATTERNS[runner_os]:
        for name in sorted(names):
            if re.search(pattern, name) and f"{name}.sig" in names:
                return {"file": name, "signature": (out / f"{name}.sig").read_text(encoding="utf-8").strip()}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--os", required=True, choices=["macos", "linux", "windows"])
    parser.add_argument("--arch", required=True)
    parser.add_argument("--updater-key", required=True)
    parser.add_argument("--artifacts", default="")
    parser.add_argument("--names", default="formcompiler", choices=NAMES)
    parser.add_argument("--app", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--out", default="out")
    args = parser.parse_args()
    if args.names == "formcompiler" and not (args.app and args.version):
        fail("--names formcompiler needs --app and --version to name the files <app>-<version>-<platform>")

    patterns = [p.strip() for p in re.split(r"[\n,]+", args.artifacts) if p.strip()] or DEFAULT_ARTIFACTS
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    staged = {}
    for pattern in patterns:
        for source in sorted(glob.glob(pattern, recursive=True)):
            path = Path(source)
            if not path.is_file():
                continue
            name = staged_name(path.name, args.os, args.arch, args.names, args.app, args.version, args.platform)
            if name in staged and staged[name] != path.resolve():
                fail(f"two files would both be staged as {name}: {staged[name]} and {path}")
            staged[name] = path.resolve()
    if not staged:
        fail(f"no files matched {', '.join(patterns)}")
    for name, source in staged.items():
        shutil.copy2(source, out / name)

    manifest = {
        "platform": args.platform,
        "updater_key": args.updater_key,
        "files": sorted(staged),
        "update": pick_updater(set(staged), args.os, out),
    }
    (out / f"{args.platform}.formcompiler.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for name in sorted(staged):
        print(f"staged {name}  <-  {staged[name]}")
    print(f"updater: {manifest['update']['file'] if manifest['update'] else 'none (no .sig beside an updater bundle)'}")


if __name__ == "__main__":
    main()
