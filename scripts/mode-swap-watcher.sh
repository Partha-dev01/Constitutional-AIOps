#!/bin/sh
# Constitutional AIOps - serving-mode swap watcher (host-side executor)
#
# Executes in-app Mode 1 <-> Mode 2 swap requests written by the backend
# (POST /api/v1/settings/serving-mode) to the EBS data dir. The backend cannot
# run the swap itself: the swap recreates the backend container, and production
# mounts no docker.sock (by design) — so this small host daemon is the only
# component with Docker rights.
#
# Channel (all under $SWAP_DIR, host path of the backend's AIOPS_DATA_DIR):
#   request.json   {"requested_mode": 1|2, "requested_at": iso, "requested_by": user}
#   status.json    {"state": "swapping"|"done"|"error", "target": N,
#                   "detail": str, "updated_at": iso}
#   last-swap.log  full mode-swap.sh output of the most recent swap
#
# Install on the VM (once):
#   sudo cp /mnt/aiops-repo/scripts/aiops-mode-swap.service /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable --now aiops-mode-swap
#
# Safety:
#   - requests older than STALE_SECONDS (default 900) are marked error and
#     ignored — a request left behind by a stopped VM must not fire a surprise
#     engine swap on thaw.
#   - the request file is deleted BEFORE the swap runs, so a re-poll can never
#     double-fire; one swap at a time by construction (single poll loop).
#   - POSIX sh (dash-safe); python3 (present on the VM) parses the JSON.

set -u

REPO_DIR="${REPO_DIR:-/mnt/aiops-repo}"
SWAP_DIR="${SWAP_DIR:-/mnt/data/app/mode-swap}"
POLL_SECONDS="${POLL_SECONDS:-10}"
STALE_SECONDS="${STALE_SECONDS:-900}"

mkdir -p "$SWAP_DIR"

now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

write_status() {
    # $1 = state, $2 = target (number or null), $3 = detail
    printf '{"state": "%s", "target": %s, "detail": "%s", "updated_at": "%s"}\n' \
        "$1" "${2:-null}" "$3" "$(now_iso)" > "$SWAP_DIR/status.json.tmp"
    mv "$SWAP_DIR/status.json.tmp" "$SWAP_DIR/status.json"
}

current_mode() {
    # Mode 2 iff the mode-2 engine container is running (same signal the
    # mode-swap.sh rails create/remove).
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^aiops-llm-mode2$'; then
        echo 2
    else
        echo 1
    fi
}

echo "aiops-mode-swap watcher: repo=$REPO_DIR swap_dir=$SWAP_DIR poll=${POLL_SECONDS}s"

while :; do
    REQ="$SWAP_DIR/request.json"
    if [ -f "$REQ" ]; then
        TARGET=$(python3 -c "import json;print(json.load(open('$REQ')).get('requested_mode',''))" 2>/dev/null || echo "")
        REQ_AGE=$(( $(date +%s) - $(stat -c %Y "$REQ" 2>/dev/null || echo 0) ))
        rm -f "$REQ"
        if [ "$TARGET" != "1" ] && [ "$TARGET" != "2" ]; then
            write_status error null "unrecognized requested_mode in request.json"
        elif [ "$REQ_AGE" -gt "$STALE_SECONDS" ]; then
            write_status error "$TARGET" "stale request (${REQ_AGE}s old) ignored; re-request from Settings"
        elif [ "$(current_mode)" = "$TARGET" ]; then
            write_status done "$TARGET" "already in mode $TARGET"
        else
            echo "swap requested -> mode $TARGET"
            write_status swapping "$TARGET" "running mode-swap.sh up-mode$TARGET"
            if (cd "$REPO_DIR" && sh scripts/mode-swap.sh "up-mode$TARGET") > "$SWAP_DIR/last-swap.log" 2>&1; then
                write_status done "$TARGET" "swap to mode $TARGET completed"
                echo "swap to mode $TARGET completed"
            else
                write_status error "$TARGET" "mode-swap.sh failed; see mode-swap/last-swap.log on the data volume"
                echo "swap to mode $TARGET FAILED (see $SWAP_DIR/last-swap.log)"
            fi
        fi
    fi
    sleep "$POLL_SECONDS"
done
