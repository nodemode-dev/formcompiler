# The app registry

Every app formcompiler releases has one file, `apps/<app>.json`. The watch reads them to know which repositories to look at, `release.yml` turns one into the build, and the publishing pipeline (`scripts/feed.py`) and the catalogue read them after a release is published. `python3 scripts/registry.py check` validates every file; the self-check runs it on every push.

A field that is not listed here is refused. Strings that hold commands are bash unless the field says otherwise, one command per line, run from the root of the app's checkout.

## Top level

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `app` | string | yes | The registry name: the file name, the download store path `<app>/<version>/`, the update feed `<app>-updates` and the release file names. Must equal the file name. |
| `repository` | string | yes | `nodemode-dev/<repo>` on GitHub: the app's source, and where its releases are created. A release is the tag `v<version>` at the released commit, titled `<title> <version>`, with its installers, `SHA256SUMS.txt`, `form-app.json`, the skills archive, `latest.json` for a Tauri-updater app and the extras' files; GitHub allows 2 GB per file. formcompiler keeps no app release of its own. |
| `title` | string | yes | The display name in release titles, for example `formvis`. |
| `enabled` | boolean | yes | `false` keeps the entry but the watch skips it and `release.yml` refuses it. |
| `disabled_reason` | string | when `enabled` is false | Why, in one sentence. |
| `release` | `"draft"` or `"publish"` | yes | `draft` leaves a stable release as a draft on the app's repository, with its `v<version>` tag already at the gated commit, for a maintainer to publish, which is the approval; `publish` publishes it when every job passed. Every app starts as `draft`. A prerelease version (`X.Y.Z-beta.N`, `-rc.N`, any prerelease part) is the beta channel and is always published when every job passed, as a GitHub prerelease, whatever this says. |
| `tag_trigger` | boolean | no | Default false. True makes a `vX.Y.Z` tag in the app repository (lightweight or annotated) start a release like a `compile_vX.Y.Z` branch. The tagged commit must be on `main` (`main...<sha>` is identical or behind), and only the app's newest version tag is considered. Off by default because every app repository has older `v*` tags that would otherwise all look new. |
| `version` | object | yes | `{"file": "<path>", "pattern": "<regex>"}`. The file is read at the compile branch's or tag's commit, and must give the version the ref names. That version must be strictly above the app's highest published version in its channel: a stable above the highest stable, a beta above every published version (semver with prereleases; yanked versions still count, and so does any `v<version>` release the app repository published before formcompiler). JSON files use their `version` field, `Cargo.toml` its `[package]` or `[workspace.package]` version, any other file needs `pattern` (first group is the version). A leading `v` is dropped. |
| `checks` | array of strings | yes | The app's check workflow file names (for example `["ci.yml"]`). Every one must have concluded `success` on the compile branch's commit before a build starts. |
| `platforms` | array of strings | yes | Desktop targets, from `macos-arm64`, `macos-x64`, `macos-universal`, `linux-x64`, `linux-arm64`, `windows-x64`, `windows-x86`, `windows-arm64`. `name=runner` overrides the runner. A trailing `?` marks a platform experimental: it may fail without failing the release. An empty list means the app has no desktop build (only `extras`). |
| `toolchain` | object | yes | See below. |
| `build` | object | yes | See below. |
| `setup` | object | no | `{"macos": "", "linux": "", "windows": ""}`: bash run before the build on that OS, after the Linux packages. Windows set-up runs in Git Bash. |
| `post_build` | object | no | Same shape: bash run after the build and before the files are collected, for packaging the app's build does not do (portable zips, renames, checks). |
| `artifacts` | array of strings | no | Globs, relative to the app root, of the files to release from each desktop runner. Empty means the Tauri bundles (dmg, the macOS updater `.app.tar.gz`, AppImage, deb, rpm, msi, nsis `-setup.exe` and every `.sig` under `src-tauri/target/**/bundle/`). |
| `extras` | array of objects | no | Jobs beside the desktop matrix: phone apps, a riscv64 tarball, a Flatpak. See below. |
| `image` | object | no | A container image pushed to GitHub's registry. See below. |
| `assets` | string | no | Bash run in the release files job after every file is downloaded, with the app's checkout at `app/` as the working directory, `$DIST` the folder of release files, `$FORMCOMPILER_VERSION`, `$FORMCOMPILER_TAG` (`v<version>`) and `$FORMCOMPILER_REPOSITORY` (`nodemode-dev/<repo>`); a URL to a release file is `https://github.com/$FORMCOMPILER_REPOSITORY/releases/download/$FORMCOMPILER_TAG/<file>`. The job holds no credential. For files made from all platforms together (a manifest, a checksum list in the app's own format, an MCP bundle, a licence source archive). Runs before formcompiler writes `SHA256SUMS.txt`. |
| `file_names` | string | no | Default `formcompiler`: each release file is named `<app>-<version>-<platform>` plus its kind's suffix (`.dmg`, `.app.tar.gz`, `.AppImage`, `.AppImage.zsync`, `.deb`, `.rpm`, `.msi`, `-setup.exe`, `.zip`, `.tar.gz`), and its `.sig` follows it. `app` keeps the names the build gives them, for an app whose own scripts or update information depend on those names. |
| `with_portal` | boolean | no | Default false. True adds, beside each desktop installer, `<installer>-<kind>[-<chip>]-with-FormPortal.zip`: that installer, FormPortal's matching installer from the catalogue's stable release (checked against its SHA-256) and a README saying the app is all that is needed and FormPortal is optional. Nothing in the bundle installs FormPortal; the person decides. The app's own files are unchanged and the catalogue does not list the bundles. Not allowed in FormPortal's own entry. |
| `notes` | string | no | Bash that prints the release notes in Markdown to standard output, in the app's checkout. Empty means: the section of `CHANGELOG.md` whose heading names the version, else a line naming the commit. |
| `updater` | object | yes | See below. |
| `signing` | object | yes | `{"macos": "apple" or "adhoc" or "none", "windows": "certificate" or "none"}`. `apple` uses formcompiler's Apple secrets when they are set and an ad hoc signature until then; `adhoc` always signs ad hoc; `certificate` signs Windows files through formcompiler's Azure Artifact Signing when it is set (or a pre-2023 .pfx certificate when only that is set): every Tauri app in the checkout gets a `tauri.windows.conf.json` with the signing command before the build, whatever command builds it, and every `.exe`, `.msi` and `.exe` inside a `.zip` the `artifacts` globs match that is still unsigned is signed after the post-build. |
| `catalog` | object | yes | The app's entry in the family catalogue FormPortal reads. See below. |
| `agents` | object | no | What the app offers agents: its skills folder and whether it has an MCP server. Every release then carries `form-app.json` and, with skills, `<app>-skills-v<version>.zip`. See below. Absent means no skills and no MCP server. |
| `notes_for_owner` | string | no | Anything a person must know before releasing this app, shown in the release summary. |

