import sys

import pytest

import gate
import github_api as gh
import readiness
import watch

SHA = "a" * 40
OTHER = "b" * 40
TAG_OBJECT = "c" * 40
ENTRY = {"app": "alpha", "repository": "nodemode-dev/alpha", "enabled": True, "checks": ["ci.yml"],
         "version": {"file": "VERSION", "pattern": ""}}


@pytest.fixture
def api(monkeypatch):
    calls = {"on_main": [], "file_at": [], "tags": 0, "deref": []}
    state = {"on_main": True, "version": "1.2.0", "checks": {"ci.yml": "success"}}

    def on_main(repo, sha):
        calls["on_main"].append(sha)
        return state["on_main"]

    def file_at(repo, path, sha):
        calls["file_at"].append(sha)
        return state["version"] + "\n"

    monkeypatch.setattr(gh, "on_main", on_main)
    monkeypatch.setattr(gh, "file_at", file_at)
    monkeypatch.setattr(gh, "checks_state", lambda repo, sha, workflows: dict(state["checks"]))
    monkeypatch.setattr(gh, "tag_target", lambda repo, name: state.get("tag", ""))
    return calls, state


def evaluate(ref, releases=(), sha=SHA):
    return readiness.evaluate(ENTRY, ref, sha, list(releases), set())


def test_a_tag_on_main_is_ready(api):
    calls, _ = api
    status, reason, version = evaluate("v1.2.0")
    assert (status, version) == (readiness.READY, "1.2.0")
    assert calls["on_main"] == [SHA]


def test_a_tag_off_main_is_refused_before_the_version_is_read(api):
    calls, state = api
    state["on_main"] = False
    status, reason, _ = evaluate("v1.2.0")
    assert status == readiness.REFUSE
    assert "not on main" in reason
    assert calls["file_at"] == []


def test_a_compile_branch_on_main_is_ready(api):
    calls, _ = api
    status, _, _ = evaluate("compile_v1.2.0")
    assert status == readiness.READY
    assert calls["on_main"] == [SHA]


def test_a_compile_branch_off_main_is_refused_before_the_version_is_read(api):
    calls, state = api
    state["on_main"] = False
    status, reason, _ = evaluate("compile_v1.2.0")
    assert status == readiness.REFUSE
    assert "not on main" in reason and "compile_v1.2.0" in reason
    assert calls["file_at"] == []


def test_a_version_not_above_the_highest_published_is_refused(api):
    calls, state = api
    state["version"] = "1.1.9"
    status, reason, _ = evaluate("v1.1.9", [{"tag_name": "v1.2.0", "draft": False}])
    assert status == readiness.REFUSE
    assert "1.2.0" in reason
    assert calls["on_main"] == [] and calls["file_at"] == []


def test_a_newer_draft_supersedes_an_older_ref(api):
    status, reason, _ = evaluate("v1.2.0", [{"tag_name": "v1.3.0", "draft": True}])
    assert status == readiness.SKIP
    assert "superseded" in reason


def test_a_published_version_is_skipped_quietly(api):
    status, _, _ = evaluate("v1.2.0", [{"tag_name": "v1.2.0", "draft": False}])
    assert status == readiness.SKIP


@pytest.mark.parametrize("ref", ["v1.2", "release-1.2.0", "V1.2.0", "vv1.2.0", "compile_1.2.0"])
def test_other_refs_are_not_release_refs(ref):
    assert readiness.ref_version(ref) == ("", "")


@pytest.mark.parametrize("ref, expected", [
    ("v1.2.0", ("1.2.0", readiness.TAG)),
    ("v2.0.0-beta.3", ("2.0.0-beta.3", readiness.TAG)),
    ("compile_v1.2.0", ("1.2.0", readiness.BRANCH)),
])
def test_release_refs_name_their_version(ref, expected):
    assert readiness.ref_version(ref) == expected


@pytest.fixture
def watched(monkeypatch, capsys):
    dispatched, deref = [], []
    entries = [dict(ENTRY, tag_trigger=True), dict(ENTRY, app="beta", repository="nodemode-dev/beta")]
    tags = {"nodemode-dev/alpha": [("v1.0.0", OTHER, "commit"), ("v1.10.0", TAG_OBJECT, "tag"), ("v1.9.0", OTHER, "commit"), ("nightly", OTHER, "commit")],
            "nodemode-dev/beta": [("v5.0.0", OTHER, "commit")]}
    tag_calls = []
    monkeypatch.setattr(watch, "all_entries", lambda: entries)
    monkeypatch.setattr(watch, "validate", lambda entry, _: [])
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "stopped_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "succeeded_release_runs", lambda repo, since: set())
    monkeypatch.setattr(gh, "dispatch", lambda repo, ref, inputs: dispatched.append((inputs["app"], inputs["version"])))
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [])
    monkeypatch.setattr(gh, "version_tags", lambda repo: tag_calls.append(repo) or tags[repo])
    monkeypatch.setattr(gh, "tag_commit", lambda repo, sha, kind: deref.append((sha, kind)) or SHA)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    def run(releases=(), evaluate=None):
        monkeypatch.setattr(gh, "releases", lambda repo: list(releases))
        monkeypatch.setattr(readiness, "evaluate", evaluate or (lambda entry, ref, sha, *_: (readiness.READY, "ok", readiness.ref_version(ref)[0])))
        monkeypatch.setattr(sys, "argv", ["watch.py"])
        watch.main()
        return dispatched, deref, tag_calls, capsys.readouterr().out

    return run


