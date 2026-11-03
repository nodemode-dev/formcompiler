import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import versions
from plan import SEMVER, parse_version

READY, SKIP, WAIT, REFUSE = "ready", "skip", "wait", "refuse"
BRANCH, TAG = "branch", "tag"


def version_at(entry, sha):
    path = entry["version"]["file"]
    text = gh.file_at(entry["repository"], path, sha)
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink):
            value = parse_version(text, path, entry["version"].get("pattern", ""))
    except SystemExit:
        raise gh.ApiError(0, sink.getvalue().strip().removeprefix("::error::")) from None
    return str(value).strip().removeprefix("v")


def ref_version(ref):
    for pattern, kind in ((gh.COMPILE_BRANCH, BRANCH), (gh.VERSION_TAG, TAG)):
        found = pattern.match(ref)
        if found:
            return found.group(1), kind
    return "", ""


def evaluate(entry, ref, sha, all_releases, active_titles, check_runs=True):
    version, kind = ref_version(ref)
    if not version:
        return SKIP, f"`{ref}` is not a release ref (a compile_vX.Y.Z branch or a vX.Y.Z tag, with an optional -beta.N)", ""
    app = entry["app"]
    tag = f"{app}-v{version}"
    release = gh.release_by_tag(all_releases, tag)
    if release and not release.get("draft"):
        return SKIP, f"{tag} is already published; bump the version to release again", version
    newer = versions.newer_draft(app, version, all_releases)
    if newer:
        return SKIP, f"superseded: the draft {app}-v{newer} is newer", version
    if release and gh.source_of(release)[1] == sha:
        return SKIP, f"{tag} is already drafted from {sha[:9]}", version
    above, why = versions.above_published(app, version, all_releases)
    if not above:
        return REFUSE, why, version
    if gh.run_title(app, version, sha) in active_titles:
        return SKIP, f"a release run for {tag} at {sha[:9]} is already running", version
    try:
        on_main = gh.on_main(entry["repository"], sha)
    except gh.ApiError as error:
        return REFUSE, f"could not compare {sha[:9]} with {gh.MAIN}: {error}", version
    if not on_main:
        what = "tag" if kind == TAG else "branch"
        return REFUSE, f"the {what} `{ref}` points at {sha[:9]}, which is not on {gh.MAIN}; release a commit already on {gh.MAIN}", version
    try:
        actual = version_at(entry, sha)
    except gh.ApiError as error:
        return REFUSE, f"could not read the version at {sha[:9]}: {error}", version
    if not SEMVER.match(actual) or actual != version:
        return REFUSE, f"`{ref}` points at {sha[:9]}, where {entry['version']['file']} says {actual}", version
    if not check_runs:
        return READY, "checks not required for this run", version
    states = gh.checks_state(entry["repository"], sha, entry["checks"])
    failed = [f"{name} {state}" for name, state in states.items() if state not in ("success", "pending", "missing")]
    if failed:
        return REFUSE, f"checks did not pass at {sha[:9]}: {', '.join(failed)}", version
    waiting = [f"{name} {state}" for name, state in states.items() if state in ("pending", "missing")]
    if waiting:
        return WAIT, f"checks not finished at {sha[:9]}: {', '.join(waiting)}", version
    return READY, f"checks passed at {sha[:9]} ({', '.join(states)})", version
