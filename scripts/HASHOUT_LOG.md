# HASHOUT_LOG · pipeline · formcompiler

Living log of all comment content, explainers, rationale, TODOs and removed code for the pipeline (the scripts, the workflows and the caller template). The source files stay comment-free per dev-rules `sub-skills/hashout-log/SUB-SKILL.md`; everything they would have said lives here, indexed. Read this first, then edit code surgically.

Current build version: v0.8.0
Last updated: 2026-11-03 · the private publishing pipeline (v0.8.0); 2026-11-03 · release file names (v0.7.1); 2026-11-03 · build minutes: hourly watch, 49-minute jobs, per-app Rust cache, macOS pip wheel cache, notarization in parallel, FormPortal's installers (v0.7.0); 2026-11-02 · formnet is formNET (v0.6.9); 2026-11-02 · formnet registered (v0.6.8); 2026-11-02 · the watch sees drafts (v0.6.7); 2026-11-02 · Git Bash, the MSVC linker and staple retries (v0.6.6); 2026-11-02 · no globstar on macOS (v0.6.5); 2026-11-02 · the build step stops setting TAURI_CONFIG (v0.6.4); 2026-11-02 · command builds get the Tauri settings, beta MSI versions (v0.6.3); 2026-11-02 · FormPortal's notes name the store's update feed (v0.6.2); 2026-10-30 · the move to the nodemode-dev organisation (v0.6.1); 2026-10-30 · the build keychain, disk image signing and the family registry fixes (v0.6.0); 2026-10-28 · the download store, tag triggers, betas and yanks (unreleased); 2026-10-28 · the watch fails when the app token cannot read, feed.yml SC2012 (unreleased); 2026-10-26 · the test suite (tests/, v0.4.8); 2026-10-25 · FormPortal optional in the bundle README (v0.4.7); app-plus-FormPortal downloads (v0.4.6); catalogue history keeps every earlier major line (v0.4.2); form-app.json v2 and the skills archive (v0.4.0); copyright holder NodeAgentc, Inc. (v0.3.3, no script changed); formencoder's LAME source and delivery tools list (v0.3.2); macOS opencv without FFmpeg, LGPL PyAV for Format and formcut (v0.3.1)

---

## v0.8.0 · the private publishing pipeline {#v0.8.0-split}

The owners decided on 2026-11-03 that formcompiler goes public and that everything about the cloud side of the download store stays private. Publishing to the store, the `<app>-updates` feeds, the catalogue signature and yanks move to a private companion repository, nodemode-dev/formpipe; formcompiler keeps the build, the signing of the apps, the drafts, the registry and every script, which formpipe checks out from here at run time. This repository starts a fresh history at v0.8.0; the entries below are its log up to then, with the cloud identifiers replaced by neutral words.

### release.yml · publish mode tells formpipe
- refers-to: .github/workflows/release.yml :: assemble :: Publish
- kind: decision
- logged: v0.8.0 · 2026-11-03

`gh workflow run feed.yml` became `POST repos/nodemode-dev/formpipe/dispatches` with `event_type` `formcompiler-published` and `client_payload.tag`, using the secret `FORMPIPE_DISPATCH_TOKEN` (fine-grained, on formpipe only, Contents read and write: the permission GitHub lists for that endpoint). `github.token` cannot reach another repository, and the job no longer needs `actions: write`. The JSON body is built by Python from `$TAG` and piped to `gh api --input -`, so the tag is never spliced into JSON by the shell. With the secret empty the step writes a notice and succeeds; a failed dispatch is a warning, not a failure, because the release is already published and a rerun would fail at the draft step. formpipe's hourly run finds every release published since its last catalogue, so both cases are picked up within the hour. A stable release a person publishes by hand sends no dispatch either; the hourly run is its path.

### removed · feed.yml, yank.yml, docs/GO_PUBLIC.md
- refers-to: .github/workflows/; docs/
- kind: decision
- logged: v0.8.0 · 2026-11-03

Both workflows and the owner checklist named the store's cloud project, bucket, service account and federation path. They live in formpipe now. scripts/feed.py, scripts/yank.py, scripts/catalog.py and scripts/public_urls.py stay here: formpipe runs them from a checkout of this repository's main. `releases.json` and `yanked.json` stay on main and change only through pull requests formpipe opens. The `release` environment and the catalogue key are no longer used by any workflow here.

---

## v0.7.1 · release file names {#v0.7.1-file-names}

The owner chose one naming rule for every downloaded file on 2026-11-03: the app, the version, the operating system and the processor in the name. Before, one FormTray release used four words for the processor (`arm64`, `x86_64`, `x64`, `amd64`) and only the extension told the operating system.

### stage.py · release_name
- refers-to: scripts/stage.py :: release_name, KINDS
- kind: decision
- logged: v0.7.1 · 2026-11-03

`<app>-<version>-<platform><suffix>`. `<app>` is the registry app name, the same as the tag prefix (`formtray-v0.9.8` gives `formtray-0.9.8-...`), so the store path, the tag and the file agree. `<platform>` is the plan's platform name (`macos-arm64`, `linux-x64`, `windows-x64`), the same words the registry uses. KINDS is checked in order, longest suffix first where two overlap (`.app.tar.gz` before `.tar.gz`, `.AppImage.zsync` before `.AppImage`). A `.sig` takes the name of the file it signs plus `.sig`. A file of no listed kind, such as `delivery-tools-PLATFORM.txt` or `formdesign-core-*`, keeps its name. An NSIS installer keeps `-setup.exe` because catalog.py and the site read `setup` to tell it from other executables. One platform making two files of the same kind fails the stage step through the existing "two files would both be staged" check.

### stage.py · app_name
- refers-to: scripts/stage.py :: app_name
- kind: compatibility
- logged: v0.7.1 · 2026-11-03

The old rule, unchanged: on macOS a bare `<App>.app.tar.gz` gains `_<arch>`. Used when the registry sets `file_names: app`. formvis needs it: its assets step builds latest.json from `*_aarch64.app.tar.gz`, `*amd64.AppImage` and `*x64-setup.exe`, and its AppImage update information names `formvis_*_ARCH.AppImage.zsync`. FormPortal names its own files (`formportal-<version>-<os>-<arch>...`) and writes manifests that list them. Either can move to `formcompiler` names once its own scripts read the new names.

### consumers
- refers-to: scripts/catalog.py :: classify; formai.tools site/backend/app/release.py :: kind_of, arch_of, platform_of; formportal core/src/deploy.rs
- kind: check
- logged: v0.7.1 · 2026-11-03

catalog.py and the site read the processor from the `arm64` or `x64` token and the kind from the extension, so the new names classify the same as before (tests/test_file_names.py; the site's functions were run on the same names). FormPortal installs from the catalogue's platform, arch and kind fields and tells an installer by its extension. Tauri's updater reads the URL in latest.json, which release_assets.py writes from the staged names. Files already released keep their names: the catalogue, the store and installed copies point at them.

---

## v0.7.0 · build minutes {#v0.7.0-minutes}

The owner's usage page for 2026-11-02 showed 509 macOS, 737 Linux and 319 Windows minutes in one day ($39.72 gross at private-repository rates), part of it from the watch's restart loops fixed in v0.6.7 and v0.6.9 (form.md 0.47.7 and formcut 2.11.2 were rebuilt that way that day). formcompiler goes public on 2026-11-04, after which standard GitHub-hosted runners, macOS included, are not billed (docs.github.com, Actions billing). These changes keep the runs short anyway; the Intel macOS builds stay as they are, by the owner's choice of 2026-11-03.

### watch.yml · every hour
- refers-to: .github/workflows/watch.yml :: schedule
- kind: decision
- logged: v0.7.0 · 2026-11-03

`*/15 * * * *` became `17 * * * *`: 24 runs a day instead of 96, each at least one billed Linux minute on a private repository. Minute 17 keeps the run off the top of the hour, when GitHub's scheduler is busiest and scheduled runs start late. Run workflow still starts a watch at once. The owner may change the interval later; the README and the "every 15 minutes" entries below are history.

### release.yml, desktop-release.yml · 49-minute jobs
- refers-to: .github/workflows/desktop-release.yml :: build `timeout-minutes` · .github/workflows/release.yml :: extras, image `timeout-minutes`
- kind: decision
- logged: v0.7.0 · 2026-11-03

The desktop build and the extras had 150 minutes and the container image 60, so a hung step held a macOS runner for two and a half hours. All three are 49, the owner's number. The 10- and 30-minute jobs are unchanged. Risk: a cold macOS build that compiles opencv from source (formDAM, formlit, formvis, formpdf, formtxt) or LGPL FFmpeg (Format, formcut) may need longer the first time, before the caches below hold anything. So the Build step itself stops at 40 minutes: a step timeout fails the step without cancelling the job, the remaining 9 minutes let the caches save (rust-cache with `cache-on-failure: true`; the pip wheels through `actions/cache/save` under `if: always()`, since `actions/cache` saves only after a successful job), and Re-run failed jobs then starts from what was built. Found in review: with the job timeout alone, a cold build that timed out saved nothing and every re-run timed out the same way.

### desktop-release.yml · the Rust cache is per app
- refers-to: .github/workflows/desktop-release.yml :: Swatinem/rust-cache `key`
- kind: fix
- logged: v0.7.0 · 2026-11-03

The key was `formcompiler-<platform>`, the same for every app. rust-cache's exact key adds a hash of the Cargo.lock and Cargo.toml files, so it always misses on a new version (the app's own version is in its lock file), and its one fallback is the prefix without that hash, which was the same for all 26 apps: a formtray build could restore formportal's target directory, download gigabytes, clean them and save its own, pushing a third app's cache out of the repository's 10 GB (Swatinem/rust-cache `src/config.ts` and `src/restore.ts`; docs.github.com dependency caching). The key is now `formcompiler-<app>-<platform>`, so the fallback is the same app's previous release. Limits that remain: GitHub drops a cache not read for 7 days, so an app released less often than weekly still builds cold; the 10 GB can be raised on a paid plan (pay as you go, changelog 2025-11-20). A persistent alternative, sccache on the download store's Google Cloud bucket, is not built.

### desktop-release.yml, registry.py · pip's wheel cache on macOS
- refers-to: .github/workflows/desktop-release.yml :: input `pip-cache-macos`, steps "pip wheel cache key", "pip wheel cache" · scripts/registry.py :: TOOLCHAIN `pip_cache_macos`, config · apps/formDAM.json, formlit.json, formvis.json, formpdf.json, formtxt.json · docs/REGISTRY.md
- kind: decision
- logged: v0.7.0 · 2026-11-03

