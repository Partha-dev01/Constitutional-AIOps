# AWS VM & Benchmark Monitoring Guide

> **Quick reference** for checking progress on the running AWS deployment from your own terminal. Updated 2026-05-12.

## Resource IDs (live, current)

| Resource | Value |
|---|---|
| Instance ID | `i-091c4de0e95d63154` |
| Instance type | `g6.xlarge` (NVIDIA L4 24GB) |
| Public IP (EIP) | `44.195.172.165` (`eipalloc-0b29e4644256a682c`) |
| EBS volume | `vol-0ff075a7541026572` (100 GB gp3 at `/mnt`) |
| Security group | `sg-09680d8eb448fb704` |
| Region / AZ | `us-east-1` / `us-east-1a` |
| SSH key | `~/.ssh/aiops-key.pem` |
| AWS CLI profile | `aiops-operator` |
| Budget | `aiops-daily-cap` ($5/day, email alerts at 80% + 100%) |

## Quick health snapshot (run anytime, < 5 sec)

```bash
# From your Windows Git Bash or PowerShell with AWS CLI
aws ec2 describe-instances --profile aiops-operator --region us-east-1 \
  --instance-ids i-091c4de0e95d63154 \
  --query 'Reservations[0].Instances[0].{State:State.Name,PublicIP:PublicIpAddress,Launch:LaunchTime}'
```

If `State=running`, the instance is up. If `stopped`, something tripped an auto-stop alarm.

## SSH into the instance

```bash
# Git Bash needs MSYS_NO_PATHCONV=1 to avoid mangling /dev paths
MSYS_NO_PATHCONV=1 ssh -i ~/.ssh/aiops-key.pem ubuntu@44.195.172.165
```

Once in:

```bash
# vLLM container status (the heart of the deployment)
sudo docker compose -f /opt/aiops/aws/docker-compose.vllm.yml ps

# Both should show "healthy" once models are loaded:
#   aiops-qwen3-4b   ... Up X minutes (healthy)
#   aiops-qwen3-14b  ... Up X minutes (healthy)

# If unhealthy or restarting, check logs:
sudo docker logs aiops-qwen3-4b --tail 30
sudo docker logs aiops-qwen3-14b --tail 30

# GPU usage (both models should appear when loaded)
nvidia-smi

# Disk usage
df -h / /mnt
```

## Test vLLM endpoints from your laptop

```bash
# After both containers report healthy, both endpoints respond to /health
curl -s http://44.195.172.165:8000/health    # Qwen3-4B
curl -s http://44.195.172.165:8001/health    # Qwen3-14B

# Quick functional test (4B model)
curl -s http://44.195.172.165:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-4b",
    "messages": [{"role":"user","content":"Reply with TEST"}],
    "temperature": 0,
    "max_tokens": 10,
    "chat_template_kwargs": {"enable_thinking": false}
  }' | python -m json.tool
```

## Cost tracking

```bash
# Current Bedrock model access status (cheap to check, no charge)
aws bedrock list-foundation-models --profile aiops-operator --region us-east-1 \
  --by-inference-type ON_DEMAND \
  --query "modelSummaries[?contains(modelId,'deepseek')].modelId" --output text

# Today's running cost — Cost Explorer is slow but accurate
aws ce get-cost-and-usage --profile aiops-operator \
  --time-period Start=$(date +%Y-%m-%d),End=$(date -d "+1 day" +%Y-%m-%d) \
  --granularity DAILY --metrics UnblendedCost \
  --filter '{"Tags":{"Key":"Project","Values":["aiops"]}}' \
  --query 'ResultsByTime[0].Total.UnblendedCost' 2>/dev/null

# Budget consumption against the $5/day cap
aws budgets describe-budget --profile aiops-operator --account-id 762099405044 \
  --budget-name aiops-daily-cap \
  --query 'Budget.{Limit:BudgetLimit.Amount,Used:CalculatedSpend.ActualSpend.Amount}'
```

Email alerts go to the configured billing-alert address at 80% and 100% — check inbox.

## Benchmark progress (once Phase 4.2 starts)

The benchmark writes to `runs/<timestamp>_v3.0_main/results.jsonl` on your local machine (the runner connects to AWS endpoints over HTTP but stores results locally).

```bash
# In the repo directory
cd "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops"

# How many cases done so far?
LATEST_RUN=$(ls -td runs/*v3.0_main* 2>/dev/null | head -1)
wc -l "$LATEST_RUN/results.jsonl" 2>/dev/null

# Running accuracy
python -c "
import json
results = [json.loads(line) for line in open('$LATEST_RUN/results.jsonl')]
correct = sum(1 for r in results if r.get('passed'))
print(f'{correct}/{len(results)} = {100*correct/len(results):.1f}%')
"

# Last 3 cases (sanity-check no silent failures)
tail -3 "$LATEST_RUN/results.jsonl" | python -m json.tool 2>&1 | tail -50
```

