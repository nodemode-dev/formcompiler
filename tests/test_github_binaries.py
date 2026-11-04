"""Once an app's repository is public, its binaries come from the GitHub release assets and only the small files
(the catalogue, the update feeds) live on the download store; a private repository's files still go through the store."""
import json
import sys

import pytest

import catalog
import feed
import github_api as gh
import public_urls
from conftest import script
from registry import load

BASE = "https://dl.formai.studio"
FORMVIS, FORMCUT = "nodemode-dev/formvis", "nodemode-dev/formcut"


def gh_release(version, repo, app):
    tag = f"v{version}"
    names = [f"{app}-{version}-macos-arm64.dmg", "form-app.json", f"{app}-skills-v{version}.zip", "SHA256SUMS.txt"]
    return {"tag_name": tag, "draft": False, "prerelease": False, "published_at": "2026-11-03T00:00:00Z",
            "html_url": f"https://github.com/{repo}/releases/tag/{tag}", "body": "",
            "assets": [{"name": n, "size": 10 + i, "url": f"https://api.github.com/assets/{n}",
                        "browser_download_url": f"https://github.com/{repo}/releases/download/{tag}/{n}"} for i, n in enumerate(names)]}


RELEASES = {FORMVIS: [gh_release("1.2.0", FORMVIS, "formvis"), gh_release("1.2.1", FORMVIS, "formvis")], FORMCUT: [gh_release("3.0.0", FORMCUT, "formcut")]}


@pytest.fixture
def family(monkeypatch):
    asked = []
    monkeypatch.setattr(catalog, "fetch_sums", lambda release: {a["name"]: "d" * 64 for a in release["assets"] if a["name"] != "SHA256SUMS.txt"})
    monkeypatch.setattr(gh, "repository_public", lambda repo: asked.append(repo) or repo == FORMVIS)
    return asked


def channels(document, product_id):
    return next(p for p in document["products"] if p["id"] == product_id)["channels"]


def test_a_public_repository_keeps_github_urls_and_a_private_one_goes_through_the_store(family):
    document = catalog.build([load("formvis"), load("formcut")], RELEASES, BASE, asset_origin="github")
    formvis, formcut = channels(document, "formvis")["stable"], channels(document, "formcut")["stable"]
    assert formvis["origin"] == "github" and formcut["origin"] == "store"
    assert all(a["url"].startswith(f"https://github.com/{FORMVIS}/releases/download/v1.2.1/") for a in formvis["artifacts"])
    assert formvis["history"][0]["origin"] == "github" and formvis["history"][0]["artifacts"][0]["url"].startswith(f"https://github.com/{FORMVIS}/releases/download/v1.2.0/")
    assert formvis["agents"]["skills"]["url"] == f"https://github.com/{FORMVIS}/releases/download/v1.2.1/formvis-skills-v1.2.1.zip"
    assert all(a["url"].startswith(f"{BASE}/formcut/3.0.0/") for a in formcut["artifacts"])
    assert formcut["agents"]["manifest"]["url"] == f"{BASE}/formcut/3.0.0/form-app.json"
    assert sorted(family) == [FORMCUT, FORMVIS], "visibility is asked once per entry"


def test_the_store_origin_is_the_default_and_asks_nothing(family):
    document = catalog.build([load("formvis"), load("formcut")], RELEASES, BASE)
    for product_id in ("formvis", "formcut"):
        stable = channels(document, product_id)["stable"]
        assert stable["origin"] == "store" and all(a["url"].startswith(f"{BASE}/{product_id}/") for a in stable["artifacts"])
    assert family == []


def test_without_a_base_every_release_is_on_github_whatever_the_origin(family):
    for asset_origin in ("store", "github"):
        document = catalog.build([load("formvis")], RELEASES, "", asset_origin=asset_origin)
        stable = channels(document, "formvis")["stable"]
        assert stable["origin"] == "github" and stable["artifacts"][0]["url"].startswith("https://github.com/")
    assert family == []


def test_an_entry_without_releases_asks_nothing_and_a_bad_origin_is_refused(family):
    document = catalog.build([load("formtray")], {}, BASE, asset_origin="github")
    assert channels(document, "formtray") == {} and family == []
    with pytest.raises(SystemExit, match="asset-origin"):
        catalog.build([load("formvis")], RELEASES, BASE, asset_origin="cdn")


def test_an_unreadable_visibility_stops_the_catalogue(monkeypatch):
    monkeypatch.setattr(catalog, "fetch_sums", lambda release: {})

    def denied(repo):
        raise gh.ApiError(403, "Forbidden")

    monkeypatch.setattr(gh, "repository_public", denied)
    with pytest.raises(SystemExit, match="could not read whether nodemode-dev/formvis is public"):
        catalog.build([load("formvis")], RELEASES, BASE, asset_origin="github")


