# Changelog

## v0.8.0 · 2026-11-03

- Publishing to the download store at https://dl.formai.studio, the `<app>-updates` feeds, the catalogue signature and yanks move to a private companion pipeline. feed.yml, yank.yml and docs/GO_PUBLIC.md are removed; the scripts they ran stay here and the pipeline runs them from this repository
- release.yml tells the pipeline about each release it publishes with a `repository_dispatch` (`formcompiler-published`, the tag in `client_payload`) using the secret `FORMPIPE_DISPATCH_TOKEN`. Without it, or if the dispatch fails, the run says so and the pipeline's hourly check picks the release up. The release job no longer needs `actions: write`
- `releases.json` and `yanked.json` change through pull requests the pipeline opens; a yank takes effect once its pull request is merged
- README, SECURITY.md, NOTICE and the registry contract no longer describe the store's cloud setup; the history in CHANGELOG.md and scripts/HASHOUT_LOG.md keeps its entries with the cloud identifiers replaced by neutral words

## v0.7.1 · 2026-11-03

- Release files are named `<app>-<version>-<platform>[-setup].<ext>` with the registry's app name and formcompiler's platform names, for example `formtray-0.9.8-macos-arm64.dmg`, `formtray-0.9.8-windows-x64-setup.exe` and `formtray-0.9.8-linux-x64.AppImage`. The disk image, the macOS update archive, AppImage, zsync, deb, rpm, MSI, NSIS setup, zip and tarball are renamed, with their `.sig` files; any other file keeps its name. Owner's decision of 2026-11-03
- `file_names` in a registry entry: `formcompiler` (the default) or `app`, which keeps the build's own names. formvis (its own updater feed and AppImage update information match Tauri's names) and FormPortal (it names its own files) use `app`
- Files already released keep their names
- FormRanker is FormBench: the repository is `nodemode-dev/formbench` (renamed 2026-11-03), the registry entry is `apps/formbench.json`, app and catalogue id `formbench`, title FormBench. The app's launcher (`formranker`) and bundle identifier (`ai.nodemode.formranker`) are the app's own and stay until the app renames them. Nothing has been released under either name

## v0.7.0 · 2026-11-03

- The watch runs every hour (`17 * * * *`), not every 15 minutes. Run workflow still starts one at once
- Desktop builds, extras and the container image stop at 49 minutes instead of 150 and 60, so a stuck job no longer holds a macOS runner for hours. The Build step itself stops at 40 minutes, so the Rust and pip caches are still saved when a cold build runs out of time, and Re-run failed jobs continues from them
- The Rust cache is kept per app (`formcompiler-<app>-<platform>`): with one key for every app, a build could restore another app's cache and push a third one out
- `pip_cache_macos` in a registry's toolchain keeps pip's locally built wheels between macOS builds; formDAM, formlit, formvis, formpdf and formtxt turn it on, so the opencv they build from source is reused while the app's set-up, Python and requirement files are unchanged
- macOS notarization submits every disk image first and then waits, so Apple checks them at the same time; it also notarizes and staples a disk image the app's post-build copied into its `artifacts`, such as FormPortal's `release-dist`
- A missing build folder no longer stops the notarize step from looking in `src-tauri/target.nosync`
- A failed release run is retried with Re-run failed jobs, which the watch's message and the README now say
- FormPortal's registry notes describe its installers (formportal 0.54.0 ships the dmg, NSIS setup, AppImage, deb and rpm without zips)

## v0.6.9 · 2026-11-02

- formnet is formNET (`apps/formNET.json`): the registry app, title, tag prefix (`formNET-v`), store path and catalogue name (FormNET) follow the repository's spelling, as formMCP and formDAM do. The CLI binary and the catalogue id stay `formnet`. Owner's decision of 2026-11-02; nothing has been released under the old name
- The watch does not start a release again after its run failed or was cancelled at the same commit: a failed run leaves no draft, so every 15-minute watch rebuilt it (formcut 2.11.2 was restarted this way). Re-run the failed run in Actions, or fix the app and release a new version
- Drafts target `main`, not the formcompiler commit the run started on: GitHub refuses the Actions token a release at a commit whose workflows differ from main's, so formencoder 0.5.1's draft failed with "Resource not accessible by integration" once v0.6.7 changed a workflow mid-run

