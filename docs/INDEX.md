# Constitutional AIOps - Documentation Index

> **Version**: 1.0.0
> **Last Updated**: 2026-09-07
> **Status**: Production (hosted demo live; self-host packaging ready)
> **Source of truth for metrics**: [KEY_METRICS.md](KEY_METRICS.md) (COMSYS 2026 camera-ready final)
> **Source of truth for the API**: the generated [openapi/openapi.json](../openapi/openapi.json) (127 paths). Hand-written docs below describe structure; the live tree and the OpenAPI snapshot are authoritative for exhaustive detail.

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [README](../README.md) | Quick start |
| [CHANGELOG](CHANGELOG.md) | Version history |
| [ISSUES](ISSUES.md) | Issue tracker |
| [KEY_METRICS](KEY_METRICS.md) | Camera-ready benchmark results |

---

## Documentation Map

### Core references
| File | Description |
|------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, dual-agent design, graph-episodic memory, deployment topology |
| [BACKEND.md](BACKEND.md) | Python backend module reference |
| [API.md](API.md) | REST API overview (defers to `openapi/openapi.json` for the full contract) |
| [FRONTEND.md](FRONTEND.md) | React frontend reference |
| [KEY_METRICS.md](KEY_METRICS.md) | Performance and accuracy metrics (camera-ready final) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment overview |

### Development and progress
| File | Description |
|------|-------------|
| [CHECKLIST.md](CHECKLIST.md) | Development progress tracker |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [ISSUES.md](ISSUES.md) | Active issues and blockers |
| [SESSION_STATE.md](SESSION_STATE.md) | Current state snapshot |
| [DOCUMENTATION_SCHEMA.md](DOCUMENTATION_SCHEMA.md) | Documentation update guidelines |

### Deployment guides
| File | Description |
|------|-------------|
| [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) | AWS deployment guide (GPU tier) |
| [JARVIS_LABS_DEPLOYMENT.md](JARVIS_LABS_DEPLOYMENT.md) | Historical Jarvis Labs hybrid setup (v1 dev hardware) |

---

## Codebase structure (directory-level)

The exhaustive file list churns quickly; the live tree is authoritative. This is the current shape.

### Backend (`src/`) - 113 Python files, 21 registered API routers

| Module | Purpose |
|--------|---------|
| `main.py`, `config.py`, `version.py` | App entry, environment config, version |
| `agents/` | Dual-model routing, fast annotator (Qwen3-4B), reasoning agent (Qwen3-14B) |
| `api/routes/` | 21 routers (see below) + schemas |
| `alerting/` | Outbound + inbound ChatOps (Telegram, Matrix), relay HMAC, webhook auto-register |
| `auth/` | Session auth, scrypt hashing, crypto (Fernet at rest), PAT, BYOK key store |
| `benchmark/` | Benchmark runner + evaluator (BERTScore, matched-substring accuracy) |
| `confidence/` | Composite confidence C(a) = alpha*C_LLM + beta*C_hist + gamma*C_sim |
| `constitutional/` | 12 principles across 3 tiers, validator, authorization matrix |
| `cost/` | Per-user cost fencing for LLM/insight calls |
| `insights` (route + `lib`) | Opt-in reasoning-tier Explain widgets and incident copilot |
| `mcp/` | Model Context Protocol tool server |
| `memory/` | Neo4j client, episode store, 384-dim embeddings, RAG retrieval |
| `notifications/` | In-app notification store and feed |
| `onboarding/` | First-run setup wizard state |
| `orchestration/` | LangGraph StateGraph agent coordination |
| `persistence/` | Durable conversation/incident storage (SQLite fallback) |
| `remediation/` | Consent-gated action proposals + executors (fail-closed) |
| `telemetry/` | LGTM collectors (Loki/Prometheus/Tempo), background processor, compression |
| `tools/` | Action tools (restart/scale) behind the kill-switch + whitelist |
| `topology/` | Service topology schema + live sync |
| `validation/` | Shared validation constants |
| `utils/` | Logging, audit trail, WebSocket manager |

**API routers** (`src/api/routes/`, prefixes under `/api/v1`): actions, agents, audit, auth, benchmark, chat, demo, graph, graph_topology, health, incidents, infrastructure, insights, metrics, notifications, prompts, relay, settings, telemetry, tools, topology.

### Frontend (`frontend/src/`) - 144 TS/TSX files, 21 pages

**Pages** (`pages/`): Dashboard, Console (Command Center), Chat, LocalChat, Incidents, Graph, Metrics, Telemetry, Infrastructure, Agents, Benchmark, Mcp, Audit, Notifications, Settings, Setup, Signup, Login, Docs, Privacy, Terms.

**Components** (`components/`): top-level shell + feature components (Layout, EpisodicGraphExplorer, IncidentTimeline, DependencyGraph, GraphCopilot, IncidentNarrative, ApprovalTicker, BlastRadiusPreview, LearnedRunbook, CommandPalette, account/setup/captcha widgets, and more), plus subfolders `chat/`, `console/`, `episodic/`, `incidents/`, `mcp/`, `schema/`, `ui/`, `viz/`. Client + libs under `lib/` (type-safe API client, WebSocket client, insight payload builders).

### Marketing site (`marketing/`)
A separate always-on static site (Vite build) served VM-independently via CloudFront; the app front is a distinct CloudFront distribution with a wake-on-visit Lambda. Not part of the backend/frontend app.

### Docker, scripts, tests
`docker/` compose variants (local / gpu / production / mode2) + Dockerfiles; `scripts/` operational tooling (incl. `dump_openapi.py`, `relay_drain.py`, `seed_benchmark_data.py`); `tests/` backend pytest suites (1089 passing) and `frontend/e2e/` Playwright suites (gated in CI).

---

## Current architecture summary

| Component | Technology | Notes |
|-----------|------------|-------|
| Fast Agent | Qwen3-4B | Telemetry annotation and classification |
| Reasoning Agent | Qwen3-14B | RCA, remediation planning, chat |
| LLM runtime | vLLM AWQ-marlin (production) / Ollama (local) | OpenAI-compatible; BYO endpoint supported |
| Primary hardware | AWS g6.xlarge L4 24GB (GPU tier) | v1 dev used Jarvis Labs A5000 24GB |
| Lite tier | CPU box + external (Bedrock) endpoint | wake-on-visit, no fixed IP |
| Graph memory | Neo4j 5.x | Incident correlation, episodic memory |
| Backend | FastAPI (Python 3.11+) | 21 routers |
| Frontend | React 18 + TypeScript + Tailwind | Command Center cockpit |
| Observability | LGTM (Loki, Grafana, Tempo, Prometheus) + OTel | |

---

## Update protocol

1. Edit the file with new content.
2. Update its header "Last Updated" date.
3. Update the relevant entry in this INDEX.
4. Add a CHANGELOG entry if the change is significant.

See [DOCUMENTATION_SCHEMA.md](DOCUMENTATION_SCHEMA.md) for detailed guidelines.

---

**Last Updated**: 2026-09-07
