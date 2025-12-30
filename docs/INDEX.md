# Constitutional AIOps - Documentation Index

> **Version**: 0.4.0
> **Last Updated**: 2025-12-30
> **Status**: Production Ready
> **Total Files Indexed**: 93+
> **Source of Truth**: [KEY_METRICS.md](KEY_METRICS.md)

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [README](../README.md) | Quick start guide |
| [CHANGELOG](CHANGELOG.md) | Version history |
| [ISSUES](ISSUES.md) | Bug tracking |

---

## Documentation Map

### Core Documentation

| File | Last Updated | Description |
|------|--------------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 2025-12-27 | System architecture, components, data flow |
| [BACKEND.md](BACKEND.md) | 2025-12-28 | Python backend module reference (43 files) |
| [API.md](API.md) | 2025-12-28 | REST API endpoint reference (50+ endpoints) |
| [FRONTEND.md](FRONTEND.md) | 2025-12-28 | React frontend architecture (23 files) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 2025-12-27 | Deployment overview (Jarvis Labs, Local, AWS) |

### Development & Progress

| File | Last Updated | Description |
|------|--------------|-------------|
| [CHECKLIST.md](CHECKLIST.md) | 2025-12-27 | Development progress tracker |
| [CHANGELOG.md](CHANGELOG.md) | 2025-12-28 | Version history and release notes |
| [ISSUES.md](ISSUES.md) | 2025-12-27 | Active issues and blockers |
| [DOCUMENTATION_SCHEMA.md](DOCUMENTATION_SCHEMA.md) | 2025-12-27 | Documentation update guidelines |

### Deployment Guides

| File | Last Updated | Description |
|------|--------------|-------------|
| [JARVIS_LABS_DEPLOYMENT.md](JARVIS_LABS_DEPLOYMENT.md) | 2025-12-27 | Detailed Jarvis Labs hybrid setup |
| [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) | 2025-12-27 | AWS g6.xlarge deployment guide |

### Project Files

| File | Location | Description |
|------|----------|-------------|
| [CLAUDE.md](../CLAUDE.md) | Root | AI session instructions |
| [.env.example](../.env.example) | Root | Environment configuration template |
| [docker-compose.yml](../docker-compose.yml) | Root | Main Docker configuration |

---

## Complete File Inventory

### Backend (src/) - 43 Python Files

#### Core
| File | Purpose |
|------|---------|
| [main.py](../src/main.py) | FastAPI app entry, lifespan, WebSocket, routes |
| [config.py](../src/config.py) | Environment-based configuration classes |
| [\_\_init\_\_.py](../src/__init__.py) | Package version (0.1.0) |

#### Agents (src/agents/)
| File | Purpose |
|------|---------|
| [base_agent.py](../src/agents/base_agent.py) | Abstract base, AgentRole, ConfidenceLevel enums |
| [model_router.py](../src/agents/model_router.py) | Dual-endpoint routing (8081/8082), NO hot-swap |
| [fast_annotator.py](../src/agents/fast_annotator.py) | Qwen3-4B telemetry annotation, <100ms P95 |
| [reasoning_agent.py](../src/agents/reasoning_agent.py) | Qwen3-14B RCA/planning/chat, 200-500ms P95 |
| [\_\_init\_\_.py](../src/agents/__init__.py) | Module exports |

#### API Routes (src/api/routes/)
| File | Prefix | Purpose |
|------|--------|---------|
| [health.py](../src/api/routes/health.py) | `/health` | System health, readiness, liveness |
| [chat.py](../src/api/routes/chat.py) | `/chat` | Interactive chat, RCA/planning |
| [incidents.py](../src/api/routes/incidents.py) | `/incidents` | Incident CRUD, RCA triggering |
| [actions.py](../src/api/routes/actions.py) | `/actions` | Action validation, approval, execution |
| [tools.py](../src/api/routes/tools.py) | `/tools` | MCP tools REST API |
| [agents.py](../src/api/routes/agents.py) | `/agents` | Agent activity and statistics |
| [telemetry.py](../src/api/routes/telemetry.py) | `/telemetry` | LGTM stack queries |
| [graph.py](../src/api/routes/graph.py) | `/graph` | Neo4j episodic memory |
| [prompts.py](../src/api/routes/prompts.py) | `/prompts` | System prompt management |
| [infrastructure.py](../src/api/routes/infrastructure.py) | `/infrastructure` | Docker container monitoring |
| [demo.py](../src/api/routes/demo.py) | `/demo` | Anomaly injection for demos |
| [\_\_init\_\_.py](../src/api/routes/__init__.py) | - | Route exports |

