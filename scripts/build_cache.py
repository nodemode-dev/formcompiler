import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

PATH = re.compile(r"[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*")


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def inside(path):
    return bool(PATH.fullmatch(path)) and ".." not in path.split("/") and path not in (".",)


def digest(root, key_files):
    if not key_files:
        fail("a build cache needs key files, or nothing would ever rebuild it")
    total = hashlib.sha256()
    for name in sorted(set(key_files)):
        if not inside(name):
            fail(f"build cache key file {name!r} must be a plain path inside the app repository")
        file = root / name
        if not file.is_file():
            fail(f"build cache key file {name} is not in the app repository")
        total.update(name.encode() + b"\0" + file.read_bytes() + b"\0")
    return total.hexdigest()[:16]


def label(text):
    return re.sub(r"[^A-Za-z0-9._-]", "_", text)


def key(app, platform, runner, key_hash):
    return f"formcompiler-build-{label(app)}-{label(platform)}-{label(runner)}-{key_hash}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--key-files", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    key_hash = digest(Path(args.root), lines(args.key_files))
    values = {"hash": key_hash, "key": key(args.app, args.platform, args.runner, key_hash)}
    text = "".join(f"{name}={value}\n" for name, value in values.items())
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()
