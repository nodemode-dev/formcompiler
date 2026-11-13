import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPS = ROOT / "apps"

PLATFORM_NAMES = {
    "macos-arm64", "macos-x64", "macos-universal", "linux-x64", "linux-arm64",
    "windows-x64", "windows-x86", "windows-arm64",
}
OS_KEYS = ("macos", "linux", "windows")
PORTAL_ID = "formai"
DEFAULT_LINUX_PACKAGES = "libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev libxdo-dev patchelf"

STR, BOOL, LIST, OBJ = "str", "bool", "list", "obj"

TOP = {
    "app": (STR, True), "repository": (STR, True), "title": (STR, True), "enabled": (BOOL, True),
    "disabled_reason": (STR, False), "release": (STR, True), "version": (OBJ, True), "checks": (LIST, True),
    "platforms": (LIST, True), "platform_env": (OBJ, False), "toolchain": (OBJ, True), "build": (OBJ, True), "setup": (OBJ, False),
    "post_build": (OBJ, False), "artifacts": (LIST, False), "extras": (LIST, False), "image": (OBJ, False),
    "assets": (STR, False), "notes": (STR, False), "updater": (OBJ, True), "signing": (OBJ, True),
    "catalog": (OBJ, True), "agents": (OBJ, False), "notes_for_owner": (STR, False), "with_portal": (BOOL, False),
    "tag_trigger": (BOOL, False), "file_names": (STR, False),
}
AGENTS = {"skills": (STR, True), "mcp": (BOOL, True), "mcp_launch": (OBJ, False)}
MCP_LAUNCH = {"command": (STR, True), "args": (LIST, False)}
VERSION = {"file": (STR, True), "pattern": (STR, False)}
TOOLCHAIN = {
    "node": (STR, True), "python": (STR, True), "rust": (BOOL, True), "rust_targets": (STR, False),
    "rust_cache": (LIST, False), "go": (STR, False), "linux_packages": (STR, False), "windows_msvc": (BOOL, False),
    "pip_cache_macos": (BOOL, False), "build_cache": (OBJ, False),
}
BUILD_CACHE = {"paths": (LIST, True), "key_files": (LIST, True)}
BUILD = {
    "mode": (STR, True), "cli": (STR, False), "install": (BOOL, False), "install_args": (STR, False),
    "install_desktop": (BOOL, False), "windows_shell": (STR, True), "macos": (STR, False), "linux": (STR, False),
    "windows": (STR, False), "tauri_config": (STR, False),
}
PER_OS = {"macos": (STR, True), "linux": (STR, True), "windows": (STR, True)}
EXTRA = {
    "name": (STR, True), "runner": (STR, True), "experimental": (BOOL, False), "node": (STR, False),
    "python": (STR, False), "java": (STR, False), "go": (STR, False), "android": (BOOL, False),
    "rust": (BOOL, False), "rust_targets": (STR, False), "linux_packages": (STR, False), "run": (STR, True),
    "artifacts": (LIST, True),
}
IMAGE = {
    "name": (STR, True), "context": (STR, True), "file": (STR, True), "platforms": (STR, True),
    "build_args": (OBJ, False), "tags": (LIST, True),
}
UPDATER = {"tauri": (BOOL, True), "tag_json": (BOOL, True), "files": (LIST, True)}
SIGNING = {"macos": (STR, True), "windows": (STR, True)}
CATALOG = {
    "id": (STR, True), "name": (STR, True), "kind": (STR, True), "summary": (STR, True),
    "identifier": (STR, True), "licence": (STR, True), "state": (STR, True),
    "project_extensions": (LIST, False), "minimum_os": (OBJ, False),
}
TYPES = {STR: str, BOOL: bool, LIST: list, OBJ: dict}


def fields(where, data, spec, problems):
    if not isinstance(data, dict):
        problems.append(f"{where} must be an object")
        return
    for key in data:
        if key not in spec:
            problems.append(f"{where}.{key} is not a registry field")
    for key, (kind, required) in spec.items():
        if key not in data:
            if required:
                problems.append(f"{where}.{key} is missing")
            continue
        if not isinstance(data[key], TYPES[kind]):
            problems.append(f"{where}.{key} must be a {dict(str='string', bool='boolean', list='list', obj='object')[kind]}")


def build_cache_problems(cache):
    problems = []
    fields("toolchain.build_cache", cache, BUILD_CACHE, problems)
    if problems:
        return problems
    for key in ("paths", "key_files"):
        if not cache[key]:
            problems.append(f"toolchain.build_cache.{key} must not be empty")
        for item in cache[key]:
            if not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*", item) or item == "." or ".." in item.split("/"):
                problems.append(f"toolchain.build_cache.{key} entry {item!r} must be a plain path inside the app repository")
    return problems


