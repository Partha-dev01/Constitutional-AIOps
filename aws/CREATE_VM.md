# AWS VM One-Time Setup Runbook

**Status**: PREPARED, awaiting user go-ahead to execute. The plan owner explicitly held VM launch until prep is complete and reviewed.

This runbook covers the **one-time** AWS provisioning: IAM, EBS, SG, instance launch, vLLM bring-up. After this completes, daily ops are handled by `aws/start-vm.sh` / `aws/stop-vm.sh` / `aws/snapshot-vm.sh`.

## Pre-flight (DO BEFORE ANY AWS RESOURCE CREATION)

- [ ] **Quota approved**: confirm Spot quota = 8 (see `aws/QUOTA_REQUEST.md`). Run:
  ```bash
  aws service-quotas get-service-quota --service-code ec2 \
      --quota-code L-3819A6DF --region us-east-1 --query 'Quota.Value'
  ```
- [ ] **Budget alarm armed**: $5/day AWS Budget set via console (see §6 below)
- [ ] **Working directory**: scripts assume execution from repo root

## 1. IAM hardening (do first — replaces root creds for daily ops)

```bash
# Create operator user
aws iam create-user --user-name aiops-operator
aws iam attach-user-policy --user-name aiops-operator \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess
aws iam attach-user-policy --user-name aiops-operator \
    --policy-arn arn:aws:iam::aws:policy/AWSBudgetsFullAccess
aws iam attach-user-policy --user-name aiops-operator \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccessV2
aws iam attach-user-policy --user-name aiops-operator \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# Generate access key (save the output — shown only once)
aws iam create-access-key --user-name aiops-operator
# Save to ~/.aws/credentials under profile [aiops-operator]
```

Then enable MFA on the root account via AWS Console (one-time, manual).

## 2. EBS gp3 volume for model weights (60 GB)

```bash
# Create volume in same AZ as planned instance
AZ=us-east-1a
VOL_ID=$(aws ec2 create-volume --size 60 --volume-type gp3 \
    --availability-zone $AZ --region us-east-1 \
    --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=aiops-models},{Key=Project,Value=aiops}]' \
    --output text --query VolumeId)
echo "Created volume: $VOL_ID"
aws ec2 wait volume-available --volume-ids $VOL_ID --region us-east-1
```

This costs ~$5/month even while the instance is stopped.

## 3. Security group

```bash
bash aws/setup-sg.sh --create
# Note the SG ID it prints — needed for instance launch
```

## 4. Elastic IP (free while attached, stable endpoint)

```bash
EIP_ALLOC=$(aws ec2 allocate-address --region us-east-1 \
    --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=aiops-vllm-eip}]' \
    --output text --query AllocationId)
echo "EIP allocation: $EIP_ALLOC"
```

## 5. Launch g6.xlarge instance

```bash
# Use AWS Deep Learning AMI (PyTorch 2.x, Ubuntu 22.04) — has NVIDIA drivers
AMI_ID=$(aws ec2 describe-images --owners amazon \
    --filters "Name=name,Values=Deep Learning AMI GPU PyTorch 2.*Ubuntu 22.04*" \
              "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text --region us-east-1)
echo "Latest DLAMI: $AMI_ID"

# Launch — fill in SG_ID and SUBNET_ID from prior steps
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type g6.xlarge \
    --key-name <your-keypair> \
    --security-group-ids <SG_ID> \
    --instance-initiated-shutdown-behavior stop \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=aiops-vllm},{Key=Project,Value=aiops},{Key=BudgetControlAction,Value=Stop}]' \
    --instance-market-options 'MarketType=spot' \
    --output text --query 'Instances[0].InstanceId' \
    --region us-east-1)
echo "Instance: $INSTANCE_ID"
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-1

# Attach EBS data volume
aws ec2 attach-volume --device /dev/sdf \
    --volume-id $VOL_ID --instance-id $INSTANCE_ID --region us-east-1

# Associate EIP
aws ec2 associate-address --allocation-id $EIP_ALLOC \
    --instance-id $INSTANCE_ID --region us-east-1
```

Save the `INSTANCE_ID` to `~/.aiops-instance-id` so `start-vm.sh`/`stop-vm.sh` pick it up.

## 6. AWS Budget (cost guardrail — daily $5 hard alert)

Create via console (Budgets → Create budget → Cost budget):
- Period: Daily
- Budget amount: $5
- Filter: Tag `Project=aiops`
- Notification: 80% actual → email to the configured billing-alert address
- Action: at 100% threshold, stop EC2 instances tagged `BudgetControlAction=Stop`

