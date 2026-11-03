"""Every app release lives on the app's own repository, tagged vX.Y.Z at the gated commit (formcompiler v0.9.0).

formcompiler is the factory and the gate; it keeps no app releases. The scripts read each app repository's release
list, the assemble job writes there with a credential from the release environment, and formpipe is told the app,
the tag and the repository.
"""
import json
import re
import sys

import pytest

import catalog
import feed
import gate
import github_api as gh
import readiness
import versions
import watch
from conftest import script
from registry import all_entries, load
from test_workflow_guards import WORKFLOWS, jobs

SHA = "a" * 40
OTHER = "b" * 40
ENTRY = {"app": "alpha", "repository": "nodemode-dev/alpha", "enabled": True, "checks": ["ci.yml"],
         "version": {"file": "VERSION", "pattern": ""}}
RELEASE = (WORKFLOWS / "release.yml").read_text()
APP_REPOSITORY = "${{ fromJSON(needs.gate.outputs.config).repository }}"
WRITE_CREDENTIALS = ("FORMCOMPILER_WRITE_TOKEN", "FORMCOMPILER_APP_PRIVATE_KEY", "FORMCOMPILER_APP_ID", "steps.app-token.outputs.token")


def gh_release(version, draft=False, repo="nodemode-dev/formvis"):
    tag = f"v{version}"
    names = [f"formvis-{version}-macos-arm64.dmg", "SHA256SUMS.txt"]
    return {"tag_name": tag, "draft": draft, "prerelease": versions.channel(version) == versions.BETA, "published_at": "2026-11-03T00:00:00Z",
            "html_url": f"https://github.com/{repo}/releases/tag/{tag}", "body": "",
            "assets": [{"name": n, "size": 10, "url": f"https://api.github.com/assets/{n}", "browser_download_url": f"https://github.com/{repo}/releases/download/{tag}/{n}"} for n in names]}


def test_release_lists_are_read_with_the_app_side_token(monkeypatch):
    """The app repositories are read with FORMCOMPILER_APP_TOKEN, as their branches and tags already are."""
    seen = []
    monkeypatch.setattr(gh, "paged", lambda path, key=None, app_side=False: seen.append((path, app_side)) or [])
    assert gh.releases("nodemode-dev/formtray") == []
    assert seen == [("/repos/nodemode-dev/formtray/releases", True)]


def test_the_gate_reads_the_app_repository_and_tags_v_version(monkeypatch):
    read = []
    written = {}
    monkeypatch.setattr(gate, "load", lambda app: ENTRY)
    monkeypatch.setattr(gate, "write_outputs", lambda values: written.update(values))
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.2.0", SHA)])
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "releases", lambda repo: read.append(repo) or [])
    monkeypatch.setattr(gh, "summary", lambda text: None)
    monkeypatch.setattr(readiness, "evaluate", lambda entry, branch, sha, releases, active: (readiness.READY, "ok", "1.2.0"))
    monkeypatch.setattr(sys, "argv", ["gate.py", "--app", "alpha", "--ref", "compile_v1.2.0"])
    gate.main()
    assert read == ["nodemode-dev/alpha"]
    assert written["tag"] == "v1.2.0" and written["sha"] == SHA


def test_readiness_names_the_app_and_its_v_tag(monkeypatch):
    monkeypatch.setattr(gh, "on_main", lambda repo, sha: True)
    status, reason, _ = readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [{"tag_name": "v1.2.0", "draft": False}], set())
    assert status == readiness.SKIP and reason.startswith("alpha v1.2.0 is already published")
    drafted = {"tag_name": "v1.2.0", "draft": True, "body": f"<!-- formcompiler-source: nodemode-dev/alpha@{SHA} -->"}
    status, reason, _ = readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [drafted], set())
    assert status == readiness.SKIP and "already drafted" in reason


