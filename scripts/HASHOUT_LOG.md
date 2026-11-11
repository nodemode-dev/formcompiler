# HASHOUT_LOG · pipeline · formcompiler

Living log of all comment content, explainers, rationale, TODOs and removed code for the pipeline (the scripts, the workflows and the caller template). The source files stay comment-free per dev-rules `sub-skills/hashout-log/SUB-SKILL.md`; everything they would have said lives here, indexed. Read this first, then edit code surgically.

Current build version: v0.13.2
Last updated: 2026-11-11 · FormPublisher is registered, disabled until its repository has code (v0.13.2); 2026-11-10 · the FormRec entry's record and CHANGELOG match its merged registry file (v0.13.1); 2026-11-10 · a tick's data error costs one summary line, not the loop (v0.13.1); 2026-11-10 · FormRec is registered after FormCut's build shape (v0.13.0); 2026-11-10 · releases without hand starts: the tick (v0.12.3); 2026-11-09 · FormCut and Format cache their LGPL FFmpeg (v0.12.2); 2026-11-09 · Intel Mac builds get 70 minutes (v0.12.1); 2026-11-08 · form.ext is registered and built in commands mode (v0.12.0); 2026-11-06 · FormCut builds for Intel Macs too (v0.11.0); 2026-11-06 · FormCut builds on the default Apple Silicon runner (v0.10.0); 2026-11-05 · the Stage step's platform survives MSVC's environment (v0.9.9); 2026-11-05 · signed zips are moved before their temporary folder is deleted (v0.9.8); 2026-11-05 · windows signing check workflow (v0.9.7); 2026-11-05 · signtool /v /debug, so a failed Windows signing shows Azure's answer (v0.9.6); 2026-11-05 · README status and badge (v0.9.5); 2026-11-04 · Linux rpm and zsync (v0.9.4); 2026-11-04 · macOS setup ignores Homebrew for OpenCV (v0.9.3); 2026-11-03 · releases on the app repositories (v0.9.0); 2026-11-03 · the private publishing pipeline (v0.8.0); 2026-11-03 · release file names (v0.7.1); 2026-11-03 · build minutes: hourly watch, 49-minute jobs, per-app Rust cache, macOS pip wheel cache, notarization in parallel, FormPortal's installers (v0.7.0); 2026-11-02 · formnet is formNET (v0.6.9); 2026-11-02 · formnet registered (v0.6.8); 2026-11-02 · the watch sees drafts (v0.6.7); 2026-11-02 · Git Bash, the MSVC linker and staple retries (v0.6.6); 2026-11-02 · no globstar on macOS (v0.6.5); 2026-11-02 · the build step stops setting TAURI_CONFIG (v0.6.4); 2026-11-02 · command builds get the Tauri settings, beta MSI versions (v0.6.3); 2026-11-02 · FormPortal's notes name the store's update feed (v0.6.2); 2026-10-30 · the move to the nodemode-dev organisation (v0.6.1); 2026-10-30 · the build keychain, disk image signing and the family registry fixes (v0.6.0); 2026-10-28 · the download store, tag triggers, betas and yanks (unreleased); 2026-10-28 · the watch fails when the app token cannot read, feed.yml SC2012 (unreleased); 2026-10-26 · the test suite (tests/, v0.4.8); 2026-10-25 · FormPortal optional in the bundle README (v0.4.7); app-plus-FormPortal downloads (v0.4.6); catalogue history keeps every earlier major line (v0.4.2); form-app.json v2 and the skills archive (v0.4.0); copyright holder NodeAgentc, Inc. (v0.3.3, no script changed); formencoder's LAME source and delivery tools list (v0.3.2); macOS opencv without FFmpeg, LGPL PyAV for Format and formcut (v0.3.1)

---

## v0.9.4 · Linux rpm and zsync {#v0.9.4-linux-rpm-zsync}

A linux-x64 run of the release steps for all 13 launch apps on an ubuntu-22.04 VM (2026-11-04) found two problems. Tauri's rpm bundler (default gzip through the `rpm` crate) spent one CPU thread on the 200 MB-plus PyInstaller engines of FormPDF and FormLit until the Build step's 40-minute limit; FormVis finished but spent about 25 minutes there. `{"bundle":{"linux":{"rpm":{"compression":{"type":"none"}}}}}` in `build.tauri_config` brought the whole build to 6.4 and 8.5 minutes with no app change. FormVis's AppImage embeds `gh-releases-zsync` update information, but linuxdeploy writes the `.AppImage.zsync` into its working directory and the runner image has no `zsyncmake`; the entry now installs `zsync` and its first post-build line moves the file into `bundle/appimage/`.

---

## v0.9.3 · macOS setup ignores Homebrew for OpenCV {#v0.9.3-opencv-setup}

