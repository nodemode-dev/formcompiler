import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stage import DEFAULT_ARTIFACTS

PACKAGES = {
    "dlib": {
        "url": "https://api.nuget.org/v3-flatcontainer/microsoft.artifactsigning.client/1.0.146/microsoft.artifactsigning.client.1.0.146.nupkg",
        "sha256": "7761e5d8f31e54b764da21d33cd8b0a2940e1b05526c7dfcb5e94b0431426f70",
        "folder": "bin/x64/",
    },
    "signtool": {
        "url": "https://api.nuget.org/v3-flatcontainer/microsoft.windows.sdk.buildtools/10.0.28000.2705/microsoft.windows.sdk.buildtools.10.0.28000.2705.nupkg",
        "sha256": "8bfdfb6ca2633f531cf80b5fa22512ba61a394d7988f0970db83baadc67929ed",
        "folder": "bin/10.0.28000.0/x64/",
    },
}
SETTINGS = ("ARTIFACT_SIGNING_ENDPOINT", "ARTIFACT_SIGNING_ACCOUNT", "ARTIFACT_SIGNING_PROFILE")
CREDENTIALS = ("AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID")
TIMESTAMP = "http://timestamp.acs.microsoft.com"
TAURI_CLI = "@tauri-apps/cli@2.12.3"
SKIP_DIRS = {"node_modules", "target", ".git", ".formcompiler", "dist", "build"}
SIGNABLE = (".exe", ".msi", ".dll")
EXCLUDED_CREDENTIALS = [
    "ManagedIdentityCredential", "WorkloadIdentityCredential", "SharedTokenCacheCredential",
    "VisualStudioCredential", "VisualStudioCodeCredential", "AzureCliCredential",
    "AzurePowerShellCredential", "AzureDeveloperCliCredential", "InteractiveBrowserCredential",
]


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def configured(env):
    settings = [env.get(name, "").strip() for name in SETTINGS]
    credentials = [env.get(name, "").strip() for name in CREDENTIALS]
    if all(settings) and all(credentials):
        return True
    if any(settings) or any(credentials):
        missing = [n for n, v in zip(SETTINGS + CREDENTIALS, settings + credentials) if not v]
        print(f"::warning::Artifact Signing is half set up, missing {', '.join(missing)}: the Windows build is unsigned")
    return False


def fetch(name, spec, tools):
    data = urllib.request.urlopen(spec["url"], timeout=300).read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != spec["sha256"]:
        fail(f"{name} package hash {digest} is not the pinned {spec['sha256']}")
    target = tools / name
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile() as handle:
        handle.write(data)
        handle.seek(0)
        with zipfile.ZipFile(handle) as archive:
            for member in archive.namelist():
                if member.startswith(spec["folder"]) and not member.endswith("/"):
                    out = target / member[len(spec["folder"]):]
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(archive.read(member))
    return target


def sign_args(tools):
    return [
        str(tools / "signtool" / "signtool.exe"), "sign", "/fd", "SHA256", "/tr", TIMESTAMP, "/td", "SHA256",
        "/dlib", str(tools / "dlib" / "Azure.CodeSigning.Dlib.dll"), "/dmdf", str(tools / "metadata.json"),
    ]


def tauri_dirs(app_dir):
    found = []
    for root, dirs, files in os.walk(app_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        if "tauri.conf.json" in files or "tauri.conf.json5" in files or "Tauri.toml" in files:
            found.append(Path(root))
    return sorted(found)


def merge_windows_config(directory, command):
    if (directory / "Tauri.windows.toml").is_file() or (directory / "tauri.windows.conf.json5").is_file():
        print(f"::warning::{directory} keeps its own Windows config in TOML or JSON5; its files are signed after the build instead")
        return False
    path = directory / "tauri.windows.conf.json"
    config = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    windows = config.setdefault("bundle", {}).setdefault("windows", {})
    windows.pop("certificateThumbprint", None)
    windows["signCommand"] = command
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"signing set for the Tauri app in {directory}")
    return True


