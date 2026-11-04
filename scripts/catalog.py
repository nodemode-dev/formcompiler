import argparse
import base64
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import public_urls
import versions
import yank
from registry import all_entries

HISTORY = 5
ORIGIN = "nodemode-dev/formcompiler"
ARCH_TOKENS = [
    (re.compile(r"(?<![a-z0-9])(aarch64|arm64)(?![a-z0-9])", re.I), "arm64"),
    (re.compile(r"(?<![a-z0-9])(x86_64|x64|amd64|intel)(?![a-z0-9])", re.I), "x86_64"),
]
SKIP = re.compile(r"(\.sig|\.tar\.gz|\.zsync|\.json|\.txt|\.md|\.sh|\.service|\.mcpb|\.msix|-with-formportal\.zip)$|SHA256SUMS", re.I)


def version_key(version):
    return versions.semver_key(version)


def line_of(key):
    return (key[0], key[1]) if key[0] == 0 else (key[0],)


def kept_history(stable):
    recent = stable[1:1 + HISTORY]
    seen = {line_of(stable[0][0])} | {line_of(item[0]) for item in recent}
    older = []
    for item in stable[1 + HISTORY:]:
        line = line_of(item[0])
        if line not in seen:
            seen.add(line)
            older.append(item)
    return recent + older


def arches(name):
    if re.search(r"universal", name, re.I):
        return ["arm64", "x86_64"]
    for pattern, arch in ARCH_TOKENS:
        if pattern.search(name):
            return [arch]
    return []


def classify(name):
    lower = name.lower()
    if SKIP.search(lower):
        return []
    if lower.endswith(".dmg"):
        return [("macos", a, "dmg") for a in arches(name)]
    if lower.endswith(".appimage"):
        return [("linux", a, "appimage") for a in arches(name)]
    if lower.endswith(".deb"):
        return [("linux", a, "deb") for a in arches(name)]
    if lower.endswith(".rpm"):
        return [("linux", a, "rpm") for a in arches(name)]
    if lower.endswith(".msi"):
        return [("windows", a, "msi") for a in arches(name)]
    if lower.endswith(".exe") and "setup" in lower:
        return [("windows", a, "nsis") for a in arches(name)]
    if lower.endswith(".apk"):
        return [("android", (arches(name) or ["arm64"])[0], "apk")]
    if lower.endswith(".ipa"):
        return [("ios", (arches(name) or ["arm64"])[0], "ipa")]
    if lower.endswith(".zip"):
        for token, platform in (("macos", "macos"), ("darwin", "macos"), ("windows", "windows"), ("linux", "linux")):
            if token in lower:
                return [(platform, a, "zip") for a in arches(name)]
    return []


def parse_sums(text):
    sums = {}
    for line in text.splitlines():
        found = re.match(r"^([0-9a-f]{64})\s+\*?(.+)$", line.strip())
        if found:
            sums[found.group(2).strip()] = found.group(1)
    return sums


def fetch_sums(release):
    assets = {asset["name"]: asset for asset in release.get("assets", [])}
    for name in ("SHA256SUMS.txt", "SHA256SUMS"):
        if name in assets:
            return parse_sums(download(assets[name]["url"]).decode("utf-8", "replace"))
    return {}


def read_sums(sums_dir: str, app: str, version: str) -> dict:
    path = Path(sums_dir) / app / version / "SHA256SUMS.txt"
    if not path.is_file():
        sys.exit(f"::error::{path} is missing: the catalogue lists {app} {version}, but the verified sums are not there")
    sums = parse_sums(path.read_text(encoding="utf-8", errors="replace"))
    if not sums:
        sys.exit(f"::error::{path} holds no sha256 line; the catalogue lists {app} {version}")
    return sums


def sums_for(release: dict, entry: dict, version: str, sums_dir: str = "") -> dict:
    return read_sums(sums_dir, entry["app"], version) if sums_dir else fetch_sums(release)


def asset_url(asset, entry, version, base):
    return public_urls.artifact_url(base, entry["app"], version, asset["name"]) if base else asset["browser_download_url"]