## Stop the instance when done for the day

```bash
# Daily: stop preserves EBS (~$8/mo) and Elastic IP — instant restart next day
bash aws/stop-vm.sh

# Or directly:
aws ec2 stop-instances --profile aiops-operator --region us-east-1 \
  --instance-ids i-091c4de0e95d63154

# Restart:
aws ec2 start-instances --profile aiops-operator --region us-east-1 \
  --instance-ids i-091c4de0e95d63154
# Then re-attach EIP (it should auto-reattach if it was associated when stopped):
aws ec2 associate-address --profile aiops-operator --region us-east-1 \
  --allocation-id eipalloc-0b29e4644256a682c \
  --instance-id i-091c4de0e95d63154
```

**NEVER** `terminate-instances` — that destroys the EBS and you lose model weights.

## What auto-stops protect against

| Trigger | Action | Recovery |
|---|---|---|
| Email alert at 80% of $5/day budget | Email only | Manual review |
| Email alert at 100% of budget | Email only (no auto-stop in current config) | Decide whether to stop or extend |
| CloudWatch idle alarm (CPU < 5% for 30 min) | **Auto-stops instance** (set after instance launch) | `aws ec2 start-instances ...` |
| Guest cron `idle-check.sh` (every 10 min) | **Auto-shutdown if vLLM idle 30 min** | Same restart |
| Spot interruption | N/A (we used On-Demand) | — |

## If something is wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| `docker ps` shows no containers | Compose pull still running OR crashed | `journalctl -u docker.service --since "30 min ago"` |
| Container "Restarting" loop | Model OOM, or FP8 repo 404 | `docker logs <container>` — check first 30 lines |
| `nvidia-smi` doesn't show vLLM processes | Models not loaded yet | Wait 5-10 min after container start |
| `curl :8000/health` returns 503 | Model still loading | Wait. First-time load takes ~5-10 min after container starts. |
| `curl :8000/health` connection refused | SG ingress lost OR instance stopped | Re-run `bash aws/setup-sg.sh` (your IP may have rotated) |
| Benchmark accuracy collapses mid-run | vLLM died OR thinking mode regression | Compare to golden smoke baseline; check container logs |
| `df -h /mnt` shows >85% | Model cache + Docker filling disk | `docker system prune -af` to reclaim unused layers |

## Useful one-liners

```bash
# Live tail of both vLLM logs in parallel (Ctrl+C to exit)
ssh -i ~/.ssh/aiops-key.pem ubuntu@44.195.172.165 \
  'sudo docker compose -f /opt/aiops/aws/docker-compose.vllm.yml logs -f --tail=10'

# Quick GPU memory snapshot from your laptop (no SSH needed)
ssh -i ~/.ssh/aiops-key.pem ubuntu@44.195.172.165 \
  'nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv'

# Re-allow your IP after laptop reconnect (your public IP rotates)
cd "c:/Users/partha/Downloads/files AIOPS NEW/constitutional-aiops"
AWS_PROFILE=aiops-operator bash aws/setup-sg.sh
```

## Phase-by-phase what to expect

| Phase | Expected duration | Hands-off? | Output to check |
|---|---|---|---|
| Image pull | 5-10 min | Yes | `docker images` shows `vllm/vllm-openai:v0.9.2` |
| Model download (both) | 10-25 min | Yes | `docker logs aiops-qwen3-14b` — "Loading checkpoint shards" |
| Container healthy | < 1 min after model load | Yes | `docker compose ps` — "healthy" |
| Golden smoke test (10 cases) | 5 min | Hands-on for first run | All 10 pass |
| Phase 2.5b OpsEval LLM filter | 1-2 hr | Yes | New rows in `benchmark/v0.11/opseval_remine.jsonl` |
| Phase 4.2 Main benchmark (500 cases) | 3-5 hr | Yes | `runs/<ts>/results.jsonl` grows monotonically |
| Phase 4.3 Ablation (3,500 inferences) | 12-18 hr | Yes (overnight) | 7 separate `runs/<ts>_ablation_*/` dirs |
| Phase 4.4-4.7 graph/paraphrase/SOTA | 8-12 hr | Mostly | Various output dirs per phase |

When all benchmark runs finish, stop the VM. The EBS preserves models for the next start.
