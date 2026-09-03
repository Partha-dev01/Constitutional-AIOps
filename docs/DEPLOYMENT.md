# Constitutional AIOps - Deployment Guide

> **Version**: 0.5.0
> **Last Updated**: 2026-09-01
> **Status**: Production deployed (AWS lite tier, TLS)

---

## Table of Contents

1. [Quick Start (self-host)](#1-quick-start-self-host)
2. [Deployment Options](#2-deployment-options)
3. [Bring Your Own LLM Endpoint](#3-bring-your-own-llm-endpoint)
4. [Lite Self-Host](#4-lite-self-host)
5. [Full GPU Stack (reference config)](#5-full-gpu-stack-reference-config)
6. [Local Development](#6-local-development)
7. [Configuration Reference](#7-configuration-reference)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Quick Start (self-host)

The fastest path is the **lite** profile: backend + frontend + your own
OpenAI-compatible LLM endpoint. No GPU, no bundled models, no Neo4j, no
observability stack required.

```bash
# 1. Clone
git clone https://github.com/Partha-dev01/Aiops_Final.git constitutional-aiops
cd constitutional-aiops

# 2. Configure your LLM endpoint
cp .env.example .env
#   edit .env and set FAST_AGENT_URL / REASONING_AGENT_URL / *_MODEL
#   (both agents may point at the SAME endpoint + model), plus LLM_API_KEY
#   if your endpoint needs a bearer token.

# 3. Start (self-contained — do NOT layer it on docker-compose.yml)
docker compose -f docker/docker-compose.lite.yml --env-file .env up -d

# 4. Open the app
#   Frontend  http://localhost:3000
#   Backend   http://localhost:8000/docs
```

> **`--env-file .env` is required.** Docker Compose reads the interpolation
> `.env` from the compose file's own directory (`docker/`), not the repo root,
> so a bare `-f docker/docker-compose.lite.yml` command does not auto-load your
> root `.env`. Without it the bring-your-own endpoint comes through blank and
> the backend refuses to boot (`WS_TOKEN must be set in production`, because
> `ENVIRONMENT` then falls back to its `production` default). Verified on Docker
> Compose v5.5.0.

> **Shortcut:** with `make` installed, `make lite-up` runs exactly the command
> above, and `make lite-down` / `make lite-logs` / `make lite-build` wrap the
> rest (`make help` lists them). The raw `docker compose` command stays the
> portable fallback on hosts without `make`.

That is the whole thing. The app degrades gracefully without Neo4j and the
LGTM observability stack (it falls back to an in-memory episode store and the
Graph/Metrics pages show fallback data), so this is a genuine one-command
self-host, not a crippled build.

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24+ | With Docker Compose v2 — install both in one step via https://get.docker.com |
| RAM | 2GB+ | Measured steady-state RSS is ~0.74 GiB (backend + frontend + edge) |
| Disk | 20GB | CPU-only image is ~1.3GB |
| LLM endpoint | any OpenAI-compatible | vLLM, Ollama, AWS Bedrock, OpenAI, ... (see [§3](#3-bring-your-own-llm-endpoint)) |

---

## 2. Deployment Options

| Option | LLM | GPU | Compose file | Best for |
|--------|-----|-----|--------------|----------|
| **Lite self-host** | Bring your own endpoint | No | `docker/docker-compose.lite.yml` | **Recommended** — cheap, portable, one command |
| Full GPU stack | Local vLLM dual-engine | Yes (24GB) | `docker-compose.yml` + `docker/docker-compose.{gpu,production}.yml` | The research-paper reference configuration |
| Local development | Mock server | No | `docker-compose.yml` + `docker/docker-compose.local.yml` | UI/API development without any LLM |

The lite tier is what runs the hosted AWS deployment: a small (t3/t4g.small,
2GiB) instance with the LLM offloaded to a remote endpoint, fronted by Caddy
with Let's Encrypt TLS.

---

## 3. Bring Your Own LLM Endpoint

The app talks to any **OpenAI-compatible** chat-completions endpoint. It uses
two logical agents — a *fast* annotator and a *reasoning* agent — but they may
point at the **same** URL and model for a minimal single-endpoint setup, or at
two separate endpoints for the dual-engine reference configuration.

```bash
# Point both agents at the same endpoint + model (minimal setup):
FAST_AGENT_URL=https://your-endpoint.example.com/v1
REASONING_AGENT_URL=https://your-endpoint.example.com/v1
FAST_AGENT_MODEL=your-model
REASONING_AGENT_MODEL=your-model

# Bearer token for a secured endpoint (optional; empty = no Authorization header).
# LLM_API_KEY covers both agents; the per-agent keys override it if set.
LLM_API_KEY=sk-...
# FAST_AGENT_API_KEY=...
# REASONING_AGENT_API_KEY=...
```

The `*_URL` points at the OpenAI-compatible base (`…/v1`). A trailing slash is
optional — it is normalized internally either way.

### Endpoint examples

| Provider | `*_URL` | `*_MODEL` | Notes |
|----------|---------|-----------|-------|
| **vLLM** (self-hosted) | `http://your-host:8000/v1` | the `--served-model-name` | Colon-free names auto-disable thinking |
| **Ollama** (self-hosted) | `http://your-host:11434/v1` | `qwen3:4b` etc. | Colon in the name keeps thinking on |
| **AWS Bedrock** | `https://bedrock-runtime.<region>.amazonaws.com/openai/v1` | `qwen.qwen3-32b-v1:0` etc. | Set `LLM_API_KEY` to a Bedrock API key |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` etc. | Set `LLM_API_KEY` to your OpenAI key |

You can also change all of this at runtime from **Settings → Models** in the
app — the endpoint, model names, and a write-only API key apply live without a
restart.

---

## 4. Lite Self-Host

The lite profile (`docker/docker-compose.lite.yml`) is self-contained. Use it
alone, not layered on `docker-compose.yml`.

### 4.1 Localhost (no TLS)

```bash
docker compose -f docker/docker-compose.lite.yml --env-file .env up -d
# frontend  http://localhost:3000
# backend   http://localhost:8000
```

The SPA calls the backend cross-origin at `:8000`, so `CORS_ORIGINS` defaults to
`http://localhost:3000` (already set for you).

### 4.2 Public edge (Caddy + Let's Encrypt TLS)

Enable the `edge` profile to put Caddy in front on a real domain. Frontend and
backend stay internal; only Caddy binds 80/443.

```bash
# .env must set APP_DOMAIN + ACME_EMAIL, and PUBLIC_API_URL=/api/v1 so the
# SPA bundle is same-origin under the domain.
APP_DOMAIN=aiops.example.com
ACME_EMAIL=you@example.com
PUBLIC_API_URL=/api/v1

docker compose -f docker/docker-compose.lite.yml --env-file .env --profile edge up -d
```

### 4.3 What lite includes (and what it drops)

| Component | Lite | Behaviour |
|-----------|------|-----------|
| Backend (FastAPI) | ✅ | CPU-only image (~1.3GB); embeddings/BERTScore run on CPU |
| Frontend (React/nginx) | ✅ | Static SPA |
| Caddy edge (TLS) | optional (`--profile edge`) | Let's Encrypt on `APP_DOMAIN` |
| Neo4j graph memory | ❌ | Graceful in-memory episode store with similarity search |
| LGTM observability | ❌ | Graph/Metrics pages show fallback data |
| Local GPU/models | ❌ | Bring your own endpoint (see [§3](#3-bring-your-own-llm-endpoint)) |

### 4.4 Container health on the Dashboard

The lite backend mounts the host Docker socket
(`/var/run/docker.sock`) read-only so the **Dashboard → Service Availability**
and **Infrastructure** pages show the real running containers and their health.
This does **not** enable restart/scale remediation — that is a separate opt-in
(`AIOPS_ENABLE_ACTION_TOOLS=true`, off by default). A container with the host
socket can control the daemon, so keep the box locked down.

---

## 5. Full GPU Stack (reference config)

The research-paper configuration runs both models locally on one 24GB GPU
(vLLM AWQ-marlin): Qwen3-4B (fast, port 8000) + Qwen3-14B (reasoning, port
8001), always loaded, plus Neo4j and the full LGTM observability stack.

```bash
# On a GPU host (e.g. AWS g6.xlarge L4 24GB) with the NVIDIA container toolkit:
git clone https://github.com/Partha-dev01/Aiops_Final.git constitutional-aiops
cd constitutional-aiops
cp .env.production.example .env   # set NEO4J_PASSWORD, AUTH_*, WS_TOKEN, ...
docker compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up -d
```

This is heavier (~8.8GB of memory limits across Neo4j + LGTM + services) and is
not required to run the product — the lite tier is the recommended self-host.

---

## 6. Local Development

### 6.1 No-GPU mock LLM

```bash
docker compose -f docker-compose.yml -f docker/docker-compose.local.yml up -d
```

The mock server returns canned responses for exercising the UI/API without any
real endpoint.

### 6.2 Hot-reload workflow

```bash
# Backend
cd src && uvicorn main:app --reload --port 8000
# Frontend (new terminal)
cd frontend && npm run dev
```

### 6.3 Tests + lint

```bash
pytest tests/ -v
black src/ --check && isort src/ --check
```

---

## 7. Configuration Reference

### 7.1 Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_AGENT_URL` | `http://localhost:8000/v1` | Fast-agent OpenAI-compatible base |
| `REASONING_AGENT_URL` | `http://localhost:8001/v1` | Reasoning-agent base (may equal the fast URL) |
| `FAST_AGENT_MODEL` | `qwen3-4b` | Fast-agent model name |
| `REASONING_AGENT_MODEL` | `qwen3-14b` | Reasoning-agent model name |
| `LLM_API_KEY` | _(unset)_ | Shared bearer token for a secured endpoint; applies to both agents. Empty = no `Authorization` header |
| `FAST_AGENT_API_KEY` | _(falls back to `LLM_API_KEY`)_ | Per-agent bearer override for the fast endpoint |
| `REASONING_AGENT_API_KEY` | _(falls back to `LLM_API_KEY`)_ | Per-agent bearer override for the reasoning endpoint |
| `AUTH_REQUIRED` | `false` | Gate the app behind the built-in session login. Set with `AUTH_ADMIN_USER` / `AUTH_ADMIN_PASSWORD` / `AUTH_SECRET_KEY` |
| `WS_TOKEN` | _(unset)_ | Required when `ENVIRONMENT=production`; guards the `/ws` websocket |
| `APP_DOMAIN` | _(unset)_ | Domain for the Caddy `edge` profile |
| `ACME_EMAIL` | `admin@example.com` | Let's Encrypt contact for the `edge` profile |
| `PUBLIC_API_URL` | `http://localhost:8000/api/v1` | SPA build-time API base; set to `/api/v1` for same-origin edge |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI (full stack only; lite falls back to in-memory) |
| `NEO4J_PASSWORD` | _(required in production)_ | Neo4j password (a dummy is fine on lite — no server runs) |
| `CONFIDENCE_THRESHOLD_AUTO` | `0.90` | Auto-approve threshold |
| `CONFIDENCE_THRESHOLD_APPROVAL` | `0.70` | Require-approval threshold |

#### Public self-service signup (hosted demo only)

Off by default — a self-host deployment keeps user creation admin-only. Turn it
on ONLY on a hosted demo instance. The abuse controls (captcha, email
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

### 7.2 Service ports (lite)

| Port | Service |
|------|---------|
| 3000 | Frontend (nginx) |
| 8000 | Backend API |
| 80 / 443 | Caddy edge (`--profile edge` only) |

The full GPU stack adds Neo4j (7474/7687), Grafana (3001), Loki (3100), Tempo
(3200), Prometheus (9090), and the OTEL collector (4317/4318).

---

## 8. Troubleshooting

### 8.1 Common issues

#### Agents show "offline" / LLM errors
```bash
# Verify your endpoint answers an OpenAI-compatible request:
curl -s "$FAST_AGENT_URL/models" -H "Authorization: Bearer $LLM_API_KEY"

# Then check the backend's view:
curl http://localhost:8000/api/v1/health | jq
```
Check `FAST_AGENT_URL` / `REASONING_AGENT_URL` / `*_MODEL` in `.env`, and that
`LLM_API_KEY` is set if the endpoint requires auth. You can also fix all of
these live from **Settings → Models**.

#### Dashboard "Service Availability" is empty
The lite backend needs the Docker socket mounted (it is, in
`docker-compose.lite.yml`). Confirm the mount and that the daemon is reachable:
```bash
docker exec aiops-backend python -c "import docker; print([c.name for c in docker.from_env().containers.list()])"
```

#### Frontend shows "Offline"
```bash
curl http://localhost:8000/api/v1/health
docker logs aiops-frontend
```

### 8.2 Logs

```bash
docker compose -f docker/docker-compose.lite.yml logs -f
docker logs -f aiops-backend
```

### 8.3 Reset

```bash
docker compose -f docker/docker-compose.lite.yml down -v   # removes volumes too
docker compose -f docker/docker-compose.lite.yml --env-file .env up -d
```

---

## Quick Commands Reference

```bash
# Start (lite)
docker compose -f docker/docker-compose.lite.yml --env-file .env up -d

# Start (lite + TLS edge)
docker compose -f docker/docker-compose.lite.yml --env-file .env --profile edge up -d

# Stop
docker compose -f docker/docker-compose.lite.yml down

# Rebuild after code changes
docker compose -f docker/docker-compose.lite.yml --env-file .env up -d --build

# Health
curl http://localhost:8000/api/v1/health
```

---

**Last Updated**: 2026-09-01
**Version**: 0.5.0
