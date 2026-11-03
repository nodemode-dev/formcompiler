"""Every app release lives on the app's own repository, tagged vX.Y.Z at the gated commit (formcompiler v0.9.0).

formcompiler is the factory and the gate; it keeps no app releases. The scripts read each app repository's release
list, the assemble job writes there with a credential from the release environment, and formpipe is told the app,
the tag and the repository.
"""
import json
import os
import re
import subprocess
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
from conftest import REPO, SCRIPTS
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
    monkeypatch.setattr(gh, "paged", lambda path, key=None, app_side=False, token_env="": seen.append((path, app_side, token_env)) or [])
    assert gh.releases("nodemode-dev/formtray") == []
    assert seen == [("/repos/nodemode-dev/formtray/releases", True, "")]


def test_the_gate_reads_the_app_repository_and_tags_v_version(monkeypatch):
    read = []
    written = {}
    monkeypatch.setattr(gate, "load", lambda app: ENTRY)
    monkeypatch.setattr(gate, "write_outputs", lambda values: written.update(values))
    monkeypatch.setattr(gh, "compile_branches", lambda repo: [("compile_v1.2.0", SHA)])
    monkeypatch.setattr(gh, "active_release_runs", lambda repo: set())
    monkeypatch.setattr(gh, "succeeded_release_runs", lambda repo, since: {"built"})
    monkeypatch.setattr(gh, "releases", lambda repo: read.append(repo) or [])
    monkeypatch.setattr(gh, "summary", lambda text: None)
    seen = {}
    monkeypatch.setattr(readiness, "evaluate", lambda entry, branch, sha, releases, active, built=frozenset(): seen.update(built=built) or (readiness.READY, "ok", "1.2.0"))
    monkeypatch.setattr(sys, "argv", ["gate.py", "--app", "alpha", "--ref", "compile_v1.2.0"])
    gate.main()
    assert read == ["nodemode-dev/alpha"]
    assert written["tag"] == "v1.2.0" and written["sha"] == SHA
    assert seen["built"] == {"built"}, "the gate passes the successful runs so a refreshed draft's own tag is accepted"


def test_readiness_names_the_app_and_its_v_tag(monkeypatch):
    monkeypatch.setattr(gh, "on_main", lambda repo, sha: True)
    status, reason, _ = readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [{"tag_name": "v1.2.0", "draft": False}], set())
    assert status == readiness.SKIP and reason.startswith("alpha v1.2.0 is already published")
    drafted = {"tag_name": "v1.2.0", "draft": True, "body": f"<!-- formcompiler-source: nodemode-dev/alpha@{SHA} -->"}
    status, reason, _ = readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [drafted], set())
    assert status == readiness.SKIP and "already drafted" in reason


def test_older_drafts_cli_reads_the_registry_repository_and_prints_ids(monkeypatch, capsys):
    read = []
    listed = [{"id": 41, "tag_name": "v0.0.1", "draft": True}, {"id": 42, "tag_name": "v0.0.2", "draft": False}, {"id": 43, "tag_name": "v0.0.3-beta.1", "draft": True}]
    monkeypatch.setattr(gh, "releases", lambda repo, token_env="": read.append((repo, token_env)) or listed)
    monkeypatch.setattr(sys, "argv", ["versions.py", "older-drafts", "--app", "formvis", "--version", "9.9.9", "--token-env", "GH_TOKEN"])
    versions.main()
    assert read == [(load("formvis")["repository"], "GH_TOKEN")]
    assert capsys.readouterr().out == "43\tv0.0.3-beta.1\n41\tv0.0.1\n"


def test_drafts_are_listed_with_the_write_credential_only(monkeypatch):
    """The read-only app token lists no draft, so the publish job must read with GH_TOKEN even when the other variable is set."""
    monkeypatch.setenv("FORMCOMPILER_APP_TOKEN", "read-only")
    monkeypatch.setenv("GH_TOKEN", "write")
    assert gh.token(app_side=True) == "read-only"
    assert gh.token(app_side=True, token_env="GH_TOKEN") == "write"
    seen = []
    monkeypatch.setattr(gh, "request", lambda method, url, body=None, app_side=False, raw=False, token_env="": seen.append((url, app_side, token_env)) or ([], ""))
    gh.releases("nodemode-dev/alpha", token_env="GH_TOKEN")
    assert seen == [("/repos/nodemode-dev/alpha/releases?per_page=100", True, "GH_TOKEN")]
    supersede = step(jobs(RELEASE)["publish"], "Supersede older drafts")
    assert "--token-env GH_TOKEN" in supersede and "FORMCOMPILER_APP_TOKEN" not in supersede