A local run of the macOS release steps for all 13 launch apps (2026-11-04) found OpenCV, built from source because of `PIP_NO_BINARY`, linking Homebrew's OpenEXR and Imath; PyInstaller then bundled dylibs with `minos 26.0` into FormLit and FormVis, which declare macOS 12 and 14. A cached wheel also broke once Homebrew upgraded OpenEXR. The setup lines now pass `-DWITH_OPENEXR=OFF -DWITH_VTK=OFF -DWITH_QT=OFF -DWITH_GTK=OFF -DWITH_EIGEN=OFF` (FormCut's own `prepare_cv.py` set, without its module list) and `CMAKE_BUILD_PARALLEL_LEVEL=4` (OpenCV took 23 to 24 minutes serially on Apple silicon). FormVis reads EXR through its contained OpenEXR binding when OpenCV has no EXR codec. The pip cache key includes the setup line, so these entries start a fresh cache. `brew install` setups gain `HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1`.

---

## v0.9.0 · releases on the app repositories {#v0.9.0-app-repo-releases}

The owner decided on 2026-11-03 that each app's Releases page is the app repository's own: formcompiler builds, signs and gates, and creates the release where the app lives, tagged `vX.Y.Z` at the gated commit. Until now every release was `<app>-vX.Y.Z` on formcompiler, with `GH_REPO: ${{ github.repository }}` and the Actions token. The releases already made here are not migrated by anything: the owner recreates the ones the catalogue should keep (formportal 0.53.5 is the one `releases.json` lists today) on their app repositories, or deletes them; the catalogue no longer reads formcompiler's releases, so until then those apps have no channel.

### release.yml · assemble and publish: the release environment and the write credential
- refers-to: .github/workflows/release.yml :: assemble, publish :: Release credential, App token for the app repository, Create or refresh the draft on the app repository, Supersede older drafts, Publish; scripts/release_credential.sh
- kind: decision
- logged: v0.9.0 · 2026-11-03

`github.token` cannot write to another repository, so the release needs a credential of its own, and the job that holds it must run no app code: the registry's `assets` command (`bash -c "$ASSETS"` in the app's checkout) and the `notes` command (`scripts/notes.py --command`) are the app's, and a hostile app commit could put a fake `gh` on `GITHUB_PATH` or read the runner's memory in a later step of the same job. So `assemble` makes the release files (download the platform artifacts, the app's assets, `form-app.json`, the FormPortal bundles, `SHA256SUMS.txt`, `latest.json`, the notes file) with no environment and no token, and uploads `dist/*` plus `release-notes.md` as the artifact `formcompiler-release-<app>` (named so that `assemble`'s own `formcompiler-<app>-*` download pattern never matches it on a re-run; `overwrite: true` for the same reason). `publish` needs `assemble`, checks out formcompiler only, downloads that artifact to `release/` and does the draft, the supersede and the publish. It runs in the `release` environment (the one v0.8.0 left unused) and reads two shapes from it: a GitHub App (`FORMCOMPILER_APP_ID`, `FORMCOMPILER_APP_PRIVATE_KEY`), for which `actions/create-github-app-token` v3.3.0 (pinned by SHA) mints a one-hour token for the one repository being released (`owner: nodemode-dev`, `repositories: <name>`, `permission-contents: write`, so the token holds nothing else even if the App is given more later); or the fine-grained `FORMCOMPILER_WRITE_TOKEN`. `scripts/release_credential.sh` chooses by which secrets exist (`secrets.X != ''` in `env:`, never in `run:`), writes the repository's short name for the App input, and fails with `::error::` naming docs/ACCOUNTS.md when neither is set, before the artifact download, so a misconfigured job wastes nothing; the tests run the script under bash for the three cases. There is no fallback from a failed App mint to the token: the mint step fails the job, and the owner fixes the installation. Only the three steps that write carry `GH_TOKEN: steps.app-token.outputs.token || secrets.FORMCOMPILER_WRITE_TOKEN`; the asset, manifest, checksum and notes steps have no token at all, and the app checkout keeps the read-only `FORMCOMPILER_APP_TOKEN`. The job's own permission drops to `contents: read`. Environment secrets are not passed by `secrets: inherit` to desktop-release.yml, which is why they live in the environment and not at repository level: the build jobs run the app's scripts. v3 of the action deprecates `app-id` for `client-id`; the secret keeps the owner's name `FORMCOMPILER_APP_ID` and holds the client ID (the numeric ID is accepted there too).

### release.yml · assemble: GH_REPO, the tag and the target
- refers-to: .github/workflows/release.yml :: assemble; scripts/gate.py :: main; scripts/release_assets.py
- kind: decision
- logged: v0.9.0 · 2026-11-03

