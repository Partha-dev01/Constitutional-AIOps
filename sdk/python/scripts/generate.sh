#!/usr/bin/env bash
# Regenerate the typed core (constitutional_aiops_client/) from the committed
# OpenAPI snapshot. Run from sdk/python/. Requires a pinned toolchain so local
# and CI produce byte-identical output:
#   pip install "openapi-python-client==0.29.1" "ruff==0.15.8"
# The sdk-drift CI workflow (.github/workflows/sdk-drift.yml) regenerates with
# this same script and runs `git diff --exit-code constitutional_aiops_client/`
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

# Deterministic formatting. With --meta none, openapi-python-client skips its own
# ruff post-format, leaving long unwrapped lines. Apply it explicitly and pinned:
# --isolated ignores any discovered pyproject (the repo root sets line-length 100,
# which the generated tree does not follow) so local and CI produce identical
# output; line-length 88 is the generator's own convention.
python -m ruff format --isolated --line-length 88 constitutional_aiops_client >/dev/null

echo "Regenerated constitutional_aiops_client/ from $schema"
