<p align="center">
  <img src="assets/app-icon/formcompiler-256.png" width="128" height="128" alt="FormCompiler icon: the Form family app icon">
</p>

<h1 align="center">FormCompiler</h1>

<p align="center">
  <b>Build and release; where every Form app is built, signed and shipped.</b><br>
  Push a compile branch, get a draft release on every platform,<br>
  plus the signed catalogue FormPortal reads. GitHub Actions and Python.
</p>

<p align="center">
  <img alt="version v0.12.2" src="https://img.shields.io/badge/version-v0.12.2-eef0f4?style=flat-square">
  <img alt="GitHub Actions" src="https://img.shields.io/badge/GitHub_Actions-watch_%C2%B7_release-2088FF?style=flat-square&logo=githubactions&logoColor=white">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Builds for macOS, Windows and Linux" src="https://img.shields.io/badge/builds-macOS_%C2%B7_Windows_%C2%B7_Linux-2f7bf5?style=flat-square">
  <img alt="License: GPL-3.0-only" src="https://img.shields.io/badge/license-GPL--3.0--only-3a3a3a?style=flat-square">
  <img alt="Status: in use" src="https://img.shields.io/badge/status-in_use-d69e2e?style=flat-square">
</p>

<p align="center">
  <a href="https://formcompiler.formai.studio/"><b>FormCompiler on formai.studio</b></a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="#run-it-from-source">Run it from source</a>
</p>

<br>

<p align="center">
  <img src="docs/images/formcompiler-hero.png" alt="Terminal running the registry check, the app list and the catalogue listing of FormCompiler" width="100%">
  <br>
  <sub>The registry check passing for 26 apps, and the three apps the catalogue lists today.</sub>
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#everything-in-the-box">In the box</a> ·
  <a href="#under-the-hood">Under the hood</a> ·
  <a href="#where-releases-come-from">Releases</a> ·
  <a href="#run-it-from-source">Run from source</a>
</p>

<br>

<table>
  <tr>
    <td width="25%" valign="top">
      <h3>One place</h3>
      Every Form app is built, signed and released here; the app repositories only run their checks.
    </td>
    <td width="25%" valign="top">
      <h3>Push to release</h3>
      Push <code>compile_vX.Y.Z</code> from main, or a tag, and get a draft release on every platform the app lists.
    </td>
    <td width="25%" valign="top">
      <h3>Checked first</h3>
      Branch, commit, version and the app's own checks must pass before anything builds.
    </td>
    <td width="25%" valign="top">
      <h3>Signed in one place</h3>
      Apple, Windows and updater keys are FormCompiler secrets; no app repository holds one.
    </td>
  </tr>
</table>

<br>

## Features

- **No secrets in the apps.** FormCompiler watches the app repositories itself, so no app holds a token for it.
- **Checked before it builds.** The ref name, the commit on main, a version above the highest published one, the version file and the app's check workflows.
- **Drafts, never surprises.** A stable release is a draft a person publishes; a published release is never overwritten.
- **Betas publish themselves.** A prerelease version becomes a GitHub prerelease once its builds pass.
- **Yank, never delete.** A version in `yanked.json` leaves the catalogue; its files stay in place.
- **Skills in every release.** Each release carries `form-app.json` and a reproducible `<app>-skills-v<version>.zip`.
- **Pinned actions.** Every third-party action is pinned to a full commit SHA.

## Everything in the box

<table>
  <tr>
    <td width="33%" valign="top">
      <h4>26 registered apps</h4>
      One <code>apps/&lt;app&gt;.json</code> each: version source · checks · platforms · toolchain · build commands · extra jobs · assets · update files · catalogue entry
    </td>
    <td width="33%" valign="top">
      <h4>4 workflows</h4>
      watch · release · desktop-release · self-check
    </td>
    <td width="33%" valign="top">
      <h4>Platforms</h4>
      macos-arm64 · macos-x64 · linux-x64 · linux-arm64 · windows-x64 · windows-arm64 · plus phone apps, tarballs, Flatpak, servers and a container image per app
    </td>
  </tr>
</table>

## Under the hood