`GH_REPO` is the registry entry's `repository` in every step that touches a release; a test refuses `GH_REPO: ${{ github.repository }}` anywhere in release.yml. The tag is the gate's output `v<version>`, and `--target` is the gated commit `$SHA`: the v0.6.9 rule (target `main`, never `$GITHUB_SHA`) was about formcompiler's own workflows differing from main's under the Actions token; on the app repository the commit is on main (the gate checked) and the credential is not the Actions token. For an app with `tag_trigger` the tag already exists and GitHub ignores the target. The "already published" guard stays, now against the app repository, and `still_a_draft` reads `isDraft` again right before each asset deletion, the edit and the upload, stopping with `::error::` if a maintainer published the draft while the run was building: before, a refresh would have stripped a just-published release of its files. Older drafts are deleted by release id (`versions.py older-drafts --token-env GH_TOKEN` prints `id<TAB>tag`), after `gh api repos/<repo>/releases/<id>` says `draft` is still true, so a draft that was published between the listing and the deletion is left alone with a warning; `gh release delete <tag>` would have resolved the tag again and could delete the wrong thing. `readiness.evaluate` refuses a `v<version>` tag that already exists in the app repository at another commit (`gh.tag_target`, annotated tags followed), because GitHub creates a release for an existing tag at that tag's commit and ignores `--target`; a tag at the gated commit (the tag_trigger case) passes. `release_assets.py` is unchanged; the workflow passes it the app repository and the plain tag, so `latest.json` points at `https://github.com/<repository>/releases/download/v<version>/<file>`, which `public_urls.feed_url` then moves to the store by comparing that tag. The dispatch to formpipe carries `app`, `tag` and `repository`, since a tag alone no longer names the app.

### versions.py, readiness.py, gate.py, yank.py, plan.py · the tag is v<version>
- refers-to: scripts/versions.py :: TAG_PREFIX, tag_of, version_of, app_releases, older_drafts, main; scripts/readiness.py :: evaluate; scripts/gate.py :: main; scripts/yank.py :: validate, main; scripts/plan.py :: main
- kind: decision
- logged: v0.9.0 · 2026-11-03

One release list per app repository, so the app's name leaves the tag: `app_releases` keeps its `(app, releases)` signature for its callers and the messages, but matches `v<semver>` and ignores every other tag (`formvis-v9.0.0`, `catalog`, `nightly`). `older_drafts` returns `v<version>` tags for `gh release delete`. `versions.py older-drafts` and `yank.py` default `--repo` to the registry entry's repository. `plan.py` loses `--tag-prefix` (and desktop-release.yml its `tag-prefix` input): its tag is `v<version>`, and the self-check's sample plan drops the option. Consequence worth knowing: an app repository's own `v*` releases from before formcompiler are published versions now, so the version-must-go-up rule compares against them; that is what the rule is for.

### github_api.py · releases read with the app-side token; watch.py · a succeeded run stands in for the draft
- refers-to: scripts/github_api.py :: releases, succeeded_release_runs; scripts/watch.py :: Lazy.releases, Lazy.succeeded, watch_app; scripts/catalog.py :: fetch_releases
- kind: decision
- logged: v0.9.0 · 2026-11-03

`releases(repo)` is always an app repository now, so it reads with `app_side=True`: `FORMCOMPILER_APP_TOKEN` when set, else `GH_TOKEN`. In the assemble job's supersede step only `GH_TOKEN` (the write credential) is set, so drafts are listed there. The watch and the gate read with the read-only app token, and GitHub lists drafts only to a token with push access (the v0.6.7 lesson), so `readiness.evaluate`'s "already drafted" and "superseded by a newer draft" checks see nothing from them. Rather than widen the read token, the watch lists release.yml's successful runs created since `RELEASES_ON_APP_REPOS_SINCE` (the v0.9.0 commit's time; earlier successes drafted on formcompiler, not on the app repository, and must not count; the owner moves the constant forward to the merge time if anything ran in between) through the API's `created=>=` filter, the newest 100, and skips a ref whose run title, `<app> <version> at <sha>`, is among them; the success check comes before the failed-or-cancelled one, so a failed first run plus a later successful re-run counts as built. The 100-run cap is the API's page; an app that has had 100 successful releases since the cut-over without a new version is not a case worth a second page. Only runs with `head_branch` main, `event` workflow_dispatch and `conclusion` success count (asked of the API with `branch=main&event=workflow_dispatch` and filtered again client-side): a run dispatched from another formcompiler branch, where the workflow and its `run-name` can be anything, could otherwise succeed with a forged title and make a `v*` tag at another commit look like formcompiler's own to `readiness.evaluate`'s `built` allowance. So the record is exactly as strong as main's protection: main takes changes only through pull requests, and the watch and gate dispatch release.yml on main. No comment in the code, by the house rule; this entry is the comment: its draft is on the app repository, or someone deleted it, and either way the hourly watch must not rebuild it. That ref then counts as ahead, so an older ref of the same app is not started under it, which is what a visible newer draft did. The gate is unchanged, so Run workflow on release.yml rebuilds the same commit and refreshes the draft. `Lazy.releases` caches per app repository, one call per app per watch. `catalog.fetch_releases` reads every enabled entry's repository once and stops with `::error::` when one cannot be listed, since a catalogue missing an app would drop it from FormPortal.

