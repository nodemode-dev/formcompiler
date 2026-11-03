#!/usr/bin/env bash
set -euo pipefail
: "${REPOSITORY:?the app repository, owner/name}"
: "${GITHUB_OUTPUT:?}"
echo "name=${REPOSITORY#*/}" >> "$GITHUB_OUTPUT"
if [ "${HAS_APP:-false}" = "true" ]; then
  echo "shape=app" >> "$GITHUB_OUTPUT"
  echo "release credential: the GitHub App, a token for $REPOSITORY only"
elif [ "${HAS_TOKEN:-false}" = "true" ]; then
  echo "shape=token" >> "$GITHUB_OUTPUT"
  echo "release credential: FORMCOMPILER_WRITE_TOKEN"
else
  echo "::error::no credential can write releases on $REPOSITORY: set FORMCOMPILER_APP_ID and FORMCOMPILER_APP_PRIVATE_KEY (a GitHub App) or FORMCOMPILER_WRITE_TOKEN in the release environment; see docs/ACCOUNTS.md"
  exit 1
fi
