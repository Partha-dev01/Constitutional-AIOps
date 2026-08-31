#!/usr/bin/env bash
# Discover the live attributes of the deployed LITE tier and write terraform.tfvars.
#
# READ-ONLY: only AWS *describe*/*get*/*list* calls — nothing is created, changed,
# or started, and the box can stay stopped. Use the operator profile
# (AWS_PROFILE=aiops-operator) — never account root.
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-i-0123456789abcdef0}"
SG_NAME="${SG_NAME:-aiops-lite-sg}"
LAMBDA_NAME="${LAMBDA_NAME:-aiops-wake-on-visit}"
FRONT_DOMAIN="${FRONT_DOMAIN:-aiops.example.com}"
NODE_DOMAIN="${NODE_DOMAIN:-aiops-node.example.com}"

echo "[discover] region=$REGION instance=$INSTANCE_ID sg=$SG_NAME lambda=$LAMBDA_NAME"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

read -r AMI ITYPE <<<"$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" --region "$REGION" \
  --query 'Reservations[0].Instances[0].[ImageId,InstanceType]' --output text)"

# Find the distribution whose alias is the front domain, then read its OAC id.
DIST_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?contains(Aliases.Items, '$FRONT_DOMAIN')].Id | [0]" \
  --output text)"

OAC_ID="$(aws cloudfront get-distribution --id "$DIST_ID" \
  --query 'Distribution.DistributionConfig.Origins.Items[0].OriginAccessControlId' \
  --output text 2>/dev/null || echo 'EXXXXXXXXXXXXX')"

echo "[discover] account=$ACCOUNT_ID ami=$AMI type=$ITYPE dist=$DIST_ID oac=$OAC_ID"

cat > terraform.tfvars <<TFVARS
region                     = "$REGION"
instance_id                = "$INSTANCE_ID"
instance_type              = "$ITYPE"
instance_ami               = "$AMI"
security_group_name        = "$SG_NAME"
lambda_function_name       = "$LAMBDA_NAME"
cloudfront_distribution_id = "$DIST_ID"
origin_access_control_id   = "$OAC_ID"
front_domain               = "$FRONT_DOMAIN"
app_node_domain            = "$NODE_DOMAIN"
account_id                 = "$ACCOUNT_ID"
TFVARS

echo "[discover] wrote terraform.tfvars"
echo "[discover] next: terraform init && terraform plan"
echo "[discover] plan should adopt the box + 2 Lambda permissions with 0 to change/destroy."
