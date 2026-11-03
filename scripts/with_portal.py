import argparse
import hashlib
import ipaddress
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import classify
from registry import PORTAL_ID, load

SUFFIX = "-with-FormPortal.zip"
DEFAULT_CATALOG = "https://github.com/nodemode-dev/formcompiler/releases/download/catalog/apps.json"
PREFER = {"windows": ("nsis", "msi"), "macos": ("dmg",), "linux": ("appimage", "deb", "rpm")}
README = """{title} {version} with FormPortal

This download holds two installers: {app_file} ({title}) and {portal_file} (FormPortal {portal_version}).

Install {title} with {app_file}. That is all {title} needs.

FormPortal is optional, and nothing installs it for you. If you want it, install it with {portal_file}:
it lists {title} under Apps, keeps it up to date (you can turn that off), keeps the previous version, and can
install the other Form apps. It needs no account and runs only while it is open. If you do not want it,
leave {portal_file} unopened and delete it; you can remove FormPortal at any time and {title} keeps working.

The two files are the same as the separate downloads on the release pages:
  {app_file}     sha256 {app_sha}
  {portal_file}  sha256 {portal_sha}
"""


def allowed(url):
    parts = urllib.parse.urlparse(url)
    if parts.scheme == "https":
        return True
    if parts.scheme == "http" and parts.hostname:
        try:
            return ipaddress.ip_address(parts.hostname).is_loopback
        except ValueError:
            return parts.hostname == "localhost"
    return False


def fetch(url):
    if not allowed(url):
        sys.exit(f"::error::{url} is not https; FormPortal's files are fetched only over https")
    request = urllib.request.Request(url, headers={"Accept": "application/octet-stream", "User-Agent": "formcompiler"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def read_catalog(source):
    if "://" in source:
        return json.loads(fetch(source))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def portal_release(catalog):
    for product in catalog.get("products", []):
        if product.get("id") == PORTAL_ID:
            return product.get("channels", {}).get("stable")
    return None


def pick(artifacts, platform, arch, kind):
    same = [a for a in artifacts if a["platform"] == platform and a["arch"] == arch]
    for wanted in (kind,) + PREFER.get(platform, ()):
        for artifact in same:
            if artifact["kind"] == wanted:
                return artifact
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="dist")
    parser.add_argument("--app", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    args = parser.parse_args()

    entry = load(args.app)
    if not entry.get("with_portal"):
        print(f"{args.app} does not ask for an app-plus-FormPortal download (with_portal)")
        return
    title = entry["catalog"]["name"]
    folder = Path(args.dir)
    try:
        catalog = read_catalog(args.catalog)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            sys.exit(f"::error::could not read the catalogue at {args.catalog}: HTTP {error.code}")
        print(f"::notice::no catalogue at {args.catalog} yet, so no app-plus-FormPortal download was made; the app's own files are unchanged")
        return
    release = portal_release(catalog)
    if not release or not release.get("artifacts"):
        print("::notice::the catalogue has no stable FormPortal release yet, so no app-plus-FormPortal download was made; the app's own files are unchanged")
        return
    artifacts = release["artifacts"]
    cache = {}
    made = []
    for app_path in sorted(p for p in folder.iterdir() if p.is_file()):
        if app_path.name.endswith(SUFFIX):
            continue
        targets = [t for t in classify(app_path.name) if t[0] in PREFER]
        chosen = {}
        for platform, arch, kind in targets:
            portal = pick(artifacts, platform, arch, kind)
            if portal:
                chosen.setdefault(portal["file"], (portal, arch))
            else:
                print(f"::notice::{app_path.name}: FormPortal {release['version']} has no {platform} {arch} build, so there is no app-plus-FormPortal download for {arch}")
        app_sha = hashlib.sha256(app_path.read_bytes()).hexdigest() if chosen else ""
        stem = app_path.name.rsplit(".", 1)[0]
        kind = targets[0][2] if targets else ""
        for portal, arch in chosen.values():
            if portal["file"] not in cache:
                body = fetch(portal["url"])
                digest = hashlib.sha256(body).hexdigest()
                if digest != portal["sha256"] or len(body) != portal["bytes"]:
                    for name in made:
                        (folder / name).unlink()
                    sys.exit(f"::error::{portal['file']} does not match the catalogue (sha256 {digest}, {len(body)} bytes); no app-plus-FormPortal download was made")
                cache[portal["file"]] = (body, digest)
            body, portal_sha = cache[portal["file"]]
            out = folder / (f"{stem}-{kind}" + (f"-{arch}" if len(chosen) > 1 else "") + SUFFIX)
            readme = README.format(
                title=title, version=args.version, app_file=app_path.name, portal_file=portal["file"],
                portal_version=release["version"], app_sha=app_sha, portal_sha=portal_sha,
            )
            with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as bundle:
                bundle.write(app_path, app_path.name)
                bundle.writestr(portal["file"], body)
                bundle.writestr("README.txt", readme)
            made.append(out.name)
            print(f"{out.name}: {app_path.name} + {portal['file']}")
    if not made:
        print("::notice::no desktop installer in this release matched a FormPortal build")


if __name__ == "__main__":
    main()
