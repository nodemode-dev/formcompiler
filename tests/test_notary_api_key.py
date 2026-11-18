"""Mac builds notarize with an App Store Connect API key, and the signing secrets live in the `signing` environment.

The key (APPLE_API_PRIVATE_KEY, base64 of the .p8) needs no Apple ID password and no two-factor code. It is written
to a file only on a macOS runner under `apple` signing, only while the notary is not refusing the account, and the file
is removed in the always-run cleanup step. The build job runs in the `signing` environment, whose deployment branch
policy admits `main` only, so a workflow pushed to any other branch cannot read the certificate or the key.
"""
import re

from conftest import REPO
from run_build import clean_secrets

WORKFLOW = (REPO / ".github" / "workflows" / "desktop-release.yml").read_text(encoding="utf-8")
API = ("APPLE_API_KEY", "APPLE_API_ISSUER", "APPLE_API_KEY_PATH")


def build_job() -> str:
    return WORKFLOW.split("\n  build:\n", 1)[1]


def step(name: str) -> str:
    body = WORKFLOW.split(f"- name: {name}\n", 1)[1]
    return re.split(r"\n      - (?:name|uses): ", body, maxsplit=1)[0]


def test_the_build_job_runs_in_the_signing_environment():
    assert re.search(r"(?m)^    environment: signing$", build_job())


def test_the_api_key_variables_are_one_secret_group():
    env = clean_secrets({"APPLE_API_KEY": "", "APPLE_API_ISSUER": "issuer", "APPLE_API_KEY_PATH": "/tmp/k.p8"})
    assert not any(name in env for name in API)
    kept = clean_secrets({"APPLE_API_KEY": "KEYID", "APPLE_API_ISSUER": "issuer", "APPLE_API_KEY_PATH": ""})
    assert kept == {"APPLE_API_KEY": "KEYID", "APPLE_API_ISSUER": "issuer"}


def test_the_key_file_is_written_only_for_apple_signing_on_macos():
    text = step("Notary API key")
    assert text.splitlines()[0].strip() == "if: runner.os == 'macOS' && inputs.macos-signing == 'apple'"
    assert "secrets.APPLE_API_PRIVATE_KEY" in text
    assert "chmod 600" in text
    assert "FORMCOMPILER_NOTARY_KEY=" in text
    assert WORKFLOW.index("- name: Notary API key") < WORKFLOW.index("- name: Notary check")


def test_every_line_of_the_decoded_key_is_masked_before_anything_else_runs():
    text = step("Notary API key")
    mask = text.index('echo "::add-mask::$line"')
    assert text.index("base64 --decode") < mask < text.index("FORMCOMPILER_NOTARY_KEY=")


def test_the_cleanup_step_removes_the_key_folder_even_after_a_failed_decode():
    text = step("Remove the Apple signing keychain")
    assert "if: always() && runner.os == 'macOS'" in text
    assert 'rm -rf "$RUNNER_TEMP/formcompiler-notary"' in text
    assert "FORMCOMPILER_NOTARY_KEY:-" not in text


def test_every_notarytool_call_takes_the_chosen_credentials():
    calls = [line for line in WORKFLOW.splitlines() if "xcrun notarytool " in line]
    assert len(calls) >= 5
    assert all('"${notary[@]}"' in line and "--apple-id" not in line for line in calls)


def test_the_tauri_build_gets_one_notary_method_and_never_under_developer_id():
    for name in ("Build", "Post-build"):
        text = step(name)
        for var in API:
            line = next(l for l in text.splitlines() if l.strip().startswith(f"{var}:"))
            assert "inputs.macos-signing == 'apple'" in line and "'developer-id'" not in line, (name, var)
            assert "env.FORMCOMPILER_NOTARY != 'refused'" in line and "env.FORMCOMPILER_NOTARY_KEY != ''" in line
        for var in ("APPLE_ID", "APPLE_PASSWORD"):
            line = next(l for l in text.splitlines() if l.strip().startswith(f"{var}:"))
            assert "env.FORMCOMPILER_NOTARY_KEY == ''" in line, (name, var)
