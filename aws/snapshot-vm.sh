#!/usr/bin/env bash
# aws/snapshot-vm.sh — create an AMI snapshot of the current VM state.
#
# Use BEFORE risky changes (vLLM version upgrade, model swap, OS update).
# Snapshots are rollback points: if a change breaks the VM, we can launch
# a new instance from the AMI and continue.
#
# Non-destructive: --no-reboot keeps the instance running during snapshot.

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-${AIOPS_INSTANCE_ID:-}}"
LABEL="${1:-checkpoint}"

if [ -z "$INSTANCE_ID" ]; then
    echo "ERROR: set INSTANCE_ID env var" >&2
    exit 2
fi

TS=$(date -u +"%Y%m%d-%H%M")
NAME="aiops-vllm-${LABEL}-${TS}"

echo "[snapshot-vm] creating AMI: $NAME"
AMI_ID=$(aws ec2 create-image \
    --instance-id "$INSTANCE_ID" --region "$REGION" \
    --name "$NAME" \
    --description "vLLM dual-model checkpoint at $TS ($LABEL)" \
    --no-reboot \
    --tag-specifications "ResourceType=image,Tags=[{Key=Project,Value=aiops},{Key=Label,Value=$LABEL}]" \
    --output text \
    --query 'ImageId')

echo ""
echo "=========================================="
echo "  AMI CREATED"
echo "=========================================="
echo "  AMI ID: $AMI_ID"
echo "  Name:   $NAME"
echo "  State:  pending (typically 5-15 min to finish)"
echo ""
echo "  Track progress:"
echo "    aws ec2 describe-images --image-ids $AMI_ID --region $REGION --query 'Images[0].State'"
echo ""
echo "  Cost: ~\$0.05/GB-month for snapshot storage (~\$3-5/mo for full instance)"
echo "  DELETE OLD SNAPSHOTS QUARTERLY to control cost."
