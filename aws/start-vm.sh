#!/usr/bin/env bash
# aws/start-vm.sh — boot the AWS g6.xlarge, wait for vLLM ready, print endpoints.
#
# Prerequisites:
#   - Instance already created (see aws/CREATE_VM.md for one-time setup)
#   - $INSTANCE_ID set in env or AIOPS_INSTANCE_ID
#   - aws CLI configured (profile: aiops-operator preferred over root)
#
# Non-destructive: only starts a stopped instance, never creates/terminates.

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-${AIOPS_INSTANCE_ID:-}}"

if [ -z "$INSTANCE_ID" ]; then
    echo "ERROR: set INSTANCE_ID env var (or AIOPS_INSTANCE_ID)" >&2
    exit 2
fi

echo "[start-vm] starting $INSTANCE_ID in $REGION..."
aws ec2 start-instances --instance-ids "$INSTANCE_ID" --region "$REGION" >/dev/null

echo "[start-vm] waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# Fetch public IP
IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

if [ -z "$IP" ] || [ "$IP" = "None" ]; then
    echo "ERROR: no public IP assigned. Allocate an EIP or check VPC config." >&2
    exit 3
fi

echo "[start-vm] instance at $IP — waiting for vLLM endpoints..."

# Poll both vLLM health endpoints
for port in 8000 8001; do
    echo -n "  port $port: "
    for i in $(seq 1 60); do  # up to 5 min wait
        if curl -sf -m 5 "http://$IP:$port/health" >/dev/null 2>&1; then
            echo "ready"
            break
        fi
        echo -n "."
        sleep 5
    done
    if ! curl -sf -m 5 "http://$IP:$port/health" >/dev/null 2>&1; then
        echo " TIMEOUT after 5 min"
        echo "  (check docker logs on instance — model load may have failed)"
        exit 4
    fi
done

echo ""
echo "=========================================="
echo "  vLLM endpoints READY"
echo "=========================================="
echo "  Qwen3-4B  : http://$IP:8000/v1"
echo "  Qwen3-14B : http://$IP:8001/v1"
echo ""
echo "  Update .env:"
echo "    FAST_AGENT_URL=http://$IP:8000/v1"
echo "    REASONING_AGENT_URL=http://$IP:8001/v1"
echo ""
echo "  STOP THE VM when done!  ./aws/stop-vm.sh   (~\$0.80/hr while running)"
