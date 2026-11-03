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
