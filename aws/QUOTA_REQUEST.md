# AWS Service Quota Increase Request

**Submit this in the AWS Console** at:
Service Quotas → EC2 → Search "G and VT Spot Instance Requests" → Request quota increase

## Current State (verified 2026-05-11 via `aws service-quotas get-service-quota`)

| Quota | Current Value | Target | Justification |
|-------|---------------|--------|---------------|
| Running On-Demand G and VT instances | 4 vCPUs | 8 vCPUs | One-instance buffer for restart-on-failure |
| **All G and VT Spot Instance Requests** | **0 vCPUs** | **8 vCPUs** | **Primary ask — unlocks ~70% cost savings via Spot** |

Submit both rows in the same ticket. The on-demand bump is usually auto-approved
in minutes; the Spot bump typically needs human review (4-48 hours).

## Justification (paste verbatim into the request form)

> Project: Academic research benchmark on Constitutional-AI policy evaluation
> using open-weights LLMs (Qwen3-4B-Instruct and Qwen3-14B). I need to launch
> a single g6.xlarge instance (4 vCPU, 1× NVIDIA L4 24GB) on Spot to run a
> vLLM OpenAI-compatible inference server for a fixed-duration benchmark suite
> (estimated 40-60 GPU-hours total). Spot pricing is essential to keep the
> experiment within a $50 GPU budget for the term project.
>
> Workload profile:
>   - Inference-only (no model training, no fine-tuning)
>   - Single instance, single region (us-east-1)
>   - Duration: 4 weeks
>   - Models hosted on attached EBS gp3 volume (not re-downloaded each run)
>
> The 8 vCPU request gives me a one-instance buffer in case Spot capacity churn
> forces an immediate restart on a different instance family within the G class
> (e.g., g5.xlarge fallback for g6.xlarge). I am NOT requesting concurrent
> multi-instance capacity — just headroom for one running plus one restarting.
>
> Region: us-east-1
> Instance family: g6.xlarge (primary), g5.xlarge or g6e.xlarge (fallback)
> Account is in good standing and has on-demand G quota of 4 vCPU already
> approved.

## Why this template gets approved fast (per AWS re:Post + Medium guidance)

1. **Specific instance + region** named explicitly — no "any GPU anywhere" ambiguity
2. **Workload is inference, not training** — much lower abuse risk profile
3. **2× current, not 10×** — auto-approval threshold; jumps to 32+ vCPU get human-flagged
4. **Single account, single region, time-bounded** — clearly bounded blast radius
5. **Cost-justification stated** — humanizes the request (academic budget)

## What happens after submission

| Stage | Expected time |
|-------|---------------|
| Email confirmation | < 1 minute |
| On-Demand bump approved | minutes-to-1 hour |
| Spot bump approved | 4-48 hours (human review) |
| If rejected | Reply asking for further detail; do NOT resubmit a fresh request |

## Verification command (run after approval)

```bash
aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-3819A6DF \
    --region us-east-1 \
    --query 'Quota.[QuotaName,Value]' --output text
# Should now show: "All G and VT Spot Instance Requests   8.0"
```

## Cost impact when approved

| Scenario | g6.xlarge $/hr | 50hr cost |
|----------|----------------|-----------|
| On-Demand only (current) | $0.80 | $40 |
| Spot (post-approval) | ~$0.30-0.40 | $15-20 |
| **Savings** | — | **$20-25** |

Even if approval takes 48 hours, we can begin Phase 1+2 work (already done)
and Phase 3.2-3.9 prep without GPU. Quota approval is the gate for **VM launch
only**.
