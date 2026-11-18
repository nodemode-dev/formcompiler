import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "desktop-release.yml"
OS = {"macos-arm64": "macos", "macos-x64": "macos", "macos-universal": "macos", "windows-x64": "windows", "windows-arm64": "windows", "linux-x64": "linux", "linux-arm64": "linux"}
CACHE_WINDOW = 9
NOTARIZE_STEP = 15
EXPECTED = {"macos-x64": (100, 125), "macos-arm64": (60, 85), "macos-universal": (60, 85)}
OTHER = (40, 49)


def limits(text: str) -> tuple[str, str]:
    build_job = re.search(r"(?ms)^  build:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", text).group(1)
    job = re.search(r"(?m)^    timeout-minutes: (.+)$", build_job).group(1).strip()
    step = re.search(r"(?m)^      - name: Build\n        timeout-minutes: (.+)$", build_job).group(1).strip()
    return job, step


def minutes(expression: str, platform: str) -> int:
    if expression.isdigit():
        return int(expression)
    m = re.fullmatch(
        r"\$\{\{ matrix\.platform == '([a-z0-9-]+)' && (\d+) \|\| \(matrix\.os == '([a-z]+)' && (\d+) \|\| (\d+)\) \}\}",
        expression,
    )
    assert m, expression
    if platform == m.group(1):
        return int(m.group(2))
    return int(m.group(4)) if OS[platform] == m.group(3) else int(m.group(5))


def notarize_step(text: str) -> str:
    body = text.split("- name: Notarize the macOS disk images\n", 1)[1]
    return re.split(r"\n      - (?:name|uses): ", body, maxsplit=1)[0]


def test_each_platform_gets_its_build_and_job_limits():
    job, step = limits(WORKFLOW.read_text(encoding="utf-8"))
    for platform in OS:
        assert (minutes(step, platform), minutes(job, platform)) == EXPECTED.get(platform, OTHER), platform


def test_every_platform_keeps_the_cache_window_after_its_build_step():
    job, step = limits(WORKFLOW.read_text(encoding="utf-8"))
    for platform in OS:
        assert minutes(job, platform) - minutes(step, platform) >= CACHE_WINDOW, platform


def test_a_mac_job_has_room_for_the_disk_image_notarization_after_its_build():
    text = WORKFLOW.read_text(encoding="utf-8")
    job, step = limits(text)
    assert f"timeout-minutes: {NOTARIZE_STEP}" in notarize_step(text)
    for platform, os_name in OS.items():
        if os_name == "macos":
            assert minutes(job, platform) - minutes(step, platform) >= CACHE_WINDOW + NOTARIZE_STEP, platform


def test_the_disk_image_wait_is_bounded_and_asks_apple_twice():
    text = notarize_step(WORKFLOW.read_text(encoding="utf-8"))
    assert 'xcrun notarytool wait "$id" "${notary[@]}" --timeout 6m' in text
    assert "for wait in 1 2; do" in text
    assert "Re-run failed jobs" in text