#### API Schemas (src/api/schemas/)
| File | Purpose |
|------|---------|
| [chat.py](../src/api/schemas/chat.py) | ChatRequest, ChatResponse, ConversationHistory |
| [incident.py](../src/api/schemas/incident.py) | Incident, IncidentCreate, RCAResult, RemediationPlan |
| [action.py](../src/api/schemas/action.py) | Action, ActionCreate, ConstitutionalValidation |
| [\_\_init\_\_.py](../src/api/schemas/__init__.py) | Schema exports |

#### Constitutional AI (src/constitutional/)
| File | Purpose |
|------|---------|
| [principles.py](../src/constitutional/principles.py) | 11 principles, 3 tiers, violation actions |
| [validator.py](../src/constitutional/validator.py) | ValidationReport, confidence→authorization |
| [\_\_init\_\_.py](../src/constitutional/__init__.py) | Module exports |

#### Memory (src/memory/)
| File | Purpose |
|------|---------|
| [neo4j_client.py](../src/memory/neo4j_client.py) | Graph DB operations, incident/action/service nodes |
| [episode_store.py](../src/memory/episode_store.py) | Episode dataclass, similarity matching |
| [retrieval.py](../src/memory/retrieval.py) | RAG context retrieval for RCA/planning |
| [\_\_init\_\_.py](../src/memory/__init__.py) | Module exports |

#### Telemetry (src/telemetry/)
| File | Purpose |
|------|---------|
| [collector.py](../src/telemetry/collector.py) | LGTM stack queries (Loki, Prometheus, Tempo) |
| [compressor.py](../src/telemetry/compressor.py) | Token compression for LLM context |
| [aggregator.py](../src/telemetry/aggregator.py) | Health scoring, incident context |
| [\_\_init\_\_.py](../src/telemetry/__init__.py) | Module exports |

#### MCP (src/mcp/)
| File | Purpose |
|------|---------|
| [server.py](../src/mcp/server.py) | Model Context Protocol tool server |
| [tools/\_\_init\_\_.py](../src/mcp/tools/__init__.py) | Tool definitions |
| [\_\_init\_\_.py](../src/mcp/__init__.py) | Module exports |

#### Utils (src/utils/)
| File | Purpose |
|------|---------|
| [logging.py](../src/utils/logging.py) | Logging configuration |
| [audit.py](../src/utils/audit.py) | Action audit trail tracking |
| [websocket.py](../src/utils/websocket.py) | WebSocketManager, EventType, real-time streaming |
| [\_\_init\_\_.py](../src/utils/__init__.py) | Module exports |

---

### Frontend (frontend/) - 23 Files

#### Configuration
| File | Purpose |
|------|---------|
| [package.json](../frontend/package.json) | Dependencies, scripts |
| [vite.config.ts](../frontend/vite.config.ts) | Vite bundler configuration |
| [tsconfig.json](../frontend/tsconfig.json) | TypeScript compiler config |
| [tsconfig.node.json](../frontend/tsconfig.node.json) | Node TypeScript config |
| [tailwind.config.js](../frontend/tailwind.config.js) | Tailwind CSS theme |
| [postcss.config.js](../frontend/postcss.config.js) | PostCSS plugins |

#### Entry Points
| File | Purpose |
|------|---------|
| [index.html](../frontend/index.html) | HTML entry point |
| [src/main.tsx](../frontend/src/main.tsx) | React bootstrap |
| [src/App.tsx](../frontend/src/App.tsx) | Root component with routes |
| [src/index.css](../frontend/src/index.css) | Global styles, CSS variables |
| [src/vite-env.d.ts](../frontend/src/vite-env.d.ts) | Environment type definitions |