def test_repository_public_reads_the_private_flag(monkeypatch):
    seen = []
    monkeypatch.setattr(gh, "get", lambda path, app_side=False, token_env="": seen.append((path, app_side)) or {"private": False})
    assert gh.repository_public(FORMVIS) is True
    monkeypatch.setattr(gh, "get", lambda path, app_side=False, token_env="": {"private": True})
    assert gh.repository_public(FORMVIS) is False
    monkeypatch.setattr(gh, "get", lambda path, app_side=False, token_env="": {})
    assert gh.repository_public(FORMVIS) is False
    assert seen == [("/repos/nodemode-dev/formvis", True)]


def test_the_catalogue_cli_takes_the_asset_origin(tmp_path):
    releases = tmp_path / "releases.json"
    releases.write_text("{}", encoding="utf-8")
    out = script("catalog.py", "build", "--releases", str(releases), "--asset-origin", "github", "--out", str(tmp_path / "apps.json"))
    assert out.returncode == 0, out.stdout + out.stderr
    assert script("catalog.py", "build", "--releases", str(releases), "--asset-origin", "cdn", "--out", str(tmp_path / "apps.json")).returncode != 0


def test_feed_public_leaves_github_urls_under_the_github_origin(tmp_path, monkeypatch):
    url = f"https://github.com/{FORMVIS}/releases/download/v1.2.3/formvis-1.2.3-macos-arm64.app.tar.gz"
    text = json.dumps({"version": "1.2.3", "platforms": {"darwin-aarch64": {"signature": "s", "url": url}}}, indent=2) + "\n"
    path = tmp_path / "latest.json"
    path.write_text(text, encoding="utf-8")
    out = script("feed.py", "public", "--app", "formvis", "--tag", "v1.2.3", "--file", str(path), "--base", BASE, "--asset-origin", "github")
    assert out.returncode == 0, out.stdout + out.stderr
    assert path.read_text(encoding="utf-8") == text and "stay on nodemode-dev/formvis" in out.stdout
    out = script("feed.py", "public", "--app", "formvis", "--tag", "v1.2.3", "--file", str(path), "--base", BASE)
    assert out.returncode == 0 and json.loads(path.read_text(encoding="utf-8"))["platforms"]["darwin-aarch64"]["url"] == f"{BASE}/formvis/1.2.3/formvis-1.2.3-macos-arm64.app.tar.gz"
    assert script("feed.py", "public", "--app", "formvis", "--tag", "v1.2.3", "--file", str(path), "--base", BASE, "--asset-origin", "cdn").returncode != 0


@pytest.mark.parametrize("path, expected", [
    ("formvis/1.2.3/formvis-1.2.3-macos-arm64.dmg", f"https://github.com/{FORMVIS}/releases/download/v1.2.3/formvis-1.2.3-macos-arm64.dmg"),
    ("/formvis/1.2.3/My%20App%201.2.3.msi", f"https://github.com/{FORMVIS}/releases/download/v1.2.3/My%20App%201.2.3.msi"),
    ("form.md/9.0.0/form.md_9.0.0_aarch64.dmg", f"https://github.com/{FORMVIS}/releases/download/v1.2.3/form.md_9.0.0_aarch64.dmg"),
])
def test_a_store_path_maps_to_the_github_asset_of_the_release(path, expected):
    assert public_urls.github_asset_url(FORMVIS, "v1.2.3", path) == expected


def test_the_mapping_round_trips_with_the_store_url_and_the_feed_rewrite():
    name = "formvis-1.2.3-macos-arm64.app.tar.gz"
    store = public_urls.artifact_url(BASE, "formvis", "1.2.3", name)
    path = store[len(BASE) + 1:]
    assert public_urls.parse_store_path(path) == ("formvis", "1.2.3", name)
    github = public_urls.github_asset_url(FORMVIS, "v1.2.3", path)
    assert public_urls.feed_url(github, BASE, "formvis", "1.2.3", "v1.2.3") == store


@pytest.mark.parametrize("repository, tag, path", [
    ("formvis", "v1.2.3", "formvis/1.2.3/a.dmg"),
    (FORMVIS, "", "formvis/1.2.3/a.dmg"),
    (FORMVIS, "v1/2", "formvis/1.2.3/a.dmg"),
    (FORMVIS, "v1.2.3", "formvis/a.dmg"),
    (FORMVIS, "v1.2.3", "formvis/1.2.3/sub/a.dmg"),
    (FORMVIS, "v1.2.3", ""),
])
def test_the_mapping_refuses_other_shapes(repository, tag, path):
    with pytest.raises(ValueError):
        public_urls.github_asset_url(repository, tag, path)
