import json
import os
import subprocess
import sys

import pytest

import catalog
import public_urls
import yank
from conftest import SCRIPTS, script
from registry import load

BASE = "https://dl.formai.studio"
DIGEST = "d" * 64


@pytest.mark.parametrize("value, expected", [
    ("", ""),
    ("  ", ""),
    ("https://dl.formai.studio", BASE),
    ("https://dl.formai.studio/", BASE),
    ("https://example.com/store/v1", "https://example.com/store/v1"),
])
def test_public_base_accepts_https_addresses(value, expected):
    assert public_urls.base_url(value) == expected


@pytest.mark.parametrize("value", ["http://dl.formai.studio", "https://dl.formai.studio/?x=1", "gs://store-bucket", "dl.formai.studio", "https://a b"])
def test_public_base_refuses_anything_else(value):
    with pytest.raises(ValueError):
        public_urls.base_url(value)


def test_artifact_url_is_app_version_file_with_each_part_quoted():
    assert public_urls.artifact_url(BASE, "form.md", "1.2.3", "form.md_1.2.3_aarch64.dmg") == f"{BASE}/form.md/1.2.3/form.md_1.2.3_aarch64.dmg"
    assert public_urls.artifact_url(BASE, "formvis", "1.2.3+b.1", "My App 1.2.3.msi") == f"{BASE}/formvis/1.2.3%2Bb.1/My%20App%201.2.3.msi"


def test_latest_json_points_at_the_versioned_store_path_only_for_its_own_tag():
    feed = {
        "version": "1.2.3", "notes": "n", "pub_date": "2026-10-28T00:00:00Z",
        "platforms": {
            "darwin-aarch64": {"signature": "sig-a", "url": "https://github.com/nodemode-dev/formcompiler/releases/download/formvis-v1.2.3/FormVis_aarch64.app.tar.gz"},
            "windows-x86_64": {"signature": "sig-w", "url": "https://github.com/nodemode-dev/formcompiler/releases/download/formvis-v1.2.3/FormVis_1.2.3_x64-setup.exe"},
            "linux-x86_64": {"signature": "sig-l", "url": "https://example.com/elsewhere/FormVis.AppImage"},
            "linux-aarch64": {"signature": "sig-o", "url": "https://github.com/nodemode-dev/formcompiler/releases/download/formvis-v1.2.2/old.AppImage"},
        },
    }
    moved = public_urls.rewrite_feed(feed, BASE, "formvis", "1.2.3", "formvis-v1.2.3")
    assert moved["platforms"]["darwin-aarch64"] == {"signature": "sig-a", "url": f"{BASE}/formvis/1.2.3/FormVis_aarch64.app.tar.gz"}
    assert moved["platforms"]["windows-x86_64"]["url"] == f"{BASE}/formvis/1.2.3/FormVis_1.2.3_x64-setup.exe"
    assert moved["platforms"]["linux-x86_64"] == feed["platforms"]["linux-x86_64"]
    assert moved["platforms"]["linux-aarch64"] == feed["platforms"]["linux-aarch64"]
    assert feed["platforms"]["darwin-aarch64"]["url"].startswith("https://github.com/")
    assert {k: v for k, v in moved.items() if k != "platforms"} == {k: v for k, v in feed.items() if k != "platforms"}
    assert public_urls.rewrite_feed(feed, "", "formvis", "1.2.3", "formvis-v1.2.3") is feed
    assert public_urls.rewrite_feed({"tag_name": "v1.2.3"}, BASE, "form.md", "1.2.3", "form.md-v1.2.3") == {"tag_name": "v1.2.3"}


def test_feed_cli_rewrites_latest_json(tmp_path):
    path = tmp_path / "latest.json"
    path.write_text(json.dumps({"version": "1.2.3", "platforms": {"darwin-aarch64": {
        "signature": "s", "url": "https://github.com/nodemode-dev/formcompiler/releases/download/formvis-v1.2.3/a.app.tar.gz"}}}), encoding="utf-8")
    out = script("feed.py", "public", "--tag", "formvis-v1.2.3", "--file", str(path), "--base", BASE + "/")
    assert out.returncode == 0, out.stdout + out.stderr
    assert json.loads(path.read_text(encoding="utf-8"))["platforms"]["darwin-aarch64"]["url"] == f"{BASE}/formvis/1.2.3/a.app.tar.gz"
    assert script("feed.py", "public", "--tag", "formvis-v1.2.3", "--file", str(path), "--base", "http://x").returncode != 0


def asset(tag, name, size=100):
    return {"name": name, "size": size, "url": f"https://api.github.com/assets/{name}",
            "browser_download_url": f"https://github.com/nodemode-dev/formcompiler/releases/download/{tag}/{name}"}


