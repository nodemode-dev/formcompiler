# Accounts · the family's GitHub apps and tokens

Two things here need an account the family does not otherwise have: FormPortal's optional sign-in (a GitHub OAuth app, below) and the credential formcompiler releases with on the app repositories (the second half of this page).

## FormPortal's sign-in

FormPortal (from v0.47.0) can sign a person in to their own GitHub account, optionally, so that sharing from Files can use that account as its storage. The family has no server, so the only shared piece is one GitHub OAuth app that belongs to the `nodemode-ai` organisation. This page says how it is registered and where its client ID goes. Nothing here is a secret: the device flow needs only the client ID, never the client secret, and the client secret is never generated for this use or stored anywhere in the family.

### Register it once (owner)

From GitHub's own steps for an OAuth app, done from the `nodemode-ai` organisation's settings (Developer settings, OAuth apps, New OAuth App), since GitHub allows an OAuth app under any organisation you administer:

| Field | Value |
| --- | --- |
| Application name | FormPortal |
| Homepage URL | `https://github.com/nodemode-dev/formportal` |
| Application description | optional; people see it when they approve |
| Authorization callback URL | `https://github.com/nodemode-dev/formportal` (the form asks for one; the device flow does not use it) |
| Enable Device Flow | on (FormPortal signs in only this way; without it GitHub answers `device_flow_disabled`) |
| Expire user access tokens | off. It is on by default; GitHub's page says to turn it off when the app does not yet handle short-lived tokens, and FormPortal does not refresh them yet, so with it on people would have to sign in again every 8 hours |

Register, then copy the client ID GitHub shows for the app.

### Where the client ID goes

One line in FormPortal's `core/github_client.txt` (below its comment lines), then a FormPortal release. Until that line exists, FormPortal's Preferences, Account says signing in is not set up and everything else works. formMCP and formskills do not sign in.

### What FormPortal asks people for

`read:user` when they sign in, and `repo` added the first time they share from Files (GitHub gives OAuth apps no narrower scope for private repositories and their collaborators). The token stays in the person's system keychain.

### Build requirement

keyring, which FormPortal uses for the keychain, links the system D-Bus library on Linux, so FormPortal's registry entry installs `libdbus-1-dev` for its Linux build (formcompiler v0.4.3). macOS and Windows need nothing extra.

## The release credential (owner)