### release.yml · publish: the tag is formcompiler's before the draft is
- refers-to: .github/workflows/release.yml :: publish :: Create or refresh the draft on the app repository, Supersede older drafts, Publish; scripts/versions.py :: tag-target; scripts/github_api.py :: tag_target, RELEASES_ON_APP_REPOS_SINCE; scripts/readiness.py :: evaluate (built); scripts/gate.py
- kind: decision
- logged: v0.9.0 · 2026-11-03

The gate's tag check left a window: between it and `gh release create` someone with write access could create `v<version>` at another commit, and GitHub makes a release at an existing tag at that tag's commit, ignoring `--target`. The publish job now creates the ref itself (`POST git/refs`, which fails if the ref exists, so the check is atomic) with the write credential, right before the draft. On failure it resolves the tag (`versions.py tag-target --token-env GH_TOKEN`, `gh.tag_target` following annotated tags): at the gated commit, fine; elsewhere with a draft at it, the tag is moved (`PATCH`, force), because that is the documented refresh, the same version pushed again from a newer commit, whose draft now exists with a tag of formcompiler's own making; elsewhere with no draft, the job stops. Before `gh release edit --draft=false` the tag is read once more and must still be the gated commit. A superseded draft's tag is deleted with the draft when it points at the draft's `target_commitish`, so a version that never shipped leaves no tag behind; otherwise the tag is left and the summary says where it points. Because the tag now exists from the draft on, `readiness.evaluate` would have refused every refresh ("tag exists at another commit"): it takes `built`, the titles of release.yml's successful runs since the cut-over, and accepts an existing tag whose commit formcompiler built for that app and version; the watch passes `state.succeeded()` and the gate fetches the same list. The constant moved to github_api.py so both read it. Consequence for the ruleset: the App or the token's user creates every tag now, so the bypass is needed for every app, not only for the betas it publishes, and the app repositories keep their `v*` tags under the ruleset so nothing else moves them.

### release.yml · publish: the provenance of SHA256SUMS.txt and form-app.json
- refers-to: .github/workflows/release.yml :: publish :: Attest the provenance of SHA256SUMS.txt, permissions; scripts/agents.py :: build, check
- kind: decision
- logged: v0.9.0 · 2026-11-03

With releases on the app repositories, formpipe can no longer tell a release this workflow made from one a person with write access drafted by hand, and it feeds whatever published `v*` release it finds. `actions/attest-build-provenance` v4.2.2 (pinned by SHA; the newest line, released 2026-08-06) signs a SLSA provenance statement for `release/dist/SHA256SUMS.txt` with the job's OIDC identity, before the draft is made, so the attestation exists for every draft and every refresh. One subject is enough: formpipe verifies that file (`gh attestation verify SHA256SUMS.txt --repo nodemode-dev/formcompiler --signer-workflow nodemode-dev/formcompiler/.github/workflows/release.yml`) and checks every other asset against its sums, so the subject name must stay `SHA256SUMS.txt` (the action takes the basename of `subject-path`). formpipe's review found that an attested sums file is not tied to its release: a person with write access could publish `v9.0.0` on an app repository carrying an older release's attested sums and files, and the verification would pass. So `form-app.json`, already a release asset written by `agents.py build` before the sums are computed (the assemble job's step order: assets, manifest, FormPortal bundles, then `release_assets.py`), now carries `repository` and `tag` beside `app`, `version` and `commit`, `agents.py check` refuses a manifest without them, and the step attests both files (`subject-path` as a two-line list). formpipe verifies both, reads `app`, `version` and `repository` from the manifest, requires them to match the release it is feeding, and only then checks the files against the sums. The job gains `id-token: write` and `attestations: write`; its checkout keeps `contents: read`. GitHub refuses attestations on a private repository without Enterprise, so the step is gated on the repository variable `FORMCOMPILER_ATTEST != 'off'`: unset attests, `off` skips while formcompiler is private, and docs/ACCOUNTS.md says to remove the variable once public. A test pins the step, its pin, the permissions, the gate and its place before the draft step.

### catalog.py, feed.py, public_urls.py · binaries from GitHub once an app is public
- refers-to: scripts/catalog.py :: GITHUB, STORE, asset_url, agent_assets, entry_origin, release_entry, build, main; scripts/feed.py :: point_at_store; scripts/public_urls.py :: parse_store_path, github_asset_url; scripts/github_api.py :: repository_public
- kind: decision
- logged: v0.9.0 · 2026-11-03

