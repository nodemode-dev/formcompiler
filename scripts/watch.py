import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import readiness
import versions
from registry import all_entries, validate

UNREADABLE = (401, 403, 404)


def outage(unreadable):
    names = ", ".join(unreadable)
    if not os.environ.get("FORMCOMPILER_APP_TOKEN", "").strip():
        return f"::error::the FORMCOMPILER_APP_TOKEN secret is not set, so {len(unreadable)} app repositories could not be read ({names}); add it with read access to them"
    return f"::error::the FORMCOMPILER_APP_TOKEN secret cannot read {len(unreadable)} app repositories ({names}); renew it or give it read access to them"


class Lazy:
    def __init__(self, repo):
        self.repo = repo
        self._releases = None
        self._active = None
        self._stopped = None

    def releases(self):
        if self._releases is None:
            self._releases = gh.releases(self.repo)
        return self._releases

    def active(self):
        if self._active is None:
            self._active = gh.active_release_runs(self.repo)
        return self._active

    def stopped(self):
        if self._stopped is None:
            self._stopped = gh.stopped_release_runs(self.repo)
        return self._stopped


def newest_tags(entry, state):
    tags = [(name, sha, kind) for name, sha, kind in gh.version_tags(entry["repository"]) if gh.VERSION_TAG.match(name)]
    found = []
    for wanted in (versions.STABLE, versions.BETA):
        mine = [t for t in tags if versions.channel(t[0][1:]) == wanted]
        if not mine:
            continue
        name, sha, kind = max(mine, key=lambda t: versions.semver_key(t[0][1:]))
        above, _ = versions.above_published(entry["app"], name[1:], state.releases())
        if above:
            found.append((name, gh.tag_commit(entry["repository"], sha, kind)))
    return found


def candidate_refs(entry, state):
    refs = list(gh.compile_branches(entry["repository"]))
    if entry.get("tag_trigger"):
        refs.extend(newest_tags(entry, state))
    return sorted(refs, key=lambda r: versions.semver_key(readiness.ref_version(r[0])[0] or "0.0.0"), reverse=True)


def watch_app(entry, refs, state, args):
    rows, started, ahead = [], 0, ""
    for ref, sha in refs:
        if ahead:
            rows.append((entry["app"], ref, readiness.SKIP, f"{ahead} is ahead; one release run per app at a time"))
            continue
        status, reason, version = readiness.evaluate(entry, ref, sha, state.releases(), state.active())
        if status == readiness.READY and gh.run_title(entry["app"], version, sha) in state.stopped():
            status = readiness.SKIP
            reason = (f"the release run for {entry['app']} {version} at {sha[:9]} failed or was cancelled; "
                      "open it in Actions and use Re-run failed jobs, or fix the app and release a new version")
        if status == readiness.READY:
            if args.dry_run:
                reason += "; dry run, not started"
            else:
                gh.dispatch(args.repo, args.ref, {"app": entry["app"], "ref": sha, "version": version})
                reason += "; release started"
                started += 1
        running = bool(version) and gh.run_title(entry["app"], version, sha) in state.active()
        if status in (readiness.READY, readiness.WAIT) or running:
            ahead = ref
        rows.append((entry["app"], ref, status, reason))
    return rows, started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nodemode-dev/formcompiler"))
    parser.add_argument("--ref", default="main")
    parser.add_argument("--app", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    entries = [e for e in all_entries() if not args.app or e.get("app") == args.app]
    if args.app and not entries:
        sys.exit(f"::error::no registry entry for {args.app}")
    state = Lazy(args.repo)
    rows, started, problems, unreadable = [], 0, 0, []
    for entry in entries:
        if validate(entry, None):
            rows.append((entry.get("app", "?"), "", readiness.REFUSE, "the registry entry is not valid; run scripts/registry.py check"))
            problems += 1
            continue
        if not entry["enabled"]:
            rows.append((entry["app"], "", readiness.SKIP, f"disabled: {entry.get('disabled_reason', '')}"))
            continue
        try:
            refs = candidate_refs(entry, state)
        except gh.ApiError as error:
            rows.append((entry["app"], "", readiness.REFUSE, str(error)))
            problems += 1
            if error.status in UNREADABLE:
                unreadable.append(entry["app"])
            continue
        if not refs:
            rows.append((entry["app"], "", readiness.SKIP, "no compile branch or new version tag"))
            continue
        try:
            app_rows, app_started = watch_app(entry, refs, state, args)
        except gh.ApiError as error:
            app_rows, app_started = [(entry["app"], "", readiness.REFUSE, f"could not check the release runs: {error}")], 0
        rows += app_rows
        started += app_started
        problems += sum(row[2] == readiness.REFUSE for row in app_rows)
    lines = ["### formcompiler watch\n", "", "| App | Branch | State | Why |", "| --- | --- | --- | --- |"]
    lines += [f"| {app} | {branch or '-'} | {state} | {reason.replace('|', '/')} |" for app, branch, state, reason in rows]
    lines += ["", f"{started} release run(s) started, {problems} refused.", ""]
    if unreadable:
        lines += [outage(unreadable).removeprefix("::error::"), ""]
    gh.summary("\n".join(lines) + "\n")
    for app, branch, state, reason in rows:
        if state == readiness.REFUSE and app not in unreadable:
            print(f"::warning::{app} {branch}: {reason}")
    if unreadable:
        print(outage(unreadable))
        sys.exit(1)


if __name__ == "__main__":
    main()