## `toolchain`

| Field | Type | Meaning |
| --- | --- | --- |
| `node` | string | Node.js version, for example `"22"`. Empty skips Node. |
| `python` | string | Python version, for example `"3.12"`. Empty skips Python. |
| `rust` | boolean | Install stable Rust with the platform's target. |
| `rust_targets` | string | Extra Rust targets, comma separated, for example `wasm32-unknown-unknown`. |
| `rust_cache` | array of strings | Cargo workspaces to cache, for example `["src-tauri"]`. |
| `go` | string | `"go.mod"` to take Go's version from the app's go.mod, a version, or empty. |
| `linux_packages` | string | apt packages for the Linux build, space separated. Empty means Tauri 2's prerequisites: `libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev libxdo-dev patchelf`. |
| `windows_msvc` | boolean | Put the MSVC developer environment on PATH for the Windows build. |
| `pip_cache_macos` | boolean | Default false. True keeps pip's locally built wheels (`$PIP_CACHE_DIR/wheels`) between macOS builds, for apps whose `setup.macos` makes pip build a package from source (opencv with `PIP_NO_BINARY`). The cache key is the app, the platform, the Python version, a hash of `setup.macos` and a hash of the app's `requirements*.txt`, `constraints*.txt` and `pyproject.toml` files; a change to any of them builds again. pip itself reuses a cached wheel only for the same package version, so an older cache restored as a fallback never puts a different opencv in a build. The app's own install must not pass `--no-cache-dir`. |

