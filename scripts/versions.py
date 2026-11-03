import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan import SEMVER

STABLE, BETA = "stable", "beta"


def identifier_key(part):
    return (0, int(part), "") if part.isdigit() else (1, 0, part)


def semver_key(version):
    found = SEMVER.match(version)
    if not found:
        raise ValueError(f"{version!r} is not a semantic version")
    major, minor, patch = (int(found.group(i)) for i in (1, 2, 3))
    pre = (found.group(4) or "").removeprefix("-")
    if not pre:
        return (major, minor, patch, 1, ())
    return (major, minor, patch, 0, tuple(identifier_key(p) for p in pre.split(".")))


def channel(version):
    found = SEMVER.match(version)
    if not found:
        raise ValueError(f"{version!r} is not a semantic version")
    return BETA if found.group(4) else STABLE


TAG_PREFIX = "v"


def tag_of(version: str) -> str:
    return f"{TAG_PREFIX}{version}"


def version_of(tag: str) -> str:
    version = tag[len(TAG_PREFIX):] if tag.startswith(TAG_PREFIX) else ""
    return version if version and SEMVER.match(version) else ""


def app_releases(app, releases):
    found = []
    for release in releases:
        version = version_of(release.get("tag_name", ""))
        if version:
            found.append((version, release))
    return sorted(found, key=lambda item: semver_key(item[0]), reverse=True)


def highest_published(app, releases):
    published = [v for v, r in app_releases(app, releases) if not r.get("draft")]
    return published[0] if published else ""


def drafts(app, releases):
    return [(v, r) for v, r in app_releases(app, releases) if r.get("draft")]


def newer_draft(app, version, releases):
    key = semver_key(version)
    newer = [v for v, _ in drafts(app, releases) if semver_key(v) > key]
    return newer[0] if newer else ""


def older_drafts(app, version, releases):
    key, beta = semver_key(version), channel(version) == BETA
    return [tag_of(v) for v, _ in drafts(app, releases) if semver_key(v) < key and not (beta and channel(v) == STABLE)]


def older_draft_ids(app, version, releases):
    tags = set(older_drafts(app, version, releases))
    return [(str(r.get("id", "")), tag_of(v)) for v, r in drafts(app, releases) if tag_of(v) in tags]


def highest_stable(app, releases):
    published = [v for v, r in app_releases(app, releases) if not r.get("draft") and channel(v) == STABLE]
    return published[0] if published else ""


def above_published(app, version, releases):
    top = highest_stable(app, releases) if channel(version) == STABLE else highest_published(app, releases)
    if top and semver_key(version) <= semver_key(top):
        return False, f"{version} is not above {app}'s highest published version {top}; bump the version to release"
    return True, ""


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    old = sub.add_parser("older-drafts")
    old.add_argument("--app", required=True)
    old.add_argument("--version", required=True)
    old.add_argument("--repo", default="", help="the app's repository; default: the registry entry's")
    old.add_argument("--token-env", default="", help="read the release list with this variable's token only (drafts need write access)")
    kind = sub.add_parser("channel")
    kind.add_argument("--version", required=True)
    args = parser.parse_args()

    if args.command == "channel":
        print(channel(args.version))
        return
    import github_api as gh
    from registry import load
    repo = args.repo or load(args.app)["repository"]
    for release_id, tag in older_draft_ids(args.app, args.version, gh.releases(repo, token_env=args.token_env)):
        print(f"{release_id}\t{tag}")


if __name__ == "__main__":
    main()