def prepare(args):
    env = os.environ
    if not configured(env):
        print("Artifact Signing not set: the Windows build is unsigned")
        return
    tools = Path(args.tools).resolve()
    for name, spec in PACKAGES.items():
        fetch(name, spec, tools)
    metadata = {
        "Endpoint": env["ARTIFACT_SIGNING_ENDPOINT"].strip(),
        "CodeSigningAccountName": env["ARTIFACT_SIGNING_ACCOUNT"].strip(),
        "CertificateProfileName": env["ARTIFACT_SIGNING_PROFILE"].strip(),
        "ExcludeCredentials": EXCLUDED_CREDENTIALS,
    }
    (tools / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    command = " ".join(sign_args(tools) + ["%1"])
    dirs = tauri_dirs(Path(args.app_dir).resolve())
    for directory in dirs:
        merge_windows_config(directory, command)
    if not dirs:
        print("no Tauri app found: the files are signed after the build")
    github_env = env.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as handle:
            handle.write(f"FORMCOMPILER_SIGNING_TOOLS={tools}\n")


def is_signed(signtool, path):
    return subprocess.run([str(signtool), "verify", "/pa", "/q", str(path)], capture_output=True).returncode == 0


def sign_file(args_list, path):
    run = subprocess.run(args_list + [str(path)], capture_output=True, text=True)
    if run.returncode != 0:
        print(run.stdout[-2000:])
        print(run.stderr[-2000:])
        fail(f"signing {path.name} failed")


def resign_updater(path):
    sig = Path(f"{path}.sig")
    if not sig.is_file():
        return
    if not os.environ.get("TAURI_SIGNING_PRIVATE_KEY", "").strip():
        fail(f"{path.name} changed when it was signed but there is no updater key to sign it again")
    npx = shutil.which("npx")
    if not npx:
        fail("npx is not on PATH to sign the updater file again")
    sig.unlink()
    run = subprocess.run([npx, "--yes", TAURI_CLI, "signer", "sign", str(path)], capture_output=True, text=True)
    if run.returncode != 0 or not sig.is_file():
        print(run.stderr[-2000:])
        fail(f"could not sign the updater file {path.name} again")
    print(f"updater signature made again for {path.name}")


def sign_zip(args_list, signtool, path):
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        unsigned = []
        with tempfile.TemporaryDirectory() as work:
            for info in infos:
                if info.filename.lower().endswith(SIGNABLE) and not info.is_dir():
                    out = Path(work) / f"{len(unsigned)}{Path(info.filename).suffix}"
                    out.write_bytes(archive.read(info))
                    if not is_signed(signtool, out):
                        sign_file(args_list, out)
                        unsigned.append((info.filename, out.read_bytes()))
            if not unsigned:
                return False
            replaced = dict(unsigned)
            rebuilt = Path(work) / "rebuilt.zip"
            with zipfile.ZipFile(rebuilt, "w") as new:
                for info in infos:
                    new.writestr(info, replaced.get(info.filename, archive.read(info)))
    shutil.move(str(rebuilt), path)
    print(f"signed {len(unsigned)} file(s) inside {path.name}")
    return True


def sign(args):
    tools_dir = os.environ.get("FORMCOMPILER_SIGNING_TOOLS", "").strip()
    if not tools_dir or not configured(os.environ):
        print("Artifact Signing not set: nothing to sign")
        return
    tools = Path(tools_dir)
    signtool = tools / "signtool" / "signtool.exe"
    args_list = sign_args(tools)
    patterns = [p.strip() for p in re.split(r"[\n,]+", args.artifacts) if p.strip()] or DEFAULT_ARTIFACTS
    files = sorted({Path(f).resolve() for p in patterns for f in glob.glob(p, recursive=True) if Path(f).is_file()})
    signed, kept = 0, 0
    for path in files:
        name = path.name.lower()
        if name.endswith(".zip"):
            if sign_zip(args_list, signtool, path):
                signed += 1
                resign_updater(path)
            continue
        if not name.endswith((".exe", ".msi")):
            continue
        if is_signed(signtool, path):
            kept += 1
            continue
        sign_file(args_list, path)
        if not is_signed(signtool, path):
            fail(f"{path.name} does not verify after signing")
        signed += 1
        print(f"signed {path.name}")
        resign_updater(path)
    print(f"Windows files: {signed} signed now, {kept} already signed during the build")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--app-dir", default=".")
    p.add_argument("--tools", required=True)
    s = sub.add_parser("sign")
    s.add_argument("--artifacts", default="")
    args = parser.parse_args()
    {"prepare": prepare, "sign": sign}[args.command](args)


if __name__ == "__main__":
    main()