def validate(entry, filename):
    problems = []
    fields("entry", entry, TOP, problems)
    if problems:
        return problems
    app = entry["app"]
    if filename and Path(filename).stem != app:
        problems.append(f"app {app!r} does not match the file name {Path(filename).name}")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9.-]{1,40}", app):
        problems.append(f"app {app!r} must be a plain repository name")
    if not re.fullmatch(r"nodemode-dev/[A-Za-z0-9._-]+", entry["repository"]):
        problems.append(f"repository {entry['repository']!r} must be nodemode-dev/<repo>")
    if entry["release"] not in ("draft", "publish"):
        problems.append("release must be draft or publish")
    if entry.get("file_names", "formcompiler") not in ("formcompiler", "app"):
        problems.append("file_names must be formcompiler or app")
    if not entry["enabled"] and not entry.get("disabled_reason", "").strip():
        problems.append("a disabled entry needs disabled_reason")
    fields("version", entry["version"], VERSION, problems)
    fields("toolchain", entry["toolchain"], TOOLCHAIN, problems)
    fields("build", entry["build"], BUILD, problems)
    fields("updater", entry["updater"], UPDATER, problems)
    fields("signing", entry["signing"], SIGNING, problems)
    fields("catalog", entry["catalog"], CATALOG, problems)
    for key in ("setup", "post_build"):
        if key in entry:
            fields(key, entry[key], PER_OS, problems)
    if problems:
        return problems
    version = entry["version"]
    suffix = Path(version["file"]).suffix
    if suffix not in (".json", ".toml") and not version.get("pattern"):
        problems.append(f"version file {version['file']} needs a pattern")
    if version.get("pattern"):
        try:
            if re.compile(version["pattern"]).groups < 1:
                problems.append("version pattern needs a group")
        except re.error as error:
            problems.append(f"version pattern does not compile: {error}")
    if not entry["checks"] or not all(isinstance(c, str) and re.fullmatch(r"[A-Za-z0-9._-]+\.ya?ml", c) for c in entry["checks"]):
        problems.append("checks must list the app's check workflow file names")
    for platform in entry["platforms"]:
        name = str(platform).rstrip("?").partition("=")[0]
        if name not in PLATFORM_NAMES:
            problems.append(f"unknown platform {platform!r}")
    listed = {str(p).rstrip("?").partition("=")[0] for p in entry["platforms"]}
    if any(name.startswith("macos-") for name in listed) and "macos-x64" not in entry["platforms"]:
        problems.append("every app with a Mac build also builds for Intel Macs: list macos-x64 (required, not macos-x64?)")
    for name, env in entry.get("platform_env", {}).items():
        if name not in listed:
            problems.append(f"platform_env names {name!r}, which is not in platforms")
        if not isinstance(env, dict) or not all(re.fullmatch(r"[A-Z][A-Z0-9_]*", k) and isinstance(v, str) for k, v in env.items()):
            problems.append(f"platform_env.{name} must map NAME to a string")
    build = entry["build"]
    if build["mode"] not in ("contract", "commands"):
        problems.append("build.mode must be contract or commands")
    if build["windows_shell"] not in ("cmd", "bash"):
        problems.append("build.windows_shell must be cmd or bash")
    if build["mode"] == "contract" and not re.fullmatch(r"[A-Za-z0-9._-]+", build.get("cli", "")):
        problems.append("build.cli must be the launcher's plain file name in contract mode")
    if build["mode"] == "contract" and not re.fullmatch(r"[A-Za-z0-9 ._=/-]*", build.get("install_args", "")):
        problems.append("build.install_args may hold only letters, digits, spaces and . _ = / -")
    if build["mode"] == "commands" and entry["platforms"]:
        wanted = {str(p).rstrip("?").partition("=")[0].split("-")[0] for p in entry["platforms"]}
        for os_name in wanted:
            if not build.get(os_name, "").strip():
                problems.append(f"build.{os_name} is empty but a {os_name} platform is listed")
    if "build_cache" in entry["toolchain"]:
        problems.extend(build_cache_problems(entry["toolchain"]["build_cache"]))
    packages = entry["toolchain"].get("linux_packages", "")
    if re.search(r"[^a-z0-9.+: -]", packages):
        problems.append("toolchain.linux_packages may hold only package names")
    names = set()
    for index, extra in enumerate(entry.get("extras", [])):
        fields(f"extras[{index}]", extra, EXTRA, problems)
        if isinstance(extra, dict) and isinstance(extra.get("name"), str):
            if not re.fullmatch(r"[a-z0-9-]+", extra["name"]) or extra["name"] in names:
                problems.append(f"extras[{index}].name must be [a-z0-9-]+ and unique")
            names.add(extra["name"])
            if re.search(r"[^a-z0-9.+: -]", extra.get("linux_packages", "")):
                problems.append(f"extras[{index}].linux_packages may hold only package names")
    if "image" in entry:
        fields("image", entry["image"], IMAGE, problems)
    if not entry["platforms"] and not entry.get("extras"):
        problems.append("an entry with no platforms needs at least one extra")
    updater = entry["updater"]
    if updater["tauri"] and updater["tag_json"]:
        problems.append("updater.tauri and updater.tag_json cannot both be true")
    if entry["signing"]["macos"] not in ("apple", "developer-id", "adhoc", "none"):
        problems.append("signing.macos must be apple, developer-id, adhoc or none")
    if entry["signing"]["windows"] not in ("certificate", "none"):
        problems.append("signing.windows must be certificate or none")
    catalog = entry["catalog"]
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", catalog["id"]):
        problems.append("catalog.id must match FormPortal's ^[a-z][a-z0-9-]{1,31}$")
    if not re.fullmatch(r"[a-z][a-z-]{1,23}", catalog["kind"]):
        problems.append("catalog.kind must match FormPortal's ^[a-z][a-z-]{1,23}$")
    if not re.fullmatch(r"[a-z0-9]+(\.[a-z0-9-]+)+", catalog["identifier"]):
        problems.append("catalog.identifier must match FormPortal's identifier pattern")
    if catalog["state"] not in ("prelaunch", "public", "live"):
        problems.append("catalog.state must be prelaunch, public or live")
    for ext in catalog.get("project_extensions", []):
        if not re.fullmatch(r"\.[a-z0-9]+", str(ext)):
            problems.append(f"catalog.project_extensions entry {ext!r} must look like .ext")
    if "minimum_os" in catalog:
        fields("catalog.minimum_os", catalog["minimum_os"], {k: (STR, False) for k in OS_KEYS}, problems)
    if "agents" in entry:
        agents = entry["agents"]
        fields("agents", agents, AGENTS, problems)
        if isinstance(agents, dict) and isinstance(agents.get("skills"), str):
            skills = agents["skills"]
            if skills and (skills.startswith("/") or ".." in Path(skills).parts or not re.fullmatch(r"[A-Za-z0-9._/-]+", skills)):
                problems.append("agents.skills must be a folder inside the app repository, for example .claude/skills, or empty")
        if isinstance(agents, dict) and "mcp_launch" in agents:
            fields("agents.mcp_launch", agents["mcp_launch"], MCP_LAUNCH, problems)
            launch = agents["mcp_launch"]
            if isinstance(launch, dict) and isinstance(launch.get("command"), str):
                if not agents.get("mcp"):
                    problems.append("agents.mcp_launch needs agents.mcp true")
                if not launch["command"].strip() or launch["command"].startswith("/") or ".." in Path(launch["command"]).parts:
                    problems.append("agents.mcp_launch.command must be a path inside the installed app, relative to form-app.json")
                if not all(isinstance(a, str) for a in launch.get("args", [])):
                    problems.append("agents.mcp_launch.args must be strings")
    if entry.get("with_portal"):
        if entry["catalog"]["id"] == PORTAL_ID:
            problems.append("with_portal is for the apps FormPortal installs, not FormPortal itself")
        if not entry["platforms"]:
            problems.append("with_portal needs desktop platforms")
    return problems