def test_older_drafts_cli_reads_the_registry_repository(monkeypatch, capsys):
    read = []
    monkeypatch.setattr(gh, "releases", lambda repo: read.append(repo) or [{"tag_name": "v0.0.1", "draft": True}, {"tag_name": "v0.0.2", "draft": False}])
    monkeypatch.setattr(sys, "argv", ["versions.py", "older-drafts", "--app", "formvis", "--version", "9.9.9"])
    versions.main()
    assert read == [load("formvis")["repository"]]
    assert capsys.readouterr().out == "v0.0.1\n"


@pytest.fixture
def watching(monkeypatch, capsys):
    entries = [ENTRY, dict(ENTRY, app="beta", repository="nodemode-dev/beta")]
    calls = {"releases": [], "dispatched": [], "succeeded": set()}
    monkeypatch.setattr(watch, "all_entries", lambda: entries)
    monkeypatch.setattr(watch, "validate", lambda entry, _: [])
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.1.0", OTHER), ("compile_v1.0.0", SHA)])
    monkeypatch.setattr(gh, "releases", lambda repo: calls["releases"].append(repo) or [])
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "stopped_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "succeeded_release_runs", lambda repo: calls["succeeded"])
    monkeypatch.setattr(gh, "dispatch", lambda repo, ref, inputs: calls["dispatched"].append((inputs["app"], inputs["version"])))
    monkeypatch.setattr(readiness, "evaluate", lambda entry, ref, sha, releases, active: (readiness.READY, "ok", readiness.ref_version(ref)[0]))
    monkeypatch.setattr(sys, "argv", ["watch.py"])
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    def run():
        watch.main()
        return capsys.readouterr().out

    return run, calls


def test_the_watch_reads_each_app_repository_release_list_once(watching):
    run, calls = watching
    run()
    assert calls["releases"] == ["nodemode-dev/alpha", "nodemode-dev/beta"]
    assert calls["dispatched"] == [("alpha", "1.1.0"), ("beta", "1.1.0")]


def test_a_succeeded_release_run_stands_in_for_the_draft_the_watch_cannot_see(watching):
    """GitHub lists an app repository's drafts only to a token with write access there; the read-only app token sees
    none, so without this the watch would rebuild a drafted commit every hour, as it did before v0.6.7."""
    run, calls = watching
    calls["succeeded"].add(gh.run_title("alpha", "1.1.0", OTHER))
    out = run()
    assert calls["dispatched"] == [("beta", "1.1.0")]
    assert "| alpha | compile_v1.1.0 | skip | the release run for alpha 1.1.0 at bbbbbbbbb succeeded; its release is on nodemode-dev/alpha" in out
    assert "| alpha | compile_v1.0.0 | skip | compile_v1.1.0 is ahead" in out


def test_succeeded_release_runs_lists_the_successful_titles(monkeypatch):
    seen = []
    monkeypatch.setattr(gh, "get", lambda path, app_side=False: seen.append(path) or {"workflow_runs": [{"display_title": "alpha 1.0.0 at " + SHA}]})
    assert gh.succeeded_release_runs("nodemode-dev/formcompiler") == {f"alpha 1.0.0 at {SHA}"}
    assert seen == ["/repos/nodemode-dev/formcompiler/actions/workflows/release.yml/runs?status=success&per_page=100"]


@pytest.fixture
def sums(monkeypatch):
    monkeypatch.setattr(catalog, "fetch_sums", lambda release: {a["name"]: "d" * 64 for a in release["assets"] if a["name"] != "SHA256SUMS.txt"})


def channels(document, product_id):
    return next(p for p in document["products"] if p["id"] == product_id)["channels"]


