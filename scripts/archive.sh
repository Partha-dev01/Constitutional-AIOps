#!/usr/bin/env bash
# scripts/archive.sh — produce a self-contained distribution zip for a tagged release.
#
# Usage:  bash scripts/archive.sh <git-tag>
# Output: dist/constitutional-aiops-<tag>.zip + matching .sha256
#
# Contents of the zip:
#   - Full git tree at the specified tag (via `git archive`)
#   - requirements.lock.txt (pip freeze snapshot of current env)
#   - data/lemma-rca.manifest.json (pointer to externally-stored 5.5GB raw data)
#   - benchmark/data/ (curated benchmark JSONs, vetted, with manifest.json)
#   - COMMIT_SHA + ARCHIVED_AT receipt files
#
# Non-destructive: only writes to dist/, never modifies the working tree.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "usage: $0 <git-tag>" >&2
    echo "available tags:" >&2
    git tag --list | sed 's/^/  /' >&2
    exit 1
fi

TAG="$1"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Verify tag exists
if ! git rev-parse --verify --quiet "${TAG}" >/dev/null; then
    echo "ERROR: tag '${TAG}' not found" >&2
    exit 2
fi

OUT_DIR="dist"
OUT_ZIP="${OUT_DIR}/constitutional-aiops-${TAG}.zip"
mkdir -p "${OUT_DIR}"

# Use a temp directory for staging
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
STAGE_NAME="caiops-${TAG}"
STAGE="${TMP}/${STAGE_NAME}"

echo "[archive] staging git tree at ${TAG} → ${STAGE}"
mkdir -p "${STAGE}"
git archive --format=tar "${TAG}" | tar -x -C "${STAGE}"

# Embed receipts
echo "[archive] writing receipts"
git rev-parse "${TAG}" > "${STAGE}/COMMIT_SHA"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${STAGE}/ARCHIVED_AT"
git tag --list "${TAG}" -n20 > "${STAGE}/TAG_MESSAGE.txt"

# Embed pip freeze of current env (best-effort, not fatal)
echo "[archive] capturing pip freeze"
if command -v pip >/dev/null 2>&1; then
    pip freeze > "${STAGE}/requirements.lock.txt" 2>/dev/null \
        || echo "(pip freeze failed; current env may not have all deps installed)" > "${STAGE}/requirements.lock.txt"
else
    echo "(pip not available)" > "${STAGE}/requirements.lock.txt"
fi

# Embed external-data manifest if present
if [ -f data/lemma-rca.manifest.json ]; then
    mkdir -p "${STAGE}/data"
    cp data/lemma-rca.manifest.json "${STAGE}/data/"
fi

# Ensure benchmark curated data is included (it's small, plain-git)
# git archive already includes it; nothing extra needed.

# Build the zip
echo "[archive] zipping → ${OUT_ZIP}"
(cd "${TMP}" && zip -rq "${OLDPWD}/${OUT_ZIP}" "${STAGE_NAME}")

# Generate checksum
sha256sum "${OUT_ZIP}" > "${OUT_ZIP}.sha256"

echo ""
echo "✓ archive complete"
echo "  zip:        ${OUT_ZIP}"
echo "  size:       $(du -h "${OUT_ZIP}" | cut -f1)"
echo "  sha256:     $(cut -d' ' -f1 "${OUT_ZIP}.sha256")"
echo "  commit:     $(cat "${STAGE}/COMMIT_SHA")"
echo "  archived:   $(cat "${STAGE}/ARCHIVED_AT")"