Once an app's repository is public its release assets are on GitHub's CDN at no cost, so only the small files (the catalogue, the update feeds) need the store. `catalog.py build --asset-origin github` asks `GET /repos/<repository>` once per entry that has releases (`private` false means public; a missing field counts as private, and an API error stops the build) and keeps each asset's `browser_download_url` for a public repository while a private one still gets `<base>/<app>/<version>/<file>`, so a mixed family works per app. `store`, the default, is the old behaviour; with no base every URL is GitHub's whatever the flag. Every release entry (current, history, beta) carries `origin`, `github` or `store`, which is where its URLs point, so formpipe copies only what the catalogue sends to the store and the site knows which host serves a file. `feed.py public --asset-origin github` leaves latest.json's URLs on the release: the feed itself is still published at `<base>/<app>/updates/latest.json`, the endpoint baked into the apps, which does not change. `public_urls.github_asset_url(repository, tag, "<app>/<version>/<file>")` maps a store path back to the release asset with the same quoting rules as `artifact_url`, so the edge redirect and formpipe use one shape; `parse_store_path` is its inverse of `artifact_url`'s path part.

### github_api.py · token_env
- refers-to: scripts/github_api.py :: token, request, paged, releases; scripts/versions.py :: main
- kind: decision
- logged: v0.9.0 · 2026-11-03

`releases()` prefers `FORMCOMPILER_APP_TOKEN` (read-only, lists no draft) whenever that variable is set. The publish job's supersede step must list drafts, so it passes `--token-env GH_TOKEN` and `token()` then reads that one variable and nothing else; the step's `env:` sets only `GH_TOKEN` as well, and a test pins both. Other callers are unchanged.

### registry · formvis assets, formdesign and formNET notes
- refers-to: apps/formvis.json :: assets; apps/formdesign.json, apps/formNET.json :: notes_for_owner; .github/workflows/release.yml :: assemble :: App release assets
- kind: fix
- logged: v0.9.0 · 2026-11-03

formvis's own feed was built with `--tag formvis-v$FORMCOMPILER_VERSION` and a base URL under formcompiler's releases, which would 404 after this change and which `public_urls.feed_url` would not move to the store (it compares the tag). The assets step now exports `FORMCOMPILER_TAG` and `FORMCOMPILER_REPOSITORY` beside `FORMCOMPILER_VERSION`, and formvis uses them; a test scans every registry entry for `-v$` and for a `releases/download/` URL that is not the app's own. formdesign's `setup/install_core` reads `formdesign-core-<triple>` from a `formdesign-v<version>` release on formcompiler: that is the app's code, flagged OWNER in its note, not fixed here. formNET's note no longer speaks of a tag prefix.

### catalog.py, feed.py · per-repository releases, --app
- refers-to: scripts/catalog.py :: app_releases, build, fetch_releases, read_releases, main; scripts/feed.py :: resolve, main
- kind: decision
- logged: v0.9.0 · 2026-11-03

`build(entries, releases_by_repo, base, yanked, origin)`: the releases are a mapping of repository to the GitHub API's list, so `--releases FILE` (formpipe's dry runs, the tests, the self-check) is a JSON object; a list is refused with a message that says so. `--repo` is gone; `--origin` names the catalogue's origin and defaults to formcompiler, which is what `origin` meant. `--sums-dir DIR` (formpipe's request): `sums_for` reads `DIR/<app>/<version>/SHA256SUMS.txt`, the copy formpipe verified against the attestation, for every release the catalogue lists, instead of `fetch_sums` downloading the asset; a missing or empty file is `::error::`, exit 1, never a fall back to the download, since a catalogue built from unverified sums would defeat the verification. Without the flag `fetch_sums` is used as before. `feed.py resolve --app <app> --tag <vX.Y.Z or X.Y.Z>` writes `app`, `title`, `version`, `tag`, `repository`, `prerelease`, `channel`, `updates` and `tag_json`; `files` and `public` take `--app` too. The old soft path ("not an app release tag; only the catalogue is rebuilt", exit 0) is gone: it existed because formcompiler's own `catalog` release reached the feed, and an unknown app or a tag that is not a version is now an error, so a typo in formpipe fails loudly instead of refreshing nothing. The contract with formpipe is in the README's "Run the scripts by hand" and the CHANGELOG.

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

### desktop-release.yml · Intel Mac builds get longer
- refers-to: .github/workflows/desktop-release.yml :: build `timeout-minutes`, Build step `timeout-minutes` · tests/test_build_timeouts.py
- kind: decision
- logged: v0.12.1 · 2026-11-09

FormCut 2.15.1's `macos-x64` build (GitHub's `macos-15-intel` runner, LGPL FFmpeg) stopped at the Build step's 40 minutes twice: first cold, then on Re-run failed jobs with its caches saved, so the cache-then-re-run design above did not get it through. Its arm64, Windows and Linux builds finished well inside the limit. Only `macos-x64` now has 70 minutes for the step and 79 for the job (an expression on `matrix.platform`, which comes from plan.py, never from outside input); every other platform keeps the owner's 40 and 49. The 9-minute window after the step, in which the caches save, is unchanged everywhere; tests/test_build_timeouts.py checks the window for every platform and the two pairs of numbers, and fails on the old workflow. For the owner: the 49 is his number; this raises it for one runner only.

