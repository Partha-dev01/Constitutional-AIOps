# Session State - Production Snapshot

> **Last Updated**: 2026-07-11
> **Purpose**: Current-state snapshot for context recovery. Historical session-by-session
> detail lives in `docs/CHANGELOG.md`.

---

## Current Status: PRODUCTION (AWS), Mode 1 serving

The app runs as a gated production deployment on a single AWS L4 GPU VM (frozen/thawed
on demand for cost control), fronted by Caddy with TLS on a dedicated domain. The app's
own **session login is the production gate** (`AUTH_REQUIRED=true`; 401s without a session);
Caddy basic-auth remains only on `/grafana`, and `/ingest/*` keeps its machine credential.

| Layer | Reality |
|-------|---------|
| Serving (Mode 1, default) | Dual vLLM AWQ-marlin: Qwen3-4B (fast, :8000) + Qwen3-14B (reasoning, :8001) |
| Serving (Mode 2, opt-in) | Single-engine overlay via `AIOPS_MODE=2` + `docker/docker-compose.mode2.yml`; swappable from Settings (host watcher) |
| Backend | FastAPI, LangGraph orchestration (mandatory), constitutional validator on every action |
| Persistence | SQLite WAL (conversations/incidents/pending actions) + Neo4j + LGTM, all on a persistent data volume |
| Frontend | React 18 + TS + Vite, lazy routes, accessible primitives, live Playwright post-deploy gate |
| Edge monitoring | Grafana Alloy agent on remote hosts → authenticated `/ingest/*` gateway |

---

## Feature state (2026-07-11)

- **Chat tool-calling**: real MCP tool execution with ordered `tool_calls` metadata and a
  reasoning-timeline UI; investigation keyword bundle; non-answer guards; evidence-based confidence.
  The agentic tool loop is enabled in production by operator choice; its in-loop completion is
  decode-capped (160 tokens) and a chat-priority interlock defers background RCA while a user turn
  is in flight — typical turns run ~10–17s.
- **Interactive suggested actions**: rows beneath an answer are clickable (`↵ Use`) and prefill the
  composer (editable, never auto-sent); actionable sends go through the normal consent pipeline.
- **Chat-driven remediation (consent model)**: action tools (`restart_service`, `scale_service`)
  never execute inside the model loop — they queue as proposed actions with an Approve/Reject card.
  Approval executes through the constitutional gate; decisions persist onto conversation history.
  Settings → Remediation controls the mode (`diagnose` / `approve` / `auto`) and the per-tool
  autonomy allowlist for `auto`.
- **Action-tool gating (fail-closed)**: `AIOPS_ENABLE_ACTION_TOOLS` kill-switch → container
  whitelist → constitutional validation (>0.90 automatic / 0.70–0.90 approval / <0.70 alert-only);
  every attempt audited. Local restarts go through the Docker SDK over the mounted socket
  (the backend image ships no docker CLI).
- **Incidents**: real gated remediation executor; paced chaos demo with verified heal against a
  remote demo host.
- **Episodic memory UX**: Episode Browser, causal-tree layouts, full-screen `/graph` with filters
  and a fill-parent canvas, glass inspector drawer.
- **Mode 2 program**: Phases 0–1 validated live (bench baselines, golden v2 34/34 on both modes,
  zero-data-loss swaps). Later phases (engine pin upgrade, prefix caching, streaming UI wiring,
  guided JSON) are code-complete or planned — see CHANGELOG 0.12.0.

---

## Gates (last verified 2026-07-11)

| Gate | Result |
|------|--------|
| Backend pytest | 722 passed / 25 skipped / 0 failed |
| Frontend tsc / eslint / build | clean / 0 errors / ✓ |
| Golden v2 (live) | 34/34 on Mode 1 and Mode 2 |
| Live Playwright post-deploy | green (see `frontend/playwright.config.live.ts`) |

---

## Key design decisions (standing)

- Dual-model simultaneous serving is the paper architecture; **Mode 1 stays frozen** as the
  reference. Mode 2 is an additive overlay — Mode 1 must remain byte-identical when Mode 2 is off.
- LangGraph orchestration is MANDATORY (no fallback).
- Constitutional validation wraps every action-class operation; human approval satisfies Tier-1
  authorization but Tier-1 safety principles themselves are never overridable.
- Action tools are disabled unless explicitly enabled by environment; the container whitelist is
  the authority on what may be touched.
- Local dev (no GPU) uses mock/Ollama endpoints; production values live only in the VM's
  `.env.production` (never committed).
