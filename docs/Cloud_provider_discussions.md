# Cloud Provider Discussions - Constitutional AIOps

> **Document Created**: 2025-12-19
> **Purpose**: Record of cloud provider research and cost analysis for LLM hosting

---

## Table of Contents
1. [SageMaker Analysis](#1-sagemaker-analysis)
2. [AWS GPU Instance Alternatives](#2-aws-gpu-instance-alternatives)
3. [Jarvis Labs GPU Cloud](#3-jarvis-labs-gpu-cloud)
4. [Hybrid Architecture (Local Dev + Remote GPU)](#4-hybrid-architecture-local-dev--remote-gpu)
5. [Final Recommendations](#5-final-recommendations)

---

## 1. SageMaker Analysis

### Initial Question
> "Can we run the actual dev system locally and use AWS SageMaker to run both LLMs (Qwen3-4B and Qwen3-14B)? Is this possible based on the current system, and what's the comparative cost?"

### Technical Feasibility: YES (with modifications)

#### Current Architecture
The system uses **OpenAI-compatible endpoints** configured via environment variables:
```
FAST_AGENT_URL=http://localhost:8081/v1      → Qwen3-4B
REASONING_AGENT_URL=http://localhost:8082/v1  → Qwen3-14B
```

The backend uses `httpx.AsyncClient` to make HTTP POST requests to `/v1/chat/completions`.

#### What SageMaker Would Need

| Requirement | SageMaker Support |
|-------------|-------------------|
| OpenAI-compatible API | Native endpoints use different format |
| `/v1/chat/completions` | SageMaker uses `/invocations` |
| Custom GGUF models | Requires custom container |
| Always-on endpoints | Real-time inference endpoints |

#### Solution: Use vLLM on SageMaker
Deploy **vLLM** as a custom container on SageMaker - it provides OpenAI-compatible API out of the box:
```
FAST_AGENT_URL=https://<sagemaker-endpoint-1>/v1
REASONING_AGENT_URL=https://<sagemaker-endpoint-2>/v1
```

**Changes Required:**
1. Create custom SageMaker container with vLLM
2. Add HTTPS/authentication headers to model_router.py
3. Handle network latency (50-200ms added per request)

### Cost Comparison

#### Option 1: Current - Single g6.xlarge (RECOMMENDED)

| Item | Spot | On-Demand |
|------|------|-----------|
| g6.xlarge (L4 24GB) | $0.35/hr | $0.80/hr |
| Monthly (24/7) | **~$252** | **~$576** |
| Includes | Everything (LLMs, backend, frontend, DB, monitoring) |

#### Option 2: Local Dev + SageMaker LLMs

**SageMaker Real-time Endpoints:**

| Model | Instance | Cost/hr | Monthly |
|-------|----------|---------|---------|
| Qwen3-4B (4GB VRAM) | ml.g4dn.xlarge (T4 16GB) | $0.74 | $533 |
| Qwen3-14B (11GB VRAM) | ml.g5.xlarge (A10G 24GB) | $1.41 | $1,015 |
| **Subtotal (SageMaker)** | | **$2.15/hr** | **$1,548** |

**Plus Local Dev:**

| Item | Cost |
|------|------|
| Local laptop | $0 |
| OR EC2 t3.medium | ~$30/month |

**Total SageMaker Option:** ~$1,548 - $1,578/month

#### Option 3: SageMaker Serverless (Pay-per-request)

| Concern | Issue |
|---------|-------|
| Cold start | 30-60 seconds (unacceptable for real-time ops) |
| Custom models | Limited support for GGUF/vLLM |
| Pricing | Complex (memory-seconds + requests) |

**Verdict:** Not suitable for always-on AIOps system.

### Cost Summary

| Architecture | Monthly Cost | vs Current |
|--------------|--------------|------------|
| g6.xlarge Spot (current) | **$252** | baseline |
| g6.xlarge On-Demand | $576 | +128% |
| SageMaker + Local | **$1,548+** | **+514%** |

**SageMaker is 6x more expensive than the current approach.**

### Why SageMaker Costs More

1. **No Spot pricing** for real-time inference (Spot only for training)
2. **Two separate endpoints** = 2x compute cost
3. **Managed service premium** - you pay for orchestration
4. **Always-on billing** - endpoints charge even when idle
5. **Data transfer** - additional costs for cross-region traffic

### When SageMaker Makes Sense

| Use Case | Relevant? |
|----------|-----------|
| Enterprise compliance (SOC2, HIPAA) | Academic project |
| Auto-scaling for variable load | Consistent load expected |
| Multi-tenant SaaS | Single deployment |
| Team already on SageMaker | New project |
| Need A/B testing models | Fixed model architecture |

**For this B.Tech project: SageMaker adds cost without benefits.**

---

## 2. AWS GPU Instance Alternatives

### Problem Statement
> "The g6.xlarge requires quota verification. Can I get an AWS instance that can host the dual 14+4 B parameter models comfortably without applying for quota?"

### VRAM Requirements
```
Qwen3-4B Q4_K_M:  ~2.5GB model + ~1GB KV cache  = ~4GB
Qwen3-14B Q4_K_M: ~8.5GB model + ~1.5GB KV cache = ~10GB
────────────────────────────────────────────────────────
Total needed: ~14GB VRAM (with some headroom: 16GB minimum)
```

### AWS GPU Instance Comparison

| Instance | GPU | VRAM | On-Demand | Spot | Default Quota | Fits Models? |
|----------|-----|------|-----------|------|---------------|--------------|
| **g4dn.xlarge** | T4 | **16GB** | $0.526/hr | ~$0.16/hr | Usually 4-8 vCPUs | Tight (14/16GB) |
| **g4dn.2xlarge** | T4 | **16GB** | $0.752/hr | ~$0.23/hr | Usually available | Tight (14/16GB) |
| **g5.xlarge** | A10G | **24GB** | $1.006/hr | ~$0.30/hr | Often needs quota | Comfortable |
| **g6.xlarge** | L4 | **24GB** | $0.805/hr | ~$0.35/hr | Needs quota | Comfortable |
| **p3.2xlarge** | V100 | **16GB** | $3.06/hr | ~$0.92/hr | Usually needs quota | Tight |

### Best Option: g4dn.xlarge (T4 16GB)

#### Why g4dn.xlarge?
1. **Usually has default quota** - Most accounts get 4-8 vCPUs for g4dn
2. **Cheapest GPU option** - $0.526/hr on-demand, ~$0.16/hr Spot
3. **16GB VRAM** - Tight but feasible for 14GB workload
4. **Widely available** - High Spot capacity, rarely interrupted

#### VRAM Fit Analysis
```
T4 16GB VRAM Budget:
├── Qwen3-4B Q4_K_M:     2.5GB
├── Qwen3-4B KV Cache:   1.0GB (8K context)
├── Qwen3-14B Q4_K_M:    8.5GB
├── Qwen3-14B KV Cache:  1.5GB (4K context)
├── CUDA overhead:       0.5GB
└── ────────────────────────────
    Total:              14.0GB / 16GB = 87.5% utilization

    Headroom: 2GB (acceptable)
```

#### Risk Mitigation
- Reduce context window if OOM: 4K for both models = saves ~1GB
- Use `--n-gpu-layers` to offload some layers to CPU if needed
- Monitor with `nvidia-smi` during testing

### Cost Comparison

| Instance | Spot/hr | Monthly (24/7) | vs g6.xlarge |
|----------|---------|----------------|--------------|
| **g4dn.xlarge** | **$0.16** | **~$115** | **-54%** |
| g4dn.2xlarge | $0.23 | ~$166 | -34% |
| g5.xlarge | $0.30 | ~$216 | -14% |
| g6.xlarge | $0.35 | ~$252 | baseline |

**g4dn.xlarge Spot is actually CHEAPER than g6.xlarge!**

### g4dn.xlarge Configuration

#### llama-swap.yaml Changes
```yaml
# Optimized for T4 16GB (tighter VRAM budget)
models:
  fast-agent:
    model: /models/qwen3-4b-q4_k_m.gguf
    port: 8081
    args:
      - --ctx-size 4096      # Reduced from 8192
      - --n-gpu-layers 99
      - --flash-attn
    ttl: -1  # Always loaded

  reasoning-agent:
    model: /models/qwen3-14b-q4_k_m.gguf
    port: 8082
    args:
      - --ctx-size 2048      # Reduced from 4096
      - --n-gpu-layers 99
      - --flash-attn
    ttl: -1  # Always loaded
```

#### Key Optimizations for T4
1. **Reduce context windows**: 4K + 2K instead of 8K + 4K
2. **Enable flash attention**: `--flash-attn` (reduces memory)
3. **Use FP16 KV cache**: Default in llama.cpp

### Checking Your Quota

Run this to check your current g4dn quota:
```bash
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-DB2E81BA \
  --region us-east-1
```

Or check in AWS Console:
1. Go to **Service Quotas** → **EC2**
2. Search for "Running On-Demand G and VT instances"
3. Look for current value (usually 4-8 vCPUs default)

g4dn.xlarge needs **4 vCPUs**, so if your quota is ≥4, you're good!

### Critical Finding
**ALL G-family instances (g4dn, g5, g6) require "On-Demand G and VT" quota approval.**

This led to exploring alternative providers (Jarvis Labs).

---

## 3. Jarvis Labs GPU Cloud

### Why Consider Jarvis Labs?
All AWS G-family instances (g4dn, g5, g6) require "On-Demand G and VT" quota approval, which can take days to weeks.

### Jarvis Labs GPU Options

| GPU | VRAM | Price/hr | Fits Models? | Notes |
|-----|------|----------|--------------|-------|
| RTX5000 | 16GB | **$0.39** | Tight | Cheapest, same as T4 |
| **A5000** | **24GB** | **$0.49** | **Perfect** | Best value for 24GB |
| A6000 | 48GB | $0.79 | Overkill | Double the VRAM needed |
| RTX6000 Ada | 48GB | $0.99 | Overkill | Latest gen |
| A100 | 40GB | $1.29 | Overkill | Data center GPU |

**Best Option: A5000 (24GB) at $0.49/hr**

### Cost Comparison

| Provider | GPU | VRAM | Hourly | Monthly (24/7) |
|----------|-----|------|--------|----------------|
| **Jarvis Labs A5000** | A5000 | 24GB | **$0.49** | **~$353** |
| Jarvis Labs RTX5000 | RTX5000 | 16GB | $0.39 | ~$281 |
| AWS g6.xlarge (if available) | L4 | 24GB | $0.35 | ~$252 |
| AWS g4dn.xlarge (if available) | T4 | 16GB | $0.16 | ~$115 |

### How Jarvis Labs Works

#### Access Options
1. **VM Mode**: Full SSH access, can run Docker
2. **Template Mode**: JupyterLab (no Docker)

**For Constitutional AIOps: Use VM Mode** (need Docker for the full stack)

#### Security
- Tier 3/4 data centers (India, Finland)
- SSH key authentication
- Stripe for payments
- Full root access on VMs

#### How to Deploy
1. Sign up at jarvislabs.ai
2. Add credits (wallet-based, no subscription)
3. Launch A5000 VM (24GB)
4. SSH in and run: `git clone ... && ./scripts/install.sh --gpu`

### Jarvis Labs vs AWS

| Factor | Jarvis Labs A5000 | AWS g6.xlarge |
|--------|-------------------|---------------|
| VRAM | 24GB | 24GB |
| Cost/hr | $0.49 | $0.35 (Spot) |
| Monthly | ~$353 | ~$252 |
| Quota needed | **No** | Yes |
| Docker support | (VM mode) | |
| SSH access | | |
| Data center | India/Finland | Worldwide |
| Billing | Per-minute | Per-second |

### Recommendation

#### If you need GPU TODAY (no quota wait):
```
Provider: Jarvis Labs
Instance: A5000 24GB VM
Cost: $0.49/hr (~$353/month if 24/7)
Status: No quota needed, instant access
```

#### For long-term (apply for AWS quota):
```
Provider: AWS
Instance: g6.xlarge or g4dn.xlarge
Cost: $0.16-0.35/hr Spot
Status: Apply for quota, use Jarvis Labs while waiting
```

---

## 4. Hybrid Architecture (Local Dev + Remote GPU)

### Question
> "Can we run everything locally and only use the remote GPU endpoint for LLMs? Can I debug and view everything at localhost?"

### Answer: YES, This WILL Work!

The `model_router.py` uses standard HTTP calls via `httpx.AsyncClient`:
```python
self._fast_client = httpx.AsyncClient(base_url=self.fast_agent_url)
self._reasoning_client = httpx.AsyncClient(base_url=self.reasoning_agent_url)
```

URLs are configurable via environment variables - can point anywhere!

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   YOUR LOCAL MACHINE                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Frontend   │  │   Backend   │  │   Neo4j     │              │
│  │ :3000       │  │  :8000      │  │  :7474      │              │
│  │ View here!  │  │  API here!  │  │  Graph DB   │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
│                          │                                       │
│  ┌─────────────┐  ┌──────┴──────┐  ┌─────────────┐              │
│  │  Grafana    │  │ SSH Tunnel  │  │  Loki       │              │
│  │  :3001      │  │ :8081/:8082 │  │  :3100      │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
└──────────────────────────┼──────────────────────────────────────┘
                           │ SSH Tunnel (encrypted)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               JARVIS LABS GPU (A5000 24GB)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              llama-swap                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────────┐          │    │
│  │  │ Qwen3-4B :8081  │  │ Qwen3-14B :8082     │          │    │
│  │  │ (~4GB VRAM)     │  │ (~11GB VRAM)        │          │    │
│  │  └─────────────────┘  └─────────────────────┘          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### What Runs Where

| Component | Location | Port | Can Debug? |
|-----------|----------|------|------------|
| Frontend (React) | **LOCAL** | 3000 | Yes! |
| Backend (FastAPI) | **LOCAL** | 8000 | Yes! |
| Neo4j | **LOCAL** | 7474 | Yes! |
| Grafana | **LOCAL** | 3001 | Yes! |
| Loki/Prometheus | **LOCAL** | 3100/9090 | Yes! |
| LLM (Qwen3-4B) | **REMOTE** | 8081 | Via logs |
| LLM (Qwen3-14B) | **REMOTE** | 8082 | Via logs |

**Everything except LLMs runs on your local machine!**

### Setup Steps

#### 1. On Jarvis Labs (GPU only)
```bash
# SSH into Jarvis Labs VM
ssh user@jarvis-ip

# Install llama-swap and models only
docker run -d --gpus all \
  -v ./models:/models \
  -p 8081:8081 -p 8082:8082 \
  ghcr.io/mostlygeek/llama-swap:latest \
  --config /config.yaml
```

#### 2. On Local Machine (everything else)
```bash
# SSH tunnel to forward LLM ports
ssh -L 8081:localhost:8081 -L 8082:localhost:8082 user@jarvis-ip

# In another terminal, run local services
docker compose -f docker-compose.yml -f docker/docker-compose.local-hybrid.yml up
```

#### 3. Environment Variables (Local)
```bash
# .env - points to localhost (tunneled to Jarvis)
FAST_AGENT_URL=http://localhost:8081/v1
REASONING_AGENT_URL=http://localhost:8082/v1
```

### Benefits of Hybrid Approach

| Benefit | Description |
|---------|-------------|
| **Local debugging** | Frontend, backend, DB all on localhost |
| **Browser DevTools** | Full React debugging at localhost:3000 |
| **Fast iteration** | Change code, refresh - no deployment |
| **Secure** | SSH tunnel encrypts LLM traffic |
| **Cost effective** | Only pay for GPU when needed |

### Security: SSH Tunnel (Recommended)

Instead of exposing LLM ports to internet:
```bash
# This forwards local ports through SSH (secure + encrypted)
ssh -L 8081:localhost:8081 -L 8082:localhost:8082 user@jarvis-ip
```

Now your backend connects to `localhost:8081` but traffic goes securely to Jarvis Labs.

---

## 5. Final Recommendations

### Summary Table

| Option | Monthly Cost | Quota Needed | Debug Local | Best For |
|--------|--------------|--------------|-------------|----------|
| g6.xlarge Spot | $252 | Yes | No | Production (after quota) |
| g4dn.xlarge Spot | $115 | Yes | No | Budget production |
| SageMaker | $1,548+ | No | Yes | Enterprise (not recommended) |
| Jarvis Labs A5000 | $353 | **No** | With hybrid | Immediate access |
| Hybrid (Local + Jarvis) | $353 | **No** | **Yes** | Development |

### Recommended Approach

1. **For Development (NOW)**:
   - Use **Hybrid Architecture** with Jarvis Labs A5000
   - Everything runs locally except LLMs
   - Full debugging at localhost:3000
   - Cost: ~$0.49/hr when developing

2. **For Production (After Quota)**:
   - Apply for AWS "On-Demand G and VT" quota
   - Use g6.xlarge Spot instance
   - Cost: ~$252/month

3. **Development Workflow**:
   - Daily dev: Local with mock LLM server (free)
   - Integration testing: Start Jarvis Labs for a few hours
   - Demo/presentation: Jarvis Labs (~$4/day for 8 hours)
   - Production: AWS g6.xlarge Spot 24/7

---

## Code Reference: model_router.py

The hybrid architecture works because of this configurable design in [model_router.py](../src/agents/model_router.py):

```python
class ModelRouter:
    def __init__(
        self,
        fast_agent_url: Optional[str] = None,
        reasoning_agent_url: Optional[str] = None,
    ):
        self.fast_agent_url = fast_agent_url or config.llm.fast_agent_url
        self.reasoning_agent_url = reasoning_agent_url or config.llm.reasoning_agent_url

        # Create separate HTTP clients for each endpoint
        self._fast_client = httpx.AsyncClient(
            base_url=self.fast_agent_url,
            timeout=config.llm.fast_agent_timeout,
        )
        self._reasoning_client = httpx.AsyncClient(
            base_url=self.reasoning_agent_url,
            timeout=config.llm.reasoning_agent_timeout,
        )
```

The URLs are standard HTTP endpoints - they can point to localhost (with SSH tunnel) or any remote server.

---

## Sources & References

- [Jarvis Labs Pricing](https://jarvislabs.ai/pricing)
- [Jarvis Labs Docs - VM](https://docs.jarvislabs.ai/vm/)
- [Jarvis Labs FAQs](https://docs.jarvislabs.ai/faqs/)
- [AWS EC2 GPU Instances](https://aws.amazon.com/ec2/instance-types/)
- [AWS Service Quotas](https://console.aws.amazon.com/servicequotas/)
- [SageMaker Pricing](https://aws.amazon.com/sagemaker/pricing/)

---

*Document generated from Constitutional AIOps development discussions, December 2025*