### desktop-release.yml, registry.py, build_cache.py · the LGPL FFmpeg is cached
- refers-to: .github/workflows/desktop-release.yml :: inputs `build-cache-paths`, `build-cache-key-files`; steps "build cache key", "build cache", "Save the build cache", "pip wheel cache key" · .github/workflows/release.yml :: desktop `with` · scripts/build_cache.py · scripts/registry.py :: TOOLCHAIN `build_cache`, BUILD_CACHE, build_cache_problems, config · apps/formcut.json, apps/format.json · docs/REGISTRY.md · tests/test_build_cache.py
- kind: decision
- logged: v0.12.2 · 2026-11-09

FormCut 2.15.1's `macos-x64` Build step (formcompiler run 42623893888) spent 20:30 to 20:46 compiling FFmpeg 8.0.3 into `backend/.lgpl-ffmpeg`, 20:46 to 20:49 building PyAV against it, 20:51 to 20:58 rebuilding opencv-python-headless 4.12.0.88 from its sdist (`backend/prepare_cv.py`), then PyInstaller and the Tauri build. The owner asked for it to be faster. FormCut's and Format's `setup/build_lgpl_av` skip the FFmpeg build when `$prefix/lib/pkgconfig/libavcodec.pc` is there, and their `.bat` when `include/libavcodec/avcodec.h` is; all three platforms use `backend/.lgpl-ffmpeg`, and the libraries carry an rpath to it, which stays valid because the checkout is always `/Users/runner/work/formcompiler/formcompiler` (or its Linux and Windows counterparts).

So a registry entry may now name `toolchain.build_cache`: folders the build reuses and the files that decide their contents. scripts/build_cache.py hashes the key files (sorted, name and bytes) and writes `formcompiler-build-<app>-<platform>-<runner>-<hash>`; the folders are restored with `actions/cache/restore` on that exact key, with no `restore-keys`, because the scripts reuse any FFmpeg they find: a fallback would put an older FFmpeg in a build whose script names a newer one. The FFmpeg version, its checksum and the configure line all live in the key files, so changing any of them builds again. The runner label is in the key so an image change of label (macos-15-intel to a later one) starts afresh; runner image updates under the same label do not. Saved with `actions/cache/save` under `if: always()` like the pip wheels, so a timed-out build still keeps what it finished. A key file missing from the checkout stops the build, since a misnamed one would leave a cache that never rebuilds. Only FormCut and Format have the field, the key starts with the app's name, and their scripts still check `libavcodec license: LGPL` in what they reuse, so the cached FFmpeg cannot reach another app or licence; tests/test_build_cache.py keeps the list of apps.

Why FormCut's pip wheel cache was off: v0.7.0 turned it on only for the five apps whose `setup.macos` sets `PIP_NO_BINARY`; FormCut rebuilds OpenCV in `backend/prepare_cv.py` instead. It is on for FormCut now, but both of FormCut's source builds (`prepare_cv.py` for OpenCV, `setup/build_lgpl_av` for PyAV) pass `--no-cache-dir`, which wins over `PIP_CACHE_DIR`, so the wheels are cached only once FormCut drops that flag (pip then stores them under `$PIP_CACHE_DIR/wheels`, keyed on the sdist). Until then the wheels folder stays empty and nothing is saved. A cached PyAV wheel is linked to the FFmpeg it was built against, so for an app with a build cache the pip key also carries the build cache's hash; apps without one keep their exact keys. Expected per Intel Mac build with a warm cache: about 16 minutes (FFmpeg) now, about 10 more (PyAV and OpenCV) once FormCut drops `--no-cache-dir`. Size: an LGPL shared FFmpeg with headers is tens of megabytes per platform, eight caches for the two apps, inside the repository's 10 GB; GitHub drops a cache not read for 7 days. Untested in Actions: the first warm run, and a timeout during FFmpeg's `make install`, which could save a partial folder that the scripts would then reuse until the key changes (delete that cache to recover).

### tick.yml, tick.py · releases without hand starts
- refers-to: .github/workflows/tick.yml · scripts/tick.py :: owns, unfed, to_dispatch, attempt, check_feed, tick_once, command_owner, command_loop, command_chain · tests/test_tick.py
- kind: decision
- logged: v0.12.3 · 2026-11-10

