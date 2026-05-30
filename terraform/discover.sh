#!/usr/bin/env bash
# Discover the live attributes of the existing AIOps infra and write terraform.tfvars.
#
# READ-ONLY: only AWS *describe* calls — no resources are created, changed, or
# started, and the instance can stay stopped. Requires AWS CLI creds with EC2
# read access.
set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
INSTANCE_ID="${INSTANCE_ID:-i-0123456789abcdef0}"
EIP="${EIP:-203.0.113.10}"
SG_NAME="${SG_NAME:-aiops-vllm-sg}"

echo "[discover] region=$REGION instance=$INSTANCE_ID eip=$EIP sg=$SG_NAME"

read -r AMI ITYPE AZ <<<"$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" --region "$REGION" \
  --query 'Reservations[0].Instances[0].[ImageId,InstanceType,Placement.AvailabilityZone]' \
  --output text)"

ALLOC="$(aws ec2 describe-addresses --public-ips "$EIP" --region "$REGION" \
  --query 'Addresses[0].AllocationId' --output text)"

ROOT_VOL="$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$REGION" \
  --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' --output text)"

echo "[discover] ami=$AMI type=$ITYPE az=$AZ alloc=$ALLOC root_vol=$ROOT_VOL"

cat > terraform.tfvars <<TFVARS
region              = "$REGION"
instance_id         = "$INSTANCE_ID"
instance_type       = "$ITYPE"
instance_ami        = "$AMI"
availability_zone   = "$AZ"
eip_allocation_id   = "$ALLOC"
root_volume_id      = "$ROOT_VOL"
# data_volume_id is the second/attached volume — confirm and set if different:
# data_volume_id    = "vol-0123456789abcdef0"
security_group_name = "$SG_NAME"
app_domain          = "aiops.imaginaerium.in"
TFVARS

echo "[discover] wrote terraform.tfvars"
echo "[discover] next: terraform init && terraform plan"
echo "[discover] plan MUST show only the 2 SG ingress rules to add, 0 to change, 0 to destroy."
