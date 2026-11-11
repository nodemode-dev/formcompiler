import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import public_urls
from registry import all_entries, validate

WORKFLOW = "tick.yml"
WATCH = "watch.yml"
FEED_REPO = "nodemode-dev/formpipe"
FEED_EVENT = "formcompiler-published"
FEED_STATE = "catalog/feed-state.json"
SUCCESSOR = re.compile(r"^tick after ([0-9]+)$")
ACTIVE = {"queued", "in_progress", "waiting", "pending", "requested"}
RETRIED = {408, 429, 500, 502, 503, 504}
WAITS = (10, 30)
SLACK_MINUTES = 2
RETRY_AFTER_MINUTES = 60


class Unreachable(Exception):
    pass


def parse_time(value: str) -> datetime.datetime:
    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)


def stamp(moment: datetime.datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def predecessor(run: dict):
    found = SUCCESSOR.match(run.get("display_title") or "")
    return int(found.group(1)) if found else None


def owns(me: int, after, runs: list) -> bool:
    active = [r for r in runs if r.get("status") in ACTIVE and r.get("id") != me]
    finishing = {predecessor(r) for r in active} | {after}
    others = [r for r in active if r.get("id") not in finishing]
    successors = [r for r in others if predecessor(r) is not None]
    if after:
        return not any(r["id"] < me for r in successors)
    return not successors and not any(r["id"] < me for r in others)


def unfed(releases_by_app: dict, planned_at: str) -> list:
    found = []
    for (app, repository), releases in releases_by_app.items():
        for release in releases:
            published = release.get("published_at") or ""
            if release.get("draft") or not published or not gh.VERSION_TAG.match(release.get("tag_name") or ""):
                continue
            if published > planned_at:
                found.append({"published_at": published, "app": app, "tag": release["tag_name"], "repository": repository})
    return sorted(found, key=lambda item: (item["published_at"], item["app"]))


def to_dispatch(waiting: list, now: datetime.datetime, every: int):
    if not waiting:
        return None, "every published release is in the store's catalogue"
    newest = waiting[-1]
    age = (now - parse_time(newest["published_at"])).total_seconds() / 60
    names = ", ".join(f"{i['app']} {i['tag']}" for i in waiting)
    if age <= every + SLACK_MINUTES:
        return newest, f"{names} not fed yet, published since the last tick"
    if now.minute < every and age >= RETRY_AFTER_MINUTES:
        return newest, f"{names} still not fed; the hour's first tick asks again"
    return None, f"{names} not fed yet; asked when published, asked again at the hour's first tick"


def attempt(what: str, call, sleep=time.sleep):
    for number, wait in enumerate((*WAITS, None), start=1):
        try:
            return call()
        except gh.ApiError as error:
            problem = str(error)
            if error.status not in RETRIED:
                raise Unreachable(f"{what}: {problem}") from None
        except (urllib.error.URLError, OSError, ValueError) as error:
            problem = str(error)
        if wait is None:
            raise Unreachable(f"{what}: {problem} (after {number} attempts)")
        sleep(wait)
    raise Unreachable(what)


def feed_state(base: str):
    url = f"{base}/{FEED_STATE}"
    request = urllib.request.Request(url, headers={"User-Agent": "formcompiler"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read()).get("planned_at", "")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise gh.ApiError(error.code, f"GET {url}") from None


def tick_runs(repo: str) -> list:
    return gh.get(f"/repos/{repo}/actions/workflows/{WORKFLOW}/runs?per_page=50").get("workflow_runs", [])


def app_releases(entries: list, sleep) -> tuple:
    found, problems = {}, []
    for entry in entries:
        repository = entry["repository"]
        try:
            found[(entry["app"], repository)] = attempt(f"releases of {repository}", lambda: gh.get(f"/repos/{repository}/releases?per_page=30", app_side=True), sleep)
        except Unreachable as error:
            problems.append(str(error))
    return found, problems


def enabled_entries() -> list:
    return [e for e in all_entries() if e.get("enabled") and not validate(e, None)]


def check_feed(args, now, sleep) -> str:
    if not args.base:
        return "feed: FORMCOMPILER_PUBLIC_BASE is not set, so the store's feed state cannot be read; not checked"
    if not os.environ.get("FORMPIPE_DISPATCH_TOKEN", "").strip():
        return "feed: FORMPIPE_DISPATCH_TOKEN is not set; not checked (formpipe's own hourly run picks releases up)"
    planned_at = attempt(f"{args.base}/{FEED_STATE}", lambda: feed_state(args.base), sleep)
    if planned_at is None:
        return f"feed: {args.base}/{FEED_STATE} does not exist yet; not checked"
    releases, problems = app_releases(enabled_entries(), sleep)
    for problem in problems:
        print(f"::warning::{problem}")
    item, why = to_dispatch(unfed(releases, planned_at), now, args.every)
    if not item:
        return f"feed: {why}"
    payload = {"event_type": FEED_EVENT, "client_payload": {k: item[k] for k in ("app", "tag", "repository")}}
    attempt(f"repository_dispatch to {FEED_REPO}", lambda: gh.request("POST", f"/repos/{FEED_REPO}/dispatches", payload, token_env="FORMPIPE_DISPATCH_TOKEN"), sleep)
    return f"feed: {why}; sent {FEED_EVENT} for {item['app']} {item['tag']}"


def tick_once(args, now, sleep) -> list:
    lines = []
    try:
        attempt(f"dispatch of {WATCH}", lambda: gh.request("POST", f"/repos/{args.repo}/actions/workflows/{WATCH}/dispatches", {"ref": args.ref}), sleep)
        lines.append("watch: started")
    except Exception as error:
        print(f"::warning::{error}")
        lines.append(f"watch: not started ({error})")
    try:
        lines.append(check_feed(args, now, sleep))
    except Exception as error:
        print(f"::warning::{error}")
        lines.append(f"feed: not checked ({error})")
    return lines


def still_owner(args, sleep) -> bool:
    try:
        return owns(args.run_id, args.after, attempt("tick runs", lambda: tick_runs(args.repo), sleep))
    except Unreachable as error:
        print(f"::warning::{error}; this tick keeps the clock")
        return True


def output(name: str, value: str):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def command_owner(args, sleep=time.sleep):
    mine = still_owner(args, sleep)
    gh.summary(f"tick {args.run_id}: {'keeps the clock' if mine else 'another tick keeps the clock; this one stops'}\n")
    output("owner", "true" if mine else "false")


def command_loop(args, clock=time.time, sleep=time.sleep):
    start = clock()
    for number in range(args.minutes // args.every + 1):
        wait = start + number * args.every * 60 - clock()
        if wait > 0:
            sleep(wait)
        if number and not still_owner(args, sleep):
            gh.summary("- another tick keeps the clock; this one stops without starting a successor\n")
            output("yielded", "true")
            return
        now = datetime.datetime.fromtimestamp(clock(), datetime.timezone.utc)
        gh.summary(f"- {stamp(now)} · " + " · ".join(tick_once(args, now, sleep)) + "\n")
    output("yielded", "false")


def command_chain(args, sleep=time.sleep):
    body = {"ref": args.ref, "inputs": {"after": str(args.run_id)}}
    try:
        attempt(f"dispatch of {WORKFLOW}", lambda: gh.request("POST", f"/repos/{args.repo}/actions/workflows/{WORKFLOW}/dispatches", body), sleep)
    except Unreachable as error:
        print(f"::error::{error}; the schedule starts the next tick")
        sys.exit(1)
    gh.summary(f"started the next tick, after {args.run_id}\n")


def run_id(value: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]{0,19}", value or ""):
        raise argparse.ArgumentTypeError(f"{value!r} is not a run id")
    return int(value)


def after_id(value: str):
    return run_id(value) if value else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("owner", "loop", "chain"))
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nodemode-dev/formcompiler"))
    parser.add_argument("--ref", default="main")
    parser.add_argument("--run-id", type=run_id, default=os.environ.get("GITHUB_RUN_ID", ""))
    parser.add_argument("--after", type=after_id, default=None)
    parser.add_argument("--minutes", type=int, default=330)
    parser.add_argument("--every", type=int, default=15)
    args = parser.parse_args()
    if not 1 <= args.every <= 60 or not 0 <= args.minutes <= 345:
        parser.error("--every is 1 to 60 minutes and --minutes 0 to 345")
    try:
        args.base = public_urls.base_url(os.environ.get("FORMCOMPILER_PUBLIC_BASE", ""))
    except ValueError as error:
        print(f"::warning::{error}")
        args.base = ""
    {"owner": command_owner, "loop": command_loop, "chain": command_chain}[args.command](args)


if __name__ == "__main__":
    main()