def gh_release(version, prerelease=False, draft=False):
    tag = f"formvis-v{version}"
    names = [f"FormVis_{version}_aarch64.dmg", f"FormVis_{version}_x64-setup.exe", "form-app.json", f"formvis-skills-v{version}.zip", "SHA256SUMS.txt"]
    return {"tag_name": tag, "draft": draft, "prerelease": prerelease, "published_at": "2026-10-28T00:00:00Z",
            "html_url": f"https://github.com/nodemode-dev/formcompiler/releases/tag/{tag}", "body": "",
            "assets": [asset(tag, name, 100 + i) for i, name in enumerate(names)]}


@pytest.fixture
def sums(monkeypatch):
    monkeypatch.setattr(catalog, "fetch_sums", lambda release: {a["name"]: DIGEST for a in release["assets"] if a["name"] != "SHA256SUMS.txt"})


RELEASES = [gh_release("1.2.0"), gh_release("1.2.1"), gh_release("1.3.0-beta.1", prerelease=True), gh_release("1.4.0", draft=True)]


def product(document):
    return next(p for p in document["products"] if p["id"] == "formvis")


def test_the_catalogue_keeps_github_urls_without_a_public_base(sums):
    stable = product(catalog.build("nodemode-dev/formcompiler", [load("formvis")], RELEASES))["channels"]["stable"]
    assert stable["version"] == "1.2.1"
    assert all(a["url"].startswith("https://github.com/nodemode-dev/formcompiler/releases/download/formvis-v1.2.1/") for a in stable["artifacts"])


def test_the_catalogue_points_at_the_store_with_the_same_sizes_and_digests(sums):
    plain = product(catalog.build("nodemode-dev/formcompiler", [load("formvis")], RELEASES))["channels"]
    moved = product(catalog.build("nodemode-dev/formcompiler", [load("formvis")], RELEASES, BASE))["channels"]
    for channel in ("stable", "beta"):
        version = moved[channel]["version"]
        assert moved[channel]["artifacts"], channel
        for before, after in zip(plain[channel]["artifacts"], moved[channel]["artifacts"]):
            assert after["url"] == f"{BASE}/formvis/{version}/{after['file']}"
            assert {k: v for k, v in after.items() if k != "url"} == {k: v for k, v in before.items() if k != "url"}
        assert moved[channel]["agents"]["skills"]["url"] == f"{BASE}/formvis/{version}/formvis-skills-v{version}.zip"
    assert moved["stable"]["history"][0]["artifacts"][0]["url"].startswith(f"{BASE}/formvis/1.2.0/")


def test_yanked_versions_leave_the_catalogue(sums):
    yanked = frozenset({("formvis", "1.2.1"), ("formvis", "1.3.0-beta.1")})
    channels = product(catalog.build("nodemode-dev/formcompiler", [load("formvis")], RELEASES, "", yanked))["channels"]
    assert channels["stable"]["version"] == "1.2.0"
    assert "history" not in channels["stable"]
    assert "beta" not in channels


def test_a_yanked_older_version_leaves_the_history_only(sums):
    channels = product(catalog.build("nodemode-dev/formcompiler", [load("formvis")], RELEASES, "", frozenset({("formvis", "1.2.0")})))["channels"]
    assert channels["stable"]["version"] == "1.2.1"
    assert "history" not in channels["stable"]
    assert channels["beta"]["version"] == "1.3.0-beta.1"


def test_a_new_beta_above_stable_is_the_beta_channel(sums):
    channels = product(catalog.build("nodemode-dev/formcompiler", [load("formvis")], [*RELEASES, gh_release("1.3.0-beta.10", prerelease=True)]))["channels"]
    assert channels["beta"]["version"] == "1.3.0-beta.10"


PUBLISHED = [{"tag_name": "formvis-v1.2.1", "draft": False}, {"tag_name": "formvis-v1.4.0", "draft": True}]


def test_yank_adds_a_published_version_with_its_reason():
    reason = yank.validate("formvis", "1.2.1", "  crashes on start  ", PUBLISHED, [])
    assert reason == "crashes on start"
    rows = yank.added([{"app": "formcut", "version": "1.0.0", "reason": "x", "date": "2026-10-01"}], "formvis", "1.2.1", reason, "2026-10-28")
    assert [(r["app"], r["version"]) for r in rows] == [("formcut", "1.0.0"), ("formvis", "1.2.1")]
    assert yank.yanked_set(rows) == {("formcut", "1.0.0"), ("formvis", "1.2.1")}


