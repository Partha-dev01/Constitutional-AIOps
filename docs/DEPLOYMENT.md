# Constitutional AIOps - Deployment Guide

> **Version**: 0.4.0
> **Last Updated**: 2025-12-30
> **Status**: Production Ready

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Deployment Options](#2-deployment-options)
3. [Jarvis Labs Hybrid (Recommended)](#3-jarvis-labs-hybrid-recommended)
4. [Local Development](#4-local-development)
5. [AWS Deployment](#5-aws-deployment)
6. [Configuration Reference](#6-configuration-reference)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24+ | With Docker Compose v2 |
| RAM | 8GB+ | For local services |
| Disk | 20GB | For containers and logs |

### 10-Minute Setup (Jarvis Labs Hybrid)

```bash
# 1. Clone repository
git clone https://github.com/Partha-dev01/Aiops_Final.git
cd constitutional-aiops

# 2. Start services (connects to Jarvis Labs for LLM)
docker compose up -d

# 3. Access the application
open http://localhost:3000       # Dashboard
open http://localhost:8000/docs  # API docs
open http://localhost:3001       # Grafana
```

---

## 2. Deployment Options

| Option | LLM Location | GPU Required | Cost | Best For |
|--------|--------------|--------------|------|----------|
| **Jarvis Labs Hybrid** | Cloud (A5000 24GB) | No (local) | $0.49/hr | **Recommended** |
| Local Development | Mock server | No | Free | Development |
| AWS g6.xlarge | Self-hosted | Yes (L4 24GB) | $0.35/hr | Self-contained |

### Architecture Comparison

```
JARVIS LABS HYBRID (Recommended):
├── Local: Frontend, Backend, Neo4j, LGTM stack
└── Cloud: Ollama with Qwen3-4B + Qwen3-14B (both always loaded)

LOCAL DEVELOPMENT:
├── Local: All services
└── LLM: Mock server (returns canned responses)

AWS SELF-CONTAINED:
└── All on g6.xlarge: Services + Ollama + Models
```

---

## 3. Jarvis Labs Hybrid (Recommended)

### 3.1 Why Jarvis Labs?

| Feature | Benefit |
|---------|---------|
| A5000 24GB GPU | Both models fit simultaneously |
| $0.49/hour | Cost-effective for development |
| Ollama pre-installed | No setup required |
| HTTPS API | Secure remote access |
| Pause/Resume | Only pay when using |

### 3.2 Jarvis Labs Setup

1. **Create Account**: [jarvislabs.ai](https://jarvislabs.ai)
2. **Launch Instance**:
   - Template: **Ollama**
   - GPU: **A5000 24GB** or higher
   - Storage: 50GB+
3. **Pull Models** (via Jarvis Labs terminal):
   ```bash
   ollama pull qwen3:4b
   ollama pull qwen3:14b
   ```
4. **Get Endpoint URL**: `https://[instance-id].notebooks.jarvislabs.net`

### 3.3 Local Configuration

Update `docker-compose.yml` or create `.env`:

```bash
# .env file
# The *_URL points at the OpenAI-compatible base (…/v1). A trailing slash is
# optional — it is normalized internally either way. Works with vLLM, Ollama,
# and hosted OpenAI-compatible endpoints such as AWS Bedrock's /openai/v1.
FAST_AGENT_URL=https://[your-instance].notebooks.jarvislabs.net/v1
REASONING_AGENT_URL=https://[your-instance].notebooks.jarvislabs.net/v1
FAST_AGENT_MODEL=qwen3:4b
REASONING_AGENT_MODEL=qwen3:14b
# Optional: bearer token for a secured bring-your-own endpoint. Leave unset for
# an unauthenticated local endpoint (behaviour unchanged). A single LLM_API_KEY
# covers both agents; FAST_AGENT_API_KEY / REASONING_AGENT_API_KEY override it
# per agent. A minimal one-endpoint self-host can point both *_URL/*_MODEL at the
# same value and set one LLM_API_KEY.
# LLM_API_KEY=sk-...
```

### 3.4 Start Services

```bash
# Start all local services
docker compose up -d

# Verify health
curl http://localhost:8000/api/v1/health
```

### 3.5 Verify LLM Connectivity

```bash
# Check models available on Jarvis Labs
curl https://[your-instance].notebooks.jarvislabs.net/api/tags

# Should show:
# {"models":[{"name":"qwen3:4b",...},{"name":"qwen3:14b",...}]}
```

---

## 4. Local Development

### 4.1 No GPU Mode (Mock LLM)

For development without GPU access:

```bash
# Start with mock LLM server
docker compose -f docker-compose.yml -f docker/docker-compose.local.yml up -d
```

The mock server returns canned responses for testing UI/API flow.

### 4.2 Development Workflow

```bash
# Backend hot-reload
cd src && uvicorn main:app --reload --port 8000

# Frontend hot-reload (new terminal)
cd frontend && npm run dev
```

### 4.3 Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Linting
black src/ --check
isort src/ --check
```

---

## 5. AWS Deployment

### 5.1 Instance Requirements

| Setting | Value |
|---------|-------|
| Instance Type | **g6.xlarge** |
| GPU | NVIDIA L4 24GB |
| vCPU | 4 |
| RAM | 16GB |
| Storage | 100GB gp3 |
| Pricing | ~$0.35/hr (Spot) |

### 5.2 Quick AWS Setup

```bash
# 1. Launch g6.xlarge with Deep Learning AMI
# 2. SSH into instance
ssh -i your-key.pem ubuntu@<instance-ip>

# 3. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 4. Pull models
ollama pull qwen3:4b
ollama pull qwen3:14b

# 5. Clone and start
git clone https://github.com/Partha-dev01/Aiops_Final.git
cd constitutional-aiops
docker compose up -d
```

### 5.3 Security Groups

| Port | Service | Access |
|------|---------|--------|
| 22 | SSH | Your IP |
| 3000 | Frontend | 0.0.0.0/0 |
| 8000 | Backend API | 0.0.0.0/0 |
| 3001 | Grafana | 0.0.0.0/0 |
| 7474 | Neo4j Browser | Your IP |

---

## 6. Configuration Reference

### 6.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_AGENT_URL` | `http://localhost:8081/v1` | Fast agent Ollama endpoint |
| `REASONING_AGENT_URL` | `http://localhost:8082/v1` | Reasoning agent endpoint |
| `FAST_AGENT_MODEL` | `qwen3:4b` | Fast agent model name |
| `REASONING_AGENT_MODEL` | `qwen3:14b` | Reasoning agent model |
| `LLM_API_KEY` | _(unset)_ | Shared bearer token for a secured BYO endpoint; applies to both agents. Empty = no `Authorization` header sent |
| `FAST_AGENT_API_KEY` | _(falls back to `LLM_API_KEY`)_ | Per-agent bearer token override for the fast endpoint |
| `REASONING_AGENT_API_KEY` | _(falls back to `LLM_API_KEY`)_ | Per-agent bearer token override for the reasoning endpoint |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_PASSWORD` | `constitutional_aiops_2025` | Neo4j password |
| `LOKI_URL` | `http://localhost:3100` | Loki log endpoint |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus endpoint |
| `CONFIDENCE_THRESHOLD_AUTO` | `0.90` | Auto-approve threshold |
| `CONFIDENCE_THRESHOLD_APPROVAL` | `0.70` | Require approval threshold |

#### Public self-service signup (hosted demo only)

Off by default — a self-host deployment keeps user creation admin-only. Turn it
on ONLY on the hosted demo instance. The abuse controls (captcha, email
verification) are all optional and configured by env; with none set, signup
still enforces the password policy and a per-IP rate limit.

| Variable | Default | Description |
|----------|---------|-------------|
| `AIOPS_ENABLE_PUBLIC_SIGNUP` | `false` | Master flag. When true, `POST /api/v1/auth/signup` creates `role=user` accounts and the SPA shows a "Create an account" link. Leave false for self-host |
| `SIGNUP_CAPTCHA_PROVIDER` | _(unset)_ | `turnstile` or `hcaptcha`; unset disables captcha. When set, signups are rejected unless the token passes server-side siteverify |
| `SIGNUP_CAPTCHA_SITE_KEY` | _(unset)_ | Public site key rendered by the SPA widget |
| `SIGNUP_CAPTCHA_SECRET` | _(unset)_ | Server secret for siteverify. If a provider is set but this is empty, signup fails closed |
| `SIGNUP_SMTP_HOST` / `SIGNUP_SMTP_PORT` | _(unset)_ / `587` | SMTP relay for the verification email (e.g. the Amazon SES SMTP endpoint `email-smtp.<region>.amazonaws.com`). Unset = the link is logged, not mailed (account still works) |
| `SIGNUP_SMTP_USER` / `SIGNUP_SMTP_PASSWORD` | _(unset)_ | SMTP credentials (SES SMTP username/password) |
| `SIGNUP_EMAIL_FROM` | `no-reply@localhost` | From address on the verification email |
| `PUBLIC_BASE_URL` | _(unset)_ | Base URL used to build the verification link (e.g. `https://aiops-node.example.com`) |

New accounts are usable immediately (the shared demo has no per-tenant data);
email verification is a soft confirmation that flips an `email_verified` flag
when the link is opened, so it does not depend on the box being awake when the
user clicks it later.

### 6.2 Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main configuration (uses Jarvis Labs by default) |
| `docker/docker-compose.local.yml` | Override for local dev (mock LLM) |
| `docker/docker-compose.gpu.yml` | Override for self-hosted GPU |

### 6.3 Service Ports

| Port | Service |
|------|---------|
| 3000 | Frontend (nginx) |
| 3001 | Grafana |
| 3100 | Loki |
| 3200 | Tempo |
| 4317 | OTEL gRPC |
| 4318 | OTEL HTTP |
| 7474 | Neo4j Browser |
| 7687 | Neo4j Bolt |
| 8000 | Backend API |
| 9090 | Prometheus |

---

## 7. Troubleshooting

### 7.1 Common Issues

#### LLM Connection Failed
```bash
# Check Jarvis Labs endpoint
curl -s https://[instance].notebooks.jarvislabs.net/api/tags

# If fails, verify:
# 1. Jarvis Labs instance is running
# 2. URL is correct in .env or docker-compose.yml
# 3. Models are pulled (qwen3:4b, qwen3:14b)
```

#### Backend Health Degraded
```bash
# Check component status
curl http://localhost:8000/api/v1/health | jq

# Common causes:
# - Neo4j not ready (wait 30s after startup)
# - LLM endpoint unreachable
```

#### Frontend Shows "Offline"
```bash
# Verify API is accessible
curl http://localhost:8000/api/v1/health

# Check nginx logs
docker logs aiops-frontend
```

#### Neo4j Connection Failed
```bash
# Check Neo4j is running
docker logs aiops-neo4j

# Verify credentials
# Default: neo4j / constitutional_aiops_2025
```

### 7.2 Logs

```bash
# All services
docker compose logs -f

# Specific service
docker logs -f aiops-backend
docker logs -f aiops-frontend
docker logs -f aiops-neo4j
```

### 7.3 Reset Everything

```bash
# Stop and remove all containers + volumes
docker compose down -v

# Fresh start
docker compose up -d
```

---

## Quick Commands Reference

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose build --no-cache && docker compose up -d

# Check health
curl http://localhost:8000/api/v1/health

# Access points
# Dashboard:  http://localhost:3000
# API Docs:   http://localhost:8000/docs
# Grafana:    http://localhost:3001
# Neo4j:      http://localhost:7474
```

---

**Last Updated**: 2025-12-27
**Version**: 0.3.1
