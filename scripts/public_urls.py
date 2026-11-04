import re
import urllib.parse

BASE = re.compile(r"^https://[A-Za-z0-9.-]+(:[0-9]{1,5})?(/[A-Za-z0-9._~-]+)*/?$")
DOWNLOAD = re.compile(r"^https://github\.com/[^/]+/[^/]+/releases/download/([^/]+)/([^/?#]+)$")


def base_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    if not BASE.match(value):
        raise ValueError(f"FORMCOMPILER_PUBLIC_BASE {value!r} must be an https:// address with no query, for example https://dl.formai.studio")
    return value.rstrip("/")


def quoted(*parts):
    return "/".join(urllib.parse.quote(part, safe="") for part in parts)


def artifact_url(base, app, version, name):
    return f"{base}/{quoted(app, version, name)}"


STORE_PATH = re.compile(r"^/?([^/]+)/([^/]+)/([^/]+)$")


def parse_store_path(path: str) -> tuple:
    found = STORE_PATH.match(path or "")
    if not found:
        raise ValueError(f"{path!r} is not a store path of the shape <app>/<version>/<file>")
    return tuple(urllib.parse.unquote(part) for part in found.groups())


def github_asset_url(repository: str, tag: str, path: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", repository or ""):
        raise ValueError(f"{repository!r} is not an owner/name repository")
    if not tag or "/" in tag:
        raise ValueError(f"{tag!r} is not a release tag")
    _, _, name = parse_store_path(path)
    return f"https://github.com/{repository}/releases/download/{quoted(tag, name)}"


def feed_url(url, base, app, version, tag):
    found = DOWNLOAD.match(url or "")
    if not base or not found or urllib.parse.unquote(found.group(1)) != tag:
        return url
    return artifact_url(base, app, version, urllib.parse.unquote(found.group(2)))


def rewrite_feed(feed, base, app, version, tag):
    platforms = feed.get("platforms")
    if not base or not isinstance(platforms, dict):
        return feed
    moved = {
        key: {**value, "url": feed_url(value.get("url", ""), base, app, version, tag)} if isinstance(value, dict) else value
        for key, value in platforms.items()
    }
    return {**feed, "platforms": moved}