- **Language:** 19 Python scripts on the standard library; `cryptography` only signs the catalogue.
- **Contract:** [`docs/REGISTRY.md`](docs/REGISTRY.md) defines the registry file every app writes.
- **Flow:** `watch.yml` runs hourly (`17 * * * *` UTC) or on demand, `release.yml` gates and builds, and a draft `vX.Y.Z` opens on the app's own repository.
- **Channels:** `X.Y.Z` is stable; anything with `-beta.N` or `-rc.N` is beta and never touches `<app>-updates`.
- **Publishing:** the download store, update feeds, catalogue signature and yanks run in a private companion pipeline.
- **Tested:** 364 tests in 15 files (registry, versions, watch, triggers, tauri config, signing, app repository releases, GitHub binaries, workflow guards).

## Where releases come from

FormCompiler builds and signs every Form app and drafts each release on the app's own repository, tagged `vX.Y.Z` at the gated commit. It is the factory and the gate and keeps no app release itself. Users install them with FormPortal or from each app's page on formai.studio.

```
app repo: bump version, push compile_v1.96.5 from main (or tag v1.96.5)
  -> watch.yml: refuse a bad ref or failed check, else start release.yml
  -> release.yml: desktop, extras, image, then draft v1.96.5 on the app's repository
  -> publishing pipeline (private): catalogue, update feeds, download store
```

Public files are served from https://dl.formai.studio as `<app>/<version>/<file>`, with the catalogue at `catalog/apps.json` and `catalog/apps.json.sig`.

## Run it from source

FormCompiler has no UI and no app to install. Run its scripts to check the registry or see what the watch would start.

**Requires:** Python 3.11+ and git. `watch.py --dry-run` also needs a `GH_TOKEN`.

```sh
git clone git@github.com:nodemode-dev/formcompiler.git
cd formcompiler
python3 scripts/registry.py check     # validate every registry file
python3 scripts/catalog.py listed     # apps and versions in releases.json
python3 scripts/watch.py --dry-run    # what the watch would start (needs GH_TOKEN)
```

To release an app, run this in its repository after the version bump is on main, then publish the draft that appears on the app's own Releases page:

```sh
git push origin main:refs/heads/compile_v1.96.5
```

If a release run fails for a runner reason, use **Re-run failed jobs** in Actions, never **Re-run all jobs**.

Secrets (`FORMCOMPILER_APP_TOKEN`, `APPLE_*`, `AZURE_*`, `TAURI_SIGNING_PRIVATE_KEY`, `FORMPIPE_DISPATCH_TOKEN`) are all optional; without them macOS builds are signed ad hoc and Windows builds are unsigned.

> [!IMPORTANT]
> **Status:** in use. It builds the 13 launch apps; the catalogue lists each app once its release is published. See [`CHANGELOG.md`](CHANGELOG.md).

**Contributing:** branch from `main`, keep changes to the registry and scripts here, and leave app code to the app repositories. Packaging and releases live in FormCompiler. See [`AGENTS.md`](AGENTS.md).

## Repository

| Path | What it is |
|---|---|
| `apps/` | One registry file per app |
| `scripts/` | The Python scripts the workflows run |
| `.github/workflows/` | watch, release, desktop-release, self-check |
| `docs/`, `tests/` | Registry contract and accounts notes; the pytest suite |
| `releases.json`, `yanked.json` | The catalogue and the versions left out of it |

Docs: [`docs/REGISTRY.md`](docs/REGISTRY.md), [`SECURITY.md`](SECURITY.md) · Agents: [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md)

---

## Maintainers

| Maintainer | Role |
|---|---|
| [@nodemode-ai](https://github.com/nodemode-ai) | Owner |
| [@gbarnai](https://github.com/gbarnai) | Co-owner |

Code owners are set in [`.github/CODEOWNERS`](.github/CODEOWNERS).

## License

FormCompiler is licensed under the GNU General Public License v3.0 only ([`LICENSE`](LICENSE), SPDX `GPL-3.0-only`). Copyright 2026 NodeAgentc, Inc. Third-party notices: [`NOTICE`](NOTICE).