The owner asked on 2026-11-10 for releases with no hand starts. On 2026-11-09 and 10 GitHub ran watch.yml's hourly schedule (minute 17) only every 4 to 10 hours, so every release was dispatched by hand; and a draft published by hand (every stable release) never told formpipe, whose own hourly schedule (minute 47) was just as late, so every feed was dispatched by hand too. Approval in the `release` environment and publishing the draft stay manual: they are the owner's gate.

The clock. A workflow may start workflow_dispatch and repository_dispatch runs with its own `GITHUB_TOKEN` (the one exception to "the Actions token starts no workflow"); watch.yml already starts release.yml that way, so the repository's default workflow permission (read) needs no change: `permissions: actions: write` in the file is enough. `tick` runs one Linux job that starts watch.yml every 15 minutes on a fixed clock (start plus k times 15 minutes, so the work does not drift it) for 330 minutes, 23 ticks, then dispatches tick.yml on main with `after` set to its own run id and ends; GitHub's job limit is 360 minutes, the loop step has 340 and the job 350. A loop was chosen over a short run that sleeps 14 minutes and dispatches itself: both hold a runner the whole time (GitHub has no delayed dispatch), the loop makes 4 runs a day instead of 96, and formcompiler is public, so standard runners cost nothing. It holds one of the organisation's concurrent job slots; that is the price. Runner time for an idle wait is allowed use: the job does nothing but release this repository's software. A tick changed on main takes effect at the next hand-over, within 5.5 hours.

The backup and who keeps the clock. tick.yml's own `*/15 * * * *` schedule restarts the clock when the chain breaks (a lost runner, a cancelled run, a failed hand-over). There is deliberately no `concurrency:` group: with `cancel-in-progress: false` every scheduled run would wait as pending behind the 5.5-hour loop and replace the successor waiting there. Instead the first step lists the workflow's runs (one call, newest 50) and decides with `owns`: runs not completed are active; a run named `tick after N` (the `run-name` carries the input) is a successor of N; the run this one follows, and any run an active successor follows, are finishing and do not count. A successor keeps the clock unless an older successor is active; any other run keeps it only when no successor and no older run is active. So a scheduled run yields to a running tick, the older of two scheduled runs wins, and a scheduled run that starts while a tick hands over yields to the predecessor or the successor, whichever it sees. Each later tick asks again and stops without a successor (`yielded`) if another run owns the clock; when the runs cannot be listed, the run keeps the clock and says so. The successor is started by a separate step that runs unless the job was cancelled or yielded, so a loop that crashed or timed out still hands over; cancelling a tick stops the chain until the schedule's next run. The job runs only on main (`github.ref`), so a tick dispatched from a branch cannot start a second clock.

