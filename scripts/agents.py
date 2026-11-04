import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan import SEMVER
from registry import load

MANIFEST = "form-app.json"
FORMAT = "form-app"
FORMAT_VERSION = 2
STAMP = (1980, 1, 1, 0, 0, 0)
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def skills_name(app, version):
    return f"{app}-skills-v{version}.zip"


def front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    found, block = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if value in (">", "|", ">-", "|-", ">+", "|+"):
                found[key], block = "", key
            else:
                found[key], block = value.strip("\"'"), None
        elif block and line.strip():
            found[block] = (found[block] + " " + line.strip()).strip()
    return found


def skill_files(folder, root):
    files = []
    for current, dirs, names in os.walk(folder, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if name in SKIP_FILES or name.endswith(".pyc"):
                continue
            path = Path(current) / name
            if path.is_symlink() and not path.resolve().is_relative_to(root.resolve()):
                fail(f"{path} links outside the skills folder")
            if path.is_file():
                files.append(path)
    return files


def collect(skills_dir):
    skills = []
    for folder in sorted(p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")):
        card = folder / "SKILL.md"
        if not card.is_file():
            continue
        meta = front_matter(card.read_text(encoding="utf-8", errors="replace"))
        skills.append({
            "folder": folder.name,
            "name": meta.get("name") or folder.name,
            "description": meta.get("description", ""),
            "files": skill_files(folder, skills_dir),
        })
    return skills


def write_zip(target, skills_dir, skills):
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for skill in skills:
            for path in skill["files"]:
                info = zipfile.ZipInfo(path.relative_to(skills_dir).as_posix(), date_time=STAMP)
                info.create_system = 3
                info.external_attr = (0o755 if os.access(path, os.X_OK) else 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())


def build(args):
    entry = load(args.app)
    agents = entry.get("agents") or {"skills": "", "mcp": False}
    if not SEMVER.match(args.version):
        fail(f"{args.version!r} is not a version")
    app_dir = Path(args.app_dir)
    dist = Path(args.dist)
    dist.mkdir(parents=True, exist_ok=True)
    mcp = {"available": bool(agents.get("mcp"))}
    if agents.get("mcp_launch"):
        mcp["command"] = agents["mcp_launch"]["command"]
        mcp["args"] = list(agents["mcp_launch"].get("args", []))
    manifest = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "id": entry["catalog"]["id"],
        "app": entry["app"],
        "name": entry["catalog"]["name"],
        "version": args.version,
        "repository": entry["repository"],
        "tag": f"v{args.version}",
    }
    if args.commit:
        manifest["commit"] = args.commit
    manifest["agents"] = {"mcp": mcp}
    if agents.get("skills"):
        skills_dir = app_dir / agents["skills"]
        if not skills_dir.is_dir():
            fail(f"apps/{args.app}.json names the skills folder {agents['skills']}, which is not in the app at this commit")
        skills = collect(skills_dir)
        if not skills:
            fail(f"{agents['skills']} holds no folder with a SKILL.md")
        target = dist / skills_name(entry["app"], args.version)
        write_zip(target, skills_dir, skills)
        manifest["agents"]["skills"] = {
            "file": target.name,
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
            "root": agents["skills"],
            "skills": [{"folder": s["folder"], "name": s["name"], "description": s["description"], "files": len(s["files"])} for s in skills],
        }
        print(f"{target.name}: {len(skills)} skills, {sum(len(s['files']) for s in skills)} files, {target.stat().st_size} bytes")
    else:
        print(f"{args.app}: no skills folder in the registry; {MANIFEST} has no skills")
    (dist / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{MANIFEST}: format_version {FORMAT_VERSION}, mcp {'yes' if mcp['available'] else 'no'}")


def check(args):
    dist = Path(args.dist)
    path = dist / MANIFEST
    if not path.is_file():
        fail(f"no {MANIFEST} in {dist}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"{MANIFEST} is not JSON: {error}")
    problems = []
    if manifest.get("format") != FORMAT:
        problems.append(f"format must be {FORMAT!r}")
    if manifest.get("format_version") != FORMAT_VERSION:
        problems.append(f"format_version must be {FORMAT_VERSION}")
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", str(manifest.get("id", ""))):
        problems.append("id must be a catalogue id")
    if not SEMVER.match(str(manifest.get("version", ""))):
        problems.append("version must be a version")
    if args.app and manifest.get("app") != args.app:
        problems.append(f"app is {manifest.get('app')!r}, not {args.app!r}")
    if "commit" in manifest and not re.fullmatch(r"[0-9a-f]{7,40}", str(manifest["commit"])):
        problems.append("commit must be a hex commit")
    if not re.fullmatch(r"nodemode-dev/[A-Za-z0-9._-]+", str(manifest.get("repository", ""))):
        problems.append("repository must be the app's nodemode-dev repository")
    if manifest.get("tag") != f"v{manifest.get('version', '')}":
        problems.append("tag must be v<version>")
    agents = manifest.get("agents")
    if not isinstance(agents, dict) or not isinstance(agents.get("mcp"), dict) or not isinstance(agents["mcp"].get("available"), bool):
        problems.append("agents.mcp.available must be a boolean")
        agents = {}
    skills = agents.get("skills")
    if skills is not None:
        name = str(skills.get("file", ""))
        archive = dist / name
        if name != skills_name(manifest.get("app", ""), manifest.get("version", "")):
            problems.append(f"agents.skills.file {name!r} is not named <app>-skills-v<version>.zip")
        elif not archive.is_file():
            problems.append(f"{name} is missing beside {MANIFEST}")
        else:
            if archive.stat().st_size != skills.get("bytes"):
                problems.append(f"{name} is {archive.stat().st_size} bytes, the manifest says {skills.get('bytes')}")
            if sha256(archive) != skills.get("sha256"):
                problems.append(f"{name} does not match its sha256")
            with zipfile.ZipFile(archive) as opened:
                names = opened.namelist()
            if any(n.startswith("/") or ".." in n.split("/") for n in names):
                problems.append(f"{name} has a path outside its folder")
            declared = {s["folder"]: s["files"] for s in skills.get("skills", [])}
            counted = {}
            for n in names:
                counted[n.split("/", 1)[0]] = counted.get(n.split("/", 1)[0], 0) + 1
            if counted != declared:
                problems.append(f"{name} holds {sorted(counted)} with {counted}, the manifest declares {declared}")
            for folder in declared:
                if f"{folder}/SKILL.md" not in names:
                    problems.append(f"{name} has no {folder}/SKILL.md")
    if problems:
        fail(f"{MANIFEST}: " + "; ".join(problems))
    count = len(skills.get("skills", [])) if skills else 0
    print(f"{MANIFEST} valid: {manifest['app']} {manifest['version']}, mcp {'yes' if agents['mcp']['available'] else 'no'}, {count} skills")


def main():
    parser = argparse.ArgumentParser(description="form-app.json and the skills asset of one release")
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("build")
    make.add_argument("--app", required=True)
    make.add_argument("--app-dir", default="app")
    make.add_argument("--dist", default="dist")
    make.add_argument("--version", required=True)
    make.add_argument("--commit", default="")
    verify = sub.add_parser("check")
    verify.add_argument("--dist", default="dist")
    verify.add_argument("--app", default="")
    args = parser.parse_args()
    build(args) if args.command == "build" else check(args)


if __name__ == "__main__":
    main()