#### Pages (src/pages/)
| File | Purpose |
|------|---------|
| [Dashboard.tsx](../frontend/src/pages/Dashboard.tsx) | System overview, real-time stats |
| [Incidents.tsx](../frontend/src/pages/Incidents.tsx) | Incident management, RCA, approval |
| [Chat.tsx](../frontend/src/pages/Chat.tsx) | Interactive agent chat |
| [Agents.tsx](../frontend/src/pages/Agents.tsx) | Agent hub (6 tabs) |
| [Settings.tsx](../frontend/src/pages/Settings.tsx) | Configuration (5 tabs) |

#### Components (src/components/)
| File | Purpose |
|------|---------|
| [Layout.tsx](../frontend/src/components/Layout.tsx) | App shell, sidebar navigation |
| [IncidentTimeline.tsx](../frontend/src/components/IncidentTimeline.tsx) | Event timeline visualization |
| [DependencyGraph.tsx](../frontend/src/components/DependencyGraph.tsx) | Service dependency graph |
| [index.ts](../frontend/src/components/index.ts) | Component exports |

#### Libraries (src/lib/)
| File | Purpose |
|------|---------|
| [api.ts](../frontend/src/lib/api.ts) | Type-safe API client (30+ interfaces) |
| [websocket.ts](../frontend/src/lib/websocket.ts) | WebSocket client (14 event types) |
| [utils.ts](../frontend/src/lib/utils.ts) | cn(), formatDate(), formatRelativeTime() |

---

### Docker & Configuration - 16 Files

#### Root Configuration
| File | Purpose |
|------|---------|
| [.env.example](../.env.example) | Environment template |
| [.gitignore](../.gitignore) | Git ignore rules |
| [requirements.txt](../requirements.txt) | Python production dependencies |
| [requirements-dev.txt](../requirements-dev.txt) | Python dev dependencies |
| [pyproject.toml](../pyproject.toml) | Project metadata, tool configs |

#### Docker Compose
| File | Purpose |
|------|---------|
| [docker-compose.yml](../docker-compose.yml) | Main full-stack configuration |
| [docker/docker-compose.local.yml](../docker/docker-compose.local.yml) | Local dev with mock LLM |
| [docker/docker-compose.gpu.yml](../docker/docker-compose.gpu.yml) | AWS GPU deployment |
| [docker/docker-compose.hybrid.yml](../docker/docker-compose.hybrid.yml) | Jarvis Labs hybrid |
| [docker/docker-compose.production.yml](../docker/docker-compose.production.yml) | Production hardened |

#### Dockerfiles
| File | Purpose |
|------|---------|
| [docker/Dockerfile.backend](../docker/Dockerfile.backend) | Python FastAPI container |
| [docker/Dockerfile.frontend](../docker/Dockerfile.frontend) | React + Nginx container |
| [docker/Dockerfile.mock-llm](../docker/Dockerfile.mock-llm) | Mock LLM for local dev |

#### Docker Configs (docker/configs/)
| File | Purpose |
|------|---------|
| [llama-swap.yaml](../docker/configs/llama-swap.yaml) | Dual-model configuration |
| [prometheus.yml](../docker/configs/prometheus.yml) | Prometheus scrape config |
| [promtail-config.yaml](../docker/configs/promtail-config.yaml) | Log collector for Loki |
| [tempo-config.yaml](../docker/configs/tempo-config.yaml) | Tempo tracing config |
| [otel-collector.yaml](../docker/configs/otel-collector.yaml) | OpenTelemetry Collector |
| [nginx.conf](../docker/configs/nginx.conf) | Frontend reverse proxy |

---

### Scripts - 4 Files

| File | Purpose |
|------|---------|
| [scripts/download-models.sh](../scripts/download-models.sh) | Download Qwen3-4B and 14B models |
| [scripts/install.sh](../scripts/install.sh) | One-command installation wizard |
| [scripts/setup-jarvis-ollama.sh](../scripts/setup-jarvis-ollama.sh) | Jarvis Labs Ollama setup |
| [scripts/setup.sh](../scripts/setup.sh) | Development environment setup |

---

### Tests - 5 Files

