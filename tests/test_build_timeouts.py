import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "desktop-release.yml"
LONG = "macos-x64"
CACHE_WINDOW = 9


def limits(text: str) -> tuple[str, str]:
    build_job = re.search(r"(?ms)^  build:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", text).group(1)
    job = re.search(r"(?m)^    timeout-minutes: (.+)$", build_job).group(1).strip()
    step = re.search(r"(?m)^      - name: Build\n        timeout-minutes: (.+)$", build_job).group(1).strip()
    return job, step


def minutes(expression: str, platform: str) -> int:
    if expression.isdigit():
        return int(expression)
    m = re.fullmatch(r"\$\{\{ matrix\.platform == '([a-z0-9-]+)' && (\d+) \|\| (\d+) \}\}", expression)
    assert m, expression
    return int(m.group(2)) if platform == m.group(1) else int(m.group(3))


def test_every_platform_keeps_the_cache_window_after_its_build_step():
    job, step = limits(WORKFLOW.read_text(encoding="utf-8"))
    for platform in ("macos-arm64", LONG, "windows-x64", "linux-x64", "linux-arm64"):
        assert minutes(job, platform) - minutes(step, platform) == CACHE_WINDOW, platform


def test_only_intel_macs_get_the_longer_build():
    job, step = limits(WORKFLOW.read_text(encoding="utf-8"))
    assert (minutes(step, LONG), minutes(job, LONG)) == (70, 79)
    for platform in ("macos-arm64", "windows-x64", "linux-x64", "linux-arm64"):
        assert (minutes(step, platform), minutes(job, platform)) == (40, 49), platform
