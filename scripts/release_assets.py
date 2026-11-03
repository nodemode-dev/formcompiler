import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="dist")
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    folder = Path(args.dir)
    manifests = sorted(folder.glob("*.formcompiler.json"))
    if not manifests:
        sys.exit(f"::error::no platform manifests in {folder}; did every build upload its files?")
    base = f"https://github.com/{args.repo}/releases/download/{args.tag}/"
    platforms = {}
    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        update = data.get("update")
        if update:
            platforms[data["updater_key"]] = {"signature": update["signature"], "url": base + update["file"]}
        manifest.unlink()

    if platforms:
        feed = {
            "version": args.version,
            "notes": f"{args.title} {args.tag}",
            "pub_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "platforms": dict(sorted(platforms.items())),
        }
        (folder / "latest.json").write_text(json.dumps(feed, indent=2) + "\n", encoding="utf-8")
        print(f"latest.json: {', '.join(sorted(platforms))}")
    else:
        print("latest.json not written: no platform has a signed updater bundle (TAURI_SIGNING_PRIVATE_KEY unset)")

    files = sorted(p for p in folder.iterdir() if p.is_file() and p.name != "SHA256SUMS.txt")
    sums = "".join(f"{sha256(p)}  {p.name}\n" for p in files)
    (folder / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    print(sums, end="")


if __name__ == "__main__":
    main()
