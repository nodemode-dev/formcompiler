import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import ledger
import readiness
import versions
from registry import all_entries, validate, write_outputs

UNREADABLE = (401, 403, 404)
RELEASES_ON_APP_REPOS_SINCE = gh.RELEASES_ON_APP_REPOS_SINCE


def outage(unreadable):
    names = ", ".join(unreadable)
    if not os.environ.get("FORMCOMPILER_APP_TOKEN", "").strip():
        return f"::error::the FORMCOMPILER_APP_TOKEN secret is not set, so {len(unreadable)} app repositories could not be read ({names}); add it with read access to them"
    return f"::error::the FORMCOMPILER_APP_TOKEN secret cannot read {len(unreadable)} app repositories ({names}); renew it or give it read access to them"


def held_reason(app, version, sha, held):
    what = f"the release run for {app} {version} at {sha[:9]}"
    run = f" (run {held['number']})" if held.get("number") else ""
    again = f"run the watch with Again set to {app} to start it once more"
    if held["state"] == ledger.SUCCEEDED:
        return f"{what} succeeded{run}; to build this commit again, start release.yml by hand"
    if held["state"] == ledger.WAITING:
        return f"{what} is waiting for approval of its release{run}; approve or reject it in Actions"
    if held["state"] == ledger.RUNNING:
        return f"{what} is already running{run}"
    if held["state"] == ledger.STARTED:
        return (f"the watch started {what} on {held.get('at', 'an earlier pass')} and Actions lists no run for it now, "
                f"so how it ended is not known; {again}")
    if held["state"] == ledger.GONE:
        return (f"{what} had not ended when the watch last saw it{run}, and Actions no longer lists it, "
                f"so how it ended is not known; {again}")
    ended = "was cancelled" if held["state"] == ledger.CANCELLED else "failed"
    return (f"{what} {ended}{run}; the same commit would end the same way, so the watch does not start it again, "
            f"also after its run is deleted from Actions; use Re-run failed jobs on the run, release a new version, or {again}")


class Lazy:
    def __init__(self, repo, record=None):
        self.repo = repo
        self.record = record
        self._runs = None
        self._releases = {}
        self._active = None
        self._stopped = None
        self._succeeded = None

    def releases(self, app_repo: str) -> list:
        if app_repo not in self._releases:
            self._releases[app_repo] = gh.releases(app_repo)
        return self._releases[app_repo]

    def active(self):
        if self._active is None:
            self._active = gh.active_release_runs(self.repo)
        return self._active

    def stopped(self):
        if self._stopped is None:
            self._stopped = gh.stopped_release_runs(self.repo)
        return self._stopped

    def succeeded(self) -> set:
        if self._succeeded is None:
            self._succeeded = gh.succeeded_release_runs(self.repo, RELEASES_ON_APP_REPOS_SINCE)
        return self._succeeded

    def fold(self, app, refs):
        if self.record is None:
            return
        if self._runs is None:
            self._runs = gh.release_runs(self.repo)
            ledger.fold(self.record, self._runs, refused=self.at_gate)
            ledger.settle(self.record, self._runs)
        ledger.fold(self.record, self._runs, app, dict(refs), refused=self.at_gate)

    def at_gate(self, run):
        return gh.gate_refused(self.repo, run)

    def refused(self, app, sha):
        entry = ledger.known(self.record, app, sha) if self.record is not None else None
        return bool(entry) and entry["state"] == ledger.REFUSED

    def known(self, app, sha):
        return ledger.known(self.record, app, sha) if self.record is not None else None

    def note_started(self, app, sha):
        if self.record is not None:
            ledger.started(self.record, app, sha)


def newest_tags(entry, state):
    tags = [(name, sha, kind) for name, sha, kind in gh.version_tags(entry["repository"]) if gh.VERSION_TAG.match(name)]
    found = []
    for wanted in (versions.STABLE, versions.BETA):
        mine = [t for t in tags if versions.channel(t[0][1:]) == wanted]
        if not mine:
            continue
        name, sha, kind = max(mine, key=lambda t: versions.semver_key(t[0][1:]))
        above, _ = versions.above_published(entry["app"], name[1:], state.releases(entry["repository"]))
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
    again = args.again == entry["app"]
    state.fold(entry["app"], refs)
    for ref, sha in refs:
        if ahead:
            rows.append((entry["app"], ref, readiness.SKIP, f"{ahead} is ahead; one release run per app at a time"))
            continue
        status, reason, version = readiness.evaluate(entry, ref, sha, state.releases(entry["repository"]), state.active(), built=state.succeeded())
        built = False
        refused = state.refused(entry["app"], sha)
        held = None if again or refused else state.known(entry["app"], sha)
        if status == readiness.READY and gh.run_title(entry["app"], version, sha) in state.succeeded():
            status, built = readiness.SKIP, True
            reason = (f"the release run for {entry['app']} {version} at {sha[:9]} succeeded; its release is on "
                      f"{entry['repository']}, or was deleted there; to build this commit again, start release.yml by hand")
        elif status == readiness.READY and not again and not refused and gh.run_title(entry["app"], version, sha) in state.stopped():
            status = readiness.SKIP
            reason = (f"the release run for {entry['app']} {version} at {sha[:9]} failed or was cancelled; "
                      "open it in Actions and use Re-run failed jobs, or fix the app and release a new version")
        elif status == readiness.READY and held:
            status, built = readiness.SKIP, held["state"] == ledger.SUCCEEDED
            reason = held_reason(entry["app"], version, sha, held)
        if status == readiness.READY:
            if args.dry_run:
                reason += "; dry run, not started"
            else:
                gh.dispatch(args.repo, args.ref, {"app": entry["app"], "ref": sha, "version": version})
                reason += "; release started"
                started += 1
                state.note_started(entry["app"], sha)
        running = bool(version) and (gh.run_title(entry["app"], version, sha) in state.active() or bool(held) and held["state"] in ledger.LIVE)
        if status in (readiness.READY, readiness.WAIT) or running or built:
            ahead = ref
        rows.append((entry["app"], ref, status, reason))
    return rows, started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nodemode-dev/formcompiler"))
    parser.add_argument("--ref", default="main")
    parser.add_argument("--app", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--record", default="")
    parser.add_argument("--again", default="")
    args = parser.parse_args()

    entries = [e for e in all_entries() if not args.app or e.get("app") == args.app]
    if args.app and not entries:
        sys.exit(f"::error::no registry entry for {args.app}")
    record = ledger.load(args.record) if args.record else None
    before = ledger.text(record) if record is not None else ""
    state = Lazy(args.repo, record)
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
    if record is not None and not args.dry_run and ledger.text(record) != before:
        ledger.save(args.record, record)
        write_outputs({"record": "changed"})
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
