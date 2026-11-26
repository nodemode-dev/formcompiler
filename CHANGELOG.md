# Changelog

## v0.24.0 · 2026-11-26

- `adaptor.yml` proposes formadaptor's generated files to its targets (formMCP, formskills, form.ext, formai-templates) at minute 48 of every hour, 15 minutes after formadaptor publishes the family spec, and on demand for one target. formadaptor's scripts are checked out at main; formadaptor holds no secret.
- Three stages: `plan` runs each target's generator with no secret and keeps a plan when there is a change; `changed` lists the targets with a plan; `propose`, the only job in the `release` environment, pushes a `bot/formadaptor-*` branch and opens the pull request, and runs no target code. A target that is missing or that the App cannot reach is skipped with one summary line.
- The token is the release App's only, minted per target with Contents and Pull requests, read and write; the write token is not a fallback.
- For the owner, once: accept the new Pull requests permission on the organisation's installation of the release App, and install it on the four targets (docs/ACCOUNTS.md). The workflow has not run yet; the first run is the test. No test was added.

## v0.23.0 · 2026-11-25

- The launch dates of two groups changed places. FormNET, FormSlot and FormSubstrate go out on 25 November; FormPromo, FormRig and FormCraft on 28 November. The v0.22.0 entry below names 25 November for FormRig and FormCraft: that is now 28 November. No entry carries a date, so nothing in a build changes with this; an app is built when its release is started.
- FormSlot is registered: `apps/formslot.json` builds `nodemode-dev/formslot` for Apple silicon and Intel Macs, Linux and Windows, as a draft release. It is a command line program with no window, so its release files are the archives its own `setup/build_release` packs, with a disk image on macOS for notarization, and the Windows start check is off.
- FormSubstrate is registered: `apps/formsubstrate.json` builds `nodemode-dev/formsubstrate` for the same four platforms, as a draft release, in commands mode. The application is Substrate. Linux makes deb, AppImage and rpm.
- Catalogue entries: `formslot`, memory, GPL-3.0-only; `formsubstrate`, workbench, GPL-3.0-only, macOS 11. Both in prelaunch. Neither has a Tauri updater.
- FormNET's entry names its skills folder and its MCP server, so its releases carry `form-app.json` and a skills zip like the other apps that have them.
- For the owner, once: the read token needs access to `formslot` and `formsubstrate` before their first build. None of the three builds has run yet; the first run is the test.
- The README counts 37 registered apps, all enabled, and 512 tests. No test was added; the count rose because several tests run once per registered app.

## v0.22.0 · 2026-11-23

- FormRig and FormCraft are registered for the Group 6 launch of 25 November: `apps/formrig.json` builds `nodemode-dev/formrig` and `apps/formcraft.json` builds `nodemode-dev/formcraft` for Apple silicon and Intel Macs, Linux and Windows, as draft releases on their private repositories. FormPromo was already registered.
- Both build in contract mode: each launcher has `install`, `install-desktop` and a `desktop build` that passes `--config` on to Tauri, in bash and in its `.bat`. Each freezes a Python engine with PyInstaller, a signed one-folder engine on macOS and a one-file sidecar elsewhere.
- Catalogue entries: `formrig`, rigging, Apache-2.0, `.frig` and `.frgreturn`, macOS 12; `formcraft`, generation, Apache-2.0, `.fcrft`, macOS 14. Both in prelaunch. FormCraft has the Tauri updater; FormRig has none yet.
- For the owner, once: the read token needs access to both repositories before their first build. FormCraft's own `ci.yml` has not run on main since 6 November (a job-level `runner.temp` GitHub refuses); its fix is a separate pull request in that repository and must merge before FormCraft's first build.
- Neither build has run yet; the first run is the test. The README counts 35 registered apps, all enabled, and 506 tests. No test was added.

## v0.21.0 · 2026-11-21

- FormMorpheus is registered: `apps/formmorpheus.json` builds `nodemode-dev/formmorpheus` for Apple silicon and Intel Macs, Linux and Windows, as a draft release on its private repository. Its catalogue entry is `formmorpheus`, Apache-2.0, `.fmo`, macOS 11, in prelaunch.
- FormPublisher is switched on. Its entry was drafted while the repository was blank; it now follows the repository at 0.3.3: licence GPL-3.0-only, a summary of what the build does, macOS 13, no Tauri updater, and a build that collects its bundles from `src-tauri/target`.
- Both build in commands mode: neither launcher has the `install-desktop` command, and neither desktop build accepts `--config`, so contract mode would stop. formcompiler's Tauri settings reach both builds through the `tauri.<os>.conf.json` it merges before every build. Linux makes deb, AppImage and rpm; Windows runs each app's `build_app.bat` and prints its log when it fails.
- For the owner, once: the read token needs access to both repositories before their first build. Neither build has run yet; the first run is the test.
- The README counts 33 registered apps, all enabled, and 501 tests. No test was added; the test for disabled apps has none to check now and is reported skipped.