def test_watch_finds_the_newest_tag_and_dereferences_only_it(watched):
    dispatched, deref, tag_calls, _ = watched()
    assert dispatched == [("alpha", "1.10.0")]
    assert deref == [(TAG_OBJECT, "tag")]
    assert tag_calls == ["nodemode-dev/alpha"]


def test_watch_ignores_tags_below_the_highest_published(watched):
    dispatched, deref, _, out = watched([{"tag_name": "v2.0.0", "draft": False}])
    assert dispatched == []
    assert deref == []
    assert "no compile branch or new version tag" in out


def test_watch_does_no_release_lookups_when_nothing_is_there(monkeypatch, capsys):
    monkeypatch.setattr(watch, "all_entries", lambda: [ENTRY])
    monkeypatch.setattr(watch, "validate", lambda entry, _: [])
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [])
    monkeypatch.setattr(gh, "releases", lambda repo: pytest.fail("releases fetched with nothing to evaluate"))
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: pytest.fail("runs fetched with nothing to evaluate"))
    monkeypatch.setattr(sys, "argv", ["watch.py"])
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    watch.main()
    assert "0 release run(s) started" in capsys.readouterr().out


def test_watch_starts_one_run_per_app_the_newest_ready(monkeypatch, watched):
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.11.0", OTHER), ("compile_v1.12.0-beta.1", OTHER)] if repo.endswith("alpha") else [])
    dispatched, _, _, out = watched()
    assert dispatched == [("alpha", "1.12.0-beta.1")]
    assert "is ahead" in out


def test_gate_dereferences_only_the_tag_it_was_given(monkeypatch):
    deref = []
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.0.0", OTHER)])
    monkeypatch.setattr(gh, "version_tags", lambda repo: [("v1.1.0", TAG_OBJECT, "tag"), ("v1.2.0", OTHER, "tag")])
    monkeypatch.setattr(gh, "tag_commit", lambda repo, sha, kind: deref.append(sha) or SHA)
    refs = gate.release_refs(dict(ENTRY, tag_trigger=True), "1.1.0")
    assert refs == {"compile_v1.0.0": OTHER, "v1.1.0": SHA}
    assert deref == [TAG_OBJECT]
    assert gate.release_refs(ENTRY, "1.1.0") == {"compile_v1.0.0": OTHER}


def test_tag_commit_follows_an_annotated_tag(monkeypatch):
    monkeypatch.setattr(gh, "get", lambda path, app_side=False: {"object": {"sha": SHA, "type": "commit"}})
    assert gh.tag_commit("nodemode-dev/alpha", TAG_OBJECT, "tag") == SHA
    assert gh.tag_commit("nodemode-dev/alpha", OTHER, "commit") == OTHER


@pytest.mark.parametrize("status, expected", [("identical", True), ("behind", True), ("ahead", False), ("diverged", False)])
def test_on_main_reads_the_compare_status(monkeypatch, status, expected):
    seen = []
    monkeypatch.setattr(gh, "get", lambda path, app_side=False: seen.append(path) or {"status": status})
    assert gh.on_main("nodemode-dev/alpha", SHA) is expected
    assert seen == [f"/repos/nodemode-dev/alpha/compare/main...{SHA}"]


def test_watch_starts_nothing_below_a_version_already_running(monkeypatch, watched):
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.11.0", OTHER)] if repo.endswith("alpha") else [])
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: {gh.run_title("alpha", "1.11.0", OTHER)})

    def running(entry, ref, sha, releases, active):
        version = readiness.ref_version(ref)[0]
        if gh.run_title(entry["app"], version, sha) in active:
            return readiness.SKIP, "already running", version
        return readiness.READY, "ok", version

    dispatched, _, _, out = watched((), running)
    assert dispatched == []
    assert "is ahead" in out


def test_watch_finds_a_stable_fix_behind_a_published_beta(monkeypatch, watched):
    tags = [("v1.6.0-beta.1", OTHER, "commit"), ("v1.5.1", TAG_OBJECT, "tag"), ("v1.5.0", OTHER, "commit")]
    monkeypatch.setattr(gh, "version_tags", lambda repo: tags if repo.endswith("alpha") else [])
    published = [{"tag_name": "v1.5.0", "draft": False}, {"tag_name": "v1.6.0-beta.1", "draft": False, "prerelease": True}]

    def evaluate(entry, ref, sha, releases, active):
        version = readiness.ref_version(ref)[0]
        if gh.release_by_tag(releases, f"v{version}"):
            return readiness.SKIP, "already published", version
        return readiness.READY, "ok", version

    dispatched, deref, _, _ = watched(published, evaluate)
    assert dispatched == [("alpha", "1.5.1")]
    assert deref == [(TAG_OBJECT, "tag")]
