# Session State - Production Snapshot

> **Last Updated**: 2026-09-07
> **Purpose**: Current-state snapshot for context recovery. Historical session-by-session
> detail lives in `docs/CHANGELOG.md`.

---

## Current Status: PRODUCTION, two deployment tiers

The app runs as a gated production deployment. There are now two tiers:

- **GPU tier**: a single AWS L4 GPU VM (frozen/thawed on demand for cost control) running dual vLLM AWQ-marlin engines, fronted by Caddy with TLS on a dedicated domain.
- **Lite tier**: a low-cost CPU box with no fixed IP, targeting an external OpenAI-compatible endpoint (AWS Bedrock), reached through a wake-on-visit Lambda behind CloudFront. The marketing site is a separate always-on static origin so it renders VM-independently.

The app's own **session login is the production gate** (`AUTH_REQUIRED=true`; 401s without a session). Caddy basic-auth remains only on `/grafana`, and `/ingest/*` keeps its machine credential. Public signup is enabled on the hosted demo behind a Cloudflare Turnstile captcha.

| Layer | Reality |
|-------|---------|
| Serving (Mode 1, default) | Dual vLLM AWQ-marlin: Qwen3-4B (fast, :8000) + Qwen3-14B (reasoning, :8001) |
| Serving (Mode 2, opt-in) | Single-engine overlay via `AIOPS_MODE=2` + `docker/docker-compose.mode2.yml`; swappable from Settings (host watcher) |
| Multi-tenant / BYOK | Per-user bring-your-own API key store (Fernet at rest), cost fencing, WebLLM in-browser `/local-chat` fallback |
| Backend | FastAPI, LangGraph orchestration (mandatory), constitutional validator on every action, 21 routers |
| Persistence | SQLite WAL (conversations/incidents/pending actions) + Neo4j + LGTM, all on a persistent data volume |
| Frontend | React 18 + TS + Vite, Command Center cockpit, lazy routes, accessible primitives, Playwright e2e gated in CI |
| Edge monitoring | Grafana Alloy agent on remote hosts to an authenticated `/ingest/*` gateway |
| ChatOps alerting | Outbound Telegram + Matrix (admin-gated, Fernet); inbound Telegram relay via API Gateway to a relay Lambda to SQS to the box drain |

---

## Feature state (2026-09-07)

- **Chat tool-calling**: real MCP tool execution with ordered `tool_calls` metadata and a reasoning-timeline UI; investigation keyword bundle; non-answer guards; evidence-based confidence. The agentic tool loop is enabled in production by operator choice, decode-capped, with a chat-priority interlock deferring background RCA during a user turn.
- **Chat-driven remediation (consent model)**: action tools (`restart_service`, `scale_service`) never execute inside the model loop. They queue as proposed actions with an Approve/Reject card; approval executes through the constitutional gate; decisions persist onto conversation history. Settings controls the mode (`diagnose` / `approve` / `auto`) and the per-tool autonomy allowlist.
- **Action-tool gating (fail-closed)**: `AIOPS_ENABLE_ACTION_TOOLS` kill-switch, then container whitelist, then constitutional validation (>0.90 automatic / 0.70-0.90 approval / <0.70 alert-only); every attempt audited. The same gate is enforced on the REST and programmatic paths, including plugin action tools via the shared validator (gate generalization).
- **LLM insight widgets (opt-in, cost-fenced)**: reasoning-tier Explain widgets across the Dashboard, an incident narrative, a graph copilot, and an incident RCA copilot, all behind an AI-widgets preference and the per-user cost fence, degrading gracefully.
- **Onboarding + service-aware UI**: first-run setup wizard, service topology schema with live sync.
- **Extensibility**: Python SDK + a fail-closed plugin loader (`AIOPS_ENABLE_PLUGINS`), PATs, and outbound webhooks (SSRF-guarded, HMAC-signed).
- **Episodic memory UX**: Episode Browser, causal-tree layouts, full-screen `/graph` with filters and a fill-parent canvas, glass inspector drawer.
- **Mode 2 program**: Phases 0-1 validated live. Later phases (engine pin upgrade, prefix caching, streaming UI wiring, guided JSON) are code-complete or planned. See CHANGELOG and ISSUES ISS-101.

---

## Gates (last verified 2026-09-07)

| Gate | Result |
|------|--------|
| Backend pytest | 1089 passed / 25 skipped / 0 failed, coverage 65.14% |
| OpenAPI snapshot | 127 paths (`scripts/dump_openapi.py --check`) |
| App frontend | vitest 210, build clean, lint 6 baseline warnings / 0 new |
| Marketing | build clean, vitest 10 |
| Playwright e2e (CI, route-mocked) | console 9 / schema 5 / graph-update 16 / setup 2 |

---

## Key design decisions (standing)

- Dual-model simultaneous serving is the paper architecture; **Mode 1 stays frozen** as the reference. Mode 2 is an additive overlay; Mode 1 must remain byte-identical when Mode 2 is off.
- LangGraph orchestration is mandatory (no fallback).
- Constitutional validation wraps every action-class operation; human approval satisfies Tier-1 authorization but Tier-1 safety principles themselves are never overridable.
- Action tools are disabled unless explicitly enabled by environment; the container whitelist is the authority on what may be touched.
- Local dev (no GPU) uses mock / Ollama endpoints; production values live only in the VM's `.env.production` (never committed).
