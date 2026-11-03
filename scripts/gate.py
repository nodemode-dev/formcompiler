import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import github_api as gh
import readiness
import versions
from registry import load, write_outputs


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def release_refs(entry, version):
    repo = entry["repository"]
    refs = dict(gh.compile_branches(repo))
    if entry.get("tag_trigger"):
        for name, sha, kind in gh.version_tags(repo):
            if gh.VERSION_TAG.match(name) and (not version or name == f"v{version}"):
                refs[name] = gh.tag_commit(repo, sha, kind)
    return refs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--version", default="")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "nodemode-dev/formcompiler"))
    parser.add_argument("--run-title", default="")
    args = parser.parse_args()

    entry = load(args.app)
    if not entry["enabled"]:
        fail(f"{args.app} is disabled in the registry: {entry.get('disabled_reason', '')}")
    refs = release_refs(entry, args.version.strip().removeprefix("v"))
    ref = args.ref.strip()
    if ref in refs:
        branch, sha = ref, refs[ref]
    elif re.fullmatch(r"[0-9a-f]{40}", ref):
        sha = ref
        heads = [name for name, head in refs.items() if head == sha]
        if args.version:
            wanted = args.version.removeprefix("v")
            heads = [name for name in heads if name in (f"compile_v{wanted}", f"v{wanted}")]
        if not heads:
            fail(f"{sha[:9]} is not the head of a compile branch or a version tag in {entry['repository']}; the ref may have moved, and the watch will pick up its new commit")
        branch = sorted(heads)[0]
    else:
        fail(f"ref {ref!r} must be a compile branch name, a vX.Y.Z tag or a full commit SHA")

    active = {t for t in gh.active_release_runs(args.repo) if t != args.run_title}
    state, reason, version = readiness.evaluate(entry, branch, sha, gh.releases(args.repo), active)
    gh.summary(f"### Gate: {entry['app']} `{branch}` at `{sha[:12]}`\n\n{state}: {reason}\n\n")
    if entry.get("notes_for_owner"):
        gh.summary(f"> {entry['notes_for_owner']}\n\n")
    if state != readiness.READY:
        fail(reason)
    prerelease = "true" if versions.channel(version) == versions.BETA else "false"
    write_outputs({"sha": sha, "branch": branch, "version": version, "tag": f"{entry['app']}-v{version}", "prerelease": prerelease})
    print(f"gate passed: {entry['app']} {version} at {sha}")


if __name__ == "__main__":
    main()