The five apps whose `setup.macos` sets `PIP_NO_BINARY=opencv-python,opencv-python-headless` (v0.3.1, for an opencv without FFmpeg) compile OpenCV on every macOS build. With `pip_cache_macos` the build sets `PIP_CACHE_DIR` under the runner's temp folder and caches its `wheels` folder, where pip keeps the wheels it builds. pip 23.1 stopped `--no-binary` from disabling that cache (pip changelog, #11453); run here with pip 26.2.2, a `PIP_NO_BINARY` package built from an sdist once and was "Using cached" on the second install into a fresh venv. The cache is restored with `actions/cache/restore` before the build and saved with `actions/cache/save` right after it, also when the build failed, unless the exact key was already restored. The key is app, platform, Python version, a hash of `setup.macos` (so a change to `CMAKE_ARGS` builds again: pip's cache does not see environment variables) and a hash of the app's `requirements*.txt`, `constraints*.txt` and `pyproject.toml`. The fallback restores only the same app, platform, Python and set-up, and pip reuses a cached wheel only for the same package version, so what the app uses has to be unchanged for the wheel to be reused, as the owner asked. Only the wheels folder is cached, not pip's download cache, to stay small. Untested in Actions: an app whose install passes `--no-cache-dir`, or installs with uv, gets nothing from it.

### desktop-release.yml · notarization in parallel, and the dmg the app copies
- refers-to: .github/workflows/desktop-release.yml :: "Notarize the macOS disk images"
- kind: decision
- logged: v0.7.0 · 2026-11-03

Each disk image was submitted with `notarytool submit --wait`, one after another, so a job with two disk images waited for Apple twice in a row. The step now signs and submits every disk image first (`--output-format json`, the id kept in `$RUNNER_TEMP/formcompiler-notarize.tsv`), then waits on each (`notarytool wait`), reads its status with `notarytool info`, prints `notarytool log` and stops when it is not `Accepted`, and staples it with the same five tries. Apple works on all of them at once while the job waits. The second loop reads the list on file descriptor 4, not stdin, so a tool inside it that reads stdin cannot swallow the remaining lines. The step also notarizes the disk images the registry's `artifacts` globs match: FormPortal's post-build copies its dmg into `release-dist` before this step runs, so the published copy was never stapled. Fix found while simulating the step with stubbed `xcrun` and `codesign`: under `bash -eo pipefail` the first `find` in the list exits 1 when one of its folders is missing (`target` usually is), errexit ends the process substitution there, and the second `find` (`src-tauri/target.nosync`) never ran; each command now ends with `|| true`. Not run on a macOS runner.

### watch.py · Re-run failed jobs
- refers-to: scripts/watch.py :: watch_app · README.md :: Quick Start
- kind: decision
- logged: v0.7.0 · 2026-11-03

The watch's message for a failed or cancelled run said "re-run it in Actions"; it now names Re-run failed jobs, and the README says why: Re-run all jobs builds every platform again, including the macOS ones that already succeeded.

### apps/formportal.json · FormPortal ships its installers
- refers-to: apps/formportal.json :: notes_for_owner
- kind: rationale
- logged: v0.7.0 · 2026-11-03

From formportal 0.54.0 `setup/package_release.py` copies the dmg, the NSIS setup, the AppImage, the deb and the rpm into `release-dist` instead of zipping them; on Linux and Windows latest.json points at the installer, which is the updater bundle, and only macOS keeps a `-update.app.tar.gz`. `catalog.py classify` already reads all of these names; no script changed for it. `artifacts` stays `release-dist/*`.

---

## v0.6.9 · formnet is formNET {#v0.6.9-formnet-name}

### registry · apps/formNET.json notes_for_owner
- refers-to: apps/formNET.json :: notes_for_owner
- kind: rationale
- logged: v0.6.9 · 2026-11-02

The owner chose the repository's spelling, formNET, over the app's lower-case name on 2026-11-02, so the registry app, title, tag prefix and store path became formNET before any release existed. The CLI binary stays `formnet` and the catalogue id stays `formnet`, the same split formMCP has (app formMCP, cli formmcp, id formmcp). Tags are therefore `formNET-vX.Y.Z` and the store path `formNET/<version>/`.
Last updated: 2026-11-02 · no retry loop, drafts target main (v0.6.9); 2026-11-02 · formnet registered (v0.6.8); 2026-11-02 · the watch sees drafts (v0.6.7); 2026-11-02 · Git Bash, the MSVC linker and staple retries (v0.6.6); 2026-11-02 · no globstar on macOS (v0.6.5); 2026-11-02 · the build step stops setting TAURI_CONFIG (v0.6.4); 2026-11-02 · command builds get the Tauri settings, beta MSI versions (v0.6.3); 2026-11-02 · FormPortal's notes name the store's update feed (v0.6.2); 2026-10-30 · the move to the nodemode-dev organisation (v0.6.1); 2026-10-30 · the build keychain, disk image signing and the family registry fixes (v0.6.0); 2026-10-28 · the download store, tag triggers, betas and yanks (unreleased); 2026-10-28 · the watch fails when the app token cannot read, feed.yml SC2012 (unreleased); 2026-10-26 · the test suite (tests/, v0.4.8); 2026-10-25 · FormPortal optional in the bundle README (v0.4.7); app-plus-FormPortal downloads (v0.4.6); catalogue history keeps every earlier major line (v0.4.2); form-app.json v2 and the skills archive (v0.4.0); copyright holder NodeAgentc, Inc. (v0.3.3, no script changed); formencoder's LAME source and delivery tools list (v0.3.2); macOS opencv without FFmpeg, LGPL PyAV for Format and formcut (v0.3.1)

---

## v0.6.9 · no retry loop, drafts target main {#v0.6.9-retry-and-target}

### scripts/watch.py · watch_app; scripts/github_api.py · stopped_release_runs
- refers-to: scripts/watch.py :: watch_app; scripts/github_api.py :: stopped_release_runs
- kind: rationale
- logged: v0.6.9 · 2026-11-02

A release run that fails or is cancelled leaves no draft, so `readiness.evaluate` found the ref ready again and the watch dispatched the same build on its next tick, every 15 minutes, until someone fixed the app or deleted the branch: formcut 2.11.2's Windows failure was rebuilt this way on 2026-11-02, about 40 runner minutes a round. The watch now lists release.yml runs that ended in failure or cancelled (the newest 100 of each) and skips a ref whose run title, `<app> <version> at <sha>`, is among them. A failure caused by formcompiler rather than the app is retried by re-running that run in Actions (a successful re-run changes its conclusion) or by dispatching release.yml by hand; gate.py is unchanged, so a manual dispatch is never refused for an earlier failure. A run still in progress was already skipped through `active_release_runs`.

### .github/workflows/release.yml · Create or refresh the draft
- refers-to: .github/workflows/release.yml :: assemble, Create or refresh the draft
- kind: rationale
- logged: v0.6.9 · 2026-11-02

The draft was created with `--target "$GITHUB_SHA"`, the formcompiler commit the release run started on. GitHub refuses the Actions token a release (and so the tag publishing makes) at a commit whose `.github/workflows` differ from the default branch, because that token can never hold the `workflows` permission; the API answers 403 "Resource not accessible by integration". formportal 0.53.5's draft was created at 19:41:53 and v0.6.7 (a watch.yml change) merged at 19:42:37; formencoder 0.5.1, started on the same commit as formportal, failed at 19:48 and again on a re-run. Drafts now target `main`, as feed.yml's feed and catalogue releases already did. Nothing reads a release's target; the app commit is in the body's `formcompiler-source` marker. A test fails if a workflow targets `$GITHUB_SHA` again.

---

## v0.6.8 · formnet registered {#v0.6.8-formnet}

### registry · apps/formnet.json notes_for_owner
- refers-to: apps/formnet.json :: notes_for_owner
- kind: rationale
- logged: v0.6.8 · 2026-11-02

formnet is registered the way form.md is: one Go binary with the web client embedded, a Tauri 2 window around it built by the app's own `build_app` and `build_app.bat`, and a `server` extra for the five static binaries from `make release`. The repository is `nodemode-dev/formNET` (capitals like formMCP and formDAM) while the app, its CLI, its tag prefix and its catalogue id are `formnet`, the name the app gives itself; GitHub resolves either spelling. The extra's `go` is `1.26` because formnet's go.mod names the minor only. No updater key: `tag_json` writes `formnet-updates/latest.json` for a later update check. The `src-tauri` shell has never been compiled; the first formcompiler build is its first compile, which the owner's notes say.

---

## v0.6.7 · the watch sees drafts {#v0.6.7-watch-drafts}

### .github/workflows/watch.yml · permissions
- refers-to: .github/workflows/watch.yml :: permissions.contents
- kind: rationale
- logged: v0.6.7 · 2026-11-02

`readiness.evaluate` skips a ref whose release is already drafted from the same commit, or superseded by a newer draft, by reading the release list. GitHub returns draft releases only to a token with push access, and the watch ran with `contents: read`, so it saw no drafts at all: on 2026-11-02 a dispatched watch restarted form.md 0.47.7 although its draft (marker `formcompiler-source: nodemode-dev/form.md@526dbd98b...`) was waiting for publish, and the 15-minute schedule would have rebuilt it every tick until someone published. The watch's token now has `contents: write`. It writes nothing: the job only reads the registry, the app repositories and the release list and dispatches release.yml, the checkout keeps no credentials, and the job runs only in nodemode-dev/formcompiler on a schedule or a maintainer's dispatch, never on a pull request. A test fails if the permission goes back to read.

---

## v0.6.6 · Git Bash, the MSVC linker and staple retries {#v0.6.6-wave-one}

### scripts/run_build.py · windows_bash, msvc_linkers
- refers-to: scripts/run_build.py :: windows_bash; scripts/run_build.py :: msvc_linkers
- kind: rationale
- logged: v0.6.6 · 2026-11-02

The first wave of family releases (formcut, form.md, formdeck, formencoder, formportal, 2026-11-02) showed two Windows faults in run_build.py. First, a bash build or post-build step ran `subprocess.run(["bash", ...])`; Windows looks in System32 before PATH, and `C:\Windows\System32\bash.exe` is the WSL launcher, so formcut's build and formportal's post-build packaging stopped with "Windows Subsystem for Linux has no installed distributions". `windows_bash` takes the first `bash.exe` on PATH outside System32 and the WindowsApps aliases, which on the runners is Git's, and the build fails plainly if there is none. Second, the Build step runs under Git Bash, whose PATH puts `C:\Program Files\Git\usr\bin` (with coreutils' `link.exe`) before Visual Studio's folders; with `VCINSTALLDIR` set, a Rust build looks for `link.exe` on PATH, and formencoder's pip build of pywinpty (no wheel for the Python it picked) linked with Git's and failed. Reordering PATH would break bash scripts that rely on Git's coreutils, so `msvc_linkers` reads the MSVC `bin\Host<arch>\<arch>` folder msvc-dev-cmd put on PATH and sets `CARGO_TARGET_<TRIPLE>_PC_WINDOWS_MSVC_LINKER` for each target whose `link.exe` exists there (x64, arm64, x86); a value the app sets itself is kept.

### .github/workflows/desktop-release.yml · Notarize the macOS disk images
- refers-to: .github/workflows/desktop-release.yml :: Notarize the macOS disk images
- kind: rationale
- logged: v0.6.6 · 2026-11-02

