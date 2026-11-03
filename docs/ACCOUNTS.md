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

From formcompiler v0.9.0 every app release is created on the app's own repository: the draft `vX.Y.Z` at the gated commit, the deletion of the app's older drafts and the publishing of a beta or of a `release: publish` app. formcompiler's own Actions token cannot write to another repository, so release.yml's draft release job runs in the `release` environment of this repository and takes its credential from that environment's secrets. The build jobs run the app's own scripts and are not in that environment: an environment secret is not passed on by `secrets: inherit`, so a build never holds it. The job accepts two shapes, chosen by which secrets exist; with neither it fails at its first step with an error that names this page.

### Shape A, a GitHub App (preferred)

A GitHub App acts as itself, expires its tokens after an hour, and `actions/create-github-app-token` mints one for the single repository being released.

1. In the `nodemode-dev` organisation: Settings, Developer settings, GitHub Apps, New GitHub App. Name `formcompiler releases`, homepage `https://github.com/nodemode-dev/formcompiler`, webhook off, no callback. Repository permissions: Contents, read and write (releases, tags and their assets); nothing else. Where can this app be installed: only on this account.
2. Create the app, then on its page generate a private key (a `.pem` file) and note the client ID (`Iv...`; the numeric App ID works too).
3. Install the app on the organisation, Only select repositories: every app repository in `apps/*.json`, never formcompiler itself. An app registered later is added here, or its release fails with a 404 from the token step.
4. In formcompiler: Settings, Environments, `release` (create it if it is not there; a required reviewer may be added, which then holds every draft release job until approved). Environment secrets: `FORMCOMPILER_APP_ID` (the client ID) and `FORMCOMPILER_APP_PRIVATE_KEY` (the whole `.pem` file).

### Shape B, a fine-grained personal access token

The fallback when the App is not set. The token acts as its user: every draft, deletion and publish is that person's.

1. For an owner's account: Settings, Developer settings, Personal access tokens, Fine-grained tokens. Resource owner `nodemode-dev`, Only select repositories: the app repositories, never formcompiler. Repository permissions: Contents, read and write. Give it an expiry and a reminder to renew it.
2. In formcompiler's `release` environment: `FORMCOMPILER_WRITE_TOKEN`.

### The ruleset `release tags`

The organisation ruleset `release tags` lets only owners create `v*` tags. A draft has no tag; GitHub creates the tag when the draft is published, as whoever publishes it. A maintainer publishing a stable draft is an owner, so that works. release.yml publishes betas and `release: publish` apps itself, with the credential above, so the App (shape A) or the token's user (shape B) must be on that ruleset's bypass list (Organization, Repository, Rulesets, `release tags`, Bypass list); otherwise the publish step fails with a ruleset violation and the draft stays. An app with `tag_trigger` already has the tag, pushed by its maintainer, so the ruleset is not involved for it.

### Reading releases

`FORMCOMPILER_APP_TOKEN` stays a read-only token (Contents and Actions, read) for checkouts, branches, tags, checks and the published releases of the app repositories; the watch and the gate read releases with it. GitHub lists a repository's draft releases only to a token with write access there, so the watch does not see a waiting draft; it skips a commit whose release run already succeeded instead, and starts the same commit again only from Run workflow on release.yml. The draft release job reads with the write credential and sees every draft.