## v0.6.8 · 2026-11-02

- formnet joins the registry (`apps/formnet.json`, id `formnet`, kind `network`, `prelaunch`): the network inspector from formnet 0.1.0, one Go binary with its web client embedded, wrapped in a Tauri 2 window and built by its own `build_app` and `build_app.bat` like form.md, with a `server` extra for the five static binaries from `make release`. The repository is `nodemode-dev/formNET`; the app names itself formnet. No workflow or script changed

## v0.6.7 · 2026-11-02

- The watch sees draft releases: GitHub lists drafts only to a token with write access, and the watch's read-only token saw none, so its "already drafted" and "superseded by a newer draft" checks never fired and every watch started a new build for an app whose release was waiting as a draft (form.md 0.47.7 was restarted this way). The watch's token now has `contents: write`

## v0.6.6 · 2026-11-02

- Windows builds and post-build steps that run in bash start Git Bash, not the WSL launcher: Python's bare `bash` resolved to `C:\Windows\System32\bash.exe`, which stopped formcut's build and formportal's packaging with "Windows Subsystem for Linux has no installed distributions"
- Windows builds name Visual Studio's linker for each MSVC target (`CARGO_TARGET_<TRIPLE>_PC_WINDOWS_MSVC_LINKER`), so a Rust build the app starts itself, such as formencoder's pywinpty wheel, no longer links with Git's `usr\bin\link.exe`
- Stapling a notarized disk image is retried up to five times: Apple's ticket service dropped the connection after notarization succeeded on formdeck's and formportal's Intel builds (error 68)
- formdeck's flatpak extra installs elfutils, which flatpak-builder needs for `eu-strip`

## v0.6.5 · 2026-11-02

- macOS disk images are found and notarized under the runners' bash 3.2: the step used `shopt -s globstar`, which bash 3.2 does not have, so every macOS build stopped right after building (formtray's run 41473779877). The extras' Collect step drops globstar too, matching its patterns with Python's recursive glob, since an extra can run on macOS

## v0.6.4 · 2026-11-02

- The build step no longer sets `TAURI_CONFIG`: tauri-build parses that variable as JSON, so the empty value an app without extra settings got stopped every app that builds with its own commands ("EOF while parsing a value"), as formtray's first run showed. The extra settings travel as `FORMCOMPILER_EXTRA_CONFIG`, and an empty `TAURI_CONFIG` is dropped before the build

## v0.6.3 · 2026-11-02

- A build an app runs with its own commands now gets formcompiler's Tauri settings: they are merged into the app's `tauri.<os>.conf.json`, which Tauri reads whatever command builds it. Before, only builds that passed `$FORMCOMPILER_CONFIG_ARG` saw them, so format, formencoder, formlit, formportal, formsurface and formvfx built without the updater key, the updater artifacts or the store's update address
- A beta's Windows MSI gets a version Windows Installer accepts: `X.Y.Z-beta.N` builds as MSI version `X.Y.Z.N` (`bundle.windows.wix.version`), where Tauri refused a non-numeric prerelease and the MSI step failed

## v0.6.2 · 2026-11-02

- FormPortal's registry notes name its update feed in the download store, `https://dl.formai.studio/formportal/updates/latest.json`, which formportal 0.53.5 reads, instead of the GitHub `formportal-updates` release on this private repository. No build or release behaviour changes.

## v0.6.1 · 2026-10-30

- The family moves from the personal account `nodemode-ai` to the organisation `nodemode-dev`: the workflows' repository guards (`github.repository == 'nodemode-dev/formcompiler'`), every registry `repository`, the scripts, tests and docs name `nodemode-dev/...`, and the container images become `ghcr.io/nodemode-dev/...`. Merge right after the transfer: before it, the guards skip every job. The GCP trust rule changes with it in formai.tools (`infra/formai_infra/downloads.py`).
## v0.6.1 · 2026-10-31