formdeck's and formportal's Intel builds were notarized, then `stapler staple` or `stapler validate` lost its connection to Apple's ticket service (NSURLErrorDomain -1005, exit 68) and the build failed. Staple and validate now run together up to five times, 20, 40, 60 and 80 seconds apart; notarization itself is not repeated.

### apps/formdeck.json · flatpak extra
- refers-to: apps/formdeck.json :: extras.flatpak.linux_packages
- kind: rationale
- logged: v0.6.6 · 2026-11-02

flatpak-builder strips the bundled binaries with `eu-strip` from the host, which the Ubuntu runner does not have until `elfutils` is installed.

---

## v0.6.5 · no globstar on macOS {#v0.6.5-macos-bash}

### .github/workflows/desktop-release.yml · Notarize the macOS disk images; release.yml · Collect
- refers-to: .github/workflows/desktop-release.yml :: Notarize the macOS disk images; .github/workflows/release.yml :: extra Collect
- kind: rationale
- logged: v0.6.5 · 2026-11-02

GitHub's macOS runners run steps in /bin/bash, which is 3.2 and has no `globstar` option, so `shopt -s nullglob globstar` stopped the notarize step with "invalid shell option name" on both macOS builds of formtray's run 41473779877, after the app had built and signed. The step now lists disk images with `find`: those under a `bundle` folder in `src-tauri/target` and `target`, and any under `src-tauri/target.nosync` (formDAM), the same set the globs matched, deduplicated by real path as before. The loop reads the list on descriptor 3 so `codesign` and `notarytool` cannot swallow it from stdin. The extras' Collect step matched each registry pattern with globstar and can run on a macOS runner too, so it now expands the pattern with Python's `glob(recursive=True)`, which gives `**` the meaning globstar did. A test fails if any workflow uses globstar again.

---

## v0.6.4 · the build step stops setting TAURI_CONFIG {#v0.6.4-tauri-config-env}

### .github/workflows/desktop-release.yml · Build env; scripts/run_build.py · without_empty_tauri_config
- refers-to: .github/workflows/desktop-release.yml :: FORMCOMPILER_EXTRA_CONFIG; scripts/run_build.py :: without_empty_tauri_config
- kind: rationale
- logged: v0.6.4 · 2026-11-02

The Build step passed the registry's extra Tauri settings to run_build.py through an environment variable named `TAURI_CONFIG`. tauri-build reads that same variable (`cargo:rerun-if-env-changed=TAURI_CONFIG`) and parses it as JSON, so an app with no extra settings got an empty string and its build script stopped with "EOF while parsing a value at line 1 column 0". Contract builds hid it, because the Tauri CLI overwrites `TAURI_CONFIG` from `--config`; a build run by the app's own script does not pass `--config`, so formtray's first release (run 41472022890) failed on macOS and Linux this way, and every command-mode app would have. The variable is now `FORMCOMPILER_EXTRA_CONFIG`, and run_build.py drops an empty `TAURI_CONFIG` before the build in case a runner or a caller sets one; a non-empty one is left for Tauri. A test fails if the workflow sets `TAURI_CONFIG` again.

---

## v0.6.3 · command builds get the Tauri settings, beta MSI versions {#v0.6.3-platform-config}

### scripts/tauri_config.py · write_platform_configs, msi_version
- refers-to: scripts/tauri_config.py :: write_platform_configs, msi_version; scripts/run_build.py :: main
- kind: rationale
- logged: v0.6.3 · 2026-11-02

formcompiler's Tauri settings (the updater's key and the store's update address, `createUpdaterArtifacts`, the ad hoc macOS identity, now the MSI version) went to a file passed as `--config`, and a build saw them only when its command used `$FORMCOMPILER_CONFIG_ARG`. Contract builds do; 16 apps build with their own scripts, and none of format, formencoder, formlit, formportal, formsurface or formvfx, the command-mode apps with `updater.tauri: true`, passed it, so their release builds would have shipped with no updater key and no update feed. `TAURI_CONFIG` in the environment is not a fix: the Tauri CLI sets that variable itself from `--config` for tauri-build, so the bundler never reads one set from outside. Tauri does read `tauri.<platform>.conf.json` beside `tauri.conf.json` for every build, so the build phase now merges the settings into that file in each Tauri app the checkout holds (found the way windows_signing.py finds them; the Windows signing step already writes `tauri.windows.conf.json` the same way, and the merge keeps its `signCommand`). An app keeping its platform config in TOML or JSON5 is left alone with a warning, as windows_signing.py does. Contract builds still get `--config` as well; the values are the same.

Windows Installer versions are numeric (`major.minor.build.revision`), and Tauri refuses an app version whose prerelease part is not numeric for the MSI target, so `0.9.8-beta.1` failed the MSI step. A prerelease now builds with `bundle.windows.wix.version` set to `X.Y.Z.N`, N being the prerelease's trailing number (0 without one, capped at 65535). Tauri's MSI allows downgrades, so the stable `X.Y.Z` (MSI `X.Y.Z.0`) still installs over a beta. Stable builds and other platforms are unchanged.

---

## v0.6.2 · FormPortal's notes name the store's update feed {#v0.6.2-formportal-notes}

### registry · apps/formportal.json notes_for_owner
- refers-to: apps/formportal.json :: notes_for_owner
- kind: rationale
- logged: v0.6.2 · 2026-11-02

formportal 0.53.5 reads its updates from `https://dl.formai.studio/formportal/updates/latest.json` and its `package_release.py --finish` writes platform URLs as `https://dl.formai.studio/formportal/<version>/<file>`, the store's layout, because this repository is private and its `formportal-updates` release never served an installed copy. The notes said the endpoint was that GitHub release; they now name the store's address, say that `feed.py public` leaves the store URLs unchanged (it rewrites GitHub release URLs only), and that the feed copies FormPortal's `latest.json` to the store as well as to `formportal-updates`. Notes only: no field the pipeline reads changed.

---

## v0.6.1 · the family moves to the nodemode-dev organisation {#v0.6.1-org-move}

- now: every `nodemode-ai/<repo>` in the workflows, scripts, tests, registry and docs is `nodemode-dev/<repo>`, and the images are `ghcr.io/nodemode-dev/<app>`. The four job guards (`watch`, `release`, `feed`, `yank`) compare `github.repository` with `nodemode-dev/formcompiler`, so this commit has to land right after the transfer: merged earlier, every job skips without an error; left out after it, the same happens the other way. GitHub's redirects from the old paths keep git and web links working, but the guards compare the exact string. CODEOWNERS and the commit identity (`nodemode-ai <mackin@nodemode.ai>`) name the owner's personal account, which stays, so they are unchanged. The cloud deploy condition in formai.tools pins the repository path and the owner id; the organisation's id is 350427207.
- not changed: CHANGELOG and this log's older entries, which record what was true then.
Last updated: 2026-10-31 · the media apps' Linux runners install GStreamer's base and good plugins (v0.6.1); 2026-10-30 · the build keychain, disk image signing and the family registry fixes (v0.6.0); 2026-10-28 · the download store, tag triggers, betas and yanks (unreleased); 2026-10-28 · the watch fails when the app token cannot read, feed.yml SC2012 (unreleased); 2026-10-26 · the test suite (tests/, v0.4.8); 2026-10-25 · FormPortal optional in the bundle README (v0.4.7); app-plus-FormPortal downloads (v0.4.6); catalogue history keeps every earlier major line (v0.4.2); form-app.json v2 and the skills archive (v0.4.0); copyright holder NodeAgentc, Inc. (v0.3.3, no script changed); formencoder's LAME source and delivery tools list (v0.3.2); macOS opencv without FFmpeg, LGPL PyAV for Format and formcut (v0.3.1)

---

## v0.6.1 · the media apps' Linux runners install GStreamer's base and good plugins {#v0.6.1-gstreamer}

### registry · linux_packages for nine apps
- refers-to: apps/format.json, form.md.json, formcut.json, formlit.json, formpromo.json, formwav.json, formvfx.json, formref.json, formtxt.json :: toolchain.linux_packages
- kind: rationale
- logged: v0.6.1 · 2026-10-31

These nine apps play audio or video in the window and now set `bundle.linux.appimage.bundleMediaFramework`, which copies GStreamer's plugins from the build machine into the AppImage, so their runners install `gstreamer1.0-plugins-base` and `gstreamer1.0-plugins-good`, as formdeck's entry already did. Only those two sets: libav would carry the runner's own FFmpeg into the bundle. Their deb packages recommend `gstreamer1.0-libav` instead, which the user's apt installs from the distribution. `python3 scripts/registry.py check`: 25 entries, 25 valid.

## v0.6.0 · macOS signs from a build keychain, every disk image signed and notarized, the family's builds fixed {#v0.6.0-build-keychain}

### desktop-release.yml · Apple signing keychain
- refers-to: build job steps "Apple signing keychain" (before the build), "Remove the Apple signing keychain" (last, `if: always()`); the Build step's `APPLE_CERTIFICATE`/`APPLE_CERTIFICATE_PASSWORD` gated on `env.FORMCOMPILER_KEYCHAIN == ''`; `APPLE_SIGNING_IDENTITY` in Build (when the certificate exists) and Post-build (when the keychain exists)
- why: five apps (formvis, formtxt, formpromo, formcel, formDAM) sign their PyInstaller engine w/ the Developer ID before `tauri build`, and Tauri only imports `APPLE_CERTIFICATE` inside its own build, so the identity was not in any keychain yet and those macOS builds failed once the Apple secrets were set. The step imports the .p12 into a temporary keychain (random password, masked), unlocks it for six hours, allows codesign through the partition list, puts it first on the user search list and checks the identity is there; it writes `FORMCOMPILER_KEYCHAIN` to GITHUB_ENV.
- one copy only: with the keychain in place the Build step gets no `APPLE_CERTIFICATE`, so Tauri signs from the keychain by name instead of importing a second copy; two copies of the same identity make codesign refuse it as ambiguous.
- run_build.py: `APPLE_SIGNING_IDENTITY` is its own secret group, so it survives `clean_secrets` w/o `APPLE_CERTIFICATE`. tauri_config.py: the ad hoc `signingIdentity "-"` is added only when neither the certificate nor the identity is set, so it can never compete w/ the Developer ID.
- APPLE_SIGNING_IDENTITY overrides `bundle.macOS.signingIdentity` in an app's tauri.conf.json (Tauri's environment variable reference), so apps that keep `"-"` there for local builds are still Developer ID signed here.

### desktop-release.yml · Notarize the macOS disk images
- refers-to: step "Notarize the macOS disk images"
- why: formtray, formskills, formMCP, formweb, formcel, formsurface and formDAM make their dmg w/ hdiutil, unsigned, and formDAM writes it to src-tauri/target.nosync. The step now finds every dmg under `src-tauri/target/**/bundle/**`, `target/**/bundle/**` and `src-tauri/target.nosync/**`, skips a path it has seen (the globs can overlap) or one already stapled, signs an unsigned one w/ the Developer ID and a timestamp, then notarizes and staples it. It runs only when the build keychain exists. The dedupe uses a string, not an associative array, because the macOS runner's /bin/bash is 3.2.

