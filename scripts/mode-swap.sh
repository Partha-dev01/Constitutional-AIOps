#!/bin/sh
# Constitutional AIOps - Mode 1 <-> Mode 2 swap helper (Mode 2 plan, Phase 1)
#
# Wraps the documented one-command swap contract:
#
#   # Mode 1 (exactly as today — the frozen artifact)
#   docker compose -f docker-compose.yml -f docker/docker-compose.production.yml up -d
#   # Mode 2
#   docker compose -f docker-compose.yml -f docker/docker-compose.production.yml \
#     -f docker/docker-compose.mode2.yml up -d
#
# Usage (run ON the deployment host, from the repo root):
#   scripts/mode-swap.sh up-mode1   # bring up the frozen Mode 1 stack
#   scripts/mode-swap.sh up-mode2   # bring up the Mode 2 overlay stack
#   scripts/mode-swap.sh status     # compose ps + GET /api/v1/health/serving
#
# Notes:
# - Uses --env-file .env.production when present (the production stack's
#   secrets/domain live there); falls back to plain environment for dry runs.
# - Swapping stops the OTHER mode's engine container(s) first: profiled-out
#   services are not orphans, so `up` alone would leave the old engines
#   holding GPU memory alongside the new one (24 GB L4 cannot fit both).
# - Data stores are untouched by design: both stacks bind-mount the same
#   /mnt/data paths, and neither this script nor the overlay touches volumes.
# - POSIX sh compatible (dash/ash safe): no arrays, no local, no [[ ]].

set -eu

MODE1_FILES="-f docker-compose.yml -f docker/docker-compose.production.yml"
MODE2_FILES="$MODE1_FILES -f docker/docker-compose.mode2.yml"

if [ -f .env.production ]; then
    ENV_FILE="--env-file .env.production"
else
    ENV_FILE=""
    echo "WARN: .env.production not found in $(pwd); continuing without --env-file" >&2
fi

# shellcheck disable=SC2086  # word-splitting of the file lists is intentional
compose_mode1() { docker compose $ENV_FILE $MODE1_FILES "$@"; }
# shellcheck disable=SC2086
compose_mode2() { docker compose $ENV_FILE $MODE2_FILES "$@"; }

serving_health() {
    # The backend publishes no host port in production (Caddy fronts it), so
    # probe from inside the container. Never fails the script: right after an
    # `up` the backend may still be starting.
    echo "--- GET /api/v1/health/serving ---"
    if docker exec aiops-backend curl -sf http://localhost:8000/api/v1/health/serving; then
        echo ""
    else
        echo "(backend not reachable yet — it may still be starting; re-run: $0 status)"
    fi
}

wait_engine_healthy() {
    # $1 = container name, $2 = timeout seconds. A vLLM engine can take several
    # minutes to load weights into VRAM — longer than compose is willing to wait
    # on its depends_on healthcheck, which aborts the whole `up` with
    # "dependency failed to start" while the engine is still mid-load.
    _waited=0
    while [ "$_waited" -lt "$2" ]; do
        _st=$(docker inspect --format '{{.State.Health.Status}}' "$1" 2>/dev/null || echo missing)
        if [ "$_st" = "healthy" ]; then
            return 0
        fi
        # Container never got created (the failed `up` died earlier than the
        # engine step) — nothing to wait on; let the retry `up` create it.
        if [ "$_st" = "missing" ] && [ "$_waited" -ge 30 ]; then
            echo "WARN: container $1 does not exist; skipping the health wait" >&2
            return 1
        fi
        sleep 10
        _waited=$((_waited + 10))
    done
    echo "WARN: $1 still not healthy after ${2}s (status: $_st)" >&2
    return 1
}

case "${1:-}" in
    up-mode1)
        echo "==> Swapping to Mode 1 (frozen dual-engine artifact)"
        # Free the GPU first. llm-mode2 is not defined in the Mode 1 file
        # set, so --remove-orphans below also removes its container.
        docker stop aiops-llm-mode2 2>/dev/null || true
        # First `up` can lose the race between the engines' multi-minute model
        # load and compose's depends_on health wait; wait the engines healthy
        # and retry once before declaring the swap failed.
        if ! compose_mode1 up -d --remove-orphans; then
            echo "WARN: up-mode1 attempt 1 failed (engine healthcheck race?); waiting for engines, then retrying once" >&2
            wait_engine_healthy aiops-qwen3-4b 600 || true
            wait_engine_healthy aiops-qwen3-14b 600 || true
            compose_mode1 up -d --remove-orphans
        fi
        serving_health
        ;;
    up-mode2)
        echo "==> Swapping to Mode 2 (overlay: docker/docker-compose.mode2.yml)"
        # Free the GPU first. qwen3-4b/qwen3-14b stay DEFINED under the
        # overlay (profiled-out, not orphans), so `up` would not stop them.
        docker stop aiops-qwen3-4b aiops-qwen3-14b 2>/dev/null || true
        if ! compose_mode2 up -d --remove-orphans; then
            echo "WARN: up-mode2 attempt 1 failed (engine healthcheck race?); waiting for the engine, then retrying once" >&2
            wait_engine_healthy aiops-llm-mode2 600 || true
            compose_mode2 up -d --remove-orphans
        fi
        serving_health
        ;;
    status)
        echo "--- docker compose ps (both modes' services; -a includes stopped) ---"
        # --profile mode1 re-activates the profiled-out Mode 1 engines so the
        # listing covers every service regardless of which mode is live.
        compose_mode2 --profile mode1 ps -a
        serving_health
        ;;
    *)
        echo "Usage: $0 {up-mode1|up-mode2|status}" >&2
        exit 1
        ;;
esac
