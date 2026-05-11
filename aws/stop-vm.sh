#!/usr/bin/env bash
# aws/stop-vm.sh — gracefully shut down vLLM and stop the AWS instance.
#
# IMPORTANT: uses `stop-instances` NOT `terminate-instances`. This preserves
# the EBS volume (containing downloaded model weights ~15 GB), so the next
# start-vm.sh boots fast without redownloading from HuggingFace.
#
# Non-destructive: stops only. Never terminates.

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-${AIOPS_INSTANCE_ID:-}}"

if [ -z "$INSTANCE_ID" ]; then
    echo "ERROR: set INSTANCE_ID env var (or AIOPS_INSTANCE_ID)" >&2
    exit 2
fi

echo "[stop-vm] gracefully shutting down vLLM containers via SSM..."
# Best-effort — don't fail if SSM agent is unavailable
aws ssm send-command \
    --instance-ids "$INSTANCE_ID" --region "$REGION" \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["cd /opt/aiops && docker compose -f aws/docker-compose.vllm.yml down 2>&1 || true"]' \
    --output text >/dev/null 2>&1 \
    || echo "  (SSM unavailable; proceeding with hard stop)"

sleep 10

echo "[stop-vm] calling aws ec2 stop-instances (preserves EBS)..."
aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region "$REGION" >/dev/null

echo "[stop-vm] waiting for instance to be stopped..."
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID" --region "$REGION"

echo ""
echo "=========================================="
echo "  VM STOPPED"
echo "=========================================="
echo "  Instance: $INSTANCE_ID"
echo "  EBS preserved: model weights intact for next start-vm.sh"
echo "  Cost while stopped: ~\$5/mo (60 GB gp3 EBS only)"
echo ""
echo "  To restart:    ./aws/start-vm.sh"
echo "  To terminate:  see aws/CREATE_VM.md (DO NOT TERMINATE UNLESS PROJECT DONE)"
