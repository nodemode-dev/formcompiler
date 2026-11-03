import argparse
import fnmatch
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import public_urls
import versions
from plan import SEMVER
from registry import all_entries, write_outputs


def resolve(tag):
    matches = []
    for entry in all_entries():
        prefix = f"{entry['app']}-v"
        if tag.startswith(prefix) and SEMVER.match(tag[len(prefix):]):
            matches.append((len(prefix), entry, tag[len(prefix):]))
    if not matches:
        return None, ""
    _, entry, version = max(matches, key=lambda m: m[0])
    return entry, version


def point_at_store(entry, version, args):
    try:
        base = public_urls.base_url(args.base)
    except ValueError as error:
        sys.exit(f"::error::{error}")
    path = Path(args.file)
    feed = json.loads(path.read_text(encoding="utf-8"))
    moved = public_urls.rewrite_feed(feed, base, entry["app"], version, args.tag)
    if moved == feed:
        print(f"{path.name}: no URL changed")
        return
    path.write_text(json.dumps(moved, indent=2) + "\n", encoding="utf-8")
    print(f"{path.name}: update URLs now under {base}/{entry['app']}/{version}/")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("resolve")
    one.add_argument("--tag", required=True)
    one.add_argument("--prerelease", default="false")
    one.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nodemode-dev/formcompiler"))
    pick = sub.add_parser("files")
    pick.add_argument("--tag", required=True)
    pick.add_argument("--assets", required=True, help="JSON list of the release's asset names")
    point = sub.add_parser("public")
    point.add_argument("--tag", required=True)
    point.add_argument("--file", required=True, help="the latest.json copied to the update feed")
    point.add_argument("--base", default="")
    args = parser.parse_args()

    entry, version = resolve(args.tag)
    if args.command == "resolve":
        if not entry:
            print(f"{args.tag} is not an app release tag; only the catalogue is rebuilt")
            write_outputs({"app": "", "version": "", "updates": "false"})
            return
        stable = versions.channel(version) == versions.STABLE and args.prerelease != "true"
        updater = entry["updater"]
        wanted = stable and (updater["tauri"] or updater["tag_json"] or bool(updater["files"]))
        top = versions.highest_stable(entry["app"], gh.releases(args.repo)) if wanted else ""
        if top and versions.semver_key(version) < versions.semver_key(top):
            print(f"::notice::{args.tag} is below {entry['app']}'s newest stable {top}; the update feed is not rolled back to it")
            wanted = False
        write_outputs({"app": entry["app"], "title": entry["title"], "version": version,
                       "channel": versions.STABLE if stable else versions.BETA,
                       "updates": "true" if wanted else "false", "tag_json": "true" if updater["tag_json"] else "false"})
        print(f"{args.tag}: {entry['app']} {version}, update feed {'refreshed' if wanted else 'not touched'}")
        return
    if not entry:
        sys.exit(f"::error::{args.tag} is not an app release tag")
    if args.command == "public":
        point_at_store(entry, version, args)
        return
    names = json.loads(args.assets)
    patterns = list(entry["updater"]["files"]) + (["latest.json"] if entry["updater"]["tauri"] else [])
    chosen = sorted({n for n in names for p in patterns if fnmatch.fnmatchcase(n, p)})
    print("\n".join(chosen))


if __name__ == "__main__":
    main()