def agent_assets(release, entry, version, sums, base=""):
    found = {}
    wanted = {"manifest": "form-app.json", "skills": f"{entry['app']}-skills-v{version}.zip"}
    by_name = {asset["name"]: asset for asset in release.get("assets", [])}
    for key, name in wanted.items():
        asset = by_name.get(name)
        if asset and sums.get(name) and asset.get("size", 0) > 0:
            found[key] = {"file": name, "url": asset_url(asset, entry, version, base), "bytes": asset["size"], "sha256": sums[name]}
    return found


def download(url):
    import urllib.request
    headers = {"Accept": "application/octet-stream", "User-Agent": "formcompiler"}
    secret = gh.token()
    if secret:
        headers["Authorization"] = f"Bearer {secret}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def release_entry(release, version, entry, sums, base=""):
    minimum = entry["catalog"].get("minimum_os", {})
    artifacts = []
    for asset in sorted(release.get("assets", []), key=lambda a: a["name"]):
        digest = sums.get(asset["name"])
        if not digest or asset.get("size", 0) < 1:
            continue
        for platform, arch, kind in classify(asset["name"]):
            artifacts.append({
                "platform": platform, "arch": arch, "kind": kind, "file": asset["name"],
                "url": asset_url(asset, entry, version, base), "bytes": asset["size"], "sha256": digest,
                "minimum_os": minimum.get(platform, "") if platform in ("macos", "windows", "linux") else "",
            })
    body = {
        "version": version,
        "published": release.get("published_at") or release.get("created_at"),
        "notes": release["html_url"],
        "artifacts": artifacts,
    }
    sha = gh.source_of(release)[1]
    if sha:
        body["commit"] = sha
    agents = agent_assets(release, entry, version, sums, base)
    if agents:
        body["agents"] = agents
    return body


def app_releases(entry: dict, releases_list: list, yanked: frozenset) -> list:
    mine = []
    for release in releases_list:
        version = versions.version_of(release.get("tag_name", ""))
        if version and not release.get("draft") and (entry["app"], version) not in yanked:
            mine.append((version_key(version), version, release))
    return sorted(mine, reverse=True)


def build(entries, releases_by_repo, base="", yanked=frozenset(), origin=ORIGIN, sums_dir=""):
    products = []
    for entry in sorted(entries, key=lambda e: e["catalog"]["id"]):
        if not entry.get("enabled"):
            continue
        mine = app_releases(entry, releases_by_repo.get(entry["repository"], []), yanked)
        stable = [m for m in mine if not m[2].get("prerelease") and versions.channel(m[1]) == versions.STABLE]
        beta = [m for m in mine if m[2].get("prerelease") or versions.channel(m[1]) == versions.BETA]
        channels = {}
        if stable:
            _, version, release = stable[0]
            current = release_entry(release, version, entry, sums_for(release, entry, version, sums_dir), base)
            history = [release_entry(r, v, entry, sums_for(r, entry, v, sums_dir), base) for _, v, r in kept_history(stable)]
            if history:
                current["history"] = history
            channels["stable"] = current
        if beta and (not stable or beta[0][0] > stable[0][0]):
            _, version, release = beta[0]
            channels["beta"] = release_entry(release, version, entry, sums_for(release, entry, version, sums_dir), base)
        catalog = entry["catalog"]
        product = {
            "id": catalog["id"], "name": catalog["name"], "kind": catalog["kind"], "summary": catalog["summary"],
            "identifier": catalog["identifier"], "repository": f"https://github.com/{entry['repository']}",
            "licence": catalog["licence"],
        }
        if catalog.get("project_extensions"):
            product["project_extensions"] = catalog["project_extensions"]
        product["state"] = catalog["state"]
        agents = entry.get("agents") or {"skills": "", "mcp": False}
        product["agents"] = {"mcp": bool(agents.get("mcp")), "skills": bool(agents.get("skills"))}
        product["channels"] = channels
        products.append(product)
    return {
        "format": "formai-catalog",
        "format_version": 1,
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "origin": f"https://github.com/{origin}",
        "products": products,
    }


