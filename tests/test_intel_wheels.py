import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "desktop-release.yml"
INDEX = "https://dl.formai.studio/deps/macos-x64/"


def steps(text: str) -> list[str]:
    build_job = re.search(r"(?ms)^  build:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", text).group(1)
    return re.split(r"(?m)^      - ", build_job)[1:]


def test_intel_mac_builds_look_for_wheels_in_the_formai_index_before_the_app_set_up():
    found = steps(WORKFLOW.read_text(encoding="utf-8"))
    names = [s.splitlines()[0] for s in found]
    wheels = names.index("name: Intel Mac wheels")
    assert wheels < names.index("name: App set-up")
    body = found[wheels]
    assert "if: matrix.platform == 'macos-x64'" in body
    assert f'PIP_FIND_LINKS={INDEX}' in body and f'UV_FIND_LINKS={INDEX}' in body


def test_no_other_platform_is_pointed_at_the_intel_index():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count(INDEX) == 2
