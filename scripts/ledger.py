import datetime
import json
import re
import zoneinfo
from pathlib import Path

FORMAT = 1
TITLE = re.compile(r"^(\S+) (\S*) at (\S+)$")
SHA = re.compile(r"^[0-9a-f]{40}$")
RUNNING, WAITING, FAILED, CANCELLED, SUCCEEDED, STARTED, GONE = "running", "waiting", "failed", "cancelled", "succeeded", "started", "gone"
REFUSED = "refused"
LIVE = (RUNNING, WAITING, STARTED)


def empty():
    return {"format": FORMAT, "builds": {}, "runs": {}}


def load(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty()
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        return empty()
    if not isinstance(data.get("builds"), dict) or not isinstance(data.get("runs"), dict):
        return empty()
    return data


def text(data):
    return json.dumps(data, indent=1, sort_keys=True) + "\n"


def save(path, data):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text(data), encoding="utf-8")


def key(app, sha):
    return f"{app} {sha}"


def at_gate(data, run, refused):
    gates = data.setdefault("gates", {})
    mark = f"{run.get('id')}/{run.get('run_attempt') or 1}"
    if mark not in gates:
        gates[mark] = bool(refused(run))
    return gates[mark]


def state_of(run, data=None, refused=None):
    if run.get("status") == "waiting":
        return WAITING
    if run.get("status") != "completed":
        return RUNNING
    if run.get("conclusion") == "success":
        return SUCCEEDED
    if run.get("conclusion") == "cancelled":
        return CANCELLED
    if refused is not None and data is not None and at_gate(data, run, refused):
        return REFUSED
    return FAILED


def fold(data, runs, app="", heads=None, refused=None):
    heads = heads or {}
    for run in sorted(runs, key=lambda r: r.get("run_number") or 0):
        found = TITLE.match(run.get("display_title") or "")
        if not found or (app and found.group(1) != app):
            continue
        name, run_id = found.group(1), str(run.get("id"))
        sha = data["runs"].get(run_id, "")
        if not sha:
            ref = found.group(3)
            sha = ref if SHA.match(ref) else heads.get(ref, "")
            if not sha:
                continue
            data["runs"][run_id] = sha
        number = run.get("run_number") or 0
        seen = data["builds"].get(key(name, sha), {})
        if number > seen.get("number", 0) or (number == seen.get("number", 0) and seen.get("state") != STARTED):
            data["builds"][key(name, sha)] = {"state": state_of(run, data, refused), "number": number, "by": (run.get("actor") or {}).get("login", "")}


def settle(data, runs):
    listed = {run.get("run_number") for run in runs}
    for entry in data["builds"].values():
        if entry.get("state") in (RUNNING, WAITING) and entry.get("number") not in listed:
            entry["state"] = GONE


def known(data, app, sha):
    return data["builds"].get(key(app, sha))


def started(data, app, sha):
    try:
        now = datetime.datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    except zoneinfo.ZoneInfoNotFoundError:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5), "EST"))
    last = data["builds"].get(key(app, sha), {}).get("number", 0)
    data["builds"][key(app, sha)] = {"state": STARTED, "number": last, "by": "watch", "at": now.strftime("%b %d, %I:%M %p %Z")}