## 7. CloudWatch idle-stop alarm

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name "aiops-idle-stop" \
    --metric-name CPUUtilization --namespace AWS/EC2 \
    --statistic Average --period 300 --evaluation-periods 6 \
    --threshold 5 --comparison-operator LessThanThreshold \
    --dimensions Name=InstanceId,Value=$INSTANCE_ID \
    --alarm-actions "arn:aws:automate:us-east-1:ec2:stop" \
    --region us-east-1
```

Stops the instance after 30 min of CPU < 5%.

## 8. First-boot configuration (SSH into the instance once)

```bash
ssh -i ~/.ssh/<your-keypair>.pem ubuntu@<EIP>

# Format and mount the data volume
sudo mkfs.ext4 -L aiops-models /dev/nvme1n1
sudo mkdir -p /mnt/models /mnt/hf-cache
sudo mount /dev/nvme1n1 /mnt/models
# Add to /etc/fstab for auto-mount on restart:
echo "LABEL=aiops-models  /mnt/models  ext4  defaults,nofail  0  2" | sudo tee -a /etc/fstab
sudo chown -R ubuntu:ubuntu /mnt/models /mnt/hf-cache

# Install Docker Compose plugin (DLAMI has docker, but maybe not v2 compose)
docker compose version || sudo apt-get install -y docker-compose-plugin

# Verify NVIDIA Container Toolkit (should be pre-installed on DLAMI)
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Pull this repo onto the instance
sudo mkdir -p /opt/aiops && sudo chown ubuntu:ubuntu /opt/aiops
cd /opt/aiops
git clone https://github.com/Partha-dev01/Constitutional-AIOps.git .
git checkout main

# Install the idle-check cron
sudo cp aws/idle-check.sh /opt/aiops/idle-check.sh
sudo chmod +x /opt/aiops/idle-check.sh
( crontab -l 2>/dev/null; echo "*/10 * * * * /opt/aiops/idle-check.sh" ) | crontab -

# First-time model pull (will take ~5-10 min, ~15 GB of HF downloads)
docker compose -f aws/docker-compose.vllm.yml up -d
docker compose -f aws/docker-compose.vllm.yml logs -f  # watch until both healthy
```

Once both containers report `healthy`, snapshot the AMI:

```bash
# From laptop:
bash aws/snapshot-vm.sh baseline
```

That AMI becomes your rollback point.

## 9. Verify endpoints (from laptop)

```bash
EIP=<your EIP>
curl -s http://$EIP:8000/v1/models | jq
curl -s http://$EIP:8001/v1/models | jq

# Determinism smoke test
curl -s -X POST http://$EIP:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "qwen3-4b",
      "messages": [{"role":"user","content":"Reply with the single word: TEST"}],
      "temperature": 0.0,
      "seed": 42,
      "max_tokens": 5,
      "chat_template_kwargs": {"enable_thinking": false}
    }' | jq .choices[0].message.content
# Expected: "TEST" (or similar single-token response — exact text varies)
```

## 10. Then: update repo `.env` with new endpoint URLs

```bash
# In local repo:
echo "FAST_AGENT_URL=http://<EIP>:8000/v1"      >> .env
echo "REASONING_AGENT_URL=http://<EIP>:8001/v1" >> .env
```

## 11. Run golden smoke test against AWS

```bash
GOLDEN_SMOKE_LIVE=1 pytest tests/test_golden_regression.py -v
# All 10 should pass before proceeding to full benchmark.
```

## Verification end-state

- [x] Quota: Spot 8 vCPU approved
- [x] IAM: aiops-operator user with EC2/Budgets/CloudWatch/SSM access
- [x] EBS: 60 GB gp3 volume `aiops-models`
- [x] SG: `aiops-vllm-sg` with 22+8000+8001 open to current IP
- [x] EIP: stable public IP allocated
- [x] Instance: g6.xlarge Spot, attached EBS, attached EIP
- [x] vLLM: both Qwen3 containers healthy on ports 8000/8001
- [x] Cost guards: Budget $5/day + CloudWatch idle alarm + guest cron
- [x] AMI snapshot: `aiops-vllm-baseline-<date>` for rollback
- [x] Golden tests: 10/10 pass live

## When done daily

```bash
./aws/stop-vm.sh
```

## DO NOT

- ❌ Run `aws ec2 terminate-instances` — would lose EBS and require redownloading models
- ❌ Expose ports 8000/8001 to 0.0.0.0/0 — vLLM has no auth, anyone could use your GPU
- ❌ Use root credentials for daily ops — use `aiops-operator` profile
- ❌ Delete the AMI snapshots without backing them up first
