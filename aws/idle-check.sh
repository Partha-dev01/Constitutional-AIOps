#!/usr/bin/env bash
# aws/idle-check.sh — guest-side cron, runs ON the VM (not from laptop).
#
# Belt-and-suspenders backup to the CloudWatch idle-CPU alarm.
# Stops the instance if no vLLM request hit either port in the last 30 min.
# Catches the "alarm-evaded" case where Docker containers idle but CPU
# baseline keeps us above the 5% threshold.
#
# Install via cron on the VM (NOT laptop):
#   */10 * * * * /opt/aiops/idle-check.sh

set -eu

IDLE_THRESHOLD_SEC=1800  # 30 min
LOG=/var/log/aiops-idle.log

# Find most recent request hitting either vLLM port
# We check the nginx-like access log of vLLM containers via docker logs.
last_req_epoch() {
    # Look at last 50 log lines for either container; extract a timestamp
    # vLLM logs requests like: INFO:     192.168.x.x:54321 - "POST /v1/chat/completions ..."
    local latest=0
    for container in aiops-qwen3-4b aiops-qwen3-14b; do
        if docker ps --filter "name=$container" --format '{{.Names}}' | grep -q "$container"; then
            # vLLM log timestamps are in container time; rough heuristic:
            # if container had ANY log line in last 30 min, consider it active.
            recent=$(docker logs --since 30m "$container" 2>&1 | grep -c "POST /v1" || true)
            if [ "$recent" -gt 0 ]; then
                latest=$(date +%s)
                break
            fi
        fi
    done
    echo "$latest"
}

NOW=$(date +%s)
LAST=$(last_req_epoch)
IDLE=$((NOW - LAST))

echo "$(date -Iseconds) idle=${IDLE}s threshold=${IDLE_THRESHOLD_SEC}s last_req=$LAST" >> "$LOG"

if [ "$LAST" = "0" ] || [ "$IDLE" -gt "$IDLE_THRESHOLD_SEC" ]; then
    echo "$(date -Iseconds) STOPPING: idle ${IDLE}s > ${IDLE_THRESHOLD_SEC}s" >> "$LOG"
    # Graceful shutdown — `shutdown` triggers EC2 stop behavior since the
    # instance is configured with InstanceInitiatedShutdownBehavior=stop
    /sbin/shutdown -h now
fi
