import json
import zipfile

import pytest

from catalog import sign
from conftest import script

SEED = "CwsLCwsLCwsLCwsLCwsLCwsLCwsLCwsLCwsLCwsLCws="
PUBLIC = "Zr5+Myx6RTMyvZ0Kf32wVfXF7xoGraZtmLOftoEMRzo="
SIGNATURE = "g03iF4zbMev3fRpRWGz1DD1El/rJVU8ZSoJxJSr7X2wJt/fqdrmxX47s5a3dSOqVyCPazHLe2mg7MXjK01CQDQ=="
BODY = b'{"format":"formai-catalog","format_version":1,"generated":"2026-10-26T00:00:00Z","origin":"shared-test-vector","products":[]}\n'


def test_signing_matches_the_vector_formportals_verifier_accepts():
    signature, public = sign(BODY, SEED)
    assert public == PUBLIC
    assert signature == SIGNATURE


def test_the_cli_writes_the_signature_file(tmp_path, monkeypatch):
    body = tmp_path / "releases.json"
    body.write_bytes(BODY)
    out = tmp_path / "apps.json.sig"
    run = __import__("subprocess").run(
        [__import__("sys").executable, "-I", str(__import__("conftest").SCRIPTS / "catalog.py"), "sign", "--file", str(body), "--out", str(out)],
        capture_output=True, text=True, env={"FORMCOMPILER_CATALOG_KEY": SEED, "PATH": "/usr/bin:/bin"},
    )
    assert run.returncode == 0, run.stderr
    assert out.read_text(encoding="ascii").strip() == SIGNATURE
    assert PUBLIC in run.stdout


def test_a_changed_body_gives_a_different_signature():
    changed = bytearray(BODY)
    changed[5] ^= 0x01
    assert sign(bytes(changed), SEED)[0] != SIGNATURE


def sample_app(root):
    skill = root / ".claude" / "skills" / "sample-harness"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: sample-harness\ndescription: Drives the sample app.\n---\n\n# Sample\n", encoding="utf-8")
    (skill / "references" / "tools.md").write_text("# Tools\n", encoding="utf-8")
    return root


def build(tmp_path):
    app = sample_app(tmp_path / "app")
    dist = tmp_path / "dist"
    out = script("agents.py", "build", "--app", "formvis", "--app-dir", str(app), "--dist", str(dist), "--version", "1.2.3", "--commit", "0123456789abcdef0123456789abcdef01234567")
    assert out.returncode == 0, out.stdout + out.stderr
    return dist


def check(dist):
    return script("agents.py", "check", "--app", "formvis", "--dist", str(dist))


def test_make_then_verify_round_trips_the_manifest_and_skills_zip(tmp_path):
    dist = build(tmp_path)
    manifest = json.loads((dist / "form-app.json").read_text(encoding="utf-8"))
    archive = dist / manifest["agents"]["skills"]["file"]
    assert archive.name == "formvis-skills-v1.2.3.zip"
    with zipfile.ZipFile(archive) as opened:
        assert sorted(opened.namelist()) == ["sample-harness/SKILL.md", "sample-harness/references/tools.md"]
    out = check(dist)
    assert out.returncode == 0, out.stdout + out.stderr


def test_the_same_input_builds_the_same_zip(tmp_path):
    first = build(tmp_path / "a")
    second = build(tmp_path / "b")
    name = "formvis-skills-v1.2.3.zip"
    assert (first / name).read_bytes() == (second / name).read_bytes()


def test_a_changed_skills_zip_fails_verify(tmp_path):
    dist = build(tmp_path)
    archive = dist / "formvis-skills-v1.2.3.zip"
    data = bytearray(archive.read_bytes())
    data[len(data) // 2] ^= 0x01
    archive.write_bytes(bytes(data))
    out = check(dist)
    assert out.returncode != 0
    assert "sha256" in out.stdout + out.stderr


def test_a_manifest_for_another_app_fails_verify(tmp_path):
    dist = build(tmp_path)
    out = script("agents.py", "check", "--app", "formcut", "--dist", str(dist))
    assert out.returncode != 0


def test_a_missing_skills_zip_fails_verify(tmp_path):
    dist = build(tmp_path)
    (dist / "formvis-skills-v1.2.3.zip").unlink()
    assert check(dist).returncode != 0


@pytest.mark.parametrize("version", ["1.2", "v1.2.3", "1.2.3.4"])
def test_build_refuses_a_bad_version(tmp_path, version):
    app = sample_app(tmp_path / "app")
    out = script("agents.py", "build", "--app", "formvis", "--app-dir", str(app), "--dist", str(tmp_path / "dist"), "--version", version)
    assert out.returncode != 0