def test_a_tag_that_already_points_elsewhere_refuses_the_release(monkeypatch):
    """GitHub makes a release for an existing tag at that tag's commit and ignores --target."""
    monkeypatch.setattr(gh, "on_main", lambda repo, sha: True)
    monkeypatch.setattr(gh, "file_at", lambda repo, path, sha: "1.2.0\n")
    monkeypatch.setattr(gh, "checks_state", lambda repo, sha, workflows: {"ci.yml": "success"})
    monkeypatch.setattr(gh, "tag_target", lambda repo, name: OTHER if name == "v1.2.0" else "")
    status, reason, _ = readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [], set())
    assert status == readiness.REFUSE and "v1.2.0 already exists in nodemode-dev/alpha at bbbbbbbbb" in reason
    monkeypatch.setattr(gh, "tag_target", lambda repo, name: SHA)
    assert readiness.evaluate(ENTRY, "v1.2.0", SHA, [], set())[0] == readiness.READY
    monkeypatch.setattr(gh, "tag_target", lambda repo, name: "")
    assert readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [], set())[0] == readiness.READY


def test_a_tag_formcompiler_made_for_that_version_is_moved_not_refused(monkeypatch):
    """The same version pushed again from a newer commit refreshes the draft; its tag, created at draft time, follows."""
    monkeypatch.setattr(gh, "on_main", lambda repo, sha: True)
    monkeypatch.setattr(gh, "file_at", lambda repo, path, sha: "1.2.0\n")
    monkeypatch.setattr(gh, "checks_state", lambda repo, sha, workflows: {"ci.yml": "success"})
    monkeypatch.setattr(gh, "tag_target", lambda repo, name: OTHER)
    built = {gh.run_title("alpha", "1.2.0", OTHER)}
    assert readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [], set(), built=built)[0] == readiness.READY
    assert readiness.evaluate(ENTRY, "compile_v1.2.0", SHA, [], set(), built={gh.run_title("alpha", "1.1.0", OTHER)})[0] == readiness.REFUSE


