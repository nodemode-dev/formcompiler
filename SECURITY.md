# Security

FormCompiler builds, signs and publishes every Form app. A weakness here reaches every user of every app, so this
file says what it guards, against whom, and how.

## Reporting a vulnerability

Use **Report a vulnerability** on this repository's Security tab (GitHub's private vulnerability reporting). Please do
not open a public issue. Reports about a single app's code belong in that app's repository, the same way.

## What FormCompiler holds

- The signing identities: Apple Developer ID and notarisation, the Windows code-signing certificate, and the Tauri
  updater key that every installed app trusts for its updates.
- A token that reads the app repositories, and a token that tells the private publishing pipeline about a published
  release.

The catalogue key (Ed25519) that signs `apps.json`, and the access to the download store `dl.formai.studio`, are held
by that private pipeline, not by this repository.

## In scope

| Threat | What stops it |
|---|---|
| An outside pull request runs code in CI | Pull requests run only `self-check.yml`: no secret, a read-only token, and `persist-credentials: false`. |
| A fork runs the release workflows | Every job that signs, publishes or starts a release is guarded by `github.repository == 'nodemode-dev/formcompiler'` (tested in `tests/test_workflow_guards.py`). |
| A compromised action or package | Actions are pinned to full commit SHAs; the signing dependencies are hash-pinned and installed before any cloud credential exists; Dependabot proposes updates only after a 7-day wait. |
| A release from an unreviewed commit | The gate releases only a maintainer's `v*` tag or `compile_v*` branch on a commit already on `main`, with the version file matching and the app's own CI green on that commit. Stable releases stay drafts until the owner publishes them. |
| A tampered download | Each release carries `SHA256SUMS.txt`, checked again before a release is copied to the store; the catalogue is signed and its URLs point only at the store. A bad release is yanked from the catalogue, not silently replaced. |
| A change to what gets built | `.github/CODEOWNERS` puts the workflows, the registry, the scripts and the yank list behind the owner's review. |

## Out of scope

- A maintainer's own GitHub account being taken over. Mitigations: two-factor authentication on every account with
  write access, and the owner publishing every stable release by hand.
- GitHub, the download store's hosting, Apple or Microsoft themselves.
- Vulnerabilities in an app's own code (report them to that app).

## Supported versions

Fixes go into `main` and ship with the next release of each affected app. Which older releases are also fixed or
yanked is the owner's decision per case.