## `build`

| Field | Type | Meaning |
| --- | --- | --- |
| `mode` | `"contract"` or `"commands"` | `contract` runs the app's launcher: `./<cli> install <install_args>`, `./<cli> install-desktop`, `./<cli> desktop build --config <file>` (or `call <cli>.bat ...` under cmd). `commands` runs `macos`, `linux` and `windows` instead. |
| `cli` | string | The launcher name for `contract`. |
| `install` | boolean | Run `<cli> install` (`contract` only). |
| `install_args` | string | Arguments for install, for example `--lite`. |
| `install_desktop` | boolean | Run `<cli> install-desktop` (`contract` only). |
| `windows_shell` | `"cmd"` or `"bash"` | How Windows runs the build: cmd runs `<cli>.bat` or the `windows` commands as a cmd script; bash runs them in Git Bash. |
| `macos`, `linux`, `windows` | string | The build commands for `commands` mode. They may use `$FORMCOMPILER_CONFIG_ARG` (`--config <file>` or empty), `$FORMCOMPILER_TAURI_CONFIG`, `$FORMCOMPILER_VERSION`, `$FORMCOMPILER_PLATFORM`, `$FORMCOMPILER_OS` (`macos`, `linux`, `windows`), `$FORMCOMPILER_ARCH` (`aarch64`, `x64`, `x86`) and `$FORMCOMPILER_TRIPLE` (the Rust target triple); under cmd as `%NAME%`. |
| `tauri_config` | string | Extra Tauri config merged into `--config`: inline JSON or a path in the app repo. |

## `extras`

Each extra is a job on its own runner with the app checked out at the compile commit.

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Short name, `[a-z0-9-]+`, unique in the app. |
| `runner` | string | For example `ubuntu-24.04` or `macos-latest`. |
| `experimental` | boolean | May fail without failing the release. |
| `node`, `python`, `java`, `go` | string | Versions; empty skips. `java` installs Temurin. |
| `android` | boolean | Install the Android SDK. |
| `rust_targets` | string | Rust targets to install; empty with `rust: false` skips Rust. |
| `rust` | boolean | Install stable Rust. |
| `linux_packages` | string | apt packages. |
| `run` | string | Bash. `$FORMCOMPILER_VERSION` holds the version. |
| `artifacts` | array of strings | Globs of the files it releases. |

## `image`

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | The image, for example `ghcr.io/nodemode-dev/form.md`. |
| `context` | string | Build context in the app repo, usually `.`. |
| `file` | string | Dockerfile path, usually `Dockerfile`. |
| `platforms` | string | For example `linux/amd64,linux/arm64`. |
| `build_args` | object | Build arguments; `{version}` in a value becomes the version and `{tag}` the release tag `v<version>`. |
| `tags` | array of strings | Tags pushed; same placeholders, for example `["{tag}", "latest"]`. |

## `updater`

| Field | Type | Meaning |
| --- | --- | --- |
| `tauri` | boolean | The app has Tauri's updater: formcompiler writes `latest.json` from the signed bundles (only when the updater key is set) and the publishing pipeline copies it to `<app>-updates` on publish, and to `<app>/updates/latest.json` in the download store. With `FORMCOMPILER_PUBLIC_BASE` set, its platform URLs are moved from the GitHub release to `<base>/<app>/<version>/<file>`. Betas never touch the update feed. |
| `tag_json` | boolean | Also write `latest.json` as `{"tag_name": "v<version>"}` on `<app>-updates`, for apps whose own update check reads that shape (form.md). Cannot be combined with `tauri`. |
| `files` | array of strings | Globs of release file names the publishing pipeline also copies to `<app>-updates` (for example `install.sh`, `*.AppImage.zsync`). |

## `catalog`

