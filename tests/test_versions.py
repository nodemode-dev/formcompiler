import pytest

import versions


@pytest.mark.parametrize("lower, higher", [
    ("1.0.0-alpha", "1.0.0-alpha.1"),
    ("1.0.0-alpha.1", "1.0.0-alpha.beta"),
    ("1.0.0-alpha.beta", "1.0.0-beta"),
    ("1.0.0-beta.2", "1.0.0-beta.10"),
    ("1.0.0-beta.11", "1.0.0-rc.1"),
    ("1.0.0-rc.1", "1.0.0"),
    ("1.0.0", "1.0.1-beta.1"),
    ("1.9.0", "1.10.0"),
    ("0.9.9", "1.0.0-beta.1"),
])
def test_semver_ordering_with_prereleases(lower, higher):
    assert versions.semver_key(lower) < versions.semver_key(higher)


def test_build_metadata_does_not_order():
    assert versions.semver_key("1.2.3+abc") == versions.semver_key("1.2.3")


@pytest.mark.parametrize("version", ["v1.2.3", "1.2", "1.2.3.4", "01.2.3", ""])
def test_a_bad_version_is_refused(version):
    with pytest.raises(ValueError):
        versions.semver_key(version)


@pytest.mark.parametrize("version, expected", [
    ("1.2.3", versions.STABLE),
    ("1.2.3+build.5", versions.STABLE),
    ("1.2.3-beta.1", versions.BETA),
    ("1.2.3-rc.2", versions.BETA),
    ("2.0.0-alpha", versions.BETA),
])
def test_beta_classification(version, expected):
    assert versions.channel(version) == expected


def release(tag, draft=False):
    return {"tag_name": tag, "draft": draft}


RELEASES = [
    release("v1.97.2"),
    release("v1.97.10"),
    release("v1.98.0-beta.1"),
    release("v1.99.0", draft=True),
    release("v1.98.5", draft=True),
    release("formvis-v9.0.0"),
    release("formvis-updates"),
    release("catalog"),
    release("nightly"),
]


def test_highest_published_uses_semver_and_ignores_drafts_and_other_tags():
    """Releases are the app repository's own, tagged vX.Y.Z; an old formcompiler-shaped tag or any other tag is not a version."""
    assert versions.highest_published("formvis", RELEASES) == "1.98.0-beta.1"
    assert versions.highest_published("formvis", [release("formvis-v9.0.0"), release("catalog")]) == ""
    assert versions.highest_published("formvis", []) == ""


@pytest.mark.parametrize("tag, version", [("v1.2.3", "1.2.3"), ("v1.2.3-beta.1", "1.2.3-beta.1"), ("1.2.3", ""), ("formvis-v1.2.3", ""), ("vv1.2.3", ""), ("v1.2", "")])
def test_a_release_tag_is_v_then_the_version(tag, version):
    assert versions.version_of(tag) == version
    assert versions.tag_of("1.2.3") == "v1.2.3"


@pytest.mark.parametrize("version, ok, named", [
    ("1.98.0", True, ""),
    ("1.98.0-beta.2", True, ""),
    ("1.98.0-beta.1", False, "1.98.0-beta.1"),
    ("1.98.0-alpha.9", False, "1.98.0-beta.1"),
    ("1.97.11", True, ""),
    ("1.97.10", False, "1.97.10"),
    ("1.97.3", False, "1.97.10"),
])
def test_version_must_go_up_within_its_channel(version, ok, named):
    """A stable must be above the highest stable, so a beta never blocks a fix on the stable line; a beta above everything."""
    above, why = versions.above_published("formvis", version, RELEASES)
    assert above is ok
    assert named in why


def test_drafts_newer_and_older():
    assert versions.newer_draft("formvis", "1.98.5", RELEASES) == "1.99.0"
    assert versions.newer_draft("formvis", "1.99.0", RELEASES) == ""
    assert versions.older_drafts("formvis", "2.0.0", RELEASES) == ["v1.99.0", "v1.98.5"]
    assert versions.older_drafts("formvis", "1.98.5", RELEASES) == []


def test_a_beta_never_supersedes_a_stable_draft():
    releases = [release("v1.2.0", draft=True), release("v1.3.0-beta.1", draft=True)]
    assert versions.older_drafts("formvis", "1.3.0-beta.2", releases) == ["v1.3.0-beta.1"]
    assert versions.older_drafts("formvis", "1.3.0", releases) == ["v1.3.0-beta.1", "v1.2.0"]