def test_the_catalogue_reads_each_app_repository_own_releases(sums):
    """A v1.2.0 on formvis's repository is formvis 1.2.0 and nothing else's; an app with no listed repository has no channel."""
    releases = {"nodemode-dev/formvis": [gh_release("1.2.0"), gh_release("1.3.0-beta.1")], "nodemode-dev/formcut": [gh_release("3.0.0", repo="nodemode-dev/formcut")]}
    document = catalog.build([load("formvis"), load("formcut"), load("formtray")], releases)
    assert channels(document, "formvis")["stable"]["version"] == "1.2.0"
    assert channels(document, "formvis")["beta"]["version"] == "1.3.0-beta.1"
    assert channels(document, "formcut") == {"stable": channels(document, "formcut")["stable"]} and channels(document, "formcut")["stable"]["version"] == "3.0.0"
    assert channels(document, "formtray") == {}
    assert document["origin"] == "https://github.com/nodemode-dev/formcompiler"
    stable = channels(document, "formvis")["stable"]
    assert stable["artifacts"][0]["url"] == "https://github.com/nodemode-dev/formvis/releases/download/v1.2.0/formvis-1.2.0-macos-arm64.dmg"
    assert stable["notes"] == "https://github.com/nodemode-dev/formvis/releases/tag/v1.2.0"


def test_the_catalogue_asks_the_api_for_every_enabled_repository_once(monkeypatch):
    asked = []
    monkeypatch.setattr(gh, "releases", lambda repo: asked.append(repo) or [])
    entries = all_entries()
    found = catalog.fetch_releases(entries)
    enabled = {e["repository"] for e in entries if e["enabled"]}
    assert set(asked) == enabled and len(asked) == len(enabled)
    assert set(found) == enabled and "nodemode-dev/formcompiler" not in found


def test_an_unreadable_app_repository_stops_the_catalogue(monkeypatch):
    def denied(repo):
        raise gh.ApiError(404, "Not Found")

    monkeypatch.setattr(gh, "releases", denied)
    with pytest.raises(SystemExit, match="could not list the releases of nodemode-dev/"):
        catalog.fetch_releases(all_entries())


def test_the_catalogue_cli_takes_releases_per_repository(tmp_path, monkeypatch):
    releases = tmp_path / "releases.json"
    releases.write_text(json.dumps({"nodemode-dev/formtray": [{**gh_release("0.9.8", repo="nodemode-dev/formtray"), "assets": []}]}), encoding="utf-8")
    out = script("catalog.py", "build", "--releases", str(releases), "--out", str(tmp_path / "apps.json"))
    assert out.returncode == 0, out.stdout + out.stderr
    document = json.loads((tmp_path / "apps.json").read_text(encoding="utf-8"))
    assert channels(document, "formtray")["stable"]["version"] == "0.9.8"
    listed = script("catalog.py", "listed", "--file", str(tmp_path / "apps.json"))
    assert listed.stdout == "formtray\t0.9.8\n"
    releases.write_text("[]", encoding="utf-8")
    out = script("catalog.py", "build", "--releases", str(releases), "--out", str(tmp_path / "apps.json"))
    assert out.returncode != 0 and "JSON object mapping each app repository" in out.stdout + out.stderr


@pytest.mark.parametrize("tag", ["v0.9.8", "0.9.8"])
def test_feed_resolve_names_the_app_its_repository_and_its_title(monkeypatch, tag):
    written = {}
    monkeypatch.setattr(feed, "write_outputs", lambda values: written.update(values))
    monkeypatch.setattr(gh, "releases", lambda repo: pytest.fail("no release list is needed for an app without update files"))
    monkeypatch.setattr(sys, "argv", ["feed.py", "resolve", "--app", "formtray", "--tag", tag])
    feed.main()
    assert written == {"app": "formtray", "title": "formtray", "version": "0.9.8", "tag": "v0.9.8", "repository": "nodemode-dev/formtray",
                       "prerelease": "false", "channel": "stable", "updates": "false", "tag_json": "false"}


def test_feed_resolve_reads_the_app_repository_for_the_update_feed(monkeypatch):
    written, read = {}, []
    monkeypatch.setattr(feed, "write_outputs", lambda values: written.update(values))
    monkeypatch.setattr(gh, "releases", lambda repo: read.append(repo) or [{"tag_name": "v1.0.0", "draft": False}])
    monkeypatch.setattr(sys, "argv", ["feed.py", "resolve", "--app", "formvis", "--tag", "v1.2.3"])
    feed.main()
    assert read == ["nodemode-dev/formvis"]
    assert written["updates"] == "true" and written["repository"] == "nodemode-dev/formvis" and written["prerelease"] == "false"
    monkeypatch.setattr(sys, "argv", ["feed.py", "resolve", "--app", "formvis", "--tag", "v1.3.0-beta.1"])
    feed.main()
    assert written["prerelease"] == "true" and written["channel"] == "beta" and written["updates"] == "false"