- The Linux runners of format, form.md, formcut, formlit, formpromo, formwav, formvfx, formref and formtxt install GStreamer's base and good plugins, which their AppImages now carry (`bundleMediaFramework`) and their deb and rpm packages recommend

## v0.6.0 · 2026-10-30

- macOS builds import the Developer ID into a temporary build keychain before the build, so apps that sign their engine before `tauri build` (formvis, formtxt, formpromo, formcel, formDAM) sign with it; the keychain is removed after the job
- Every macOS disk image is signed, notarized and stapled, including the ones apps make themselves with hdiutil and formDAM's under `src-tauri/target.nosync`
- Every form* app builds for macOS, Linux and Windows: formref is enabled, formsurface gains windows-x64, and every Windows build passes formcompiler's config
- Registry fixes from the family audit: formdeck builds Windows under cmd, format gets nasm and pkg-config, formMCP gets libdbus, formweb builds rpm and AppImage, formcut signs macOS with the Developer ID and ships its NSIS installer, formvis asks for macOS 14
- The disabled-app test runs on a held-back copy of the registry
- Updater settings (`plugins.updater`, `createUpdaterArtifacts`) go only to apps whose registry says `updater.tauri: true`; with the updater key set, an app without the plugin, such as formwav, no longer fails to compile on Tauri's generated context
- formvis drops macos-universal, windows-x86 and windows-arm64: its pinned native wheels do not exist for them

## v0.5.0 · 2026-10-30

