"""The workflows that sign, publish or start releases run only in nodemode-dev/formcompiler, never in a fork.

A fork copies the workflows but not the secrets, environments or variables; without the guard its scheduled watch
and any dispatched release would run and fail (or, with a fork owner's own secrets, publish under our names). A job
is guarded when its own `if:` names the repository, or when it needs a guarded job and so cannot start without it.
"""
import re
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
GUARD = "github.repository == 'nodemode-dev/formcompiler'"
# Run on pull requests from anyone, use no secret and write nothing.
OPEN_TO_FORKS = {"self-check.yml"}


def jobs(text: str) -> dict[str, str]:
    body = text.split("\njobs:\n", 1)[1]
    parts = re.split(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", body)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def needs(job: str) -> list[str]:
    m = re.search(r"(?m)^    needs:\s*(.+)$", job)
    if not m:
        return []
    return [n.strip() for n in m.group(1).strip("[] ").split(",") if n.strip()]


def job_if(job: str) -> str:
    m = re.search(r"(?ms)^    if:\s*(>-\s*\n(?:      .*\n?)+|.*?$)", job)
    return m.group(1) if m else ""


def guarded(name: str, all_jobs: dict[str, str]) -> bool:
    job = all_jobs[name]
    if GUARD in job_if(job):
        return True
    return any(guarded(n, all_jobs) for n in needs(job) if n in all_jobs)


def release_workflows() -> list[Path]:
    paths = sorted(WORKFLOWS.glob("*.yml"))
    # A reusable workflow runs only when a guarded caller calls it.
    return [p for p in paths if p.name not in OPEN_TO_FORKS and "workflow_call:" not in p.read_text().split("\njobs:\n")[0]]


@pytest.mark.parametrize("path", release_workflows(), ids=lambda p: p.name)
def test_every_release_job_runs_only_in_formcompiler(path):
    all_jobs = jobs(path.read_text())
    unguarded = [name for name in all_jobs if not guarded(name, all_jobs)]
    assert not unguarded, f"{path.name}: {unguarded} can run in a fork; add `if: {GUARD}`"


@pytest.mark.parametrize("name", sorted(OPEN_TO_FORKS))
def test_fork_pull_request_checks_keep_no_token_on_disk(name):
    text = (WORKFLOWS / name).read_text()
    checkouts = len(re.findall(r"uses: actions/checkout@", text))
    assert checkouts and text.count("persist-credentials: false") == checkouts
    assert "secrets." not in text


def test_no_workflow_step_needs_bash_4_globstar():
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        assert "globstar" not in workflow.read_text(), f"{workflow.name}: macOS runners run bash 3.2, which has no globstar"


def test_releases_target_the_branch_not_the_commit_the_run_started_on():
    """The Actions token cannot hold `workflows`, so GitHub refuses a release at a commit whose workflows differ from main's."""
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        assert "--target \"$GITHUB_SHA\"" not in workflow.read_text(), f"{workflow.name}: target main, not the run's commit"


OPTIONAL = {"extras", "image"}


def downstream_of(name: str, all_jobs: dict[str, str], targets: set[str]) -> bool:
    direct = [n for n in needs(all_jobs[name]) if n in all_jobs]
    return any(n in targets or downstream_of(n, all_jobs, targets) for n in direct)


def test_jobs_after_an_optional_job_still_run_when_it_is_skipped():
    all_jobs = jobs((WORKFLOWS / "release.yml").read_text(encoding="utf-8"))
    for name, job in all_jobs.items():
        if name in OPTIONAL or not downstream_of(name, all_jobs, OPTIONAL):
            continue
        cond = job_if(job)
        assert "always()" in cond or "!cancelled()" in cond, f"{name} is skipped whenever an app has no extras or image"


def test_no_windows_step_reads_a_variable_msvc_also_sets():
    text = (WORKFLOWS / "desktop-release.yml").read_text(encoding="utf-8")
    stage = text.split("      - name: Stage\n", 1)[1].split("\n      - ", 1)[0]
    assert not re.search(r"(?m)^\s+PLATFORM:", stage), "MSVC's environment sets Platform, and Windows merges PLATFORM into it, so bash reads an empty $PLATFORM"
    assert "$PLATFORM" not in stage