def load(app):
    path = APPS / f"{app}.json"
    if not path.is_file():
        sys.exit(f"::error::no registry entry apps/{app}.json")
    entry = json.loads(path.read_text(encoding="utf-8"))
    problems = validate(entry, path)
    if problems:
        sys.exit("::error::" + "; ".join(f"apps/{app}.json: {p}" for p in problems))
    return entry


def all_entries():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(APPS.glob("*.json"))]


def per_os(entry, key, os_name):
    return entry.get(key, {}).get(os_name, "")


def config(entry):
    tool, build = entry["toolchain"], entry["build"]
    return {
        "app": entry["app"],
        "repository": entry["repository"],
        "title": entry["title"],
        "release": entry["release"],
        "version_file": entry["version"]["file"],
        "version_pattern": entry["version"].get("pattern", ""),
        "checks": ",".join(entry["checks"]),
        "has_desktop": bool(entry["platforms"]),
        "platforms": ",".join(entry["platforms"]),
        "platform_env": json.dumps(entry.get("platform_env", {}), separators=(",", ":")),
        "cli": build.get("cli", "") or entry["app"],
        "build_mode": build["mode"],
        "install": bool(build.get("install", False)) and build["mode"] == "contract",
        "install_args": build.get("install_args", ""),
        "install_desktop": bool(build.get("install_desktop", False)) and build["mode"] == "contract",
        "windows_shell": build["windows_shell"],
        "build_macos": build.get("macos", "") if build["mode"] == "commands" else "",
        "build_linux": build.get("linux", "") if build["mode"] == "commands" else "",
        "build_windows": build.get("windows", "") if build["mode"] == "commands" else "",
        "tauri_config": build.get("tauri_config", ""),
        "setup_macos": per_os(entry, "setup", "macos"),
        "setup_linux": per_os(entry, "setup", "linux"),
        "setup_windows": per_os(entry, "setup", "windows"),
        "post_build_macos": per_os(entry, "post_build", "macos"),
        "post_build_linux": per_os(entry, "post_build", "linux"),
        "post_build_windows": per_os(entry, "post_build", "windows"),
        "artifacts": "\n".join(entry.get("artifacts", [])),
        "node": tool["node"],
        "python": tool["python"],
        "rust": tool["rust"],
        "rust_targets": tool.get("rust_targets", ""),
        "rust_cache": "\n".join(tool.get("rust_cache", [])) or "src-tauri",
        "go": tool.get("go", ""),
        "linux_packages": tool.get("linux_packages", "") or DEFAULT_LINUX_PACKAGES,
        "windows_msvc": bool(tool.get("windows_msvc", False)),
        "pip_cache_macos": bool(tool.get("pip_cache_macos", False)),
        "build_cache_paths": "\n".join(tool.get("build_cache", {}).get("paths", [])),
        "build_cache_key_files": "\n".join(tool.get("build_cache", {}).get("key_files", [])),
        "macos_signing": entry["signing"]["macos"],
        "windows_signing": entry["signing"]["windows"],
        "updater_tauri": entry["updater"]["tauri"],
        "has_extras": bool(entry.get("extras")),
        "has_image": "image" in entry,
        "has_assets": bool(entry.get("assets", "").strip()),
        "with_portal": bool(entry.get("with_portal", False)),
        "file_names": entry.get("file_names", "formcompiler"),
    }