def test_tag_target_cli_reads_with_the_named_token(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(gh, "tag_target", lambda repo, name, token_env="": seen.append((repo, name, token_env)) or SHA)
    monkeypatch.setattr(sys, "argv", ["versions.py", "tag-target", "--repo", "nodemode-dev/alpha", "--tag", "v1.2.0", "--token-env", "GH_TOKEN"])
    versions.main()
    assert capsys.readouterr().out == SHA + "\n"
    assert seen == [("nodemode-dev/alpha", "v1.2.0", "GH_TOKEN")]


def test_tag_target_reads_both_refs_with_the_named_token(monkeypatch):
    monkeypatch.setenv("FORMCOMPILER_APP_TOKEN", "read-only")
    monkeypatch.setenv("GH_TOKEN", "write")
    calls = []
    monkeypatch.setattr(gh, "get", lambda path, app_side=False, token_env="": calls.append(token_env) or ({"object": {"sha": "c" * 40, "type": "tag"}} if "/ref/" in path else {"object": {"sha": SHA, "type": "commit"}}))
    assert gh.tag_target("nodemode-dev/alpha", "v1.2.0", token_env="GH_TOKEN") == SHA
    assert calls == ["GH_TOKEN", "GH_TOKEN"]


def test_tag_target_follows_the_tag_and_answers_empty_for_none(monkeypatch):
    def get(path, app_side=False, token_env=""):
        if path.endswith("/git/ref/tags/v9.9.9"):
            raise gh.ApiError(404, "Not Found")
        if path.endswith("/git/ref/tags/v1.2.0"):
            return {"object": {"sha": "c" * 40, "type": "tag"}}
        return {"object": {"sha": SHA, "type": "commit"}}

    monkeypatch.setattr(gh, "get", get)
    assert gh.tag_target("nodemode-dev/alpha", "v9.9.9") == ""
    assert gh.tag_target("nodemode-dev/alpha", "v1.2.0") == SHA


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
    monkeypatch.setattr(gh, "succeeded_release_runs", lambda repo, since: calls["succeeded"])
    monkeypatch.setattr(gh, "dispatch", lambda repo, ref, inputs: calls["dispatched"].append((inputs["app"], inputs["version"])))
    monkeypatch.setattr(readiness, "evaluate", lambda entry, ref, sha, releases, active, built=frozenset(): (readiness.READY, "ok", readiness.ref_version(ref)[0]))
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


def test_a_later_successful_rerun_outranks_an_earlier_failure(watching, monkeypatch):
    run, calls = watching
    title = gh.run_title("alpha", "1.1.0", OTHER)
    calls["succeeded"].add(title)
    monkeypatch.setattr(gh, "stopped_release_runs", lambda repo: {title})
    out = run()
    assert "succeeded; its release is on nodemode-dev/alpha" in out and "failed or was cancelled" not in out


def test_succeeded_release_runs_counts_only_runs_since_the_cut_over(monkeypatch):
    """Successful runs before v0.9.0 drafted on formcompiler, not on the app repository, so they do not stand in for a draft there."""
    seen = []
    since = watch.RELEASES_ON_APP_REPOS_SINCE
    run = {"head_branch": "main", "event": "workflow_dispatch", "conclusion": "success", "created_at": "2026-11-04T00:00:00Z"}
    runs = [{**run, "display_title": "old 1.0.0 at " + SHA, "created_at": "2026-11-01T00:00:00Z"}, {**run, "display_title": "new 1.0.0 at " + SHA}]
    monkeypatch.setattr(gh, "get", lambda path, app_side=False, token_env="": seen.append(path) or {"workflow_runs": runs})
    assert gh.succeeded_release_runs("nodemode-dev/formcompiler", since) == {f"new 1.0.0 at {SHA}"}
    assert seen == [f"/repos/nodemode-dev/formcompiler/actions/workflows/release.yml/runs?status=success&branch=main&event=workflow_dispatch&created=%3E%3D{since.replace(':', '%3A')}&per_page=100"]
    assert re.fullmatch(r"2026-11-0[3-9]T\d\d:\d\d:\d\dZ", since)


def test_only_main_dispatch_successes_count_as_built(monkeypatch):
    """A run from another formcompiler branch, or started by another event, can carry any run-name, so a forged title
    must not make a tag at another commit look like formcompiler's own; the record is as strong as main's protection."""
    run = {"display_title": f"alpha 1.0.0 at {OTHER}", "head_branch": "main", "event": "workflow_dispatch", "conclusion": "success", "created_at": "2026-11-04T00:00:00Z"}
    runs = [run, {**run, "head_branch": "feat/forged-run-name"}, {**run, "event": "push"}, {**run, "conclusion": "failure"}, {**run, "display_title": f"beta 1.0.0 at {OTHER}"}]
    monkeypatch.setattr(gh, "get", lambda path, app_side=False, token_env="": {"workflow_runs": runs})
    assert gh.succeeded_release_runs("nodemode-dev/formcompiler", gh.RELEASES_ON_APP_REPOS_SINCE) == {f"alpha 1.0.0 at {OTHER}", f"beta 1.0.0 at {OTHER}"}
    runs[0] = {**run, "head_branch": "feat/forged-run-name"}
    assert gh.succeeded_release_runs("nodemode-dev/formcompiler", gh.RELEASES_ON_APP_REPOS_SINCE) == {f"beta 1.0.0 at {OTHER}"}


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


@pytest.mark.parametrize("env, shape, code", [
    ({"HAS_APP": "true", "HAS_TOKEN": "true"}, "app", 0),
    ({"HAS_APP": "false", "HAS_TOKEN": "true"}, "token", 0),
    ({"HAS_APP": "false", "HAS_TOKEN": "false"}, "", 1),
])
def test_the_release_credential_script_chooses_the_app_then_the_token_then_fails(tmp_path, env, shape, code):
    output = tmp_path / "output"
    output.write_text("", encoding="utf-8")
    run = subprocess.run(["bash", str(SCRIPTS / "release_credential.sh")], capture_output=True, text=True,
                         env={"PATH": os.environ["PATH"], "REPOSITORY": "nodemode-dev/formtray", "GITHUB_OUTPUT": str(output), **env})
    assert run.returncode == code, run.stdout + run.stderr
    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "name=formtray"
    assert lines[1:] == ([f"shape={shape}"] if shape else [])
    if code:
        assert "::error::" in run.stdout and "docs/ACCOUNTS.md" in run.stdout and "FORMCOMPILER_WRITE_TOKEN" in run.stdout


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


def publish():
    return jobs(RELEASE)["publish"]


def step(job, name):
    return job.split(f"- name: {name}", 1)[1].split("\n      - ", 1)[0]


def test_the_publish_job_releases_on_the_app_repository_in_the_release_environment():
    job = publish()
    assert re.search(r"(?m)^    environment: release$", job)
    assert re.search(r"(?m)^    permissions:\n      contents: read$", job), "formcompiler's own token needs no write: the releases live on the app repositories"
    assert re.search(r"(?m)^    needs: \[gate, assemble\]$", job)
    repos = re.findall(r"(?m)^\s+GH_REPO: (.+)$", RELEASE)
    assert repos and all(value == APP_REPOSITORY for value in repos), repos
    assert "GH_REPO: ${{ github.repository }}" not in RELEASE
    assert '--target "$SHA"' in job and "--target main" not in job
    assert "SHA: ${{ needs.gate.outputs.sha }}" in job


def test_the_publish_job_runs_no_app_code_and_the_assemble_job_holds_no_credential():
    """The registry's assets and notes commands are the app's own; the job that runs them must never hold the write credential."""
    assemble, job = jobs(RELEASE)["assemble"], publish()
    assert "environment:" not in assemble and "GH_TOKEN" not in assemble and "secrets.FORMCOMPILER_WRITE_TOKEN" not in assemble
    assert 'bash -eo pipefail -c "$ASSETS"' in assemble and "scripts/notes.py" in assemble
    assert "formcompiler-release-${{ inputs.app }}" in assemble and "release-notes.md" in assemble and "overwrite: true" in assemble
    assert 'REPO: ${{ fromJSON(needs.gate.outputs.config).repository }}' in assemble
    assert "FORMCOMPILER_TAG: ${{ needs.gate.outputs.tag }}" in assemble and "FORMCOMPILER_REPOSITORY: ${{ fromJSON(needs.gate.outputs.config).repository }}" in assemble
    assert job.count("uses: actions/checkout@") == 1 and "repository: ${{ fromJSON" not in job and "path: app" not in job
    assert "ASSETS" not in job and "notes.py" not in job and "agents.py" not in job and "with_portal.py" not in job
    assert "name: formcompiler-release-${{ inputs.app }}" in job and "path: release" in job
    assert "working-directory: release/dist" in job and 'notes="$GITHUB_WORKSPACE/release/release-notes.md"' in job
    assert "pattern: formcompiler-${{ inputs.app }}-*" in assemble and not re.search(r"formcompiler-release-[a-z]", "formcompiler-formvis-*")


def test_only_the_publish_steps_that_write_hold_the_write_credential():
    for name, job in jobs(RELEASE).items():
        for secret in WRITE_CREDENTIALS:
            assert (secret in job) == (name == "publish"), f"{secret} in {name}"
    for other in ("desktop-release.yml", "watch.yml", "self-check.yml"):
        text = (WORKFLOWS / other).read_text()
        assert not any(secret in text for secret in WRITE_CREDENTIALS), other
    job = publish()
    token = "GH_TOKEN: ${{ steps.app-token.outputs.token || secrets.FORMCOMPILER_WRITE_TOKEN }}"
    assert job.count(token) == 3
    for name in ("Create or refresh the draft on the app repository", "Supersede older drafts", "Publish (a beta, or registry release is publish)"):
        assert token in step(job, name), name
    assert "token: ${{ secrets.FORMCOMPILER_APP_TOKEN || github.token }}" in jobs(RELEASE)["assemble"]


def test_the_publish_job_attests_sha256sums_before_the_draft():
    """formpipe feeds any published v* release on an app repository, so it verifies SHA256SUMS.txt came from this workflow."""
    job = publish()
    assert re.search(r"(?m)^    permissions:\n      contents: read\n      id-token: write\n      attestations: write$", job)
    attest = step(job, "Attest the provenance of SHA256SUMS.txt")
    assert re.search(r"uses: actions/attest-build-provenance@[0-9a-f]{40} # v\d+\.\d+\.\d+", attest)
    assert "if: vars.FORMCOMPILER_ATTEST != 'off'" in attest
    assert job.index("- name: Attest the provenance of SHA256SUMS.txt") > job.index("uses: actions/download-artifact@")
    assert job.index("- name: Attest the provenance of SHA256SUMS.txt") < job.index("- name: Create or refresh the draft on the app repository")
    assert attest.endswith("subject-path: |\n            release/dist/SHA256SUMS.txt\n            release/dist/form-app.json")
    for name, other in jobs(RELEASE).items():
        if name != "publish":
            assert "attest" not in other and "id-token" not in other, name
    assemble = jobs(RELEASE)["assemble"]
    assert assemble.index("scripts/agents.py build") < assemble.index("scripts/release_assets.py"), "form-app.json must be written before the sums are computed"


def test_the_manifest_names_its_release(tmp_path):
    out = script("agents.py", "build", "--app", "formtray", "--app-dir", str(tmp_path), "--dist", str(tmp_path / "dist"), "--version", "0.9.8", "--commit", SHA)
    assert out.returncode == 0, out.stdout + out.stderr
    manifest = json.loads((tmp_path / "dist" / "form-app.json").read_text(encoding="utf-8"))
    assert {k: manifest[k] for k in ("app", "version", "repository", "tag", "commit")} == {
        "app": "formtray", "version": "0.9.8", "repository": "nodemode-dev/formtray", "tag": "v0.9.8", "commit": SHA}
    assert script("agents.py", "check", "--app", "formtray", "--dist", str(tmp_path / "dist")).returncode == 0
    for key, value in (("repository", "someone/formtray"), ("tag", "formtray-v0.9.8"), ("repository", None), ("tag", None)):
        broken = {k: v for k, v in manifest.items() if v is not None and k != key} if value is None else {**manifest, key: value}
        (tmp_path / "dist" / "form-app.json").write_text(json.dumps(broken), encoding="utf-8")
        out = script("agents.py", "check", "--app", "formtray", "--dist", str(tmp_path / "dist"))
        assert out.returncode != 0 and key in out.stdout + out.stderr, (key, value)


def test_the_tag_is_formcompilers_before_the_draft_and_still_at_the_commit_when_published():
    job = publish()
    draft = step(job, "Create or refresh the draft on the app repository")
    assert 'tag_at() { python3 -I "$GITHUB_WORKSPACE/scripts/versions.py" tag-target --repo "$GH_REPO" --tag "$TAG" --token-env GH_TOKEN; }' in draft
    assert 'gh api -X POST "repos/$GH_REPO/git/refs" -f "ref=refs/tags/$TAG" -f "sha=$SHA"' in draft
    create = draft.index('gh api -X POST "repos/$GH_REPO/git/refs"')
    assert create < draft.index('if draft="$(gh release view "$TAG"'), "the tag before any release call"
    assert create > draft.index("tag_at() {")
    move = draft.index('gh api -X PATCH "repos/$GH_REPO/git/refs/tags/$TAG" -f "sha=$SHA" -F force=true')
    guard = draft.index('if [ "$(gh release view "$TAG" --json isDraft --jq .isDraft 2>/dev/null)" != "true" ]; then')
    assert guard < move < draft.index("still_a_draft() {"), "a tag is moved only when a draft is at it"
    assert "and no draft of formcompiler's is at it; move or delete the tag, or bump the version" in draft
    assert 'if [ "$(tag_at)" != "$SHA" ]; then' in draft
    release = step(job, "Publish (a beta, or registry release is publish)")
    assert 'at="$(python3 -I scripts/versions.py tag-target --repo "$GH_REPO" --tag "$TAG" --token-env GH_TOKEN)"' in release
    assert release.index('if [ "$at" != "$SHA" ]; then') < release.index('gh release edit "$TAG" --draft=false')
    assert "the draft was left unpublished" in release and "SHA: ${{ needs.gate.outputs.sha }}" in release
    supersede = step(job, "Supersede older drafts")
    assert supersede.index('gh api -X DELETE "repos/$GH_REPO/releases/$id"') < supersede.index('gh api -X DELETE "repos/$GH_REPO/git/refs/tags/$old"')
    assert 'if [ -n "$at" ] && [ "$at" = "$target" ]; then' in supersede


def test_a_draft_is_only_changed_while_it_is_still_a_draft():
    draft = step(publish(), "Create or refresh the draft on the app repository")
    assert "still_a_draft() {" in draft
    body = draft.split("still_a_draft() {", 1)[1]
    for mutation in ('gh release delete-asset "$TAG" "$asset" --yes', 'gh release edit "$TAG" --draft', 'gh release upload "$TAG" --clobber'):
        before = body.split(mutation, 1)[0].rstrip().splitlines()[-1].strip()
        assert before == "still_a_draft", (mutation, before)
    assert "already has a published release $TAG; bump the version to release again" in draft


def test_older_drafts_are_deleted_by_id_after_a_second_look():
    supersede = step(publish(), "Supersede older drafts")
    assert "--token-env GH_TOKEN" in supersede
    assert "IFS=$'\\t' read -r id old" in supersede
    assert """gh api "repos/$GH_REPO/releases/$id" --jq '[.draft, .target_commitish] | @tsv'""" in supersede
    assert 'gh api -X DELETE "repos/$GH_REPO/releases/$id"' in supersede
    assert "gh release delete" not in supersede and "--cleanup-tag" not in supersede


def test_the_github_app_token_is_pinned_and_scoped_to_the_one_app_repository():
    job = publish()
    pinned = re.search(r"uses: actions/create-github-app-token@([0-9a-f]{40}) # v\d+\.\d+\.\d+", job)
    assert pinned, "pin the action to a full commit SHA with its version as a trailing comment"
    assert "client-id: ${{ secrets.FORMCOMPILER_APP_ID }}" in job
    assert "private-key: ${{ secrets.FORMCOMPILER_APP_PRIVATE_KEY }}" in job
    assert "owner: nodemode-dev" in job
    assert "repositories: ${{ steps.credential.outputs.name }}" in job
    assert "permission-contents: write" in job
    assert "run: bash scripts/release_credential.sh" in job
    assert "if: steps.credential.outputs.shape == 'app'" in job


def test_a_missing_write_credential_fails_the_publish_job_before_the_download():
    job = publish()
    credential = step(job, "Release credential")
    assert "HAS_APP: ${{ secrets.FORMCOMPILER_APP_ID != '' && secrets.FORMCOMPILER_APP_PRIVATE_KEY != '' }}" in credential
    assert "HAS_TOKEN: ${{ secrets.FORMCOMPILER_WRITE_TOKEN != '' }}" in credential
    assert job.index("- name: Release credential") < job.index("uses: actions/download-artifact@"), "fail before any work is done"


def test_the_dispatch_to_formpipe_names_the_app_the_tag_and_the_repository():
    job = publish()
    assert '"client_payload": {"app": sys.argv[1], "tag": sys.argv[2], "repository": sys.argv[3]}' in job
    assert '"$APP" "$TAG" "$GH_REPO"' in job
    assert '"event_type": "formcompiler-published"' in job
    assert "already has a published release $TAG; bump the version to release again" in job


def test_no_workflow_or_registry_entry_shapes_a_tag_as_app_dash_v():
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        text = workflow.read_text()
        assert "tag-prefix" not in text and "}}-v" not in text, workflow.name
    assert "echo '{}' > \"$RUNNER_TEMP/releases.json\"" in (WORKFLOWS / "self-check.yml").read_text()
    for path in sorted((REPO / "apps").glob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        commands = json.dumps({k: v for k, v in entry.items() if k != "notes_for_owner"})
        assert not re.search(r"-v\$", commands), f"{path.name}: a command builds an <app>-v tag"
        assert "formcompiler/releases" not in commands, f"{path.name}: a command reads a release on formcompiler"
        for url in re.findall(r"https://github\.com/([^/\s\"]+/[^/\s\"]+)/releases/download/", commands):
            assert url in (entry["repository"], "$FORMCOMPILER_REPOSITORY"), f"{path.name}: {url} is not the app's own repository"
    formvis = load("formvis")["assets"]
    assert '--tag "$FORMCOMPILER_TAG"' in formvis and 'https://github.com/$FORMCOMPILER_REPOSITORY/releases/download/$FORMCOMPILER_TAG/' in formvis
