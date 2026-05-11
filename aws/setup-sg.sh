#!/usr/bin/env bash
# aws/setup-sg.sh — create or update the AWS security group for vLLM endpoints.
#
# CRITICAL per vLLM security docs: NEVER expose ports 8000/8001 to 0.0.0.0/0.
# The OpenAI-compatible server has no auth by default. We restrict to current IP.
#
# Run this script when:
#   - First-time VM setup (use `--create` flag)
#   - Your laptop IP changes (re-run without args; it updates ingress)
#
# Non-destructive: only adds/replaces SG rules. Never deletes the SG itself.

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
SG_NAME="${SG_NAME:-aiops-vllm-sg}"
VPC_ID="${VPC_ID:-}"

CREATE_MODE=false
if [ "${1:-}" = "--create" ]; then
    CREATE_MODE=true
fi

# Get current public IP
MY_IP=$(curl -sf https://checkip.amazonaws.com | tr -d '[:space:]')
if [ -z "$MY_IP" ]; then
    echo "ERROR: could not determine current public IP" >&2
    exit 2
fi
MY_CIDR="${MY_IP}/32"
echo "[setup-sg] current public IP: $MY_IP"

# Find or create SG
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" \
    --region "$REGION" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    if [ "$CREATE_MODE" = false ]; then
        echo "ERROR: SG '$SG_NAME' not found. Run with --create to provision." >&2
        exit 3
    fi
    if [ -z "$VPC_ID" ]; then
        VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
            --region "$REGION" --query 'Vpcs[0].VpcId' --output text)
        echo "[setup-sg] using default VPC: $VPC_ID"
    fi
    echo "[setup-sg] creating SG '$SG_NAME' in $VPC_ID..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "vLLM dual-model inference endpoints (SSH + 8000 + 8001)" \
        --vpc-id "$VPC_ID" \
        --region "$REGION" \
        --output text \
        --query 'GroupId')
    echo "[setup-sg] created: $SG_ID"
fi

echo "[setup-sg] SG ID: $SG_ID"

# Revoke stale rules (find any prior CIDRs and remove)
# This is the "update" path — keep SG, just rotate the IP allowlist.
for port in 22 8000 8001; do
    STALE_CIDRS=$(aws ec2 describe-security-groups --group-ids "$SG_ID" \
        --region "$REGION" \
        --query "SecurityGroups[0].IpPermissions[?FromPort==\`$port\`].IpRanges[].CidrIp" \
        --output text 2>/dev/null || echo "")
    for cidr in $STALE_CIDRS; do
        if [ "$cidr" != "$MY_CIDR" ]; then
            echo "  removing stale rule: port $port from $cidr"
            aws ec2 revoke-security-group-ingress --group-id "$SG_ID" \
                --protocol tcp --port "$port" --cidr "$cidr" \
                --region "$REGION" 2>/dev/null || true
        fi
    done
done

# Add current IP for each port (idempotent — aws CLI errors if rule exists, we ignore)
for port in 22 8000 8001; do
    if aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
        --protocol tcp --port "$port" --cidr "$MY_CIDR" \
        --region "$REGION" 2>&1 | grep -q "InvalidPermission.Duplicate"; then
        echo "  port $port: already open to $MY_CIDR"
    else
        echo "  port $port: opened to $MY_CIDR"
    fi
done

echo ""
echo "=========================================="
echo "  SECURITY GROUP READY"
echo "=========================================="
echo "  SG ID:        $SG_ID"
echo "  Open ports:   22 (SSH), 8000 (Qwen3-4B), 8001 (Qwen3-14B)"
echo "  Allowed from: $MY_CIDR (your current public IP)"
echo ""
echo "  WHEN YOUR IP CHANGES: re-run this script (no args needed)"
echo "  WHEN YOU'RE DONE FOR THE DAY: stop the VM (./aws/stop-vm.sh)"