def extras_matrix(entry):
    rows = []
    for extra in entry.get("extras", []):
        row = {key: extra.get(key, default) for key, default in (
            ("name", ""), ("runner", ""), ("experimental", False), ("node", ""), ("python", ""),
            ("java", ""), ("go", ""), ("android", False), ("rust", False), ("rust_targets", ""),
            ("linux_packages", ""), ("run", ""))}
        row["artifacts"] = "\n".join(extra["artifacts"])
        rows.append(row)
    return {"include": rows}


def write_outputs(values):
    target = os.environ.get("GITHUB_OUTPUT")
    lines = []
    for key, value in values.items():
        text = value if isinstance(value, str) else json.dumps(value, separators=(",", ":"))
        lines.append(f"{key}<<FORMCOMPILER_EOF\n{text}\nFORMCOMPILER_EOF\n")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.writelines(lines)
    return lines


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    listing = sub.add_parser("list")
    listing.add_argument("--enabled", action="store_true")
    show = sub.add_parser("config")
    show.add_argument("--app", required=True)
    args = parser.parse_args()

    if args.command == "check":
        bad = 0
        paths = sorted(APPS.glob("*.json"))
        catalog_ids = {}
        for path in paths:
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                print(f"apps/{path.name}: not JSON: {error}")
                bad += 1
                continue
            problems = validate(entry, path)
            if isinstance(entry, dict) and isinstance(entry.get("catalog"), dict):
                cid = entry["catalog"].get("id")
                if cid in catalog_ids:
                    problems.append(f"catalog.id {cid!r} is also used by {catalog_ids[cid]}")
                catalog_ids[cid] = path.name
            for problem in problems:
                print(f"apps/{path.name}: {problem}")
            bad += bool(problems)
        print(f"registry: {len(paths)} entries, {len(paths) - bad} valid")
        sys.exit(1 if bad or not paths else 0)
    if args.command == "list":
        apps = [e["app"] for e in all_entries() if e.get("enabled") or not args.enabled]
        print(json.dumps(apps))
        return
    entry = load(args.app)
    if not entry["enabled"]:
        sys.exit(f"::error::{entry['app']} is disabled in the registry: {entry.get('disabled_reason', '')}")
    values = {"config": config(entry), "extras": extras_matrix(entry), "image": entry.get("image", {}),
              "assets": entry.get("assets", ""), "notes": entry.get("notes", ""), "updater": entry["updater"],
              "notes_for_owner": entry.get("notes_for_owner", "")}
    write_outputs(values)
    print(json.dumps(values, indent=2))


if __name__ == "__main__":
    main()