@pytest.mark.parametrize("args, says", [
    (["--app", "formvis", "--tag", "formvis-v1.2.3"], "not a release tag"),
    (["--app", "formvis", "--tag", "v1.2"], "not a release tag"),
    (["--app", "nosuchapp", "--tag", "v1.2.3"], "no registry entry"),
])
def test_feed_refuses_a_tag_that_is_not_v_version_or_an_unknown_app(args, says):
    out = script("feed.py", "resolve", *args)
    assert out.returncode != 0 and says in out.stdout + out.stderr


def test_feed_files_takes_the_app(tmp_path):
    out = script("feed.py", "files", "--app", "formvis", "--tag", "v1.2.3", "--assets", json.dumps(["latest.json", "formvis-1.2.3-linux-x64.AppImage.zsync", "a.dmg"]))
    assert out.returncode == 0, out.stderr
    assert out.stdout == "formvis-1.2.3-linux-x64.AppImage.zsync\nlatest.json\n"
    assert script("feed.py", "files", "--tag", "v1.2.3", "--assets", "[]").returncode != 0


def test_latest_json_points_at_the_app_repository_release(tmp_path):
    (tmp_path / "formtray-0.9.8-macos-arm64.app.tar.gz").write_bytes(b"bundle")
    manifest = {"platform": "macos-arm64", "updater_key": "darwin-aarch64", "files": ["formtray-0.9.8-macos-arm64.app.tar.gz"],
                "update": {"file": "formtray-0.9.8-macos-arm64.app.tar.gz", "signature": "sig"}}
    (tmp_path / "macos-arm64.formcompiler.json").write_text(json.dumps(manifest), encoding="utf-8")
    out = script("release_assets.py", "--dir", str(tmp_path), "--version", "0.9.8", "--tag", "v0.9.8", "--repo", "nodemode-dev/formtray", "--title", "formtray")
    assert out.returncode == 0, out.stdout + out.stderr
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["platforms"]["darwin-aarch64"]["url"] == "https://github.com/nodemode-dev/formtray/releases/download/v0.9.8/formtray-0.9.8-macos-arm64.app.tar.gz"
    assert latest["version"] == "0.9.8"
    sums = (tmp_path / "SHA256SUMS.txt").read_text(encoding="utf-8")
    assert "formtray-0.9.8-macos-arm64.app.tar.gz" in sums and "latest.json" in sums