### registry · the family audit (2026-10-30)
- Every Windows build that ignored formcompiler's config now passes it (format, formvfx, formlit, formencoder, formranker, form.md and formportal w/ `call`), so Windows updater files exist for apps w/ `updater.tauri`.
- formdeck builds Windows under cmd (its bash build_app refuses Windows). format gets nasm and pkg-config (apt, and brew on macOS) for its FFmpeg source build. formMCP gets libdbus-1-dev. formweb builds deb, rpm and AppImage. formpdf and formsculpt use libayatana-appindicator3-dev.
- Owner notes that the app fixes made stale were rewritten; the versions they name are the ones those fixes shipped as.
- formref is enabled from FormRef 0.38.0 (the shell bundles its window and starts a frozen engine). formsurface builds windows-x64 through formsurface.bat w/ MSVC. formcut signs macOS w/ the Developer ID and releases its NSIS installer beside the zip, and gets nasm and pkg-config. formwav's MSYS2 setup refreshes the package database (`pacman -Sy`). formvis asks for macOS 14.

### tauri_config.py · updater settings only for apps with the updater
- refers-to: `build_config` :: `uses_updater`; desktop-release.yml input `updater-tauri` (default true) and Build env `FORMCOMPILER_UPDATER_TAURI`; release.yml passes `updater_tauri` from the registry
- why: with `TAURI_SIGNING_PRIVATE_KEY` set, every app got `plugins.updater` in its --config. Tauri's `generate_context!` then emits code that names `serde_json`, and formwav (no updater plugin, no serde_json dependency) failed to compile: `cannot find serde_json in the crate root`. Found by a local Linux build through run_build.py with a throwaway updater key (2026-10-30). Unset means true, so callers that pass nothing keep the old behaviour.

### registry · formvis platforms
- why: on PyPI at the pinned versions, numpy, onnxruntime, opencv-python-headless, Pillow, pillow-heif, rawpy and psd-tools have no universal2 wheel, five of them no win32 wheel, and opencv-python-headless no win_arm64 wheel, so PyInstaller cannot freeze the engine on macos-universal, windows-x86 or windows-arm64. Their platform_env entries went with them.

### tests/test_release_matrix.py · the disabled gate on a held-back copy
- why: every app is enabled now, so the registry has no disabled entry to test against. The `held_back` fixture copies scripts/ and apps/ into a temporary folder, disables the first enabled app there and checks it is neither listed nor configurable; the parametrized test on the real registry's disabled apps stays for when one is disabled again.

---

## v0.5.0 · signing names masked, Windows signed through Azure Artifact Signing {#v0.5.0-windows-signing}

### desktop-release.yml · Mask the signing names
- refers-to: build job, first step "Mask the signing names"
- why: GitHub masks a secret only as its whole value, so a line printing the name inside `APPLE_SIGNING_IDENTITY` (`Developer ID Application: <name> (<team>)`) without the rest would show it. The step derives the name and the Team ID and adds a mask for each, before any other step prints. It runs on every platform, since the Windows publisher name is the same legal name. Matters most once the repository and its logs are public (docs/GO_PUBLIC.md).

### desktop-release.yml · Windows Artifact Signing and Sign the Windows files
- refers-to: steps "Windows Artifact Signing" (before the build), "Sign the Windows files" (after Post-build, before Stage); the Build step's `AZURE_` env; secrets `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`; variables `ARTIFACT_SIGNING_ENDPOINT`, `ARTIFACT_SIGNING_ACCOUNT`, `ARTIFACT_SIGNING_PROFILE`
- why: since June 2023 the CA/Browser Forum requires code-signing keys in hardware, so a new certificate cannot be the base64 .pfx the "Windows signing certificate" step imports. Azure Artifact Signing signs from CI with no token. The .pfx step stays for a pre-2023 certificate and is skipped while `ARTIFACT_SIGNING_ACCOUNT` is set, so the two never both reach Tauri.
- gating: all three run only on Windows runners and only for `windows-signing: certificate`; macOS and Linux steps are unchanged.
- why before and after: 18 of the 25 apps build with their own commands and ignore `--config`, so the signing command cannot reach them through tauri_config.py. Tauri merges `tauri.windows.conf.json` beside `tauri.conf.json` (JSON Merge Patch) whatever starts the build, so writing it there signs the app's own exe, its sidecars and its installers during the build, and Tauri's updater `.sig` is made after that signature. The step after the build is the safety net for anything still unsigned (non-Tauri files, a TOML or JSON5 Windows config, exes inside a portable `.zip`).
- secrets in the build: the `AZURE_` values reach the Build step's environment on Windows, as the Apple and updater secrets already do on their platforms, because Tauri runs signtool during the build. run_build.py drops the group when `AZURE_CLIENT_ID` is empty.

