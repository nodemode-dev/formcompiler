import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
COMPILE_BRANCH = re.compile(r"^compile_v((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?)$")
VERSION_TAG = re.compile(r"^v((0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?)$")
MAIN = "main"
RELEASES_ON_APP_REPOS_SINCE = "2026-11-03T22:47:59Z"
SOURCE_MARK = re.compile(r"formcompiler-source: (\S+)@([0-9a-f]{40})")


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(f"{status}: {message}")
        self.status = status


def token(app_side=False, token_env=""):
    if token_env:
        return os.environ.get(token_env, "").strip()
    if app_side and os.environ.get("FORMCOMPILER_APP_TOKEN", "").strip():
        return os.environ["FORMCOMPILER_APP_TOKEN"].strip()
    return os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()


def request(method, path, body=None, app_side=False, raw=False, token_env=""):
    url = path if path.startswith("http") else f"{API}{path}"
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "formcompiler"}
    secret = token(app_side, token_env)
    if secret:
        headers["Authorization"] = f"Bearer {secret}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = response.read()
            link = response.headers.get("Link", "")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:300]
        raise ApiError(error.code, f"{method} {url}: {detail}") from None
    if raw:
        return payload, link
    return (json.loads(payload) if payload else None), link


def get(path, app_side=False, token_env=""):
    return request("GET", path, app_side=app_side, token_env=token_env)[0]


def paged(path, key=None, app_side=False, token_env=""):
    url = path + ("&" if "?" in path else "?") + "per_page=100"
    items = []
    while url:
        data, link = request("GET", url, app_side=app_side, token_env=token_env)
        items.extend(data[key] if key else data)
        found = re.search(r'<([^>]+)>;\s*rel="next"', link or "")
        url = found.group(1) if found else ""
    return items


def compile_branches(repo):
    try:
        refs = get(f"/repos/{repo}/git/matching-refs/heads/compile_v", app_side=True)
    except ApiError as error:
        if error.status == 404:
            raise ApiError(404, f"{repo} is not readable: make it public or give FORMCOMPILER_APP_TOKEN read access") from None
        raise
    return [(ref["ref"].removeprefix("refs/heads/"), ref["object"]["sha"]) for ref in refs]


def version_tags(repo):
    refs = get(f"/repos/{repo}/git/matching-refs/tags/v", app_side=True)
    return [(ref["ref"].removeprefix("refs/tags/"), ref["object"]["sha"], ref["object"]["type"]) for ref in refs]


def tag_commit(repo, sha, kind, token_env=""):
    seen = 0
    while kind == "tag" and seen < 5:
        target = get(f"/repos/{repo}/git/tags/{sha}", app_side=True, token_env=token_env)["object"]
        sha, kind, seen = target["sha"], target["type"], seen + 1
    if kind != "commit":
        raise ApiError(0, f"tag object {sha[:9]} in {repo} does not point at a commit")
    return sha


def tag_target(repo: str, name: str, token_env: str = "") -> str:
    try:
        ref = get(f"/repos/{repo}/git/ref/tags/{urllib.parse.quote(name)}", app_side=True, token_env=token_env)
    except ApiError as error:
        if error.status == 404:
            return ""
        raise
    return tag_commit(repo, ref["object"]["sha"], ref["object"]["type"], token_env)


def on_main(repo, sha):
    data = get(f"/repos/{repo}/compare/{MAIN}...{sha}", app_side=True)
    return data.get("status") in ("identical", "behind")


def file_at(repo, path, sha):
    quoted = urllib.parse.quote(path)
    data = get(f"/repos/{repo}/contents/{quoted}?ref={sha}", app_side=True)
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        raise ApiError(0, f"{repo}:{path} at {sha[:9]} is not a file")
    return base64.b64decode(data["content"]).decode("utf-8")


def checks_state(repo, sha, workflows):
    runs = paged(f"/repos/{repo}/actions/runs?head_sha={sha}", key="workflow_runs", app_side=True)
    states = {}
    for workflow in workflows:
        mine = [r for r in runs if r.get("path", "").split("@")[0].endswith(f".github/workflows/{workflow}")]
        if not mine:
            states[workflow] = "missing"
            continue
        latest = max(mine, key=lambda r: (r.get("run_attempt", 1), r.get("created_at", "")))
        if latest.get("status") != "completed":
            states[workflow] = "pending"
        else:
            states[workflow] = latest.get("conclusion") or "unknown"
    return states


def releases(repo: str, token_env: str = "") -> list:
    return paged(f"/repos/{repo}/releases", app_side=True, token_env=token_env)


def release_by_tag(all_releases, tag):
    for release in all_releases:
        if release.get("tag_name") == tag:
            return release
    return None


def source_of(release):
    found = SOURCE_MARK.search(release.get("body") or "")
    return (found.group(1), found.group(2)) if found else (None, None)


def active_release_runs(repo):
    titles = set()
    for status in ("queued", "in_progress", "waiting", "pending", "requested"):
        runs = get(f"/repos/{repo}/actions/workflows/release.yml/runs?status={status}&per_page=100")
        titles.update(run.get("display_title", "") for run in runs.get("workflow_runs", []))
    return titles


def stopped_release_runs(repo):
    titles = set()
    for status in ("failure", "cancelled"):
        runs = get(f"/repos/{repo}/actions/workflows/release.yml/runs?status={status}&per_page=100")
        titles.update(run.get("display_title", "") for run in runs.get("workflow_runs", []))
    return titles


def succeeded_release_runs(repo: str, since: str) -> set[str]:
    created = urllib.parse.quote(f">={since}", safe="")
    runs = get(f"/repos/{repo}/actions/workflows/release.yml/runs?status=success&branch={MAIN}&event=workflow_dispatch&created={created}&per_page=100")
    return {
        run.get("display_title", "")
        for run in runs.get("workflow_runs", [])
        if run.get("head_branch") == MAIN and run.get("event") == "workflow_dispatch"
        and run.get("conclusion") == "success" and run.get("created_at", "") >= since
    }


def run_title(app, version, sha):
    return f"{app} {version} at {sha}"


def dispatch(repo, ref, inputs):
    request("POST", f"/repos/{repo}/actions/workflows/release.yml/dispatches", {"ref": ref, "inputs": inputs})


def summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text)
    sys.stdout.write(text)