## v0.20.0 · 2026-11-20

- FormPortal's "What changed" on an Updates row, and the What's new tab of an app's page, can now show what a release brings. Until now both showed one line: the address of the release page.
- The catalogue's `notes` for a release is the What's new part of its page, as plain text, when the page starts with the line `<!-- formai-notes -->` and a `## What's new` heading. A page without that keeps the address, so nothing changes for a release nobody has written notes for.
- The text stops before the page's table of files and before formcompiler's own last lines, loses its heading marks, backticks and bold marks, and is cut at 4000 characters.
- No app is rebuilt. The feed's next pass writes the text for every release whose page has it, older versions included. No workflow changed.
- The README counts 497 tests: one new test for this.

## v0.19.0 · 2026-11-19

- A new workflow, `binaries`, builds FormCAD's two worker programs, the OpenCascade kernel and the Netgen mesher, which the app downloads from `nodemode-dev/formai-binaries` and does not carry. It is started by hand with the worker, a release number and whether to release.
- The workers are frozen on four runners (Apple silicon, Intel Mac, Linux, Windows), signed and notarized with the values the app builds already use, started once after signing, recorded and packed by FormCAD's own scripts. With `publish` checked a draft release `occt-<release>` or `mesher-<release>` opens in formai-binaries; a person publishes it. Without it the run is a full rehearsal that stops before the release.
- Two short checks run before any Mac or Windows runner starts: every signing value is present, and, when releasing, the release credential can create a release in formai-binaries and the tag is free.
- For the owner, once: the release GitHub App has to be installed on `formai-binaries` (docs/ACCOUNTS.md). Nothing is asked of FormCAD's repository.
- The workflow has not run yet; its first run is its test. The README counts 7 workflows and 496 tests (the fork guard now covers the new workflow). No test was added.

## v0.18.0 · 2026-11-19

- Every Windows build is tried on its runner before it is staged: the installer the build made is installed, the app is started, its window is looked for, it is closed, nothing of it may be left running, and it is started a second time. The second start is the case a tester hit, where a leftover engine kept an app from opening.
- The check also looks for an error dialog, such as the "Unhandled exception in script" a tester saw from FormWeb's engine, and starts each helper program alone with no console to see that none shows one.
- The result is a table in the job summary and a small report kept with the run. It does not fail a build yet: a new registry field, `windows_start_check`, is `report` for every app, and can be set to `gate` once the check has proven itself, or `off`.
- The Windows and Linux build job may run 56 minutes, was 49, so the check has room after a long build.
- None of the check's Windows code has run before the first Windows build after this release; its first reports are also the test of the check itself.
- The README counts 23 Python scripts. No test was added.

## v0.17.2 · 2026-11-19

- The gate waits for the app's own checks. A release started while the app's CI is still running on that commit now waits for it, up to 45 minutes, and goes on when it passes. Before, it stopped with "checks not finished", as FormCel 0.44.0 did minutes after its merge.
- A check that failed still stops the release at once, with its name.
- A run that stopped at the gate does not count as a failed build. The watch starts that commit once its checks pass, without anyone using Again. A build that failed is held as in v0.17.1.
- After the watch starts a commit, an older run of the same commit can no longer make it start a second time.

## v0.17.1 · 2026-11-19

- The watch builds a commit once. It keeps a record of every release run it has seen or started, by app and commit, and does not start a commit again when its run failed, was cancelled, is still running or waits for approval of its release. On 2026-11-19 it had started FormVis 2.3.6 a second time after the first run of the same commit failed, and FormSculpt 1.21.1 after a person had already run it.
- The record outlives the run. Deleting a failed run from Actions no longer makes the watch start that commit again on its next pass.
- A run a person starts with a branch or tag name counts too. Before, the watch knew a run only by a title that ended in the full commit id.
- A new version, or a new commit on the same compile branch, builds as before.
- Run workflow on the watch has a new field, Again: an app's name there starts that app's held commit once more. Re-run failed jobs on the failed run works as before, and the watch then shows that commit as running.
- The watch's summary says why each commit is held: failed, cancelled, running, waiting for approval, succeeded, or started with no run to show for it.
- The README counts 22 Python scripts. No test was added: the change is to be seen on GitHub first.

## v0.17.0 · 2026-11-19