### windows_signing.py
- refers-to: scripts/windows_signing.py `prepare`, `sign`
- packages: Microsoft.ArtifactSigning.Client 1.0.146 (2026-10-08) for the dlib and Microsoft.Windows.SDK.BuildTools 10.0.28000.2705 (2026-08-26) for signtool, both downloaded from nuget.org and checked against a pinned sha256 before use; the dlib needs .NET 8 or later, which the GitHub Windows runners carry. Microsoft licences, used on the runner only and never shipped. The x64 tools run on the windows-arm64 runner under emulation.
- metadata.json: endpoint, account and profile, with every DefaultAzureCredential source but EnvironmentCredential excluded, so the dlib signs in with the three `AZURE_` values only (Microsoft Learn, Artifact Signing signing integrations).
- signCommand: the string form Tauri's Windows signing guide documents, `%1` for the file; the tools live under `$RUNNER_TEMP`, a path without spaces. Timestamp server `http://timestamp.acs.microsoft.com`, required because the certificates live three days.
- tauri_dirs: every folder holding `tauri.conf.json`, `tauri.conf.json5` or `Tauri.toml`, skipping `node_modules`, `target`, `dist`, `build` and dot folders (the `.formcompiler` checkout among them). An existing `tauri.windows.conf.json` is merged, not replaced, and its `certificateThumbprint` is dropped so it cannot compete with `signCommand`.
- sign: a file that `signtool verify /pa` accepts is left as is. A file signed here gets its updater `.sig` made again with `@tauri-apps/cli@2.12.3 signer sign` (Authenticode changes the file's bytes); without the updater key that stops the job rather than ship a `.sig` that no longer matches. A `.zip` is rewritten with the same entries and only its unsigned `.exe` and `.dll` replaced.
- half set: settings or credentials partly set warn and leave the build unsigned instead of failing it.

### registry · formcut
- refers-to: apps/formcut.json `signing.windows`
- why: was `none`; the owner wants every app installable and signed on Windows. formcut's `setup/build_release` runs `npx tauri build` itself, which still merges the `tauri.windows.conf.json`; its `release-dist/*.zip` is covered by the zip pass. macOS stays `adhoc`, as before.

---

## unreleased · release gate hardening {#unreleased-gate-hardening}

### readiness.py · compile branches held to main
- refers-to: scripts/readiness.py `evaluate`; tests/test_triggers.py `test_a_compile_branch_on_main_is_ready`, `test_a_compile_branch_off_main_is_refused_before_the_version_is_read`
- now: a `compile_vX.Y.Z` branch's commit must be on main too (compare status `identical` or `behind`), the same as a tag. A branch cut from main's head and left there passes even after main moves on.
- why: SECURITY.md promises that only commits already on main are built and signed, and the rulesets let anyone with write access push a fast-forward to a compile branch. Before, such a push, including one that edits the app's own check workflow so it passes, was signed with the family's identities. Reverses the earlier "a branch is cut on purpose" rule; the owner may keep the old rule by dropping this commit.

### versions.py, watch.py · the version must go up within its channel
- refers-to: scripts/versions.py `highest_stable`, `above_published`; scripts/watch.py `newest_tags`; tests/test_versions.py `test_version_must_go_up_within_its_channel`; tests/test_triggers.py `test_watch_finds_a_stable_fix_behind_a_published_beta`
- now: a stable version must be above the highest published stable; a beta must be above the highest published version of any channel. With 1.5.0 and 1.6.0-beta.1 published, 1.5.1 ships and 1.5.2-beta.1 is refused.
- watch: with `tag_trigger`, the newest tag of each channel is considered, each against its own ceiling, so a published beta tag no longer hides a newer stable tag. One release run per app at a time still holds; the newer ref goes first.
- why: the earlier rule's own note said a maintenance line would need it relaxed per channel. A stable fix could not ship while any beta was out. Behaviour change for the owner; drop this commit to keep the single ceiling.

### github_api.py, watch.py · a failed lookup of running releases fails closed
- refers-to: scripts/github_api.py `active_release_runs`; scripts/watch.py `main`; tests/test_watch.py
- now: an API error while listing queued or running release runs is raised instead of skipped. The watch refuses that app for this pass (a row, a warning) and moves on; gate.py fails its run.
- why: a skipped status read as "nothing running", so a transient 502 let the watch start a second build of a ref already building.

### feed.py, feed.yml · no rollback from an older tag
- refers-to: scripts/feed.py `main` (resolve), `--repo`; .github/workflows/feed.yml step `resolve` (GH_TOKEN)
- now: resolve leaves `<app>-updates` and the store's latest.json alone when the tag is below the app's newest published stable, with a notice; the catalogue is still rebuilt.
- why: the manual run's tag input invites re-running an old release, which rewrote every installed app's update feed back to it.

### with_portal.py · a missing catalogue
- refers-to: scripts/with_portal.py `main`
- now: a 404 for the catalogue gives a notice and no app-plus-FormPortal download, like a catalogue with no FormPortal release; any other HTTP error fails the step.
- why: the catalogue URL is a GitHub release download, which 404s while formcompiler is private and before the first catalog release.

### docs/GO_PUBLIC.md · FORMCOMPILER_PUBLIC_BASE at repository level
- now: set at repository level; the other store variables stay in the `release` environment.
- why: desktop-release.yml's build job reads it for the apps' updater endpoint and is not in that environment.

---

## unreleased · the download store, tag triggers, betas and yanks {#unreleased-distribution}

### feed.yml · the download store
- refers-to: .github/workflows/feed.yml steps "Download store settings", the cloud sign-in steps and the three "to the download store" steps (feed.yml moved to the private publishing pipeline in v0.8.0)
- why: formcompiler is private, so every GitHub download URL in the catalogue 404s for the public, which breaks FormPortal and formai.tools' `/get/<app>/<platform>` redirect. A store bucket served at https://dl.formai.tools is the public copy.
- layout: `<app>/<version>/<file>` (every release asset, SHA256SUMS.txt among them), `<app>/updates/<file>` (latest.json and the registry's `updater.files`), `catalog/apps.json` and `catalog/apps.json.sig`.
- caching: versioned files `public, max-age=31536000, immutable` and copied with `--no-clobber`, so an object a CDN may hold for a year is never rewritten; a rerun only fills in what is missing. Everything under `updates/` and the catalogue is `public, max-age=60`: the brief named latest.json and the catalogue, and the other update files (install.sh, `*.AppImage.zsync`) are replaced under the same name on every release, so they cannot be immutable either.
- integrity: each release is downloaded from GitHub and checked with `sha256sum --check --strict` against its own SHA256SUMS.txt before anything is copied, so the store holds exactly the bytes the catalogue's digests describe. SHA256SUMS.txt is copied last and is the marker that a release is complete in the store.
- self-healing: the catalogue is built first (not yet published), and `catalog.py listed` names every release it points at (stable, its history, beta). Every one of them whose `<app>/<version>/SHA256SUMS.txt` is not in the bucket is copied, plus the tag of this run. So the first run after the variables are set backfills older releases, and a feed run that GitHub cancelled while pending (one pending run per concurrency group) is made good by the next run. With nothing missing the step is one `gcloud storage ls`.
- order (changed after review): store settings, then the catalogue is built, then the releases it names are copied to the store, and only then does anything get published: `<app>-updates` on GitHub (latest.json already pointing at the store), releases.json on main, the catalog release, the store's update feed, the store's catalogue. A failure in the copy stops the run before any published file names the store. The brief said "after the existing GitHub steps"; this order keeps their content and moves the copy of the versioned files ahead of them, which is the only way a catalogue naming the store is never published ahead of its files. apps.json goes before apps.json.sig; a reader in the second between them sees a signature mismatch and FormPortal refuses that copy and retries, which is safer than the reverse.
- push: the releases.json commit rebases onto main before pushing (yank.yml or a person may have pushed meanwhile), as yank.yml does.
- auth: keyless federation from the workflow to the store's cloud account, through pinned actions; no key file. Overwriting apps.json and latest.json needs delete permission on objects, so the publishing identity has object read, write and delete on the store bucket.
- switch: the store is used only when the store's four settings (the federation provider, the publishing identity, the bucket and FORMCOMPILER_PUBLIC_BASE) are all set. None set: a notice. Some set: a warning naming the missing ones. Either way the run publishes to GitHub as before and the catalogue keeps GitHub URLs, so the catalogue never names a store that is not being filled. A bucket that looks like a URL, or a base that is not https, fails the run.
- environment: the whole feed job runs in the `release` environment, with `id-token: write` on that job only (the workflow default is `contents: read`). One job rather than a GitHub job and a store job, bc a required reviewer approves each job that names the environment, and the catalogue job must see FORMCOMPILER_PUBLIC_BASE to write the public URLs. The cost, raised in review: the same job holds the contents-write token and can mint the OIDC token, and it runs `pip install cryptography` unpinned. Splitting it would need two approvals per run or the variables at repository level; left for the owner (GO_PUBLIC's provider condition limits the OIDC token to this repository's `release` environment).

### catalog.py, feed.py, public_urls.py · public URLs
- refers-to: scripts/public_urls.py; scripts/catalog.py `asset_url`, `build(base=...)`; scripts/feed.py `point_at_store`
- now: with FORMCOMPILER_PUBLIC_BASE set, every artifact and agents URL in the catalogue is `<base>/<app>/<version>/<file>`, each part percent-encoded; file, bytes and sha256 are untouched (they come from the GitHub asset and SHA256SUMS.txt as before). latest.json copied to `<app>-updates` and to the store has each platform URL that pointed at this release's GitHub download moved to the versioned store path, bc the updater bundles live only in the versioned folder; the `updates/` folder carries latest.json and the update files, not the bundles. URLs pointing anywhere else are left as they are. Tauri's updater signatures cover the bundle, not latest.json, so rewriting the URLs keeps them valid. The release's own latest.json (in SHA256SUMS.txt) is never changed.
- module name: `public_urls`, not `public`, bc catalog.py already uses `public` as a local name for the key.

### readiness.py, watch.py, gate.py, github_api.py · tags as triggers
- refers-to: scripts/github_api.py `VERSION_TAG`, `version_tags`, `tag_commit`, `on_main`; scripts/readiness.py `ref_version`, `evaluate`; scripts/watch.py `newest_tag`, `candidate_refs`, `watch_app`, `Lazy`; scripts/gate.py `release_refs`; scripts/registry.py `tag_trigger`
- now: a `vX.Y.Z` tag (lightweight or annotated, annotated ones followed to their commit) in the app repository starts a release like a `compile_vX.Y.Z` branch. The tagged commit must be on main: the compare API's `main...<sha>` status is `identical` or `behind`. Compile branches were not checked against main until the gate hardening (see that section).
- opt-in: only for apps whose registry entry sets `tag_trigger: true`. Every app repository already has years of `v*` tags from before formcompiler, and formcompiler has no published release yet, so watching tags for every app at once would have started a build of each app's newest old tag in the first run. Each app switches when its owner is ready, which is the gradual move.
- cost: per app per run one call for compile branches and, with `tag_trigger`, one for tags. Only the newest tag is considered (a lower one could never be released once it is above nothing), and only it is dereferenced. A newest tag below the highest published version is ignored quietly instead of warning every 15 minutes. The release list and the running release runs are fetched lazily, once per run, and not at all when no app has a ref to evaluate.

### readiness.py, versions.py · the version must go up
- refers-to: scripts/versions.py `semver_key`, `above_published`, `newer_draft`, `older_drafts`; scripts/readiness.py `evaluate`
- now: a version not strictly above the app's highest published version (drafts excluded, yanked included) is refused with that version named. Ordering is semver 2.0 with prereleases: numeric identifiers numerically, numeric before alphanumeric, a release above its prereleases, build metadata ignored. catalog.py's `version_key` now uses the same ordering (beta.10 above beta.2; before it compared the prerelease as a string).
- consequence: once 1.4.0-beta.1 was published, a 1.3.x stable could no longer be released. Relaxed per channel by the gate hardening (see that section).

### release.yml, watch.py · one run per app, newer supersedes older
- refers-to: release.yml `concurrency.group`, assemble step "Supersede older drafts"; scripts/watch.py `watch_app`; scripts/readiness.py superseded skip
- now: release.yml's concurrency group is `release-<app>`, so one run per app runs at a time and a later one waits (GitHub keeps one pending run per group and cancels an older pending one, which is the supersession wanted). The watch evaluates an app's refs newest first and stops after the first one that is ready, waiting, or already running, so it starts at most one run per app per pass and never queues an older version behind a newer one. After a draft is created or refreshed, every draft of the same app with a lower version is deleted (drafts have no git tag yet, so nothing else is left), and readiness skips a ref when a newer draft exists, so the deleted draft's branch does not rebuild it. Exception: a beta never deletes a stable draft, so a stable release waiting for the owner survives a beta of the next version; the owner may still publish it (publishing is not gated), and the catalogue then shows that stable with the beta above it.

### release.yml · betas publish themselves
- refers-to: release.yml assemble step "Publish (a beta, or registry release is publish)"
- now: a version with a prerelease part (`-beta.N`, `-rc.N`, any) is the beta channel, as catalog.py already models it (`channels.beta`, a prerelease newer than stable). Once every job passed it is published as a GitHub prerelease and feed.yml is started for its tag by `gh workflow run`. A release published with GITHUB_TOKEN raises no `release: published` event, but a workflow_dispatch made with GITHUB_TOKEN does start a run, which is the documented exception and what the publish-mode path already used (v0.3.0). Dispatch rather than workflow_call keeps id-token out of release.yml and keeps feed.yml's own concurrency group. feed.py leaves `<app>-updates` untouched for a beta, as before, so the stable update feed never offers a beta; the beta's files and the catalogue go to the store.

### yank.yml, yank.py · yanking a version
- refers-to: .github/workflows/yank.yml; scripts/yank.py; yanked.json; scripts/catalog.py `build(yanked=...)`
- now: Run workflow with app, version and a one-line reason. yank.py checks the app is registered, the version is semver, the release is published (a draft is deleted, not yanked) and not already yanked, then adds `{app, version, reason, date}` to yanked.json, sorted. The workflow commits it to main as the feed's identity (rebasing first, since feed.yml also pushes to main) and starts feed.yml with no tag, which rebuilds, signs and publishes the catalogue to the catalog release and the store. catalog.py leaves a yanked version out of stable, its history and beta; the next version down takes its place. The release and its files stay on GitHub and in the store. The yanked version still counts as published for the go-up rule.
- not done: the update feed (`<app>-updates`, `<app>/updates/latest.json`) is not touched, so an app whose updater reads it is still offered a yanked version until a newer one is published. Pointing latest.json back at an older version would not downgrade anyone who already updated (Tauri only moves forward); the owner decides whether yank should do it.
- concurrency: yank has its own group; sharing feed's would let a later feed dispatch cancel a pending yank.

### watch.yml · every 15 minutes
- refers-to: watch.yml `schedule`, `timeout-minutes`
- now: `*/15 * * * *`, timeout 10 minutes so a stuck run ends before the next. With nothing new a pass is one or two API calls per app plus a registry check.

## unreleased · the watch fails when the app token cannot read {#unreleased}

### watch.py · outage
- refers-to: scripts/watch.py `UNREADABLE`, `outage`, `main`; tests/test_watch.py
- why: a scheduled watch reported "0 release run(s) started, 23 refused" and passed, every app refused with `404: nodemode-ai/<app> is not readable`. With FORMCOMPILER_APP_TOKEN missing or unable to read, nothing can ever release, and a green run with 23 warnings hid that.
- now: an app whose compile branches cannot be listed for 401, 403 or 404 is unreadable. The run still lists every app, still starts every ready app it could read, and then exits 1 with one `::error::` that names the FORMCOMPILER_APP_TOKEN secret and the unreadable apps: "is not set" when the secret is empty, "cannot read" when it is set (expired, revoked, or not granted the repository). The same sentence goes into the step summary. Unreadable apps get no per-app warning, so the error is the one message. Any other API status (a 5xx, say) stays a per-app refusal, as do failed checks, a version mismatch and no compile branch; those never fail the run.
- dry run: the same table with "dry run, not started", and the same exit 1 when an app is unreadable, bc a dry run that cannot read the apps reports nothing true. Locally `GH_TOKEN` with read access stands in for the secret (`github_api.token`), so a dry run from a maintainer's shell passes.
- tested: `tests/test_watch.py` stubs the GitHub calls and runs `watch.main` for no secret, a secret that gets 401, one of two apps unreadable (the other still dispatched), ordinary refusals and a 502 (exit 0), and dry run both ways. Four of the seven fail on the previous watch.py.

### feed.yml · the update feed summary
- refers-to: .github/workflows/feed.yml step "Refresh <app>-updates", last line
- why: actionlint's shellcheck flagged `ls -1 updates | sed 's/^/- /'` (SC2012, info), which failed the self-check lint job.
- now: a glob over `updates/*` prints `- <name>` per file. Same list (neither form shows dot files), and names with spaces or newlines no longer depend on `ls` output. Clean under actionlint 1.7.12 with shellcheck 0.9.0 and 0.10.0.

## v0.4.8 · the test suite {#v0-4-8}

- refers-to: tests/conftest.py, tests/test_registry.py, tests/test_release_matrix.py, tests/test_signing_and_skills.py, tests/test_f4_versions.py, tests/test_f9_release_profiles.py, tests/requirements.txt, .github/workflows/self-check.yml (job test)
- kind: decision
- logged: v0.4.8 · 2026-10-26

`FAMILY_TEST_PLAN.md` P1 for formcompiler. The scripts are driven the way the workflows drive them, as `python3 -I scripts/<name>.py ...` subprocesses, except where a module constant has to point elsewhere (`registry.APPS` at a temporary registry, so a broken or duplicated entry can be shown to fail `check` without touching `apps/`). The version-source test writes each entry's declared file into a temporary repo with the shape the app really uses: JSON and TOML files are built from the type, and the two pattern sources (form.md's Makefile line, formcut's `APP_VERSION`) carry their real line in `PATTERN_LINES`; a test fails when a pattern entry is added without one, so a new app cannot pass by being skipped. The signing test is a shared vector: seed 32 bytes of 0x0b, the body in the test, and the public key and signature that formportal-core's own verifier (ed25519-dalek) produced and accepted for them on 2026-10-26; `catalog.sign` must give those exact bytes (Ed25519 is deterministic), so a change on either side breaks it here. The disabled-app tests first assert the registry still holds a disabled entry (formref today), since with none they would pass on nothing. `test_f4_versions.py` and `test_f9_release_profiles.py` are the formai_dev sidecar's family templates, unchanged; this repo has no Cargo crate or frozen engine, so F9 guards against one arriving stripped. Proven on a copy of the tree: listing disabled apps for release, letting a disabled app configure, accepting a disabled entry with no reason, skipping the skills zip's digest check, signing the wrong bytes and a VERSION that drifts from the CHANGELOG each fail the suite.

## Org-navi-map

```
formcompiler/
├── .github/workflows/
│   ├── watch.yml             every 15 minutes and on Run workflow: starts release.yml for ready compile branches and tags
│   ├── release.yml           gate, desktop, extras, image, the draft release
│   ├── desktop-release.yml   reusable: plan and build per platform (called by release.yml)
│   ├── feed.yml              on publish: <app>-updates, releases.json, the catalog release, the download store
│   ├── yank.yml              Run workflow: a version into yanked.json, then feed.yml
│   └── self-check.yml        actionlint, py_compile, registry, plan and catalogue dry runs, text rules
├── apps/<app>.json           the registry, one file per app (docs/REGISTRY.md)
├── assets/                   the owner's icon (README) and its glyph
├── scripts/
│   ├── HASHOUT_LOG.md        this log
│   ├── registry.py           validation and the build config
│   ├── github_api.py         REST calls with urllib
│   ├── readiness.py          the per-branch decision
│   ├── watch.py, gate.py     the decision over every app, and for one run
│   ├── plan.py               version, tag, platform matrix
│   ├── run_build.py          build contract, own commands, post-build
│   ├── tauri_config.py       the --config JSON
│   ├── stage.py              collects one platform's files
│   ├── agents.py             form-app.json v2 and the skills archive of a release
│   ├── with_portal.py        app-plus-FormPortal downloads (registry with_portal)
│   ├── release_assets.py     SHA256SUMS.txt and latest.json
│   ├── notes.py              release notes
│   ├── feed.py               tag to app, update files, latest.json URLs in the store
│   ├── versions.py           semver ordering, channels, published and draft versions
│   ├── public_urls.py        download store URLs
│   ├── yank.py               yanked.json
│   └── catalog.py            FormPortal's catalogue, signing, key pair
├── docs/REGISTRY.md          the registry contract
├── docs/GO_PUBLIC.md         the owner's checklist: secrets, the release environment, rulesets, going public
├── releases.json             the catalogue (written by feed.yml)
├── yanked.json               versions left out of the catalogue (written by yank.yml)
├── README.md                 front door
├── LICENSE                   GPL-3.0-only
└── NOTICE                    copyright and third-party actions
```

---

## v0.4.7 · FormPortal stays optional in the bundle {#v0-4-7}

### with_portal.py · README
- refers-to: scripts/with_portal.py `README`; docs/REGISTRY.md `with_portal` row
- why: the owner, 2026-10-25: FormPortal must never install itself or be pressed on anyone who does not want it. The 0.4.6 README told people to install FormPortal first.
- now: the README says the app's installer is all the app needs, that FormPortal is optional and nothing installs it, what it does if they want it, and that the file can be deleted unopened. Nothing in the bundle runs anything; it is a zip of two installers and a text file. `with_portal` stays off by default, so an app's owner turns it on per app, and the app's own downloads are always there without FormPortal.

## v0.4.6 · an app-plus-FormPortal download beside each installer {#v0-4-6}

### with_portal.py · main, pick, allowed
- refers-to: scripts/with_portal.py; release.yml assemble step "App plus FormPortal"; scripts/registry.py `with_portal`, `PORTAL_ID`; scripts/catalog.py `SKIP`
- why: FormPortal's parity row 2 (Creative Cloud's desktop app arrives with the first app download). The family plan chose a second download per installer rather than changing any app's own installer, so the normal files, their sums and the catalogue entries are untouched and the bundle can be ignored by anyone who does not want FormPortal.
- how: runs only when the registry entry sets `with_portal` (refused for FormPortal's own entry, catalogue id `formai`, and for an entry with no desktop platforms). Reads the published catalogue (`DEFAULT_CATALOG`, or `--catalog` for a file or address), takes FormPortal's stable release, and for every desktop installer in `dist` (`catalog.classify`, so only what the catalogue itself would list) picks FormPortal's file for the same platform and chip, preferring the same kind, then nsis, msi on Windows, dmg on macOS, appimage, deb, rpm on Linux. A universal dmg gets one bundle per chip FormPortal builds for. Each FormPortal file is downloaded once (https or loopback only), checked against the catalogue's sha256 and size, and stored with the app's installer and a README in `<installer stem>-<kind>[-<chip>]-with-FormPortal.zip`, uncompressed since installers are compressed already.
- safety: a FormPortal file that does not match the catalogue fails the release step and removes every bundle made in that run, so no half set is released. No stable FormPortal release in the catalogue, or no FormPortal build for a platform, is a notice, not a failure: the app releases as before.
- order: after the app's assets and `agents.py`, before `release_assets.py`, so `SHA256SUMS.txt` covers the bundles. `catalog.py`'s `SKIP` ends in `-with-formportal.zip`, so the bundles never become artifacts of the app in the catalogue and FormPortal never installs one as the app.
- not done: the bundle is not signed beyond the sums (each installer inside keeps its own signature); FormPortal's catalogue signature is not checked here because the catalogue is read from formcompiler's own release over https and every file is checked against its digest.
- tested: against a stand-in catalogue served on loopback, with placeholder installers for every desktop kind (bundles byte-equal to the inputs, the catalogue skips them), a mismatch on the first and on the last file (no bundle left), a catalogue with no FormPortal release (notice, folder unchanged), the option off, and a plain-http address (refused). Not run in GitHub Actions.

## v0.4.2 · every earlier major line stays in the catalogue {#v0-4-2}

### catalog.py · kept_history and line_of
- refers-to: scripts/catalog.py :: `line_of`, `kept_history`, `build` (the stable channel's history)
- kind: rationale
- logged: v0.4.2 · 2026-10-24

FormPortal's parity row #19 (previous major versions with no stated cutoff) was Partial because history stopped at five earlier releases. History is now the five newest earlier stable releases plus the newest release of every older major line that those five do not already cover. A major line is the major number, or `0.minor` while the major is 0, since a 0.x app breaks on minor versions. Each kept release still costs one SHA256SUMS fetch, so the extra cost is one fetch per older line. Checked: for 0.45.1 with 0.30.0 and 0.9.x behind it, history is the five newest then 0.43.0, 0.42.1, 0.30.0 and 0.9.9; with no earlier release, no history; an empty releases list still builds a catalogue of 22 products.

## v0.4.0 · the app manifest and the skills archive {#v0-4-0}

### agents.py · a script of its own, not stage.py
- refers-to: scripts/agents.py, release.yml :: App manifest and skills
- kind: decision
- logged: v0.4.0 · 2026-10-24

The family plan (Phase 2) named `stage.py` for this. `stage.py` runs once per desktop platform and collects that runner's bundles; the manifest and the skills belong to the release as a whole and must exist once, for apps with no desktop build too. So they are written in the assemble job by `agents.py`, after the app's own `assets` (which may write files of their own) and before `release_assets.py`, so `SHA256SUMS.txt` covers both and `catalog.py` can carry their digests. `check` re-reads what `build` wrote: format, id, version, the archive's size and digest, and that the archive holds exactly the declared skill folders with their file counts and a `SKILL.md` each.

### agents.py · a reproducible archive
- refers-to: scripts/agents.py :: write_zip, skill_files
- kind: rationale
- logged: v0.4.0 · 2026-10-24

Files are walked in sorted order, every entry is dated 1980-01-01 with mode 644 (755 when executable), so two runs over one tree give the same bytes and the same digest; checked on formvis 1.97.1's `.claude/skills` (42 files, unzipped tree identical to the source). `os.walk` does not follow linked folders; a linked file inside the skills folder is stored by content, one pointing outside stops the release.

### agents.py · front matter without a YAML library
- refers-to: scripts/agents.py :: front_matter
- kind: rationale
- logged: v0.4.0 · 2026-10-24

The scripts use the standard library only. SKILL.md front matter in the family is flat `key: value` lines, sometimes with a folded `description: >` block; the parser reads those two shapes, which is all `name` and `description` need. Anything else is ignored rather than guessed.

### registry.py · agents is optional, mcp_launch waits for the apps
- refers-to: scripts/registry.py :: AGENTS, MCP_LAUNCH
- kind: decision
- logged: v0.4.0 · 2026-10-24

An entry without `agents` releases as before plus a manifest with `mcp.available` false. `mcp_launch` is accepted but set on no app: FormPortal looks for `form-app.json` inside the installed app and starts the command it names, and no app's bundle carries a stdio MCP launcher yet (the `./<app> mcp` launchers are source-checkout scripts). Until one does, `mcp.available` is what the catalogue and formMCP use.

### catalog.py · formcompiler's SHA256SUMS.txt first
- refers-to: scripts/catalog.py :: fetch_sums, agent_assets
- kind: rationale
- logged: v0.4.0 · 2026-10-24

Some apps attach their own `SHA256SUMS` from `assets` (formvis), written before formcompiler adds the manifest and the skills archive. `fetch_sums` took whichever of the two came first in the API's list; it now takes `SHA256SUMS.txt`, formcompiler's own, when present, so the new files always have a digest.

## v0.3.2 · formencoder's release contents {#v0-3-2}

- LAME (bundle audit, formencoder): LAME 3.100 is LGPL-2.0-or-later and runs as a separate program, so the unmodified release tarball is its source offer. `apps/formencoder.json` `assets` downloads `lame-3.100.tar.gz` from SourceForge and asserts the SHA-256 that formencoder's `setup/install_tools.py` pins (`ddfe36ca...`); when formencoder moves the pin, move this one with it.
- Delivery tools list: the build runs `install_tools.py --stage --keep-going`, which skips a tool that fails to build. `post_build` on every platform writes `delivery-tools-$FORMCOMPILER_PLATFORM.txt` (the names in `src-tauri/tools`, empty when none were staged) at the checkout root. Setting `artifacts` replaces stage.py's `DEFAULT_ARTIFACTS`, so the entry lists those eight globs again plus `delivery-tools-*.txt`; keep it in step if the defaults change. Post-build runs in bash on Windows too (`--windows-shell=bash`), so one command serves all three.

## v0.3.1 · bundle audit fixes in the registry {#v0-3-1}

- macOS opencv (bundle audit, should-fix): the macOS binary wheels of opencv-python and opencv-python-headless 5.0.0.93 carry Homebrew's FFmpeg with libx264, libx265, rubberband, vidstab and postproc (GPL). The Linux wheels carry LGPL FFmpeg and Qt; the Windows wheels opencv's own LGPL `opencv_videoio_ffmpeg`. `setup.macos` of formDAM, formlit, formvis, formpdf and formtxt now writes `PIP_NO_BINARY=opencv-python,opencv-python-headless` and `CMAKE_ARGS=-DWITH_FFMPEG=OFF -DWITH_GSTREAMER=OFF` to `$GITHUB_ENV`, so every later pip step builds opencv from its sdist without FFmpeg. None of these apps reads video through OpenCV (no VideoCapture or VideoWriter). The apps' macOS freezes stop if any of those libraries reach the engine (FormTxt from 0.29.5; the others with their next release). formcut rebuilds OpenCV itself (`backend/prepare_cv.py`) and is unchanged here.
- PyAV (B2 formcut, B3 Format): the owner chose an LGPL PyAV build. Each app now carries `setup/build_lgpl_av` (macOS and Linux) and `setup/build_lgpl_av.bat` (Windows, MSYS2 with `--toolchain=msvc`), which build the unmodified FFmpeg 8.0.3 release (`--disable-gpl --disable-nonfree --disable-version3 --disable-autodetect`, shared) and PyAV 18.1.0 from source against it, then run `setup/check_lgpl_av.py`. The apps' freezes refuse a PyAV linked to anything else. Both entries set `windows_msvc` so cl is on PATH for the Windows build. Format's `assets` attaches the FFmpeg source with `setup/ffmpeg_source`; formcut's `setup/release_assets` attaches it and the sidecar's 7.1.5 source. Measured here on Linux x86_64: the build took 9 minutes on 2 cores; the Windows script was not run.

## v0.3.0 · formcompiler builds the apps {#v0-3-0}

### the direction of the pipeline
- refers-to: watch.yml, release.yml, desktop-release.yml, feed.yml
- kind: decision
- logged: v0.3.0 · 2026-10-22

Until v0.2.1 each app called desktop-release.yml from its own repository with a tag. The owner's plan of 2026-10-22 (DEV_PLAN v0.3.0) reverses that: no app repository builds or releases anything, and formcompiler alone builds, signs and releases. The apps' build workflows were removed in Phase 1; each app now runs its checks on main and on `compile_v*` branches. Watching was chosen over a dispatch from each app because nodemode-ai is a personal account: a dispatch would need one token copied into 22 repositories, the watch needs at most one read token here, and none once the apps are public. The cost is up to 8 hours of delay, which the Run workflow button removes.

### templates/desktop.yml and docs/ADOPTION.md removed
- refers-to: templates/desktop.yml, docs/ADOPTION.md
- kind: removed-code
- logged: v0.3.0 · 2026-10-22

The caller template existed for apps to call formcompiler; no app does any more. ADOPTION.md's per-app inputs became the registry (`apps/*.json`, contract in docs/REGISTRY.md). Its runner notes still hold: `macos-x64` on `macos-15-intel`, `linux-x64` on `ubuntu-22.04` for the glibc 2.35 floor, Tauri 2's `libayatana-appindicator3-dev`.

### registry.py · strict fields
- refers-to: scripts/registry.py :: `TOP`, `validate`
- kind: rationale
- logged: v0.3.0 · 2026-10-22

An unknown field is an error rather than ignored, because a misspelt `post_buidl` would otherwise drop a packaging step silently and the release would just be missing files. Command strings are only ever passed to a shell through environment variables (workflow `env:` blocks), never interpolated into `run:` text.

### readiness.py · the five outcomes
- refers-to: scripts/readiness.py :: `evaluate`
- kind: explainer
- logged: v0.3.0 · 2026-10-22

skip: not a compile branch name; already published; already drafted from this exact commit (the draft's body carries `formcompiler-source: <repo>@<sha>`); a release run with the same title is queued or running. refuse: the version file at that commit disagrees with the branch name, or a required check concluded anything but success. wait: a required check is still running or has not started. ready: all checks succeeded. A branch moved to a new commit after a draft was made is ready again, so a second push refreshes the draft.

### release.yml · run-name and the duplicate guard
- refers-to: release.yml :: `run-name`; scripts/github_api.py :: `run_title`, `active_release_runs`
- kind: rationale
- logged: v0.3.0 · 2026-10-22

The runs API does not return a dispatch's inputs, so the run title `<app> <version> at <sha>` carries them; the watch compares titles of queued and running release runs to avoid starting the same build twice when a build outlasts the 8-hour interval. gate.py leaves its own run out of that comparison.

### release.yml · assemble on formcompiler's commit
- refers-to: release.yml :: assemble :: Create or refresh the draft
- kind: rationale
- logged: v0.3.0 · 2026-10-22

The tag `<app>-vX.Y.Z` lives in formcompiler, so it must point at a formcompiler commit (`GITHUB_SHA`), not at the app's. The app commit is recorded in the notes footer and the marker. Drafts are created with `--latest=false` so no app's release becomes the repository's "latest" over another's; the update feeds and the catalogue never use "latest".

### release.yml · publish mode starts feed.yml by dispatch
- refers-to: release.yml :: assemble :: Publish
- kind: warning-context
- logged: v0.3.0 · 2026-10-22

A release published with `GITHUB_TOKEN` creates no `release: published` event for other workflows, so publish-mode apps start feed.yml with `gh workflow run`, which `GITHUB_TOKEN` may do. Every app starts as draft (owner, 2026-10-22), so this path is unused until an app is switched.

### desktop-release.yml · the app checkout, post-build, signing
- refers-to: desktop-release.yml :: plan, build
- kind: explainer
- logged: v0.3.0 · 2026-10-22

The app is checked out from its repository at the compile commit with `FORMCOMPILER_APP_TOKEN` (read only) or the workflow token. `persist-credentials: false` keeps that token out of the app's build. Experimental platforms (`?` in the registry) run with `continue-on-error`. Apple secrets reach the build only for `macos-signing: apple`; the Windows certificate is imported only for `windows-signing: certificate` and only when the secret exists, and its thumbprint goes into `--config` (tauri_config.py). The disk-image notarization step skips an image that is already stapled, so an app whose post-build notarizes (formvis) is not submitted twice. The release job that used to live here moved to release.yml's assemble job, which also sees the extras.

### plan.py · cross builds
- refers-to: scripts/plan.py :: `PLATFORMS`, `plan_matrix`
- kind: explainer
- logged: v0.3.0 · 2026-10-22

`macos-universal` and `windows-x86` build with `--target` (`target_args`), install their Rust targets, and put their bundles under `src-tauri/target/<triple>/release`, given to post-build as `FORMCOMPILER_RELEASE_DIR`. `windows-x86` gets a 32-bit Python (`pyarch`), as formvis's matrix had. Registry `rust_targets` are added to every row.

### run_build.py · cmd placeholders substituted before cmd runs
- refers-to: scripts/run_build.py :: `run_cmd`, `default_lines`
- kind: warning-context
- logged: v0.3.0 · 2026-10-22

cmd leaves `%NAME%` as literal text when NAME is undefined, and an empty value may not survive into the child environment on Windows, so every `%FORMCOMPILER_*%` is replaced with its value before the script is written, and the contract's own build line carries the config path and target arguments directly instead of variables.

### stage.py · which update archives are renamed
- refers-to: scripts/stage.py :: `staged_name`
- kind: fix
- logged: v0.3.0 · 2026-10-22

Only Tauri's own `<product>.app.tar.gz` (no `-` or `_` in the name) gets the `_<arch>` suffix. Before, any `.app.tar.gz` without `_<arch>` was renamed, which would have renamed FormPortal's `-update.app.tar.gz` behind the back of the latest.json its own packager writes.

```text
            if name.endswith(suffix) and f"_{arch}" not in name:
```

### catalog.py · artifacts FormPortal can install
- refers-to: scripts/catalog.py :: `classify`, `build`
- kind: explainer
- logged: v0.3.0 · 2026-10-22

Only kinds in FormPortal's schema are listed (zip, dmg, appimage, msi, nsis, deb, rpm, apk, ipa) and only with an arch the schema has (arm64, x86_64); a universal disk image is listed under both arches. Hashes come from the release's SHA256SUMS.txt, never recomputed. stable is the newest published non-prerelease `<app>-v` release with up to five earlier ones as history (from v0.4.2 also the newest of each older major line, see v0.4.2 above); beta is a newer prerelease. The signature is Ed25519 over the exact bytes uploaded as apps.json, base64, as FormPortal's `core/src/signature.rs` verifies.

---

## Table of contents

- [.github/workflows/desktop-release.yml](#workflow-desktop-release)
- [.github/workflows/self-check.yml](#workflow-self-check)
- [scripts/plan.py](#scripts-plan)
- [scripts/run_build.py](#scripts-run-build)
- [scripts/tauri_config.py](#scripts-tauri-config)
- [scripts/stage.py](#scripts-stage)
- [scripts/release_assets.py](#scripts-release-assets)
- [templates/desktop.yml](#templates-desktop)

---

## .github/workflows/desktop-release.yml {#workflow-desktop-release}

### desktop-release.yml · pinned `uses:` lines
- refers-to: desktop-release.yml :: every `uses:` of a third-party action
- kind: rationale
- logged: v0.1.0 · 2026-10-18

Each action is pinned to the full commit SHA of its current tag, resolved with `git ls-remote` on 2026-10-18; the trailing `# vX.Y.Z` is the version marker Dependabot and Renovate read to propose updates, so it stays inline as a machine-read pragma. A moved tag would otherwise change every app's release at once. `dtolnay/rust-toolchain` is pinned at `v1` and given `toolchain: stable` explicitly, since a SHA pin loses the branch-name toolchain selection.

### desktop-release.yml · scripts checked out at formcompiler-ref
- refers-to: desktop-release.yml :: the second `actions/checkout` in plan, build and release
- kind: rationale
- logged: v0.1.0 · 2026-10-18

A reusable workflow's `./path` references resolve in the caller's checkout, not in formcompiler, so the scripts are checked out from `nodemode-ai/formcompiler` into `.formcompiler`. The ref is an input bc a workflow cannot read the ref it was itself called at; callers pinned to a tag set `formcompiler-ref` to the same tag so the scripts and the workflow match.

### desktop-release.yml · env-only inputs
- refers-to: desktop-release.yml :: every `run:` step
- kind: warning-context
- logged: v0.1.0 · 2026-10-18

No `${{ inputs.* }}` expression appears inside a `run:` script. Inputs are free text from the caller, so they reach the shell only as environment variables; `run_build.py` additionally restricts `cli` and `install-args` to safe characters, and the Linux packages step restricts package names. Keep it that way when adding inputs.

### desktop-release.yml · build · npm cache
- refers-to: desktop-release.yml :: build :: setup-node `cache`
- kind: explainer
- logged: v0.1.0 · 2026-10-18

The npm cache is enabled only when `frontend/package-lock.json` exists, bc setup-node fails a job whose cache dependency path is missing, and some form* apps keep their lockfile elsewhere.

### desktop-release.yml · build · APPIMAGE_EXTRACT_AND_RUN
- refers-to: desktop-release.yml :: build :: Build step env
- kind: explainer
- logged: v0.1.0 · 2026-10-18

Tauri's AppImage bundler runs linuxdeploy, itself an AppImage; GitHub's runners have no FUSE, so extracting and running it is required. formcut's release workflow sets the same variable.

### desktop-release.yml · release · published-tag refusal
- refers-to: desktop-release.yml :: release :: Create or update the draft
- kind: rationale
- logged: v0.1.0 · 2026-10-18

An existing draft has its assets deleted and re-uploaded, so a rerun never leaves files from two builds mixed. A published release is refused outright: replacing files people already downloaded would make their checksums lie.

### desktop-release.yml · release · not on pull requests
- refers-to: desktop-release.yml :: release :: `if:`
- kind: rationale
- logged: v0.1.0 · 2026-10-18

A pull request may build every platform (useful to check packaging changes) but never drafts a release, whatever `release` says.

### desktop-release.yml · build · rust-targets
- refers-to: desktop-release.yml :: inputs.rust-targets, build :: rust-toolchain `targets`
- kind: explainer
- logged: v0.2.0 · 2026-10-18

Passed straight to `dtolnay/rust-toolchain`'s `targets`, which takes a comma list and installs nothing for an empty string. The host target is always present. formwav needs `wasm32-unknown-unknown`.

### desktop-release.yml · build · MSVC environment
- refers-to: desktop-release.yml :: inputs.windows-msvc, build :: MSVC environment step
- kind: rationale
- logged: v0.2.0 · 2026-10-18

`ilammy/msvc-dev-cmd` (MIT) pinned to v1.13.0, commit `0b201ec74fa43914dc39ae48a89fd1d8cb592756` (the peeled tag, resolved with `git ls-remote`), exports the Visual Studio developer environment to later steps so `nmake` and `cl` work; formencoder's own workflow used the same action for LAME. `arch` maps the preset's `aarch64` to the action's `arm64` and anything else to `x64`. Off by default bc Tauri's own build finds MSVC without it.

### desktop-release.yml · build · FORMCOMPILER_OS, _ARCH, _TRIPLE
- refers-to: desktop-release.yml :: build :: Build step env
- kind: explainer
- logged: v0.2.0 · 2026-10-18

Exported so an app's own build commands can name the platform without formcompiler knowing each packer's vocabulary: formcut's `setup/package_release.py --target "$FORMCOMPILER_TRIPLE"`, formportal's `--platform "$FORMCOMPILER_OS" --arch` after mapping `aarch64` to `arm64` and `x64` to `x86_64` in its command. `run_build.py` copies the whole environment into the command, so no change was needed there.

---

## .github/workflows/self-check.yml {#workflow-self-check}

### self-check.yml · actionlint download
- refers-to: self-check.yml :: lint :: actionlint
- kind: rationale
- logged: v0.1.0 · 2026-10-18

actionlint 1.7.12 is downloaded and checked against the SHA-256 from its release checksums file (`8aca8db9...`), rather than through a third-party action. `--proto-redir '=https'` keeps redirects on HTTPS. The lint covers `templates/` too; it cannot check the template's inputs against a remote ref, so input names were checked by linting temporary callers that point at the local workflow inside a git project (actionlint resolves local reusable workflows only when it finds the project root).

---

## scripts/plan.py {#scripts-plan}

### plan.py · PLATFORMS
- refers-to: plan.py :: PLATFORMS
- kind: explainer
- logged: v0.1.0 · 2026-10-18

Runner labels are the ones the form* apps already use in their own workflows: `macos-latest` (arm64), `macos-15-intel` (format, formdeck, formportal), `ubuntu-22.04` (glibc 2.35 floor for the AppImage), `ubuntu-22.04-arm` (formdeck, formportal), `windows-latest`, `windows-11-arm` (formportal). The `updater` keys are Tauri's `latest.json` platform names. `arch` is the suffix `stage.py` adds to the macOS updater archive and matches formdeck's naming (`aarch64`, `x64`). `triple` (added v0.2.0) is the Rust target triple of the runner's host, the value formcut's release workflow passed to its packer per platform.

### plan.py · read_version
- refers-to: plan.py :: read_version
- kind: explainer
- logged: v0.1.0 · 2026-10-18

Order: a regex if `--version-pattern` is given; else `version` in a JSON file (tauri.conf.json, package.json); else `[package]` or `[workspace.package]` in a TOML file; else the first line of a plain file (a `VERSION` file, as formsurface and formweb keep). `tomllib` needs Python 3.11, which every runner's setup-python 3.12 provides.

### plan.py · tag check
- refers-to: plan.py :: main (the `refs/tags/` comparison)
- kind: rationale
- logged: v0.1.0 · 2026-10-18

In a reusable workflow `GITHUB_REF` is the caller's ref, so a tag push is checked against the app's version before any runner starts. A manual run is not checked, which is how a `version` override builds a test release.

---

## scripts/run_build.py {#scripts-run-build}

### run_build.py · clean_secrets
- refers-to: run_build.py :: SECRET_GROUPS, clean_secrets
- kind: rationale
- logged: v0.1.0 · 2026-10-18

GitHub passes an unset secret as an empty string. Tauri treats a present but empty `APPLE_CERTIFICATE` as a certificate to import and fails, so each group is removed when its first variable is empty, and any empty companion is removed on its own. This is the same guard formvis's and format's workflows apply in bash.

### run_build.py · default_lines and run_cmd
- refers-to: run_build.py :: default_lines, run_cmd
- kind: explainer
- logged: v0.1.0 · 2026-10-18

Under cmd every line is followed by `if errorlevel 1 exit /b 1`, bc cmd does not stop on a failing `call`; formdes, format, formvfx and formencoder use the same `|| exit /b 1` pattern. The script is written to a temporary `.cmd` in `RUNNER_TEMP` and run with `cmd /d /c`. Not run yet: there is no Windows host in the build environment.

### run_build.py · minimum_macos
- refers-to: run_build.py :: minimum_macos and its call in main
- kind: rationale
- logged: v0.1.0 · 2026-10-18

Sets `MACOSX_DEPLOYMENT_TARGET` from `bundle.macOS.minimumSystemVersion` so the Rust shell and any engine build link for the macOS the bundle declares, as formcut's release workflow does by hand. A value already in the environment wins.

---

## scripts/tauri_config.py {#scripts-tauri-config}

### tauri_config.py · build_config
- refers-to: tauri_config.py :: build_config
- kind: rationale
- logged: v0.1.0 · 2026-10-18

`createUpdaterArtifacts` only with a signing key, bc updater bundles are signed with it; formvis's and format's workflows make the same choice. The ad hoc signature (`signingIdentity: "-"`) applies on macOS when no Apple certificate is set: formcut's `release.yml` records that an unsealed bundle is reported damaged after a download with no way to open it. The app's own `tauri-config` is merged last so it can override either.

### tauri_config.py · write_config
- refers-to: tauri_config.py :: write_config
- kind: explainer
- logged: v0.1.0 · 2026-10-18

The config is written to an absolute path with forward slashes and passed as `--config <file>`, not as inline JSON, bc inline JSON does not survive cmd quoting and a relative path depends on where each app's launcher runs Tauri from.

---

## scripts/stage.py {#scripts-stage}

### stage.py · staged_name
- refers-to: stage.py :: staged_name
- kind: rationale
- logged: v0.1.0 · 2026-10-18

Tauri names the macOS updater archive `<Product>.app.tar.gz` with no architecture, so an arm64 and an Intel build would overwrite each other on the release. The archive and its `.sig` get `_<arch>` before the suffix, the naming formdeck and format already use. Every other bundle name already carries its architecture.

### stage.py · pick_updater
- refers-to: stage.py :: UPDATER_PATTERNS, pick_updater
- kind: explainer
- logged: v0.1.0 · 2026-10-18

The updater file for a platform is the first match that has a `.sig` beside it: the `.app.tar.gz` on macOS, the AppImage on Linux, the NSIS `-setup.exe` on Windows and then the MSI. Without signatures (no `TAURI_SIGNING_PRIVATE_KEY`) the manifest records no update and `latest.json` is skipped.

---

## scripts/release_assets.py {#scripts-release-assets}

### release_assets.py · main
- refers-to: release_assets.py :: main
- kind: explainer
- logged: v0.1.0 · 2026-10-18

Manifests are deleted after reading so they are not released. `latest.json` follows the format the form* apps already publish (`version`, `notes`, `pub_date`, `platforms` with `signature` and `url`). `SHA256SUMS.txt` covers every released file including `latest.json`, in the two-space format `sha256sum -c` reads.

---

## templates/desktop.yml {#templates-desktop}

### desktop.yml · triggers and pinning
- refers-to: templates/desktop.yml :: on, jobs.desktop.uses
- kind: rationale
- logged: v0.1.0 · 2026-10-18

Tag push plus manual dispatch is what most form* apps' `desktop.yml` already use. The template pins the workflow and `formcompiler-ref` to the current version's tag (`v0.2.1`), bumped with every release; an app that wants fixes to arrive without edits can use `@main` for both, trading reproducible releases for automatic fixes. `concurrency` never cancels a running release, so two pushes of the same tag queue rather than race. `APP_NAME` is a placeholder the adopter replaces.
