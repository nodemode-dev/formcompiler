import datetime
import re
import sys

import pytest

import github_api as gh
import tick
from conftest import REPO, entries

WORKFLOW = (REPO / ".github" / "workflows" / "tick.yml").read_text(encoding="utf-8")
NOW = datetime.datetime(2026, 11, 10, 12, 40, tzinfo=datetime.timezone.utc)
PLANNED = "2026-11-10T04:04:34Z"


def run(number, status="in_progress", title="tick schedule"):
    return {"id": number, "status": status, "display_title": title}


def release(tag, published, draft=False):
    return {"tag_name": tag, "published_at": published, "draft": draft}


def test_the_tick_runs_only_in_formcompiler_and_only_on_main():
    assert "if: github.repository == 'nodemode-dev/formcompiler' && github.ref == 'refs/heads/main'" in WORKFLOW


def test_the_tick_has_its_own_schedule_as_a_backup_and_a_dispatch_for_its_successor():
    assert 'cron: "*/15 * * * *"' in WORKFLOW
    assert "workflow_dispatch:" in WORKFLOW and "after:" in WORKFLOW
    assert "run-name: tick ${{ inputs.after && format('after {0}', inputs.after) || github.event_name }}" in WORKFLOW


def test_the_tick_may_dispatch_workflows_and_read_contents_only():
    block = WORKFLOW.split("\npermissions:\n", 1)[1].split("\n\n", 1)[0]
    assert sorted(line.strip() for line in block.splitlines()) == ["actions: write", "contents: read"]


def test_no_concurrency_group_queues_the_backup_behind_a_running_tick():
    assert "concurrency:" not in WORKFLOW


def test_the_tick_stays_inside_the_job_limit_and_hands_over_before_it():
    assert "timeout-minutes: 350" in WORKFLOW and "timeout-minutes: 340" in WORKFLOW
    assert "--minutes 330 --every 15" in WORKFLOW


def test_the_next_tick_starts_unless_cancelled_or_yielded():
    assert "if: ${{ !cancelled() && steps.owner.outputs.owner == 'true' && steps.loop.outputs.yielded != 'true' }}" in WORKFLOW
    assert "python3 -I scripts/tick.py chain" in WORKFLOW


def test_the_loop_gets_the_tokens_it_needs_through_env():
    for line in ("GH_TOKEN: ${{ github.token }}", "FORMCOMPILER_APP_TOKEN: ${{ secrets.FORMCOMPILER_APP_TOKEN }}",
                 "FORMPIPE_DISPATCH_TOKEN: ${{ secrets.FORMPIPE_DISPATCH_TOKEN }}", "FORMCOMPILER_PUBLIC_BASE: ${{ vars.FORMCOMPILER_PUBLIC_BASE }}"):
        assert line in WORKFLOW


def test_no_expression_inside_a_run_script():
    for script in re.findall(r"(?m)^ +run: (.*)$", WORKFLOW):
        assert "${{" not in script


def test_every_action_is_pinned_to_a_full_sha_with_its_version():
    uses = re.findall(r"(?m)^\s+(?:- )?uses: (\S+)(.*)$", WORKFLOW)
    assert uses
    for target, rest in uses:
        assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", target), target
        assert re.fullmatch(r" # v\d+(\.\d+)*", rest), target


def test_a_successor_owns_the_clock_while_its_predecessor_finishes():
    runs = [run(10, title="tick schedule"), run(11, "queued", "tick after 10"), run(12, title="tick schedule")]
    assert tick.owns(11, 10, runs)
    assert not tick.owns(12, None, runs)


def test_a_backup_run_yields_to_a_running_tick():
    assert not tick.owns(12, None, [run(10), run(12)])
    assert not tick.owns(12, None, [run(10, title="tick after 5"), run(12)])


def test_of_two_backup_runs_the_older_owns_the_clock():
    runs = [run(20), run(21)]
    assert tick.owns(20, None, runs) and not tick.owns(21, None, runs)


def test_a_finished_tick_does_not_hold_the_clock():
    assert tick.owns(30, None, [run(10, "completed"), run(30)])


def test_published_releases_after_the_feed_state_are_unfed():
    found = tick.unfed({("alpha", "nodemode-dev/alpha"): [
        release("v1.2.0", "2026-11-10T12:30:00Z"),
        release("v1.1.0", "2026-11-09T12:30:00Z"),
        release("v1.3.0", "", draft=True),
        release("alpha-v9.0.0", "2026-11-10T12:31:00Z"),
    ], ("beta", "nodemode-dev/beta"): [release("v2.0.0-beta.1", "2026-11-10T12:00:00Z")]}, PLANNED)
    assert [(i["app"], i["tag"]) for i in found] == [("beta", "v2.0.0-beta.1"), ("alpha", "v1.2.0")]
    assert found[-1]["repository"] == "nodemode-dev/alpha"


def test_a_release_published_since_the_last_tick_is_sent_at_once():
    item, why = tick.to_dispatch([{"published_at": "2026-11-10T12:30:00Z", "app": "alpha", "tag": "v1.2.0", "repository": "r"}], NOW, 15)
    assert item["tag"] == "v1.2.0" and "since the last tick" in why


def test_an_older_unfed_release_waits_for_the_hours_first_tick():
    waiting = [{"published_at": "2026-11-10T10:00:00Z", "app": "alpha", "tag": "v1.2.0", "repository": "r"}]
    assert tick.to_dispatch(waiting, NOW, 15)[0] is None
    assert tick.to_dispatch(waiting, NOW.replace(hour=13, minute=5), 15)[0]["tag"] == "v1.2.0"


