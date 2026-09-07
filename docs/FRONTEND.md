# Frontend Architecture

> **Version**: 1.0.0
> **Last Updated**: 2026-09-07
> **Framework**: React 18 + TypeScript + Vite (144 TS/TSX files, 21 pages)
> **Authoritative detail**: the live `frontend/src/` tree. This reference is kept at page and component-group granularity, not per-file. Earlier revisions of this doc described a pre-cockpit UI (~23 files) and are superseded.

---

## Overview

The Constitutional AIOps frontend is a React single-page application. The primary operator surface is the **Command Center** cockpit (the Console page). Beyond it the app provides:

- **Dashboard**: system health and real-time stats, with opt-in reasoning-tier Explain widgets (cost-fenced)
- **Incident management**: list, detail, RCA, consent-gated approval, incident narrative + RCA copilot
- **Interactive chat**: multi-turn chat with the reasoning agent, a tool-call timeline, and Approve/Reject remediation cards; plus an in-browser WebLLM chat (`LocalChat`) that needs no server endpoint
- **Episodic graph**: full-screen force-directed knowledge graph with a graph copilot
- **Observability**: Metrics, Telemetry, and Infrastructure views over the LGTM stack
- **Extensibility and settings**: constitutional thresholds, model config, remediation autonomy, ChatOps alerting (Telegram/Matrix + inbound relay), BYOK keys, PATs, webhooks, and system prompts
- **Onboarding and access**: first-run setup wizard, public signup (Cloudflare Turnstile), session login, in-app docs, and legal pages

A separate always-on marketing site lives under `marketing/` (its own Vite build) and is not part of this app.

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| TypeScript (strict) | Type safety; no `any` |
| Vite | Build tool |
| React Router | Client-side routing |
| TanStack Query | Server state |
| Zustand | Client state |
| Tailwind CSS | Styling (class-based dark mode) |
| Recharts | Charts |
| Lucide React | Icons |
| react-force-graph-2d | Force-directed graph |

---

## Project structure (directory-level)

```
frontend/
├── index.html, vite.config.ts, tsconfig*.json, tailwind.config.js
└── src/
    ├── main.tsx, App.tsx, index.css
    ├── pages/         # 21 route components (see below)
    ├── components/     # shell + feature components + subgroups
    │   ├── chat/  console/  episodic/  incidents/  mcp/  schema/  ui/  viz/
    │   └── (Layout, EpisodicGraphExplorer, GraphCopilot, IncidentNarrative,
    │        ApprovalTicker, BlastRadiusPreview, LearnedRunbook, CommandPalette,
    │        AnomalyScan, TopologySchemaEditor, WhatChangedDiff, SavedViews,
    │        ShortcutsHelp, ErrorBoundary, RequireAuth, AccountSettings,
    │        CaptchaWidget, SetupNudge, LegalPage, JsonView, ...)
    └── lib/           # api client, websocket client, insights payload builders, utils
```

---

## Pages (`src/pages/`)

| Page | Purpose |
|------|---------|
| `Console.tsx` | Command Center cockpit: Fast / Reasoning tabs, embedded schema graph, chat pane |
| `Dashboard.tsx` | System overview and real-time stats; opt-in Explain widgets |
| `Chat.tsx` | Reasoning-agent chat with tool timeline and consent cards |
| `LocalChat.tsx` | In-browser WebLLM chat (`/local-chat`), no server endpoint |
| `Incidents.tsx` | Incident list/detail, RCA, approval, incident copilot + narrative |
| `Graph.tsx` | Full-screen episodic graph explorer |
| `Metrics.tsx` | LGTM observability metrics + validation report |
| `Telemetry.tsx` | Log / metric / trace viewer |
| `Infrastructure.tsx` | Container monitoring |
| `Agents.tsx` | Agent activity view |
| `Benchmark.tsx` | Benchmarking interface |
| `Mcp.tsx` | MCP tools browser |
| `Audit.tsx` | Action audit log |
| `Notifications.tsx` | In-app notification feed |
| `Settings.tsx` | Configuration (constitutional, models, remediation, alerting, BYOK, telemetry, prompts) |
| `Setup.tsx` | First-run onboarding wizard |
| `Signup.tsx` | Public signup (Turnstile captcha) |
| `Login.tsx` | Session login |
| `Docs.tsx` | In-app documentation |
| `Privacy.tsx`, `Terms.tsx` | Legal pages |

Admin-only surfaces and instance-wide mutation routes are role-gated (see ISSUES SEC-004). The public `/demo` tier serves several of these from client-side fixtures.

---

## Libraries (`src/lib/`)

- **api client**: type-safe wrappers over the backend REST API (health, chat, incidents, actions, tools, insights, settings, auth, and more). Base URL from `VITE_API_URL`, defaults to `/api/v1`.
- **websocket client**: `useWebSocket` hook with auto-reconnect and event-type subscriptions for incident / action / RCA / system events.
- **insights payload builders**: bounded, empty-safe payloads for the opt-in reasoning-tier Explain widgets and copilots.
- **utils**: `cn()`, date and relative-time formatters, and other helpers.

---

## Styling

Tailwind with class-based dark mode and HSL CSS variables (`--background`, `--foreground`, `--primary`, `--destructive`, and so on) defined in `index.css`. Semantic colors: primary for actions and focus, destructive for errors and critical severity, muted for disabled and placeholders.

---

## Build and development

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000 (API proxied to :8000)
npm run build    # tsc + vite build -> frontend/dist/
npm run lint     # eslint (max-warnings-0; 6 baseline warnings tracked)
npx vitest run   # unit tests (210)
```

Playwright end-to-end suites live under `frontend/e2e/` and are gated in CI against a vite-preview of the prod bundle (console / schema / graph-update / setup).

### Environment variables
```bash
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

---

**See Also**:
- [API.md](API.md) - REST API reference
- [BACKEND.md](BACKEND.md) - Backend architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