From formcompiler v0.9.0 every app release is created on the app's own repository: the draft `vX.Y.Z` at the gated commit, the deletion of the app's older drafts and the publishing of a beta or of a `release: publish` app. formcompiler's own Actions token cannot write to another repository, so release.yml's `publish` job runs in the `release` environment of this repository and takes its credential from that environment's secrets. That job checks out formcompiler only and downloads the finished release files; every job that runs the app's own code (the builds, the extras, and the release files job that runs the registry's `assets` and `notes` commands) is outside the environment and holds nothing: an environment secret is not passed on by `secrets: inherit`, and a job without `environment: release` cannot read one. The job accepts two shapes, chosen by which secrets exist (`scripts/release_credential.sh`); with neither it fails before any work with an error that names this page. There is no fallback from one shape to the other: when the App secrets are set and the token cannot be minted (the App is not installed on that repository, the key was revoked), the job fails and says so, and the token is not tried, because a mint failure is a configuration to fix, not a reason to act as a person.

### Shape A, a GitHub App (preferred)

A GitHub App acts as itself, expires its tokens after an hour, and `actions/create-github-app-token` mints one for the single repository being released.

1. In the `nodemode-dev` organisation: Settings, Developer settings, GitHub Apps, New GitHub App. Name `formcompiler releases`, homepage `https://github.com/nodemode-dev/formcompiler`, webhook off, no callback. Repository permissions: Contents, read and write (releases, tags and their assets); nothing else. Where can this app be installed: only on this account.
2. Create the app, then on its page generate a private key (a `.pem` file) and note the client ID (`Iv...`; the numeric App ID works too).
3. Install the app on the organisation, Only select repositories: every app repository in `apps/*.json`, never formcompiler itself. An app registered later is added here, or its release fails with a 404 from the token step.
4. In formcompiler: Settings, Environments, `release` (create it if it is not there). Deployment branches and tags: Selected branches, `main` only, so a workflow on any other branch cannot reach the secrets. A required reviewer may be added, which then holds every `publish` job until approved. Environment secrets: `FORMCOMPILER_APP_ID` (the client ID) and `FORMCOMPILER_APP_PRIVATE_KEY` (the whole `.pem` file).
5. Organisation settings, Third-party access, GitHub Apps: limit who may install GitHub Apps to organisation owners, so no member can install another app that reads the same repositories.
6. If the private key is ever exposed (a log, a laptop, a wrong paste), generate a new key on the App's page, replace the secret, and delete the old key there; every token minted from it dies within the hour anyway.

### Shape B, a fine-grained personal access token

The fallback when the App is not set, and the worse of the two if leaked: it acts as its user on every repository it was given, lives until its expiry, and shows in the audit log as that person. Prefer the App. The token acts as its user: every draft, deletion and publish is that person's.

1. For an owner's account: Settings, Developer settings, Personal access tokens, Fine-grained tokens. Resource owner `nodemode-dev`, Only select repositories: the app repositories, never formcompiler. Repository permissions: Contents, read and write. Give it an expiry and a reminder to renew it.
2. In formcompiler's `release` environment: `FORMCOMPILER_WRITE_TOKEN`.

### The ruleset `release tags`

The organisation ruleset `release tags` lets only owners create, move or delete `v*` tags, and every app repository keeps its `v*` tags under it, so nothing but an owner or the App touches them. The `publish` job creates the tag `v<version>` at the gated commit itself, right before the draft (`POST git/refs` with the write credential): a release at an existing tag is made at that tag's commit whatever target is asked for, so the tag must be formcompiler's before the draft is. If the tag already exists it is read again (annotated tags followed): at the gated commit it is kept; elsewhere with a draft at it, which is the same version rebuilt from a newer commit, it is moved (`PATCH`, force) and the draft refreshed; elsewhere with no draft, the job stops with an error and the owner moves or deletes the tag or bumps the version. A superseded draft's tag is deleted with the draft when it still points at the draft's commit. Before a beta or a `release: publish` app is published the tag is read once more and must still point at the gated commit. So the App (shape A) or the token's user (shape B) must be on that ruleset's bypass list (Organization, Repository, Rulesets, `release tags`, Bypass list) for every app, not only for betas; otherwise the tag step fails with a ruleset violation and no draft is made. That is the only bypass either may hold: never add the App or the token's user to a ruleset that protects `main` or any branch, since a release credential that can push to main is a supply-chain key. An app with `tag_trigger` already has the tag, pushed by its maintainer, so the ruleset is not involved for it; a `v<version>` tag that already exists at another commit refuses the release at the gate, because GitHub makes a release for an existing tag at that tag's commit whatever target is asked for.

### Provenance

The publishing pipeline feeds any published `v*` release it finds on an app repository, so it needs proof that the release came from this workflow and not from a person with write access. Before the draft is made, the `publish` job runs `actions/attest-build-provenance` on two files, `release/dist/SHA256SUMS.txt` and `release/dist/form-app.json` (subject names `SHA256SUMS.txt` and `form-app.json`, which stay stable), with `id-token: write` and `attestations: write`. An attested sums file alone would not say which release it belongs to, so someone with write access could publish `v9.0.0` carrying an older release's attested sums and files; `form-app.json` carries `app`, `version`, `repository`, `tag` and `commit` (the gated sha), is attested too, and is listed in the sums. The pipeline downloads both from the release, runs `gh attestation verify <file> --repo nodemode-dev/formcompiler --signer-workflow nodemode-dev/formcompiler/.github/workflows/release.yml` on each, reads `app`, `version` and `repository` from the manifest and requires them to match the release it is feeding, then checks every asset against the sums (`sha256sum --check`); a release that fails any of this is not fed. GitHub refuses attestations on a private repository without Enterprise, so while formcompiler is private the repository variable `FORMCOMPILER_ATTEST` is set to `off` and the step is skipped; the variable must be removed the moment formcompiler is public, or every release stays unverifiable. There is no other value: unset means attest.

### Reading releases

`FORMCOMPILER_APP_TOKEN` stays a read-only token (Contents and Actions, read) for checkouts, branches, tags, checks and the published releases of the app repositories; the watch and the gate read releases with it. GitHub lists a repository's draft releases only to a token with write access there, so the watch and the gate do not see a waiting draft: "already drafted" and "superseded by a newer draft" never fire for them. The watch skips a commit whose release run already succeeded instead (release.yml runs since the v0.9.0 cut-over, the newest 100 successful ones), and starts the same commit again only from Run workflow on release.yml. The `publish` job reads with the write credential (`versions.py older-drafts --token-env GH_TOKEN`), sees every draft, and deletes the app's older drafts by release id after reading each one is still a draft.