| File | Purpose |
|------|---------|
| [tests/conftest.py](../tests/conftest.py) | Pytest fixtures, mock data |
| [tests/test_agents/test_agents.py](../tests/test_agents/test_agents.py) | Agent unit tests |
| [tests/test_agents/test_model_router.py](../tests/test_agents/test_model_router.py) | Model routing tests |
| [tests/test_api/test_routes.py](../tests/test_api/test_routes.py) | API endpoint tests |
| [tests/test_constitutional/test_validator.py](../tests/test_constitutional/test_validator.py) | Constitutional validation tests |

---

### Research & Diagrams - 5 Files

| File | Purpose |
|------|---------|
| [docs/research/references.bib](research/references.bib) | BibTeX citations |
| [docs/research/diagrams/constitutional-ai-framework.svg](research/diagrams/constitutional-ai-framework.svg) | 11 principles visualization |
| [docs/research/diagrams/dual-agent-architecture.svg](research/diagrams/dual-agent-architecture.svg) | Dual-model architecture |
| [docs/research/diagrams/token-compression-pipeline.svg](research/diagrams/token-compression-pipeline.svg) | Token compression flow |

---

## Documentation Structure

```
constitutional-aiops/
├── README.md                    # Quick Start (entry point)
├── CLAUDE.md                    # AI Session Guide
│
├── src/                         # Backend (43 Python files)
│   ├── main.py, config.py
│   ├── agents/                  # 5 files
│   ├── api/routes/              # 12 files
│   ├── api/schemas/             # 4 files
│   ├── constitutional/          # 3 files
│   ├── memory/                  # 4 files
│   ├── telemetry/               # 4 files
│   ├── mcp/                     # 3 files
│   └── utils/                   # 4 files
│
├── frontend/                    # Frontend (23 files)
│   ├── src/pages/               # 5 files
│   ├── src/components/          # 4 files
│   └── src/lib/                 # 3 files
│
├── docker/                      # Docker (11 files)
├── scripts/                     # Scripts (4 files)
├── tests/                       # Tests (5 files)
│
└── docs/
    ├── INDEX.md                 # THIS FILE - Master index
    ├── BACKEND.md               # Backend reference
    ├── API.md                   # API reference
    ├── FRONTEND.md              # Frontend reference
    ├── ARCHITECTURE.md          # System design
    ├── DEPLOYMENT.md            # Deployment overview
    ├── JARVIS_LABS_DEPLOYMENT.md
    ├── AWS_DEPLOYMENT.md
    ├── CHECKLIST.md
    ├── CHANGELOG.md
    ├── ISSUES.md
    ├── DOCUMENTATION_SCHEMA.md
    └── research/                # Academic materials
        ├── references.bib
        └── diagrams/            # 3 SVG files
```

---

## Current Architecture Summary

| Component | Technology | Notes |
|-----------|------------|-------|
| Fast Agent | Qwen3-4B | Telemetry annotation, <100ms P95 |
| Reasoning Agent | Qwen3-14B | RCA, remediation, 200-500ms P95 |
| LLM Hosting | Jarvis Labs Ollama | A5000 24GB, $0.49/hr |
| Graph Memory | Neo4j 5.x | Incident correlation |
| Backend | FastAPI | Python 3.11+ |
| Frontend | React 18 + TypeScript | Tailwind CSS |
| Observability | LGTM Stack | Loki, Grafana, Tempo, Prometheus |

---

## Update Protocol

When updating documentation:

1. **Edit the file** with new content
2. **Update header** - Change "Last Updated" date in file header
3. **Update this INDEX** - Modify the table entry for that file
4. **Add CHANGELOG entry** - If change is significant

See [DOCUMENTATION_SCHEMA.md](DOCUMENTATION_SCHEMA.md) for detailed guidelines.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.4.0 | 2025-12-28 | Added BACKEND.md, API.md, FRONTEND.md, complete file inventory |
| 0.3.2 | 2025-12-28 | Fixed SVG diagrams to match code |
| 0.3.1 | 2025-12-27 | Complete documentation restructure |
| 0.3.0 | 2025-12-26 | Dashboard fixes, Demo Mode |
| 0.2.0 | 2025-12-20 | Jarvis Labs integration |
| 0.1.0 | 2025-12-14 | Initial architecture |

---

**Last Updated**: 2025-12-30
