import sys
from pathlib import Path

import pytest

import github_api as gh
import readiness
import watch

APPS = [
    {"app": "alpha", "repository": "nodemode-dev/alpha", "enabled": True},
    {"app": "beta", "repository": "nodemode-dev/beta", "enabled": True},
]


@pytest.fixture
def stubbed(monkeypatch, capsys):
    dispatched = []
    monkeypatch.setattr(watch, "all_entries", lambda: APPS)
    monkeypatch.setattr(watch, "validate", lambda entry, _: [])
    monkeypatch.setattr(gh, "releases", lambda repo: [])
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "stopped_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "succeeded_release_runs", lambda repo, since: set())
    monkeypatch.setattr(gh, "dispatch", lambda repo, ref, inputs: dispatched.append(inputs["app"]))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("FORMCOMPILER_APP_TOKEN", raising=False)

    def run(branches, evaluate=None, *args):
        monkeypatch.setattr(gh, "compile_branches", branches)
        monkeypatch.setattr(readiness, "evaluate", evaluate or (lambda entry, branch, sha, *_, **__: (readiness.READY, "checks passed", "1.0.0")))
        monkeypatch.setattr(sys, "argv", ["watch.py", *args])
        code = 0
        try:
            watch.main()
        except SystemExit as stop:
            code = stop.code
        return code, capsys.readouterr().out, dispatched

    return run


def unreadable(repo):
    raise gh.ApiError(404, f"{repo} is not readable: make it public or give FORMCOMPILER_APP_TOKEN read access")


def test_every_app_unreadable_without_the_token_fails_once_naming_the_secret(stubbed):
    code, out, dispatched = stubbed(unreadable)
    assert code == 1
    errors = [line for line in out.splitlines() if line.startswith("::error::")]
    assert len(errors) == 1
    assert "FORMCOMPILER_APP_TOKEN secret is not set" in errors[0] and "alpha, beta" in errors[0]
    assert "::warning::" not in out
    assert dispatched == []


def test_a_token_that_cannot_read_fails_and_says_so(stubbed, monkeypatch):
    monkeypatch.setenv("FORMCOMPILER_APP_TOKEN", "set")

    def denied(repo):
        raise gh.ApiError(401, "Bad credentials")

    code, out, _ = stubbed(denied)
    assert code == 1
    assert "FORMCOMPILER_APP_TOKEN secret cannot read 2 app repositories" in out


def test_readable_apps_still_start_when_one_is_unreadable(stubbed):
    code, out, dispatched = stubbed(lambda repo: unreadable(repo) if repo.endswith("beta") else [("compile_v1.0.0", "a" * 40)])
    assert code == 1
    assert dispatched == ["alpha"]
    assert "(beta)" in out


def test_ordinary_refusals_stay_non_fatal(stubbed):
    def refuse(entry, branch, sha, *_, **__):
        return readiness.REFUSE, "checks did not pass", "1.0.0"

    code, out, dispatched = stubbed(lambda repo: [("compile_v1.0.0", "a" * 40)], refuse)
    assert code == 0
    assert out.count("::warning::") == 2
    assert "::error::" not in out
    assert dispatched == []


def test_a_server_error_is_a_refusal_not_an_outage(stubbed):
    def broken(repo):
        raise gh.ApiError(502, "Bad Gateway")

    code, out, _ = stubbed(broken)
    assert code == 0
    assert out.count("::warning::") == 2


def test_dry_run_starts_nothing_and_still_reports_the_outage(stubbed):
    code, out, dispatched = stubbed(lambda repo: unreadable(repo) if repo.endswith("beta") else [("compile_v1.0.0", "a" * 40)], None, "--dry-run")
    assert code == 1
    assert dispatched == []
    assert "dry run, not started" in out
    assert "FORMCOMPILER_APP_TOKEN" in out


def test_dry_run_with_every_app_readable_succeeds(stubbed):
    code, _, dispatched = stubbed(lambda repo: [], None, "--dry-run")
    assert code == 0
    assert dispatched == []


def test_a_failed_lookup_of_running_releases_is_not_read_as_none_running(monkeypatch):
    """A transient API error used to look like "nothing running", so the watch could start the same build twice."""
    def failing(path, app_side=False):
        raise gh.ApiError(502, "Bad Gateway")

    monkeypatch.setattr(gh, "get", failing)
    with pytest.raises(gh.ApiError):
        gh.active_release_runs("nodemode-dev/formcompiler")


def test_the_watch_starts_nothing_for_an_app_whose_running_releases_cannot_be_listed(monkeypatch, capsys):
    entry = {"app": "alpha", "repository": "nodemode-dev/alpha", "enabled": True, "checks": ["ci.yml"], "version": {"file": "VERSION", "pattern": ""}}
    dispatched = []

    def failing(repo):
        raise gh.ApiError(502, "Bad Gateway")

    monkeypatch.setattr(watch, "all_entries", lambda: [entry])
    monkeypatch.setattr(watch, "validate", lambda entry, _: [])
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.2.0", "a" * 40)])
    monkeypatch.setattr(gh, "releases", lambda repo: [])
    monkeypatch.setattr(gh, "active_release_runs", failing)
    monkeypatch.setattr(gh, "succeeded_release_runs", lambda repo, since: set())
    monkeypatch.setattr(gh, "dispatch", lambda *a: dispatched.append(a))
    monkeypatch.setattr(sys, "argv", ["watch.py"])
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    watch.main()
    out = capsys.readouterr().out
    assert dispatched == []
    assert "Bad Gateway" in out and "0 release run(s) started, 1 refused" in out


def test_the_watch_token_can_list_draft_releases():
    text = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "watch.yml").read_text()
    assert "permissions:\n  contents: write\n" in text, "GitHub lists draft releases only to a token with write access; without it every scheduled watch rebuilds an app whose release waits as a draft"


def test_a_release_that_failed_or_was_cancelled_is_not_started_again_by_the_watch(stubbed, monkeypatch):
    """A failed run leaves no draft, so the watch used to rebuild the same commit on every 15-minute tick."""
    sha = "a" * 40
    monkeypatch.setattr(gh, "stopped_release_runs", lambda repo: {gh.run_title("alpha", "1.0.0", sha)})
    code, out, dispatched = stubbed(lambda repo: [("compile_v1.0.0", sha)])
    assert code == 0
    assert dispatched == ["beta"]
    assert "| alpha | compile_v1.0.0 | skip | the release run for alpha 1.0.0 at aaaaaaaaa failed or was cancelled" in out


def test_stopped_release_runs_lists_failed_and_cancelled_titles(monkeypatch):
    seen = []

    def fake(path, app_side=False):
        seen.append(path)
        status = path.split("status=")[1].split("&")[0]
        return {"workflow_runs": [{"display_title": f"alpha 1.0.0 at {status}"}]}

    monkeypatch.setattr(gh, "get", fake)
    assert gh.stopped_release_runs("nodemode-dev/formcompiler") == {"alpha 1.0.0 at failure", "alpha 1.0.0 at cancelled"}
    assert all("/actions/workflows/release.yml/runs?status=" in path for path in seen)
