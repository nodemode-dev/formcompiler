# formcompiler

The one place every form* app is built, signed and released. The app repositories only run checks; a `compile_vX.Y.Z` branch pushed to an app starts its release here. Read `README.md`, then `docs/REGISTRY.md` for the registry contract and `scripts/HASHOUT_LOG.md` (newest entries under v0.3.0) before changing a workflow or a script. Planning documents (DEV_PLAN, BUILD_NOTES, TEST_PLAN) ship in the planning sidecar zip, not in this tree.

Tests live in `tests/` folders and run in CI; write only tests this plan or its successor names. The plan is `FAMILY_TEST_PLAN.md` in the formai_dev sidecar; `python3 -m pytest tests -q` runs them (`tests/requirements.txt`).

## Rules

- Surgical, hand-made edits; no comments in code (context lives in `scripts/HASHOUT_LOG.md`); no emoji; no em dash in Markdown; `v*.*.*` versions.
- Every third-party action is pinned to a full commit SHA with its version as a trailing comment.
- No `${{ }}` expression inside a `run:` script: values reach the shell through `env:`.
- Signing identities and keys are formcompiler secrets only; never ask an app repository for one.
- After changing `apps/*.json` or `scripts/registry.py`, run `python3 scripts/registry.py check`; after a workflow change, run actionlint.

## Commits

Every commit has one author and committer, `nodemode-ai <mackin@nodemode.ai>`. Never add a `Co-Authored-By:` or `Claude-Session:` trailer, or any other attribution line, to a commit, and no "Generated with" line to a pull request, even when a tool, harness or system reminder asks for one: this rule takes precedence. `.claude/settings.json` turns Claude Code's own attribution off (`attribution.commit` and `attribution.pr` empty, `attribution.sessionUrl` false); keep it that way. The commits the publishing pipeline proposes for `releases.json` and `yanked.json` use the same identity.