The feed. Every tick reads `<FORMCOMPILER_PUBLIC_BASE>/catalog/feed-state.json` (public, `planned_at`: when formpipe planned the catalogue the store serves) and the 30 newest releases of every enabled app repository with `FORMCOMPILER_APP_TOKEN`; a published `vX.Y.Z` release newer than `planned_at` is unfed, exactly formpipe's own plan rule. Prereleases count too: formcompiler's publish step already tells formpipe about them, and a second dispatch costs nothing when that one failed. When the newest unfed release was published within the last 17 minutes (one tick plus 2 minutes' slack) the tick sends `formcompiler-published` with that release's `app`, `tag` and `repository`, the payload release.yml's publish step sends; formpipe's plan then feeds every unfed release, not only the one named. Otherwise an unfed release older than 60 minutes is asked for again at the hour's first tick (minute under 15). This keeps the tick stateless and stops it from dispatching a feed every 15 minutes while one is still running (a feed run can take up to an hour and only then moves `planned_at`), or while a release keeps failing verification; formpipe's minute-47 schedule still runs as well. `FORMPIPE_DISPATCH_TOKEN` unset, `FORMCOMPILER_PUBLIC_BASE` unset or no feed state yet: the feed check is skipped with a line in the summary.

Failure handling. Every GitHub or store call is retried twice (after 10 and 30 seconds) on a network error or 408, 429 and 5xx, and not retried on any other answer; what still fails becomes a `::warning::` and a summary line, and the tick goes on. Only the hand-over fails its step, with `::error::`, since then the schedule must restart the clock. Each tick writes one summary line: the time, whether the watch started, and what the feed check found.

A live read on 2026-11-10 (no dispatch) found formcut v2.15.2, published 10:36:45Z, newer than the store's `planned_at` 04:04:34Z: the case this closes.

### apps/formcut.json · prepare_cv.py keys the build cache
- refers-to: apps/formcut.json :: toolchain.build_cache.key_files · tests/test_tick.py :: test_formcut_keys_its_build_cache_on_the_opencv_build_too
- kind: decision
- logged: v0.12.3 · 2026-11-10

v0.12.2 put the build cache's hash into FormCut's pip wheel key so a PyAV built against an older FFmpeg is never restored, but OpenCV's wheel is built by `backend/prepare_cv.py`, whose flags were in no key: a change there would restore the old wheel. `backend/prepare_cv.py` is now a key file. Consequence: the build cache key moves with it, so the first FormCut build after this (and after any change to prepare_cv.py) builds FFmpeg again on every platform; the file is on formcut's main today, and a missing key file stops the build.

### apps/formrec.json · FormRec is registered after FormCut's build shape
- refers-to: apps/formrec.json
- kind: decision
- logged: v0.13.0 · 2026-11-10

FormRec (nodemode-dev/formREC), the Form family's recorder, is a Tauri 2 app whose sidecar is its Node 22 server, and its `src-tauri` and `setup/build_release` follow FormCut's, so the entry mirrors apps/formcut.json: commands mode, `setup/build_release --target $FORMCOMPILER_TRIPLE` on every desktop runner (bash, Git Bash on Windows), `release-dist/*.zip` and the Windows NSIS `release-dist/*-setup.exe` as artifacts, Apple signing on macOS and certificate signing on Windows, check `ci.yml`, catalogue id `formrec` in state prelaunch, no updater (FormPortal updates it), no extras and no assets script.

The first draft (56a41cd) was written before FormRec's desktop build existed: version from `package.json`, Python 3.12 on the runners because FormCut's packaging step is Python, `agents.skills` empty, and notes for the owner listing every field to confirm before the first compile branch. Once FormRec 0.3.0's build was on its main, 542b3e1 matched the entry to it. The version is read from `src-tauri/tauri.conf.json`, since FormRec's `setup/stage_desktop` refuses to build unless `package.json`, `tauri.conf.json` and `src-tauri/Cargo.toml` agree. `toolchain.python` is empty because `build_release` needs no Python. `zip` joins `linux_packages` because the Linux zip (which holds the AppImage) is made with it. `agents.skills` is `.claude/skills`, where FormRec ships the formrec-harness and formrec-skillset skills, so every FormRec release carries a skills archive and `agents.py build` fails if the folder has no SKILL.md. The notes for the owner now describe the real outputs (one zip per platform and the NSIS installer), the network the build needs (nodejs.org for Node 22.23.4, checked against `setup/node-runtime.sha256`, and the npm registry), macOS signing and notarization with `allow-jit` for the `formrec-node` sidecar, the script's staple retries and seal check of the unzipped app, Windows signing of both executables and the installer, and that the headless recorder's Chromium is downloaded on first use, not bundled. `macos-x64` stays experimental until a first release shows it builds on the Intel runner. This section was missing when v0.13.0 shipped (the index line above named it) and was written in v0.13.1 from the two commits.

### tick.py · a data error costs one summary line, not the loop
- refers-to: scripts/tick.py :: tick_once · .github/workflows/tick.yml :: Start the next tick
- kind: fix
- logged: v0.13.1 · 2026-11-10

`tick_once` caught only `Unreachable`, and `attempt` turns only GitHub, network, OS and `ValueError` failures into one. An error in the data repeated on every pass escaped: a non-string `planned_at` in the store's `catalog/feed-state.json` (`unfed` compares it with `>` and raises `TypeError`), a feed state whose top level is not an object (`AttributeError` from `.get`), or an `apps/*.json` that is not an object. The loop step then failed on its first pass without writing `yielded`, "Start the next tick" dispatched the successor at once, and the successor failed the same way: a tick run and a watch dispatch about every minute until someone cancelled a run, which the 15-minute schedule cannot stop. Both blocks of `tick_once` now catch any exception and report it the way they report `Unreachable` (a `::warning::` and `watch: not started (...)` or `feed: not checked (...)`), so the loop keeps its 15-minute clock and the chain hands over every 5.5 hours as designed. A crash outside `tick_once` (the summary write, `still_owner`'s parsing) would still hand over at once; no lower bound on the loop's run time was added. Checked with a scratch script that patched `check_feed` to raise `TypeError` and ran `command_loop` for 30 minutes: three passes, each with a `feed: not checked` line, ending with `yielded=false`; tests/test_tick.py passes.

### apps/formpublisher.json · FormPublisher is registered, disabled
- refers-to: apps/formpublisher.json
- kind: decision
- logged: v0.13.2 · 2026-11-11

FormPublisher (nodemode-dev/formpublisher) is private and has no code yet, but the owner wants it in every catalogue now. It is registered with `enabled: false` and a `disabled_reason`, so watch.py and catalog.py skip it and the feed's planner never queries a repository it may not be able to read. The build fields are the family's Tauri defaults, taken from apps/formdesign.json without its Rust core extra, and the catalogue block is a neutral in-development summary in `prelaunch`. Its notes for the owner list what to check against the real repository before enabling: the version file, the check workflow, the toolchain, the platforms, the artifacts, the agents and the summary, plus the read token's access to the repository. formai.studio lists its store folder on dl. from the start (formai.studio v0.66.6), so its first release is served the moment formpipe feeds it.
