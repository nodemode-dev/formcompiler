import argparse
import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import public_urls
import versions
from plan import SEMVER
from registry import all_entries, write_outputs


def resolve(app: str, tag: str) -> tuple:
    version = tag.strip().removeprefix(versions.TAG_PREFIX)
    if not SEMVER.match(version):
        sys.exit(f"::error::{tag!r} is not a release tag of the shape vX.Y.Z")
    entry = next((e for e in all_entries() if e.get("app") == app), None)
    if not entry:
        sys.exit(f"::error::no registry entry for {app!r}")
    return entry, version


def point_at_store(entry, version, args):
    try:
        base = public_urls.base_url(args.base)
    except ValueError as error:
        sys.exit(f"::error::{error}")
    path = Path(args.file)
    if args.asset_origin == "github":
        print(f"{path.name}: update URLs stay on {entry['repository']}'s release (asset origin github)")
        return
    feed = json.loads(path.read_text(encoding="utf-8"))
    moved = public_urls.rewrite_feed(feed, base, entry["app"], version, versions.tag_of(version))
    if moved == feed:
        print(f"{path.name}: no URL changed")
        return
    path.write_text(json.dumps(moved, indent=2) + "\n", encoding="utf-8")
    print(f"{path.name}: update URLs now under {base}/{entry['app']}/{version}/")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("resolve")
    one.add_argument("--app", required=True)
    one.add_argument("--tag", required=True, help="vX.Y.Z or X.Y.Z")
    one.add_argument("--prerelease", default="false")
    pick = sub.add_parser("files")
    pick.add_argument("--app", required=True)
    pick.add_argument("--tag", required=True)
    pick.add_argument("--assets", required=True, help="JSON list of the release's asset names")
    point = sub.add_parser("public")
    point.add_argument("--app", required=True)
    point.add_argument("--tag", required=True)
    point.add_argument("--file", required=True, help="the latest.json copied to the update feed")
    point.add_argument("--base", default="")
    point.add_argument("--asset-origin", default="store", choices=("github", "store"), help="github leaves the release's download URLs in latest.json")
    args = parser.parse_args()

    entry, version = resolve(args.app, args.tag)
    tag = versions.tag_of(version)
    if args.command == "resolve":
        stable = versions.channel(version) == versions.STABLE and args.prerelease != "true"
        updater = entry["updater"]
        wanted = stable and (updater["tauri"] or updater["tag_json"] or bool(updater["files"]))
        top = versions.highest_stable(entry["app"], gh.releases(entry["repository"])) if wanted else ""
        if top and versions.semver_key(version) < versions.semver_key(top):
            print(f"::notice::{entry['app']} {tag} is below its newest stable {top}; the update feed is not rolled back to it")
            wanted = False
        write_outputs({"app": entry["app"], "title": entry["title"], "version": version, "tag": tag,
                       "repository": entry["repository"], "prerelease": "false" if stable else "true",
                       "channel": versions.STABLE if stable else versions.BETA,
                       "updates": "true" if wanted else "false", "tag_json": "true" if updater["tag_json"] else "false"})
        print(f"{entry['app']} {tag} on {entry['repository']}: {entry['title']} {version}, update feed {'refreshed' if wanted else 'not touched'}")
        return
    if args.command == "public":
        point_at_store(entry, version, args)
        return
    names = json.loads(args.assets)
    patterns = list(entry["updater"]["files"]) + (["latest.json"] if entry["updater"]["tauri"] else [])
    chosen = sorted({n for n in names for p in patterns if fnmatch.fnmatchcase(n, p)})
    print("\n".join(chosen))


if __name__ == "__main__":
    main()