def test_nothing_unfed_sends_nothing():
    assert tick.to_dispatch([], NOW, 15)[0] is None


def test_a_hiccup_is_retried_then_reported_and_a_refusal_is_not_retried():
    calls, waits = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise gh.ApiError(502, "bad gateway")
        return "ok"

    assert tick.attempt("x", flaky, waits.append) == "ok" and waits == [10, 30]

    def broken():
        raise gh.ApiError(503, "down")

    with pytest.raises(tick.Unreachable, match="after 3 attempts"):
        tick.attempt("x", broken, lambda _: None)
    calls.clear()

    def refused():
        calls.append(1)
        raise gh.ApiError(403, "no")

    with pytest.raises(tick.Unreachable):
        tick.attempt("x", refused, lambda _: None)
    assert len(calls) == 1


@pytest.fixture
def api(monkeypatch, tmp_path):
    sent = []
    monkeypatch.setattr(gh, "request", lambda method, path, body=None, **kw: sent.append((method, path, body, kw.get("token_env", ""))) or (None, ""))
    monkeypatch.setattr(tick, "enabled_entries", lambda: [{"app": "alpha", "repository": "nodemode-dev/alpha"}])
    monkeypatch.setattr(tick, "feed_state", lambda base: PLANNED)
    monkeypatch.setattr(gh, "get", lambda path, **kw: [release("v1.2.0", "2026-11-10T12:30:00Z")])
    monkeypatch.setenv("FORMPIPE_DISPATCH_TOKEN", "set")
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out"))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
    return sent


def arguments(**extra):
    values = {"repo": "nodemode-dev/formcompiler", "ref": "main", "run_id": 99, "after": None, "minutes": 30, "every": 15, "base": "https://dl.example"}
    return type("Args", (), {**values, **extra})()


def test_a_tick_dispatches_the_watch_and_the_feed_with_the_payload_formpipe_reads(api):
    lines = tick.tick_once(arguments(), NOW, lambda _: None)
    assert ("POST", "/repos/nodemode-dev/formcompiler/actions/workflows/watch.yml/dispatches", {"ref": "main"}, "") in api
    feed = [s for s in api if s[1] == "/repos/nodemode-dev/formpipe/dispatches"]
    assert feed == [("POST", "/repos/nodemode-dev/formpipe/dispatches",
                     {"event_type": "formcompiler-published", "client_payload": {"app": "alpha", "tag": "v1.2.0", "repository": "nodemode-dev/alpha"}},
                     "FORMPIPE_DISPATCH_TOKEN")]
    assert lines[0] == "watch: started" and "sent formcompiler-published for alpha v1.2.0" in lines[1]


def test_a_tick_without_the_dispatch_token_starts_the_watch_only(api, monkeypatch):
    monkeypatch.delenv("FORMPIPE_DISPATCH_TOKEN")
    lines = tick.tick_once(arguments(), NOW, lambda _: None)
    assert [s[1] for s in api] == ["/repos/nodemode-dev/formcompiler/actions/workflows/watch.yml/dispatches"]
    assert "FORMPIPE_DISPATCH_TOKEN is not set" in lines[1]


def test_a_failed_watch_dispatch_never_fails_the_tick(api, monkeypatch, capsys):
    def down(method, path, body=None, **kw):
        raise gh.ApiError(500, "down")

    monkeypatch.setattr(gh, "request", down)
    lines = tick.tick_once(arguments(), NOW, lambda _: None)
    assert lines[0].startswith("watch: not started") and lines[1].startswith("feed: not checked")
    assert "::warning::" in capsys.readouterr().out


def test_the_loop_ticks_on_a_fixed_clock_and_stops_when_another_tick_owns_it(api, monkeypatch, tmp_path):
    clock = [1_700_000_000.0]
    slept = []
    monkeypatch.setattr(tick, "still_owner", lambda args, sleep: True)
    tick.command_loop(arguments(minutes=30), lambda: clock[0], lambda s: (slept.append(s), clock.__setitem__(0, clock[0] + s)))
    assert slept == [900, 900]
    assert "yielded=false" in (tmp_path / "out").read_text()
    monkeypatch.setattr(tick, "still_owner", lambda args, sleep: False)
    tick.command_loop(arguments(minutes=30), lambda: clock[0], lambda s: clock.__setitem__(0, clock[0] + s))
    assert (tmp_path / "out").read_text().endswith("yielded=true\n")


def test_the_chain_dispatches_the_next_tick_naming_this_one(api):
    tick.command_chain(arguments(), lambda _: None)
    assert api == [("POST", "/repos/nodemode-dev/formcompiler/actions/workflows/tick.yml/dispatches", {"ref": "main", "inputs": {"after": "99"}}, "")]


@pytest.mark.parametrize("value", ["abc", "1; rm", "-1", "0"])
def test_a_bad_after_is_refused(value, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["tick.py", "owner", "--run-id", "5", "--after", value])
    with pytest.raises(SystemExit):
        tick.main()


def test_formcut_keys_its_build_cache_on_the_opencv_build_too():
    formcut = next(e for e in entries() if e["app"] == "formcut")
    assert "backend/prepare_cv.py" in formcut["toolchain"]["build_cache"]["key_files"]
