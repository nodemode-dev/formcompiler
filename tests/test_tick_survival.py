import pytest

import github_api as gh
import tick
from test_tick import api, arguments, release


def drive_loop(**extra):
    clock = [1_700_000_000.0]
    tick.command_loop(arguments(minutes=30, **extra), lambda: clock[0], lambda s: clock.__setitem__(0, clock[0] + s))


def runs_then_releases(runs):
    return lambda path, **kw: runs if "/actions/workflows/" in path else [release("v1.2.0", "2026-11-10T12:30:00Z")]


def test_a_feed_state_that_is_not_a_string_costs_a_line_per_pass_not_the_loop(api, monkeypatch, tmp_path):
    monkeypatch.setattr(tick, "feed_state", lambda base: 12345)
    monkeypatch.setattr(tick, "still_owner", lambda args, sleep: True)
    drive_loop()
    summary = (tmp_path / "summary").read_text()
    assert summary.count("feed: not checked") == 3
    assert summary.count("watch: started") == 3
    assert (tmp_path / "out").read_text().endswith("yielded=false\n")


def test_a_registry_that_is_not_an_object_costs_a_line_per_pass(api, monkeypatch, tmp_path):
    def broken():
        raise AttributeError("'list' object has no attribute 'get'")

    monkeypatch.setattr(tick, "enabled_entries", broken)
    monkeypatch.setattr(tick, "still_owner", lambda args, sleep: True)
    drive_loop()
    assert (tmp_path / "summary").read_text().count("feed: not checked") == 3
    assert (tmp_path / "out").read_text().endswith("yielded=false\n")


def test_an_unexpected_watch_error_costs_a_line_per_pass(api, monkeypatch, tmp_path):
    def boom(method, path, body=None, **kw):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(gh, "request", boom)
    monkeypatch.setattr(tick, "still_owner", lambda args, sleep: True)
    drive_loop()
    assert (tmp_path / "summary").read_text().count("watch: not started") == 3
    assert (tmp_path / "out").read_text().endswith("yielded=false\n")


@pytest.mark.parametrize("runs, after", [
    ([], None),
    ({"workflow_runs": ["not a run"]}, None),
    ({"workflow_runs": [{"status": "in_progress", "display_title": "tick after 5"}]}, 5),
])
def test_a_malformed_runs_listing_keeps_the_clock_and_the_loop(api, monkeypatch, tmp_path, capsys, runs, after):
    monkeypatch.setattr(gh, "get", runs_then_releases(runs))
    drive_loop(after=after)
    summary = (tmp_path / "summary").read_text()
    assert summary.count("watch: started") == 3
    assert (tmp_path / "out").read_text().endswith("yielded=false\n")
    assert capsys.readouterr().out.count("this tick keeps the clock") == 2


def test_a_malformed_runs_listing_lets_the_owner_step_keep_the_clock(api, monkeypatch, tmp_path):
    monkeypatch.setattr(gh, "get", runs_then_releases([]))
    tick.command_owner(arguments(), lambda _: None)
    assert (tmp_path / "out").read_text() == "owner=true\n"
