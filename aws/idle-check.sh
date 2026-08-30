#!/usr/bin/env bash
# aws/idle-check.sh — guest-side idle-stop, runs ON the deployment VM.
#
# Stops the instance after IDLE_THRESHOLD_SEC of NO external HTTP traffic.
# Liveness is measured from CADDY's access log: Caddy is the only public-facing
# service (80/443), so it sees real visitor traffic, while internal Docker
# healthchecks talk to containers directly on aiops-network and never traverse
# Caddy — so they cannot keep the box falsely "alive". This replaces the old
# vLLM-container-log probe, which hard-stopped a GPU-less (bring-your-own-
# endpoint) host on EVERY run because the aiops-qwen3-4b/-14b containers don't
# exist there.
#
# FAIL-SAFE (the key fix): anything that makes liveness UNKNOWN — box freshly
# booted, an admin SSH'd in, the Caddy container absent, its logs unreadable —
# means DO NOT STOP. The old script did the opposite (unknown -> stop), which is
# exactly why it would kill the new host every 10 minutes.
#
# Pairs with the wake-on-visit front door: something else STARTS the box (a
# visitor via the Lambda front door); this script is only the "stop when idle"
# half. Boot-grace keeps a just-woken box alive long enough to serve its first
# request during cold-start.
#
# Install ON the VM (not the laptop) via the shipped systemd timer:
#   aws/systemd/aiops-idle-check.{service,timer}  (runs this every ~10 min)
# Tunables (env, all optional):
#   IDLE_THRESHOLD_SEC  window of no traffic before stopping     (default 1800)
#   BOOT_GRACE_SEC      never stop within this long after boot   (default 600)
#   CADDY_CONTAINER     edge container name to read logs from    (default aiops-caddy)
#   AIOPS_IDLE_LOG      log file path                            (default /var/log/aiops-idle.log)

set -eu

IDLE_THRESHOLD_SEC="${IDLE_THRESHOLD_SEC:-1800}"   # 30 min of no external requests
BOOT_GRACE_SEC="${BOOT_GRACE_SEC:-600}"            # never stop within 10 min of boot
CADDY_CONTAINER="${CADDY_CONTAINER:-aiops-caddy}"
LOG="${AIOPS_IDLE_LOG:-/var/log/aiops-idle.log}"
# Caddy access-log marker: the http.log.access logger's message is "handled
# request" in BOTH console and json formats, so a substring match is robust.
ACCESS_MARKER="${AIOPS_ACCESS_MARKER:-handled request}"

log() { echo "$(date -Iseconds) $*" >> "$LOG" 2>/dev/null || true; }

# --- Guard 0: boot grace. A just-woken box (wake-on-visit) has not served its
# first request yet — never stop it mid-cold-start.
UPTIME_SEC=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0)
if [ "$UPTIME_SEC" -lt "$BOOT_GRACE_SEC" ]; then
    log "SKIP: uptime ${UPTIME_SEC}s < boot grace ${BOOT_GRACE_SEC}s (fail-open)"
    exit 0
fi

# --- Guard 1: an interactive admin session keeps the box alive (fail-open) so
# idle-stop never yanks the VM out from under someone SSH'd in.
if who 2>/dev/null | grep -q .; then
    log "SKIP: interactive login present — not stopping (fail-open)"
    exit 0
fi

# --- Guard 1b: also protect NON-PTY ssh sessions (`ssh host <cmd>` maintenance
# runs), which never appear in who/utmp. Any established inbound connection on
# :22 (server-side source port 22) keeps the box alive (fail-open). Discovered
# live: without this, a maintenance ssh-command session gets the box stopped
# out from under it the moment the idle timer fires.
if command -v ss >/dev/null 2>&1 && \
   ss -tnH state established '( sport = :22 )' 2>/dev/null | grep -q .; then
    log "SKIP: active SSH connection on :22 — not stopping (fail-open)"
    exit 0
fi

# --- Guard 2: Caddy must be present to measure external liveness. If docker or
# the edge container is missing we CANNOT tell whether the box is idle -> never
# stop (fail-open). This is the exact inversion of the old unknown->stop bug.
if ! command -v docker >/dev/null 2>&1; then
    log "SKIP: docker CLI not found — cannot measure liveness (fail-open)"
    exit 0
fi
if ! docker ps --filter "name=${CADDY_CONTAINER}" --format '{{.Names}}' 2>/dev/null | grep -q "${CADDY_CONTAINER}"; then
    log "SKIP: ${CADDY_CONTAINER} not running — cannot measure external liveness (fail-open)"
    exit 0
fi

# --- Liveness: count external HTTP requests Caddy handled in the idle window.
WINDOW_MIN=$(( (IDLE_THRESHOLD_SEC + 59) / 60 ))
if ! CADDY_LOGS=$(docker logs --since "${WINDOW_MIN}m" "${CADDY_CONTAINER}" 2>&1); then
    log "SKIP: could not read ${CADDY_CONTAINER} logs — cannot measure liveness (fail-open)"
    exit 0
fi
REQ_COUNT=$(printf '%s\n' "$CADDY_LOGS" | grep -c "$ACCESS_MARKER" || true)

if [ "${REQ_COUNT:-0}" -gt 0 ]; then
    log "ACTIVE: ${REQ_COUNT} request(s) in last ${WINDOW_MIN}m — not stopping"
    exit 0
fi

# No external traffic in the window -> genuinely idle -> stop the instance.
log "STOPPING: 0 external requests in last ${WINDOW_MIN}m (>= idle threshold ${IDLE_THRESHOLD_SEC}s)"
# InstanceInitiatedShutdownBehavior=stop makes `shutdown -h` a STOP, not a
# terminate — EBS data survives. Same stop mechanism as before.
/sbin/shutdown -h now