The fields of the app's product entry in FormPortal's catalogue (`catalog/schema/apps.schema.json` in formportal): `id`, `name`, `kind`, `summary`, `identifier`, `licence`, `state` (`prelaunch`, `public` or `live`) and optional `project_extensions`; plus `minimum_os` (`{"macos": "", "windows": "", "linux": ""}`) written into every artifact of that platform. `repository` is taken from the top level. `id`, `name`, `kind` and `summary` follow formportal's `catalog/products.json` where the app is listed there; `identifier` is the app's real bundle identifier from its `tauri.conf.json`. Artifact and skills URLs are the app repository's release download URLs (`https://github.com/<repository>/releases/download/v<version>/<file>`), or `<FORMCOMPILER_PUBLIC_BASE>/<app>/<version>/<file>` when that variable and the rest of the download store's variables are set; with `catalog.py build --asset-origin github` a public repository keeps the release URLs and a private one uses the store, and each release entry records which in `origin` (`github` or `store`); `file`, `bytes` and `sha256` are the same either way. The catalogue reads every enabled entry's `repository` and takes its releases tagged `v<version>`; each listed release's `SHA256SUMS.txt` is downloaded from the release, or, with `catalog.py build --sums-dir DIR`, read from `DIR/<app>/<version>/SHA256SUMS.txt` (the copy the publishing pipeline verified), where a missing or empty file stops the build; a stable channel is the newest published release with no prerelease part, a beta channel the newest prerelease above it. A version listed in `yanked.json` (written by the yank workflow) is left out of every channel and history. The catalogue also gives each product `agents` (`{"mcp": bool, "skills": bool}`, from the registry's `agents`) and each release whose files include them `agents.manifest` and `agents.skills` (`file`, `url`, `bytes`, `sha256` from `SHA256SUMS.txt`).

## `agents`

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `skills` | string | yes | The app's skills folder, relative to its repository root, usually `.claude/skills`; empty when it has none. Each folder in it with a `SKILL.md` is one skill. |
| `mcp` | boolean | yes | The app has an MCP server agents can use. |
| `mcp_launch` | object | no | `{"command": "<path>", "args": []}`: how an installed copy starts its stdio MCP server, relative to the folder holding `form-app.json`. Only with `mcp` true. Leave it out until the app's bundle carries such a launcher. |

In the release job, after the app's own `assets` and before `SHA256SUMS.txt`, `scripts/agents.py build` writes two files from the app's checkout at the compile commit, and `scripts/agents.py check` refuses the release if either is wrong:

- `<app>-skills-v<version>.zip`: every skill folder under `skills`, at the top of the archive (`<skill>/SKILL.md`, `<skill>/references/...`), with `__pycache__`, `node_modules`, `.git`, `.DS_Store` and `.pyc` left out. Entries are sorted and dated 1980-01-01, so the same tree always gives the same bytes. A symbolic link that leaves the skills folder stops the release.
- `form-app.json`, format_version 2:

```json
{
  "format": "form-app",
  "format_version": 2,
  "id": "formvis",
  "app": "formvis",
  "name": "FormVis",
  "version": "1.97.2",
  "repository": "nodemode-dev/formvis",
  "tag": "v1.97.2",
  "commit": "<the compile commit>",
  "agents": {
    "mcp": {"available": true},
    "skills": {
      "file": "formvis-skills-v1.97.2.zip", "bytes": 173571, "sha256": "<hex>", "root": ".claude/skills",
      "skills": [{"folder": "formvis-harness", "name": "formvis-harness", "description": "<from SKILL.md>", "files": 21}]
    }
  }
}
```

`agents.mcp` gains `command` and `args` when the registry sets `mcp_launch`; `agents.skills` is left out when `skills` is empty. `repository`, `tag` and `commit` name the release the file belongs to: the publish job attests this file beside `SHA256SUMS.txt`, and the publishing pipeline reads `app`, `version` and `repository` from it and requires them to match the release it is feeding, so an attested manifest cannot be reused under another version. Version 1 of this file (`agents.mcp.command` required) is still read by FormPortal.
