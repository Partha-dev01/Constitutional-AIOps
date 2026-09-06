#!/usr/bin/env bash
# Regenerate the typed core (constitutional_aiops_client/) from the committed
# OpenAPI snapshot. Run from sdk/python/. Requires openapi-python-client:
#   pip install "openapi-python-client==0.29.1"
# CI regenerates and runs `git diff --exit-code constitutional_aiops_client/`
# to catch drift between the snapshot and the checked-in client.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
schema="$here/../../openapi/openapi.json"

cd "$here"
rm -rf constitutional_aiops_client
openapi-python-client generate \
  --path "$schema" \
  --config codegen.yml \
  --meta none \
  --output-path constitutional_aiops_client \
  --overwrite
rm -rf constitutional_aiops_client/.ruff_cache
echo "Regenerated constitutional_aiops_client/ from $schema"
