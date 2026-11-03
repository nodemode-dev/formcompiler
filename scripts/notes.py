import argparse
import re
import subprocess
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,4})\s+(.*)$")


def changelog_section(path, version):
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    token = re.compile(rf"(?<![0-9A-Za-z.]){re.escape(version)}(?![0-9A-Za-z])")
    start = level = None
    for index, line in enumerate(lines):
        found = HEADING.match(line)
        if not found:
            continue
        if start is None and token.search(found.group(2).replace("v" + version, version)):
            start, level = index + 1, len(found.group(1))
        elif start is not None and len(found.group(1)) <= level:
            return "\n".join(lines[start:index]).strip()
    return "\n".join(lines[start:]).strip() if start is not None else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-dir", default="app")
    parser.add_argument("--version", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--command", default="")
    parser.add_argument("--out", default="release-notes.md")
    args = parser.parse_args()

    app = Path(args.app_dir)
    body = ""
    if args.command.strip():
        result = subprocess.run(["bash", "-eo", "pipefail", "-c", args.command], cwd=app, capture_output=True, text=True)
        if result.returncode:
            sys.stderr.write(result.stderr)
            sys.exit(f"::error::the registry's notes command exited {result.returncode}")
        body = result.stdout.strip()
    if not body:
        for name in ("CHANGELOG.md", "CHANGES.md"):
            body = changelog_section(app / name, args.version)
            if body:
                break
    if not body:
        body = f"Built from [{args.repo}@{args.sha[:9]}](https://github.com/{args.repo}/commit/{args.sha}); the app's CHANGELOG has no section for {args.version}."
    footer = (
        f"\n\n---\n\nBuilt by formcompiler from [`{args.repo}`](https://github.com/{args.repo}) "
        f"ref `{args.branch}` at [`{args.sha[:12]}`](https://github.com/{args.repo}/commit/{args.sha}). "
        f"`SHA256SUMS.txt` lists every file.\n\n<!-- formcompiler-source: {args.repo}@{args.sha} -->\n"
    )
    Path(args.out).write_text(body + footer, encoding="utf-8")
    print(body + footer)


if __name__ == "__main__":
    main()