- Windows builds are signed through Azure Artifact Signing (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` secrets; `ARTIFACT_SIGNING_ENDPOINT`, `ARTIFACT_SIGNING_ACCOUNT`, `ARTIFACT_SIGNING_PROFILE` variables): every Tauri app is signed during its own build whatever command builds it, and any `.exe`, `.msi` or exe inside a `.zip` still unsigned is signed after it, with its updater signature made again. Only Windows runners are affected
- formcut's Windows builds are signed (`apps/formcut.json`)
- The name and Team ID inside the Apple signing identity are masked in build logs
- The release gate hardening, the stable-while-beta and feed rollback fixes, and the download store work listed under unreleased in `scripts/HASHOUT_LOG.md` ship in this version

## v0.4.8 · 2026-10-26

- A test suite checks the registry, the release matrix (disabled apps never reach it), every app's version source, catalogue signing against the vector FormPortal's verifier accepts, and the skills archive, and runs in self-check on every change.

## v0.4.7 · 2026-10-25

- The app-plus-FormPortal README says the app is all that is needed and FormPortal is optional, not something to install first; nothing in the bundle installs it

## v0.4.6 · 2026-10-25

- A registry entry can set `with_portal`: each desktop installer of that app's release gets a second download with FormPortal's matching installer beside it, checked against the catalogue. Off for every app until its owner turns it on; the normal downloads and the catalogue are unchanged

## v0.4.5 · 2026-10-25

- FormRanker's entry declares its MCP server (`agents.mcp`), served by the installed app as `formranker mcp` from FormRanker 0.8.0

## v0.4.4 · 2026-10-25

- FormRanker joins the registry (`apps/formranker.json`): the desktop app from FormRanker 0.7.0, a Tauri shell with the engine frozen by PyInstaller, built by its own `build_app` on macOS and Linux and `build_app.bat` on Windows

## v0.4.3 · 2026-10-24

- `docs/ACCOUNTS.md`: the family's GitHub OAuth app for FormPortal's optional sign-in, registered once by the owner (device flow on, expiring tokens off); only its public client ID is used
- FormPortal's Linux build installs `libdbus-1-dev` (`apps/formportal.json`), for the keychain its sign-in uses

## v0.4.2 · 2026-10-24

- The catalogue keeps the newest release of every earlier major version in each app's history, beside the five newest earlier releases (`scripts/catalog.py`)

## v0.4.1 · 2026-10-24

- formMCP and formskills are in the registry (`apps/formMCP.json`, `apps/formskills.json`): built on macOS, Linux and Windows from their own `build_app`, released as drafts, in the catalogue as `formmcp` and `formskills` (identifiers `ai.nodemode.formmcp`, `ai.nodemode.formskills`) once they have a release

## v0.4.0 · 2026-10-24

- Every release carries `form-app.json` (format_version 2: the app's id and version, whether it has an MCP server, and its skills with their names and descriptions) and `<app>-skills-v<version>.zip` (its `.claude/skills`, the same bytes for the same tree), both checked before the release is drafted and both in `SHA256SUMS.txt`
- The registry's new `agents` block names each app's skills folder and whether it has an MCP server; the catalogue carries both per product, and the manifest and skills archive (URL, size, SHA-256) per release
- The catalogue reads formcompiler's own `SHA256SUMS.txt` before an app's `SHA256SUMS`

## v0.3.3 · 2026-10-24

- The copyright holder in LICENSE, NOTICE and the README is NodeAgentc, Inc.

## v0.3.2 · 2026-10-23

- formencoder's releases attach the LAME 3.100 source (its LGPL source offer), checked against its pinned SHA-256, and a `delivery-tools-PLATFORM.txt` for each platform listing the delivery tools staged in that bundle

## v0.3.1 · 2026-10-23

- macOS builds of formDAM, formlit, formvis, formpdf and formtxt install OpenCV from source without FFmpeg, because the macOS wheels carry GPL codec libraries
- Format and formcut build with the MSVC environment on Windows, for their LGPL PyAV build; Format's releases attach the FFmpeg source its PyAV links

## v0.3.0 · 2026-10-22

- formcompiler now builds the apps itself: the app repositories only run checks, and a `compile_vX.Y.Z` branch pushed to an app starts its release here
- `watch.yml`: every 8 hours and on Run workflow, finds compile branches in every registered app and starts the ready ones; refuses a branch whose version file disagrees or whose checks failed, waits while checks run, skips what is published, drafted or running
- `release.yml`: gate, the desktop matrix, extra jobs (phone apps, tarballs, Flatpak, server binaries), a container image, the app's own release assets, release notes from its CHANGELOG, and a draft `<app>-vX.Y.Z` on this repository
- `feed.yml`: on publish, the app's `<app>-updates` release (latest.json and update files) and the family catalogue (`releases.json` on main, `apps.json` and `apps.json.sig` on the `catalog` release) in FormPortal's schema
- The registry: `apps/<app>.json` for 21 apps (formref disabled until its bundle can be built), contract in `docs/REGISTRY.md`, validated by `scripts/registry.py check`
- Signing in formcompiler only: Apple Developer ID and notarization, the Windows certificate, the updater key and the catalogue key; builds are ad hoc (macOS) and unsigned (Windows) until they are set
- New platforms `macos-universal` and `windows-x86`, experimental platforms, per-platform environment, a post-build hook, Go
- The caller template and `docs/ADOPTION.md` are removed; FormPortal's `-update.app.tar.gz` is no longer renamed when staged

## v0.2.1 · 2026-10-18

- NOTICE, README and the pipeline log describe formcompiler as nodemode-ai's own work; history rewritten to match before any push
- No change to the workflows or scripts

## v0.2.0 · 2026-10-18

- `rust-targets` input: extra Rust targets on every runner (formwav's `wasm32-unknown-unknown`)
- `windows-msvc` input: MSVC developer environment on Windows through `ilammy/msvc-dev-cmd` v1.13.0 (formencoder)
- Build commands see `FORMCOMPILER_OS`, `FORMCOMPILER_ARCH` and `FORMCOMPILER_TRIPLE`; each platform preset carries its Rust target triple (formcut, formportal)
- formcut and formwav move to ready to try in `docs/ADOPTION.md`
- Not yet run on GitHub; the repo is private and unpushed

## v0.1.0 · 2026-10-18

- Reusable workflow `desktop-release.yml`: plan, build per platform, draft release with `SHA256SUMS.txt` and `latest.json`
- Scripts `plan.py`, `run_build.py`, `tauri_config.py`, `stage.py`, `release_assets.py`
- Caller template `templates/desktop.yml` and per-app guide `docs/ADOPTION.md`
- Self-check workflow: actionlint 1.7.12, Python compile, a plan run
- Not yet run on GitHub; formvis is the first planned adopter
