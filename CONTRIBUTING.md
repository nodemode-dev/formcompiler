# Contributing to FormCompiler

Thank you for helping. FormCompiler aims to be the one place every Form app is built,
signed and released, with every release traceable to a reviewed commit, and it gets
there through real use and real contributions.

## Where to start

- **Report what goes wrong.** A clear bug report, with the workflow run, the app and
  version being released, and what you expected, is one of the most useful things you
  can give. A problem in an app's own code belongs in that app's repository.
- **Look at the open issues.** Comment on one before starting larger work, so nobody
  builds the same thing twice.
- **A new app in the registry** is the owner's decision: propose it in an issue first.
  The registry contract is [docs/REGISTRY.md](docs/REGISTRY.md).

## Setting up

Clone the repository; you need Python 3.11 or newer. The scripts use the standard
library (`cryptography` only to sign the catalogue), and the tests need:

```sh
python3 -m pip install -r tests/requirements.txt
```

The README's "Run the scripts by hand" shows each script on its own.

The code lives in:

| Folder | What is there |
| --- | --- |
| `.github/workflows` | watch, release, desktop-release, feed, yank and self-check |
| `apps` | one registry file per app |
| `scripts` | the Python the workflows run: registry, readiness, gate, plan, build, staging, catalogue, feed, yank |
| `tests` | the test suite |
| `docs` | the registry contract, accounts and the going-public checklist |
| `releases.json`, `yanked.json` | the published catalogue and the yank list, written by the feed and yank workflows |

## Before you open a pull request

Run the same checks CI runs (`self-check.yml`):

```sh
python3 -m pytest tests -q -p no:cacheprovider
actionlint .github/workflows/*.yml
python3 -m py_compile scripts/*.py
python3 -I scripts/registry.py check
```

CI also emits every enabled app's build config, runs `plan.py`, `agents.py` and
`catalog.py` on sample inputs, and refuses an em dash in tracked Markdown or an emoji
in any tracked text.

- Keep each pull request to one change, with tests for what it adds or fixes.
- Write commit subjects the way the history does, in Conventional Commits:
  `feat(release): ...`, `fix(watch): ...`, `chore(registry): ...`. Leave `VERSION`
  and the CHANGELOG version alone; the maintainer bumps them.
- Every third-party action is pinned to a full commit SHA with its version as a
  trailing comment.
- No `${{ }}` expression inside a `run:` script: values reach the shell through
  `env:`.
- Pull requests run with no secrets. Never add `pull_request_target`, and keep the
  `github.repository` guard on every job that signs, publishes or starts a release
  (`tests/test_workflow_guards.py` checks it).
- Signing identities and keys are FormCompiler secrets only; never ask an app
  repository for one.
- No comments in code; the context lives in `scripts/HASHOUT_LOG.md`.

## How changes land

Only the maintainer pushes to `main`. Everyone else forks the repository and opens a pull request into `main`. A pull request merges when both checks pass on an up-to-date branch and the maintainer has approved it after its last push. Changes to the workflows, the registry, the scripts and the yank list also need the owner's review (`.github/CODEOWNERS`).

## Releases

FormCompiler releases the Form apps; a change here takes effect once it is on `main`,
where the watch, release, feed and yank workflows run from. The maintainer bumps
FormCompiler's own `VERSION` and CHANGELOG. An app is released only from a
maintainer's `compile_vX.Y.Z` branch or `vX.Y.Z` tag on a commit already on that app's
`main`, with its version file matching, its version above the last published one and
its own checks green on that commit; a stable release is then a draft that a
maintainer publishes. No contributor's push starts a release. See the README's
"How a release flows".

## Licensing

FormCompiler is licensed under the GNU General Public License v3.0 only
([LICENSE](LICENSE), SPDX `GPL-3.0-only`). By contributing, you agree that your
contribution is licensed under the same terms. Only add code you have the right to
contribute, and name any third-party code and its licence in the pull request. Each
app FormCompiler builds keeps its own licence.

## Patents and other people's IP

A feature may be held back or removed if it would infringe someone else's patent or
other intellectual property. The maintainers decide.

## Conduct

Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md). Security
problems go through [SECURITY.md](SECURITY.md), never a public issue.
