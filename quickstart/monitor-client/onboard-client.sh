#!/usr/bin/env bash
#
# Onboard a REMOTE Linux Docker host ("client") into AIOps monitoring.
# Run this FROM YOUR LAPTOP (Git Bash on Windows works). It installs Docker on the
# client if needed, copies the Grafana Alloy agent, points it at the AWS /ingest
# endpoints, and starts it. From then on EVERY Docker container on that client --
# including the one you care about -- ships logs + metrics to AWS tagged edge=<label>.
#
# Usage:
#   ./onboard-client.sh <ssh-target> <ssh-key.pem> <edge-label> [ingest-pass]
#
# Examples:
#   ./onboard-client.sh ubuntu@203.0.113.9 ~/.ssh/client.pem prod-web1 tRNeQ9RPkji07Uzb
#   INGEST_PASS=... ./onboard-client.sh ec2-user@10.0.0.5 ~/.ssh/k.pem db-host
#
# Verify afterward in Grafana (https://aiops.imaginaerium.in/grafana/):
#   Loki:        {edge="<label>"}
#   Prometheus:  up{edge="<label>"}
set -euo pipefail

TARGET="${1:?ssh target required, e.g. ubuntu@1.2.3.4}"
KEY="${2:?path to ssh private key required}"
LABEL="${3:?edge label required, e.g. prod-web1}"
PASS="${4:-${INGEST_PASS:-}}"
DOMAIN="${AIOPS_DOMAIN:-https://aiops.imaginaerium.in}"

[ -z "$PASS" ] && { echo "ERROR: ingest password required (arg 4 or INGEST_PASS env)"; exit 1; }

# monitoring-agent/ lives two levels up from this script.
AGENT_DIR="$(cd "$(dirname "$0")/../../monitoring-agent" && pwd)"
[ -f "$AGENT_DIR/config.alloy" ] || { echo "ERROR: cannot find monitoring-agent/config.alloy at $AGENT_DIR"; exit 1; }

SSH="ssh -i $KEY -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15"
SCP="scp -i $KEY -o StrictHostKeyChecking=accept-new"
REMOTE_DIR="aiops-monitoring"

echo "[1/4] Ensuring Docker is installed on $TARGET ..."
$SSH "$TARGET" 'command -v docker >/dev/null 2>&1 || { curl -fsSL https://get.docker.com | sudo sh; sudo usermod -aG docker $USER; }'

echo "[2/4] Copying the Alloy agent ..."
$SSH "$TARGET" "mkdir -p ~/$REMOTE_DIR"
$SCP "$AGENT_DIR/config.alloy" "$AGENT_DIR/docker-compose.yml" "$TARGET:~/$REMOTE_DIR/"

echo "[3/4] Writing .env (edge=$LABEL -> $DOMAIN) ..."
$SSH "$TARGET" "cat > ~/$REMOTE_DIR/.env <<EOF
EDGE_LABEL=$LABEL
INGEST_USER=edge
INGEST_PASS=$PASS
LOKI_PUSH_URL=$DOMAIN/ingest/loki/loki/api/v1/push
PROM_RW_URL=$DOMAIN/ingest/prom/api/v1/write
OTLP_HTTP_URL=$DOMAIN/ingest/otlp
EOF"

echo "[4/4] Starting the agent ..."
$SSH "$TARGET" "cd ~/$REMOTE_DIR && sudo docker compose up -d && sleep 6 && sudo docker compose logs --tail 15 alloy"

echo
echo "Done. The client is now monitored. In Grafana run:  {edge=\"$LABEL\"}"
echo "To stop monitoring:  ssh -i $KEY $TARGET 'cd ~/$REMOTE_DIR && sudo docker compose down'"