def fetch_releases(entries) -> dict:
    found = {}
    for entry in entries:
        if entry.get("enabled") and entry["repository"] not in found:
            try:
                found[entry["repository"]] = gh.releases(entry["repository"])
            except gh.ApiError as error:
                sys.exit(f"::error::could not list the releases of {entry['repository']}: {error}")
    return found


def read_releases(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(v, list) for v in data.values()):
        sys.exit(f"::error::{path} must be a JSON object mapping each app repository to its list of releases")
    return data


def listed_releases(document, entries):
    apps = {entry["catalog"]["id"]: entry["app"] for entry in entries}
    found = set()
    for product in document.get("products", []):
        app = apps.get(product.get("id"))
        for current in (product.get("channels") or {}).values():
            for item in [current, *current.get("history", [])]:
                if app and item.get("version"):
                    found.add((app, item["version"]))
    return sorted(found)


def sign(body, seed_b64):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    seed = base64.b64decode(seed_b64.strip())
    if len(seed) != 32:
        sys.exit("::error::FORMCOMPILER_CATALOG_KEY must be the base64 of a 32-byte Ed25519 seed")
    key = Ed25519PrivateKey.from_private_bytes(seed)
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(key.sign(body)).decode("ascii"), base64.b64encode(public).decode("ascii")


def keygen():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.generate()
    seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    print("FORMCOMPILER_CATALOG_KEY (a secret of the publishing pipeline, never committed):")
    print(base64.b64encode(seed).decode("ascii"))
    print("public key (one line in formportal's core/catalog_keys.txt):")
    print(base64.b64encode(public).decode("ascii"))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("build")
    make.add_argument("--origin", default=ORIGIN, help="the repository named as the catalogue's origin")
    make.add_argument("--out", default="releases.json")
    make.add_argument("--releases", default="", help="a JSON object of repository to releases instead of the API, for a dry run")
    make.add_argument("--yanked", default=str(yank.YANKED), help="the yanked versions, left out of the catalogue")
    make.add_argument("--sums-dir", default="", help="read <DIR>/<app>/<version>/SHA256SUMS.txt for every listed release instead of downloading it")
    signer = sub.add_parser("sign")
    signer.add_argument("--file", default="releases.json")
    signer.add_argument("--out", default="apps.json.sig")
    sub.add_parser("keygen")
    shown = sub.add_parser("listed")
    shown.add_argument("--file", default="releases.json")
    args = parser.parse_args()

    if args.command == "listed":
        document = json.loads(Path(args.file).read_text(encoding="utf-8"))
        print("".join(f"{app}\t{version}\n" for app, version in listed_releases(document, all_entries())), end="")
        return
    if args.command == "keygen":
        keygen()
        return
    if args.command == "sign":
        seed = os.environ.get("FORMCOMPILER_CATALOG_KEY", "")
        if not seed.strip():
            print("FORMCOMPILER_CATALOG_KEY is not set: the catalogue is published unsigned, and FormPortal refuses an unsigned catalogue")
            return
        signature, public = sign(Path(args.file).read_bytes(), seed)
        Path(args.out).write_text(signature + "\n", encoding="ascii")
        print(f"signed {args.file}; FormPortal must trust public key {public}")
        return
    try:
        base = public_urls.base_url(os.environ.get("FORMCOMPILER_PUBLIC_BASE", ""))
        yanked = yank.yanked_set(yank.load(args.yanked))
    except (ValueError, yank.YankError) as error:
        sys.exit(f"::error::{error}")
    entries = all_entries()
    releases_by_repo = read_releases(args.releases) if args.releases else fetch_releases(entries)
    document = build(entries, releases_by_repo, base, yanked, args.origin, args.sums_dir)
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    Path(args.out).write_text(text, encoding="utf-8")
    live = sum(1 for p in document["products"] if p["channels"])
    where = f"artifacts at {base}" if base else "artifacts on GitHub"
    print(f"{args.out}: {len(document['products'])} products, {live} with a release, {len(yanked)} yanked, {where}")


if __name__ == "__main__":
    main()