- The gate keeps the family's version rule: `x.yy.z` with x from 0 to 9, yy from 0 to 99 and z from 0 to 9, and no zero padding. A release asked for with a version outside the rule is refused, and the message names the version to use instead: 0.15.10 is refused with 0.16.0 to use, 0.100.0 with 1.0.0, and past 9.99.9 it says to ask the owner. Prerelease versions (`-beta.N`, `-rc.N`) work as before. The watch refuses such a version too and goes on to the app's other versions. The 101 version tags in the family's public repositories, read on 2026-11-18, are all inside the rule.
- A symbolic link that leaves an app's skills folder stops the release in every case: a linked file, a linked subfolder, or a skill folder that is itself a link. A link that stays inside the skills folder is not followed, as before.
- FormCel and FormTxt declare their skills folder and their MCP server, so from its next release each carries a skills archive, and its `form-app.json` says an MCP server is available.
- The catalogue names FormDeck by that name. Its id stays `formslide`, because installed copies of FormPortal know the app by that id.
- FormPortal's catalogue identifier is `studio.formai.portal`, the app's real bundle identifier. `releases.json` keeps the old identifier and the name FormSlide until the publishing pipeline next writes it.
- The owner notes in the registry entries of FormCut, FormDAM, FormTxt, FormAT, FormTray and FormWeb match the app repositories again. Nothing a build reads changed in them.
- The documents say what the tree holds. The README's version badge, which had stayed at v0.14.5, shows the current version, and a test fails when it falls behind. The README no longer names a count of launch apps, and says the watch runs every hour and on demand and that the tick also starts it every 15 minutes. CONTRIBUTING names the six workflows, the scripts and the two documents that exist, and points at README sections that exist. `docs/ACCOUNTS.md` names the `nodemode-dev` organisation.
- The README counts 495 tests in 23 files, and 32 registered apps, 31 of them enabled.

## v0.16.1 · 2026-11-19

- FormCAD is registered (`apps/formCAD.json`): `contract` mode for Apple silicon, Intel Macs, Linux and Windows (Git Bash there), `apple` on macOS like every app since v0.16.0, rpm compression off, no updater. Its repository is private and its release stays a draft, so nothing reaches the catalogue or the download store. Its kernel and mesher workers are not in the build; the app downloads them from the `formcad/` releases of formai-binaries once the first is published.
- The README counts 473 tests in 23 files: the per-entry registry tests gain three with the new entry.

## v0.16.0 · 2026-11-18