@pytest.mark.parametrize("app, version, reason, rows, says", [
    ("nosuchapp", "1.2.1", "r", [], "no registry entry"),
    ("formvis", "v1.2.1", "r", [], "semantic version"),
    ("formvis", "1.2.1", "", [], "one line"),
    ("formvis", "1.2.1", "two\nlines", [], "one line"),
    ("formvis", "1.2.1", "x" * 301, [], "one line"),
    ("formvis", "1.4.0", "r", [], "not a published release"),
    ("formvis", "1.9.9", "r", [], "not a published release"),
    ("formvis", "1.2.1", "r", [{"app": "formvis", "version": "1.2.1"}], "already yanked"),
])
def test_yank_refuses(app, version, reason, rows, says):
    with pytest.raises(yank.YankError, match=says):
        yank.validate(app, version, reason, PUBLISHED, rows)


def test_yanked_json_must_have_its_shape(tmp_path):
    assert yank.load(tmp_path / "missing.json") == []
    bad = tmp_path / "yanked.json"
    bad.write_text('{"yanked": [{"app": "formvis"}]}', encoding="utf-8")
    with pytest.raises(yank.YankError):
        yank.load(bad)


def test_the_catalogue_cli_reads_yanked_json_and_the_public_base(tmp_path):
    releases = tmp_path / "releases.json"
    releases.write_text("[]", encoding="utf-8")
    listed = tmp_path / "yanked.json"
    listed.write_text('{"yanked": [{"app": "formvis", "version": "1.2.1", "reason": "r", "date": "2026-10-28"}]}', encoding="utf-8")
    env = {**os.environ, "FORMCOMPILER_PUBLIC_BASE": BASE}
    run = subprocess.run([sys.executable, "-I", str(SCRIPTS / "catalog.py"), "build", "--releases", str(releases), "--yanked", str(listed), "--out", str(tmp_path / "apps.json")],
                         capture_output=True, text=True, env=env)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "1 yanked" in run.stdout and BASE in run.stdout
    env["FORMCOMPILER_PUBLIC_BASE"] = "http://insecure"
    run = subprocess.run([sys.executable, "-I", str(SCRIPTS / "catalog.py"), "build", "--releases", str(releases), "--out", str(tmp_path / "apps.json")],
                         capture_output=True, text=True, env=env)
    assert run.returncode != 0


def test_listed_releases_names_every_release_the_catalogue_points_at(sums):
    document = catalog.build("nodemode-dev/formcompiler", [load("formvis"), load("form.md")], RELEASES, BASE)
    assert catalog.listed_releases(document, [load("formvis"), load("form.md")]) == [("formvis", "1.2.0"), ("formvis", "1.2.1"), ("formvis", "1.3.0-beta.1")]


def test_the_listed_cli_prints_app_and_version(tmp_path, sums):
    document = catalog.build("nodemode-dev/formcompiler", [load("formvis")], RELEASES, BASE)
    path = tmp_path / "releases.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    out = script("catalog.py", "listed", "--file", str(path))
    assert out.returncode == 0, out.stderr
    assert out.stdout == "formvis\t1.2.0\nformvis\t1.2.1\nformvis\t1.3.0-beta.1\n"


@pytest.mark.parametrize("tag, updates", [
    ("formvis-v1.3.0", "true"),
    ("formvis-v1.2.0", "false"),
    ("formvis-v1.4.0-beta.1", "false"),
])
def test_the_update_feed_is_refreshed_only_for_the_newest_stable(monkeypatch, capsys, tag, updates):
    """A manual feed run with an older tag must not roll every installed app back to it."""
    import feed
    import github_api

    published = [{"tag_name": t, "draft": False} for t in ("formvis-v1.2.0", "formvis-v1.3.0", "formvis-v1.4.0-beta.1")]
    monkeypatch.setattr(github_api, "releases", lambda repo: published)
    written = {}
    monkeypatch.setattr(feed, "write_outputs", lambda values: written.update(values))
    monkeypatch.setattr(sys, "argv", ["feed.py", "resolve", "--tag", tag, "--prerelease", "false"])
    feed.main()
    assert written["updates"] == updates
    assert written["version"] == tag.split("-v", 1)[1]


def test_with_portal_skips_when_the_catalogue_is_not_there_yet(monkeypatch, capsys, tmp_path):
    """While formcompiler is private, or before the first catalog release, the catalogue URL answers 404."""
    import urllib.error

    import with_portal

    def missing(url):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr(with_portal, "load", lambda app: {"with_portal": True, "catalog": {"name": "FormVis"}})
    monkeypatch.setattr(with_portal, "fetch", missing)
    monkeypatch.setattr(sys, "argv", ["with_portal.py", "--app", "formvis", "--version", "1.2.3", "--dir", str(tmp_path)])
    with_portal.main()
    assert "no app-plus-FormPortal download was made" in capsys.readouterr().out
