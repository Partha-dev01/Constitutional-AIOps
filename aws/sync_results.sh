#!/usr/bin/env bash
# sync_results.sh — pull all benchmark run results from AWS instance to local machine
# Usage (from constitutional-aiops/ root):
#   bash aws/sync_results.sh
#   bash aws/sync_results.sh --dry-run    # preview what would be copied
#
# Pulls /mnt/runs/ on the instance → benchmark/results_aws/ locally.
# Safe to run repeatedly — rsync skips unchanged files.

INSTANCE_IP="44.195.172.165"
KEY_PATH="$HOME/.ssh/aiops-key.pem"
REMOTE_PATH="/mnt/runs/"
LOCAL_PATH="$(dirname "$0")/../benchmark/results_aws/"

DRY_RUN=""
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN="--dry-run"
  echo "[sync] DRY RUN — no files will be copied"
fi

echo "[sync] Pulling results from ${INSTANCE_IP}:${REMOTE_PATH} → ${LOCAL_PATH}"

mkdir -p "${LOCAL_PATH}"

MSYS_NO_PATHCONV=1 rsync -avz --progress ${DRY_RUN} \
  -e "ssh -i ${KEY_PATH} -o StrictHostKeyChecking=no" \
  "ubuntu@${INSTANCE_IP}:${REMOTE_PATH}" \
  "${LOCAL_PATH}"

echo "[sync] Done. Run dirs now at: benchmark/results_aws/"
echo "[sync] Index: benchmark/results_aws/RUNS_INDEX.md"