def test_the_plan_tags_v_version_and_takes_no_prefix(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    out = script("plan.py", "--version", "1.2.3", "--platforms", "linux-x64", "--ref", "", cwd=tmp_path)
    assert out.returncode == 0, out.stdout + out.stderr
    assert json.loads(out.stdout)["tag"] == "v1.2.3"
    assert script("plan.py", "--version", "1.2.3", "--platforms", "linux-x64", "--tag-prefix", "formvis-v", cwd=tmp_path).returncode != 0


def test_yank_checks_the_app_repository_v_tag():
    import yank
    published = [{"tag_name": "v1.2.1", "draft": False}]
    assert yank.validate("formvis", "1.2.1", "r", published, []) == "r"
    with pytest.raises(yank.YankError, match="formvis v1.2.2 is not a published release"):
        yank.validate("formvis", "1.2.2", "r", published, [])
    with pytest.raises(yank.YankError, match="not a published release"):
        yank.validate("formvis", "1.2.1", "r", [{"tag_name": "formvis-v1.2.1", "draft": False}], [])


def assemble():
    return jobs(RELEASE)["assemble"]


def test_the_assemble_job_releases_on_the_app_repository_in_the_release_environment():
    job = assemble()
    assert re.search(r"(?m)^    environment: release$", job)
    assert re.search(r"(?m)^    permissions:\n      contents: read$", job), "formcompiler's own token needs no write: the releases live on the app repositories"
    repos = re.findall(r"(?m)^\s+GH_REPO: (.+)$", RELEASE)
    assert repos and all(value == APP_REPOSITORY for value in repos), repos
    assert "GH_REPO: ${{ github.repository }}" not in RELEASE
    assert '--target "$SHA"' in job and "--target main" not in job
    assert "SHA: ${{ needs.gate.outputs.sha }}" in job
    assert 'REPO: ${{ fromJSON(needs.gate.outputs.config).repository }}' in job


def test_only_the_assemble_steps_that_write_hold_the_write_credential():
    for name, job in jobs(RELEASE).items():
        for secret in WRITE_CREDENTIALS:
            assert (secret in job) == (name == "assemble"), f"{secret} in {name}"
    for other in ("desktop-release.yml", "watch.yml", "self-check.yml"):
        text = (WORKFLOWS / other).read_text()
        assert not any(secret in text for secret in WRITE_CREDENTIALS), other
    job = assemble()
    token = "GH_TOKEN: ${{ steps.app-token.outputs.token || secrets.FORMCOMPILER_WRITE_TOKEN }}"
    assert job.count(token) == 3
    for step in ("Create or refresh the draft on the app repository", "Supersede older drafts", "Publish (a beta, or registry release is publish)"):
        body = job.split(f"- name: {step}", 1)[1].split("- name: ", 1)[0]
        assert token in body, step
    for step in ("App release assets", "App manifest and skills", "App plus FormPortal", "Checksums and updater feed", "Release notes"):
        body = job.split(f"- name: {step}", 1)[1].split("- name: ", 1)[0]
        assert "GH_TOKEN" not in body and "FORMCOMPILER_WRITE_TOKEN" not in body, step
    assert "token: ${{ secrets.FORMCOMPILER_APP_TOKEN || github.token }}" in job


def test_the_github_app_token_is_pinned_and_scoped_to_the_one_app_repository():
    job = assemble()
    pinned = re.search(r"uses: actions/create-github-app-token@([0-9a-f]{40}) # v\d+\.\d+\.\d+", job)
    assert pinned, "pin the action to a full commit SHA with its version as a trailing comment"
    assert "client-id: ${{ secrets.FORMCOMPILER_APP_ID }}" in job
    assert "private-key: ${{ secrets.FORMCOMPILER_APP_PRIVATE_KEY }}" in job
    assert "owner: nodemode-dev" in job
    assert "repositories: ${{ steps.credential.outputs.name }}" in job
    assert "permission-contents: write" in job
    assert 'echo "name=${REPOSITORY#*/}" >> "$GITHUB_OUTPUT"' in job
    assert "if: steps.credential.outputs.shape == 'app'" in job


def test_a_missing_write_credential_fails_the_assemble_job_naming_the_accounts_page():
    job = assemble()
    credential = job.split("- name: Release credential", 1)[1].split("- name: ", 1)[0]
    assert "::error::" in credential and "docs/ACCOUNTS.md" in credential
    assert "FORMCOMPILER_APP_ID and FORMCOMPILER_APP_PRIVATE_KEY" in credential and "FORMCOMPILER_WRITE_TOKEN" in credential
    assert "exit 1" in credential
    assert job.index("- name: Release credential") < job.index("uses: actions/checkout@"), "fail before any work is done"


def test_the_dispatch_to_formpipe_names_the_app_the_tag_and_the_repository():
    job = assemble()
    assert '"client_payload": {"app": sys.argv[1], "tag": sys.argv[2], "repository": sys.argv[3]}' in job
    assert '"$APP" "$TAG" "$GH_REPO"' in job
    assert '"event_type": "formcompiler-published"' in job
    assert "already has a published release $TAG; bump the version to release again" in job


def test_no_workflow_shapes_a_tag_as_app_dash_v():
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        text = workflow.read_text()
        assert "tag-prefix" not in text and "}}-v" not in text, workflow.name
    assert "echo '{}' > \"$RUNNER_TEMP/releases.json\"" in (WORKFLOWS / "self-check.yml").read_text()
