# Accounts · the family's GitHub app

FormPortal (from v0.47.0) can sign a person in to their own GitHub account, optionally, so that sharing from Files can use that account as its storage. The family has no server, so the only shared piece is one GitHub OAuth app that belongs to the `nodemode-ai` organisation. This page says how it is registered and where its client ID goes. Nothing here is a secret: the device flow needs only the client ID, never the client secret, and the client secret is never generated for this use or stored anywhere in the family.

## Register it once (owner)

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

## Where the client ID goes

One line in FormPortal's `core/github_client.txt` (below its comment lines), then a FormPortal release. Until that line exists, FormPortal's Preferences, Account says signing in is not set up and everything else works. formMCP and formskills do not sign in.

## What FormPortal asks people for

`read:user` when they sign in, and `repo` added the first time they share from Files (GitHub gives OAuth apps no narrower scope for private repositories and their collaborators). The token stays in the person's system keychain.

## Build requirement

keyring, which FormPortal uses for the keychain, links the system D-Bus library on Linux, so FormPortal's registry entry installs `libdbus-1-dev` for its Linux build (formcompiler v0.4.3). macOS and Windows need nothing extra.
