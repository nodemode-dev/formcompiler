import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan import SEMVER
from registry import APPS, ROOT

YANKED = ROOT / "yanked.json"
REASON_MAX = 300


class YankError(Exception):
    pass


def load(path=YANKED):
    if not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("yanked") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not all(isinstance(r, dict) and {"app", "version"} <= r.keys() for r in rows):
        raise YankError(f"{Path(path).name} must be {{\"yanked\": [{{\"app\", \"version\", \"reason\", \"date\"}}]}}")
    return rows


def yanked_set(rows):
    return frozenset((row["app"], row["version"]) for row in rows)


def validate(app, version, reason, releases, rows):
    if not (APPS / f"{app}.json").is_file():
        raise YankError(f"no registry entry apps/{app}.json")
    if not SEMVER.match(version):
        raise YankError(f"{version!r} is not a semantic version (no leading v)")
    text = reason.strip()
    if not text or len(text) > REASON_MAX or "\n" in text or "\r" in text:
        raise YankError(f"the reason must be one line of 1 to {REASON_MAX} characters")
    tag = f"{app}-v{version}"
    release = next((r for r in releases if r.get("tag_name") == tag), None)
    if not release or release.get("draft"):
        raise YankError(f"{tag} is not a published release; delete a draft instead of yanking it")
    if (app, version) in yanked_set(rows):
        raise YankError(f"{tag} is already yanked")
    return text


def added(rows, app, version, reason, today):
    row = {"app": app, "version": version, "reason": reason, "date": today}
    return sorted([*rows, row], key=lambda r: (r["app"], r["version"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nodemode-dev/formcompiler"))
    parser.add_argument("--file", default=str(YANKED))
    args = parser.parse_args()

    import github_api as gh
    version = args.version.strip()
    try:
        rows = load(args.file)
        reason = validate(args.app.strip(), version, args.reason, gh.releases(args.repo), rows)
    except YankError as error:
        sys.exit(f"::error::{error}")
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    document = {"yanked": added(rows, args.app.strip(), version, reason, today)}
    Path(args.file).write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"yanked {args.app}-v{version}: {reason}")


if __name__ == "__main__":
    main()