- Every app signs its Mac builds with `apple` again: signed with the Developer ID and notarized with the App Store Connect API key. FormTray 0.16.4 proved it on both Mac platforms (run 44371292910: both disk images and the apps inside pass `spctl` as "Notarized Developer ID" and are stapled). Each app is notarized from its next release.
- Mac builds get time for Apple. A Mac build now waits on the notary twice, for the app inside the Build step and for the disk images after it, and on 2026-11-18 Apple's first answers for a new account came after the Build step's 40 minutes. Apple silicon: Build step 60 minutes, job 85. Intel: 100 and 125 (FormCut's Intel build already took 62 of its 70). Windows and Linux keep 40 and 49. The window after a Mac Build step is 25 minutes, so the disk image notarization fits after the cache saves.
- The disk image notarization has its own 15-minute limit and asks Apple at most twice, six minutes each. When Apple is still working, the step stops with an error that says the build is fine and to use Re-run failed jobs, instead of waiting until the job is killed.
- The README counts 470 tests in 23 files.

## v0.15.1 · 2026-11-18

- FormTray signs its Mac builds with `apple` again: signed with the Developer ID and notarized with the App Store Connect API key from v0.15.0. It is the first app back on the notary, through its 0.16.3 release, which stays a draft on the app repository until it is checked (FormTray's family contract allows no prerelease versions); the other apps stay on `developer-id` until its notarized disk images check out on both Mac platforms.

## v0.15.0 · 2026-11-18

- Mac builds can notarize with an App Store Connect API key instead of an Apple ID and app-specific password. Set `APPLE_API_KEY` (the key ID), `APPLE_API_ISSUER` (the issuer ID) and `APPLE_API_PRIVATE_KEY` (the base64 of the `.p8` file); a new Notary API key step writes the key to a file readable only by the runner user, the Notary check, the Tauri build, Post-build and the disk image notarization all use it, and the always-run cleanup step removes it. When the key is set the Apple ID and password are not passed to Tauri, so a build uses one notary method. Without the key nothing changes. The key needs no two-factor code, so notarization no longer depends on whoever receives the Apple ID's codes.
- The build job runs in a new `signing` environment. Its deployment branch policy admits `main` only, so a workflow pushed to any other branch cannot read the Apple certificate or the notary key kept there. An environment secret replaces an organisation or repository secret of the same name, so the Apple secrets move into `signing`; the gate holds once the repository and organisation copies are removed, which follows the merge (docs/ACCOUNTS.md, "Mac signing and notarization"). The decoded key's lines are masked in the logs, and the cleanup step removes the key's whole folder. The environment has no required reviewer, so builds do not wait.
- The README counts 467 tests in 22 files.

## v0.14.5 · 2026-11-17

- FormFabric 0.25.1, FormSculpt 1.21.0 and FormSurface 0.62.1 are yanked until their release on Thursday 2026-11-19 at 12:00 EST. v0.14.4 alone did not take them out: the publishing pipeline refuses to publish a catalogue that loses every release of an app the store lists today unless those versions are yanked, so the first feed after v0.14.4 stopped and published nothing, and every later feed would have stopped the same way. The builds are sound; they were published before their date. To release them: remove their three rows from `yanked.json`, make the three repositories public and start a feed.

## v0.14.4 · 2026-11-17

- A release on a private app repository is no longer listed in the catalogue. FormSculpt 1.21.0, FormSurface 0.62.1 and FormFabric 0.25.1, due on Thursday 2026-11-19 at 12:00 EST with their repositories still private, had their drafts published on the night of 2026-11-16, and the catalogue of 2026-11-17 10:02 EST offered all three, so formai.studio and FormPortal showed them as released two days early. `catalog.py build` now asks GitHub whether each repository with a release is public and leaves a private one's releases out, with a notice naming it; the app stays listed with no release, which is how both show an app that is not out yet. An app opens when its repository is made public. A dry run with `--releases FILE` is unchanged. The files of those three releases are already in the download store; taking them down is the publishing pipeline's side.

## v0.14.3 · 2026-11-16

- A Mac build under `signing.macos` `apple` no longer fails while Apple's notary refuses the account. Before the build, a new Notary check step asks the notary for the account's history; when the answer is that a required agreement is missing or has expired, that one run builds as `developer-id` does (signed with the Developer ID, nothing sent to the notary) and shows a warning. Any other answer changes nothing, and the first run after the agreement is accepted is notarized again. No registry entry changed. FormRef 0.39.2, FormWeb 0.21.2, Format 0.26.3, form.ext 0.4.1, FormMCP 0.10.4 and FormPortal 0.64.1 failed on both Mac platforms on 2026-11-16 at notarization with that 403; start a new release run for each, because re-running the failed jobs keeps the old workflow. A fallback build is not notarized, so macOS does not open it on a plain double-click the first time. Unproven until a Mac run: that the history request gets the same 403 as a submission; if it does not, the build fails at notarization as before.
- Every registered app now signs its Mac builds with `developer-id`, not just the six that did. Apple's notary still answers 403 (a required agreement is missing or has expired): at 17:32 to 17:37 UTC on 2026-11-16 the releases of FormAT 0.26.3, FormRef 0.39.2 and FormWeb 0.21.2 (Group 3, due 17:00), and of form.ext, FormDeck, FormMCP, FormPortal, FormSkills, FormPath, FormVis, form.md and FormDesign, all stopped at `failed to notarize app` on both Mac runners. Their Mac builds ship signed but not notarized, so macOS asks once before the first open. Switch every entry back to `apple` once the account holder accepts the agreement and a notarization succeeds.

## v0.14.2 · 2026-11-13

- The Intel Mac wheel downloads retry five times on any error, a connection reset included (`--retry-all-errors`). FormTxt 0.32.0's Intel build (run 43485904101) stopped on `curl: (56) Recv failure: Connection reset by peer`, which plain `--retry` does not retry.

## v0.14.1 · 2026-11-13

- A fourth macOS signing mode, `developer-id`: the app is signed with formcompiler's Developer ID certificate as `apple` signs it, but no Apple ID, password or team id reach the build and the disk images are not sent to the notary service. Since about 14:40 UTC Apple's notary answers 403 (a required agreement is missing or has expired) for every Mac build; until the account holder accepts it, FormCel, FormTxt and FormTools ship signed but not notarized, so macOS asks once before the first open. Switch them back to `apple` once notarization works.

## v0.14.0 · 2026-11-13

- FormTxt's Linux build passes `--bundles deb,appimage`, as FormCel's does. With no bundle targets set, Tauri also built an rpm, and FormTxt 0.32.0's rpm step ran silent for 35 minutes until the 40-minute limit stopped the job (release run 43443905509).

## v0.13.9 · 2026-11-13

- Windows desktop builds set `PY_PYTHON` and `PY_PYTHON3` to the recipe's Python, so an app launcher's `py -3 -m venv` makes a 3.12 venv instead of taking the newest Python on the runner (3.15). FormTxt 0.32.0 and FormTools 0.8.0 failed on Windows because onnxruntime and rawpy have no Python 3.15 wheels.

## v0.13.8 · 2026-11-13

- FormTools is registered (`apps/formtools.json`) for Apple silicon, Intel Macs, Windows and Linux, in contract mode after FormPath and FormDesign: `install`, `install-desktop`, then `desktop build`, with `formtools.bat` under cmd on Windows. It is in launch Group 2 with FormCel and FormTxt. The catalogue entry follows formai.studio's `catalog/products.json`.

## v0.13.7 · 2026-11-12

- Two more Intel Mac wheels in `deps-macos-x64.json`, built from source and checked by an inference run on x86_64 Python: onnxruntime 1.31.0 for Python 3.14, which FormPDF's OCR set-up uses, and onnxruntime 1.30.0 for Python 3.12, which FormWav pins. Both 0.60.3 and 2.26.3 still failed for Intel with the 1.31.0 Python 3.12 wheel alone, after the hash check had passed. FormDAM 1.29.0 shipped for Intel with v0.13.6.

## v0.13.6 · 2026-11-12

- Intel Mac builds download the wheels listed in `deps-macos-x64.json` from https://storage.googleapis.com/formai-dl/deps/macos-x64/, check each against the SHA256 committed there, and only then point pip at that local folder (`PIP_FIND_LINKS` and `UV_FIND_LINKS`, set only on `macos-x64`). A file that does not match fails the build, so write access to the bucket alone cannot change what goes into a signed build. onnxruntime publishes no Intel Mac wheel after 1.23.2 and cryptography none after 48.0.1, so FormWav 2.26.3, FormPDF 0.60.3 and FormDAM 1.29.0 failed to build for Intel. The index holds onnxruntime 1.31.0 and cryptography 50.0.1 and 50.0.2, built from source for macOS 14 or later on x86_64, with SHA256SUMS and onnxruntime's licence and notices. Other platforms still install from PyPI only.
- The README counts 448 tests in 21 files.

## v0.13.5 · 2026-11-11

- Every app with a Mac build builds for Intel Macs by default (Greg, 2026-11-11). `macos-x64` is now required, not optional, for FormVFX, FormPDF, FormVis, Form.ext, FormRec, FormSculpt, FormSurface, FormPromo and FormPublisher, as it already was for the rest; each is built natively on `macos-15-intel`.
- `registry.py check` refuses an entry with a Mac build that does not list `macos-x64`, or lists it only as optional `macos-x64?`, so a new app cannot ship without an Intel build. Entries with no Mac build are unaffected.
- The README counts 445 tests in 20 files.

## v0.13.4 · 2026-11-11

- Intel Macs get a build of FormWav too: `apps/formwav.json` lists `macos-x64`, built natively on `macos-15-intel`. FormWav 2.26.2 shipped without one, so Intel Macs were sent to the download page.

## v0.13.3 · 2026-11-11

- A tick that cannot make sense of the list of tick runs (a listing that is not an object, a run that is not one, or a run without an id) now reports it as a warning and keeps its 15-minute clock, as it does when GitHub cannot be reached. Before, the error ended the loop on its second pass without saying whether it yielded, so its successor started at once.
- The tick's survival on bad data has regression tests: a feed state that is not a string, a registry that is not an object, an unexpected error from the watch dispatch, and the malformed run listings above.
- FormRec's notes for the owner say the entry matches FormRec 0.9.0's desktop build; it was checked against 0.9.0 and is unchanged.
- Intel Macs get a build of FormDAM, FormDesign, FormCel, FormTxt, FormRef and FormWeb: each lists `macos-x64`, built natively on `macos-15-intel` like FormPath and Format. FormDesign's `core-macos-x64` extra is gone, because its Intel build now makes the `x86_64-apple-darwin` layout core itself; two copies would collide in the release files.
- The README counts 441 tests in 20 files.

## v0.13.2 · 2026-11-11

- FormPublisher is registered, disabled: `apps/formpublisher.json` names `nodemode-dev/formpublisher`, which is private and has no code yet, so nothing builds, watches or feeds it. Its build fields are the family's Tauri defaults and its catalogue entry is `formpublisher`, Apache-2.0, in prelaunch; the notes for the owner list what to confirm before enabling it.
- The README counts 434 tests in 19 files.

## v0.13.1 · 2026-11-10

- A tick that meets bad data, such as a feed state the store wrote in an unexpected shape, now reports it as a warning and a line in the summary and keeps its 15-minute clock. Before, the error ended the tick at once and its successor started straight away, so the chain restarted about once a minute until someone cancelled a run.
- The v0.13.0 entry above and the pipeline's rationale log now describe FormRec's registry entry as it was merged: version from `src-tauri/tauri.conf.json`, no Python, `zip` on Linux, and its two skills from `.claude/skills`.
- The README counts what is in the repository: 6 workflows (with `tick` and the Windows signing check), 21 Python scripts and 432 tests in 19 files.

## v0.13.0 · 2026-11-10

- FormRec, the recorder for walkthroughs, podcasts, corporate messages and live feeds, is registered. `apps/formrec.json` follows FormCut's build: commands mode, `setup/build_release --target $FORMCOMPILER_TRIPLE` on every desktop runner, the release zips and the Windows NSIS installer from `release-dist/`, with the Node 22 server as the Tauri sidecar. Its version comes from `src-tauri/tauri.conf.json` and its check is `ci.yml`. No Python is set up; `zip` is installed on Linux for the Linux zip. Its catalogue entry is `formrec`, Apache-2.0, in prelaunch, with an MCP server and the formrec-harness and formrec-skillset skills from `.claude/skills`. The Intel Mac build is experimental for its first release, and its notes for the owner describe FormRec 0.3.0's build outputs, signing and seal check.

## v0.12.3 · 2026-11-10

- Releases start and reach the download store without anyone dispatching a workflow. A new `tick` workflow starts the watch every 15 minutes, because GitHub ran the watch's hourly schedule only every 4 to 10 hours. One tick keeps the clock for about five and a half hours, then starts its successor with the Actions token; its own `*/15` schedule restarts the clock if the chain ever breaks, and a scheduled run that finds a tick already running stops at once. On each tick it also reads the store's feed state and every app's releases, and when a release published by hand (every stable release) is not in the store yet it sends formpipe the same `formcompiler-published` dispatch the publish step sends for prereleases, with the existing `FORMPIPE_DISPATCH_TOKEN`. A GitHub hiccup is retried, then reported as a warning; it never fails the tick. Approving and publishing stay manual.
- FormCut's build cache is also keyed on `backend/prepare_cv.py`, so a change to OpenCV's build flags builds again instead of restoring an older wheel.

## v0.12.2 · 2026-11-09

- A registry entry can cache folders its build makes and reuses: `toolchain.build_cache` names the folders and the files whose contents key them. FormCut and Format cache their LGPL FFmpeg (`backend/.lgpl-ffmpeg`) on every platform, keyed on the app, the platform, the runner and a hash of the scripts that build it, so a new FFmpeg version or configure line builds again. Their scripts skip the FFmpeg build when the folder is there; FormCut 2.15.1's Intel Mac build spent 16 of its minutes on it. The cache restores only on its exact key, saves after a failed or timed-out build too, and no other app has one. FormCut also keeps its macOS pip wheels, which takes effect once its OpenCV and PyAV installs stop passing `--no-cache-dir`; the pip key of an app with a build cache includes the build cache's hash, so a PyAV built against an older FFmpeg is never restored.

## v0.12.1 · 2026-11-09

- Intel Mac builds get 70 minutes for the Build step and 79 for the job; every other platform keeps 40 and 49. FormCut 2.15.1's `macos-x64` build hit the 40-minute step limit twice, the second time with its caches already saved, while its other platforms built well inside it. The 9 minutes between the step and the job, which let the caches save after a timed-out build, stay the same for every platform, and a test keeps them.

## v0.12.0 · 2026-11-08

- form.ext, the extension studio, is built here. `apps/form.ext.json` registers it with its own `build_app` and `build_app.bat` in commands mode, since it has no `install-desktop` and its `build_app` takes no `--config`; signing reaches it through `src-tauri/tauri.<os>.conf.json` as for every app. The Rust build is pointed at `src-tauri/target` (its default is a cache folder outside the checkout), the macOS build no longer copies itself into `/Applications` on the runner, Linux adds rpm and AppImage to the deb, and a failed Windows build prints `build_app.log`. Its catalogue entry is `formext`, GPL-3.0-only, macOS 13 or later. Intel Mac and Linux ARM builds are experimental for its first release.

## v0.11.0 · 2026-11-06

- FormCut builds for Intel Macs too. Its registry entry adds `macos-x64`, built natively on GitHub's `macos-15-intel` runner like every other app's Intel build, so FormCut releases carry a `formcut-<version>-macos-x64.zip` beside the Apple Silicon one. FormCut's own `setup/build_release` accepts `x86_64-apple-darwin` from 2.12.2; a test checks FormCut lists both Mac platforms.

## v0.10.0 · 2026-11-06

- FormCut's Apple Silicon build runs again. Its registry entry asked for the `macos-14` runner image, which GitHub no longer starts: the job was cancelled at once with no runner, twice for 2.11.9, so FormCut never reached a draft. It now uses the default Apple Silicon runner like every other app, and a test refuses any registry entry that pins a retired image (macos-12, macos-13, macos-14)

## v0.9.9 · 2026-11-05

- Windows file names keep their platform for apps that build with MSVC. The Stage step read `PLATFORM`, but MSVC's environment sets `Platform`, Windows merges the two names, and Git Bash then sees an empty `$PLATFORM`: FormEncoder's installers came out as `formencoder-0.5.5--setup.exe` and `formencoder-0.5.5-.msi`. The step now uses `STAGE_PLATFORM`, and a test keeps `PLATFORM` out of it

## v0.9.8 · 2026-11-05

- Windows signing of programs inside a release zip works. `sign_zip` rebuilt the zip in a temporary folder and moved it into place only after that folder was deleted, so every app whose release carries a zip with programs inside (FormVis's portable zip) failed with `FileNotFoundError ... rebuilt.zip` as soon as signing was on. The zip is now moved before the folder goes, with the original closed first so Windows lets it be replaced; `tests/test_sign_zip.py` covers it

## v0.9.7 · 2026-11-05

- A `windows signing check` workflow, started by hand, signs one small program through Azure Artifact Signing with the same setup as the release builds and prints Azure's answer (signtool `/v /debug`). It needs no app, makes no release and does not need `ARTIFACT_SIGNING_ACCOUNT` set (the account is an input), so it can run while Windows releases stay unsigned. It runs in the `release` environment, so it waits for a reviewer before the Azure secrets open

## v0.9.6 · 2026-11-05

- The draft release is made for every app again. An app with no extras and no container image (most of them) had its `draft release` job skipped after every build passed, because GitHub skips a job whenever any earlier job in its chain was skipped; the job now runs when the gate and the release files succeed, as the release files job already did. Only form.md, which has both, reached a draft on 2026-11-05
- Windows signing prints Azure's own answer when it fails. Signing through Azure Artifact Signing failed on every app with only "An unexpected internal error" or "No signature found"; signtool now runs with `/v /debug`, so the build log shows why Azure refused (sign-in, permission, profile) and which file was signed. Nothing else in the builds changes

## v0.9.5 · 2026-11-05

- The README's status note no longer counts the apps in the catalogue, the version badge reads `v0.9.5` like the app repositories', and the test count is 364 in 15 files. Nothing in the builds changes

## v0.9.4 · 2026-11-04

- FormLit, FormPDF and FormVis bundle their Linux rpm without compression (`build.tauri_config`): with their large PyInstaller engines, Tauri's rpm step ran single-threaded past the Build step's 40 minutes (FormPDF and FormLit timed out on a 16-vCPU VM; FormVis took 25 of its 30 minutes there). Without compression the whole Linux build took 6.4 and 8.5 minutes
- FormVis installs `zsync` on Linux and moves the `.AppImage.zsync` that linuxdeploy writes outside the bundle folder into `bundle/appimage/`, where the artifact glob and the AppImage's embedded update information expect it

## v0.9.3 · 2026-11-04

- macOS setup for the apps that build OpenCV from source (FormDAM, FormLit, FormPDF, FormTxt, FormVis) turns off OpenEXR, VTK, Qt, GTK and Eigen, so OpenCV no longer links whatever the runner's Homebrew has (a local build bundled OpenEXR dylibs that need macOS 26), and compiles with four jobs so a cold pip cache stays inside the Build step's 40 minutes
- macOS `brew install` lines (FormAT, FormWav) skip Homebrew's auto-update and dependent upgrades
- `tests/test_registry.py` holds every entry to both rules

## v0.9.2 · 2026-11-04

- The README follows the family template, with a terminal screenshot of the registry check and the catalogue listing in `docs/images/`, and describes v0.9.0's releases on each app's own repository. Nothing in the builds changes

## v0.9.1 · 2026-11-04

- The unified v3 app icon replaces the old formcompiler icon in `assets/`, with a 256 px copy in `assets/app-icon/`
- `.github/CODEOWNERS` adds @gbarnai beside @nodemode-ai on every rule

## v0.9.0 · 2026-11-03

- Every app release is created on the app's own repository, the registry entry's `repository`: a draft tagged `vX.Y.Z` at the gated commit, titled `<title> <version>`, with the same files as before (installers, `SHA256SUMS.txt`, `form-app.json`, the skills archive, `latest.json` for a Tauri-updater app, the extras). The app repository owns its Releases page; formcompiler is the factory and the gate and keeps no app release. A stable release of a `release: draft` app is approved by a maintainer publishing the draft there, which creates the tag
- The release files (installers, `SHA256SUMS.txt`, `form-app.json`, `latest.json`, the notes) are assembled by a job with no credential, since it runs the registry's `assets` and `notes` commands from the app's checkout; a separate `publish` job in the `release` environment checks out formcompiler only, downloads them and writes with a credential from the environment: a GitHub App (`FORMCOMPILER_APP_ID`, `FORMCOMPILER_APP_PRIVATE_KEY`, a token minted for the one repository being released) or, without it, the fine-grained token `FORMCOMPILER_WRITE_TOKEN` (`scripts/release_credential.sh` chooses). The build jobs keep the read-only `FORMCOMPILER_APP_TOKEN`. With neither secret the `publish` job fails and names docs/ACCOUNTS.md, which says how to set either up, that the environment allows `main` only, and that the organisation ruleset `release tags` needs the App or the token's user on its bypass list and no other
- A draft is only changed while it is still a draft: the publish job reads `isDraft` again before each asset deletion, the edit and the upload, and stops if someone published it meanwhile. Older drafts are deleted by release id after reading each is still a draft. The gate refuses a `v<version>` tag that already exists at another commit, since GitHub would make the release at that commit
- The publish job creates the tag `v<version>` at the gated commit itself, right before the draft, reads it again (annotated tags followed) when it already exists, moves it when a draft of the same version is rebuilt from a newer commit, deletes it with a superseded draft, and refuses any other tag at another commit; the tag is read once more before a beta or a `release: publish` app is published. The gate and the watch accept an existing tag only at the gated commit or at a commit formcompiler built for that version
- `form-app.json` carries `repository` and `tag` beside `app`, `version` and `commit`, and `agents.py check` requires them. The publish job attests the provenance of `SHA256SUMS.txt` and `form-app.json` (`actions/attest-build-provenance`, `id-token: write`, `attestations: write`) before the draft is made, so the publishing pipeline verifies each release came from this workflow and is the release it claims to be (`gh attestation verify <file> --repo nodemode-dev/formcompiler --signer-workflow nodemode-dev/formcompiler/.github/workflows/release.yml` on both, the manifest's app, version and repository matched, then the files checked against the sums). The repository variable `FORMCOMPILER_ATTEST=off` skips it while formcompiler is private, where GitHub refuses attestations; remove the variable once public
- Tags are `v<version>`, no longer `<app>-v<version>`; the gate's `tag` output, `versions.py`, `readiness.py`, `yank.py` and `plan.py` (whose `--tag-prefix` is gone) follow. The release list every rule reads (published, drafted, superseded, version must go up) is the app repository's, read with the app-side token. Any `v<version>` release the app repository published before formcompiler counts as published
- The watch skips a commit whose release run already succeeded (runs since the v0.9.0 cut-over, the newest 100): a read-only token sees no draft on the app repository, so without this a drafted commit would be rebuilt every hour. Run workflow on release.yml builds the same commit again
- formvis's `assets` command builds its own feed from `$FORMCOMPILER_TAG` and `$FORMCOMPILER_REPOSITORY`, which the release files job now exports beside `$FORMCOMPILER_VERSION`, instead of a `formvis-v` URL on formcompiler. formdesign's owner note says its `setup/install_core` must read the app repository's release
- `latest.json` points at `https://github.com/<repository>/releases/download/v<version>/<file>`
- `catalog.py build --asset-origin github|store` (default `store`, today's behaviour): with `github`, every app whose repository is public keeps its release's own download URLs in the catalogue, read once per entry through the API, and a private repository's files still go through the store; each release entry records `origin`. `feed.py public --asset-origin github` leaves the updater's URLs on the release; `public_urls.github_asset_url` maps a store path `<app>/<version>/<file>` back to the release asset for the pipeline and the edge redirect
- `catalog.py build --sums-dir DIR` reads each listed release's sums from `DIR/<app>/<version>/SHA256SUMS.txt`, the copy the publishing pipeline verified, instead of downloading them; a missing or empty file is an error, never a download
- `catalog.py build` takes no `--repo`: it reads every enabled entry's repository (`--releases FILE` is now a JSON object of repository to releases); `feed.py resolve`, `files` and `public` take `--app` beside `--tag` (`vX.Y.Z` or `X.Y.Z`), and `resolve` also writes `repository`, `tag` and `prerelease`; `versions.py older-drafts` and `yank.py` read the registry entry's repository. The dispatch to the publishing pipeline carries `app`, `tag` and `repository`
- The releases made on this repository before v0.9.0 (`<app>-vX.Y.Z`) are not read any more; the owner recreates on the app repositories the ones that should stay in the catalogue, or deletes them. Not yet run in Actions

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
