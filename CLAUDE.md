# CLAUDE.md - Constitutional AIOps Development Instructions

> **Version**: 5.2
> **Last Updated**: 2026-09-07
> **Architecture**: Simultaneous Dual-Model (24GB VRAM); Mode 1 default, single-engine Mode 2 overlay available
> **Status**: PRODUCTION (two tiers: AWS L4 GPU + lite CPU/Bedrock); gated + TLS; multi-tenant BYOK, public signup, ChatOps alerting, consent-gated remediation all live

---

## 🚨 CRITICAL: READ ON EVERY SESSION START

This file contains essential context for the Constitutional AIOps project. **Claude MUST read this file and check documentation status at the start of EVERY conversation.**

### Mandatory Session Start Commands
```bash
# 1. Check what to work on
cat docs/CHECKLIST.md | head -80

# 2. Check for blockers
cat docs/ISSUES.md | head -30

# 3. Check recent changes
cat docs/CHANGELOG.md | head -40

# 4. Check documentation index
cat docs/INDEX.md | head -50

# 5. Check key metrics (for paper updates)
cat docs/KEY_METRICS.md | head -100
```

---

## 🔄 Context Compaction Recovery Protocol

**If Claude Code context is compacted, this file contains ALL essential information to resume work:**

### System Status
- **Implementation**: core complete + production-hardened; chat-driven consent-gated remediation SHIPPED (2026-07)
- **SaaS surface (2026-09)**: multi-tenant BYOK + cost fencing, public signup (Turnstile), ChatOps alerting (Telegram/Matrix + inbound Telegram relay), opt-in reasoning-tier insight widgets + copilots, a Python SDK + fail-closed plugin loader, and a separate always-on marketing site; a lite tier targets an external (Bedrock) endpoint behind a wake-on-visit Lambda
- **Production runtime**: AWS g6.xlarge L4 24GB with **vLLM AWQ-marlin** dual engines (Mode 1), behind a Caddy/Let's-Encrypt domain; the app's own session login is the gate (`AUTH_REQUIRED=true`; Caddy basic-auth only on `/grafana`); VM frozen/thawed on demand for cost
- **Serving Mode 2** (opt-in overlay): single-engine profile via `AIOPS_MODE=2` + `docker/docker-compose.mode2.yml`; swappable from Settings (host-side watcher); Mode 1 stays byte-identical when off
- **Remediation model**: action tools NEVER execute inside the model loop — proposals queue for an Approve/Reject card in chat; Settings→Remediation picks diagnose/approve/auto (+ per-tool autonomy allowlist); everything passes the constitutional gate + audit log
- **Local dev**: Ollama / mock endpoints (OpenAI-compatible) — local defaults unchanged
- **Current state snapshot**: `docs/SESSION_STATE.md` · consolidated history: `docs/CHANGELOG.md` (1.0.0)

### Key Files Inventory
| Category | Count | Location |
|----------|-------|----------|
| Backend Python | 113 files | `src/` |
| Frontend TS/TSX | 144 files | `frontend/src/` |
| API routers | 21 registered | FastAPI routes (`src/main.py`) |
| Documentation | 18 files | `docs/` |

### Observability Stack
| Component | Version | Retention |
|-----------|---------|-----------|
| Loki | v2.9 | 30 days |
| Grafana | v10.2 | - |
| Tempo | v2.3 | 7 days |
| Prometheus | v2.48 | 30 days |

### Models (Always Loaded Simultaneously)
Production runtime is vLLM AWQ-marlin (served-model-name in parens); local dev may use Ollama Q4_K_M.
| Agent | Model | Served name | Port | VRAM |
|-------|-------|-------------|------|------|
| Fast Agent | Qwen3-4B-AWQ | qwen3-4b | 8000 | ~3-4GB |
| Reasoning Agent | Qwen3-14B-AWQ | qwen3-14b | 8001 | ~15GB |

**⚠️ ALWAYS run session start commands before continuing work!**

---

## 📋 Project Overview

**Constitutional AIOps** is an autonomous infrastructure management system combining:
- **Dual-agent LLM architecture** (Qwen3-4B + Qwen3-14B running simultaneously)
- **Constitutional AI safety framework** (12 principles, 3 tiers)
- **Graph-episodic memory** (Neo4j) for incident correlation
- **Human-in-the-loop workflows** for uncertain actions

**Target**: Self-hosted B.Tech final year project with research paper
**Hardware**: AWS g6.xlarge L4 24GB (primary, vLLM) / Jarvis Labs A5000 24GB (v1 dev, decommissioned 2026-05)
**License**: Academic/Research

---

## 🏛️ Architecture (FINALIZED)

### Simultaneous Dual-Model Configuration
```
┌─────────────────────────────────────────────────────────────────┐
│           24GB VRAM (A5000/L4) - BOTH ALWAYS LOADED             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST AGENT (Port 8000)                                   │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-4B Q4_K_M (~2.5GB + 1GB KV = ~4GB)         │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  │  Context: 8K tokens | Latency: <100ms P95 | TTL: -1      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8001)                              │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-14B Q4_K_M (~9GB + 1.5GB KV = ~11GB)       │  │
│  │  Purpose: RCA, remediation planning, human chat           │  │
│  │  Context: 4K tokens | Latency: 200-500ms P95 | TTL: -1   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  FREE VRAM: ~9GB (overhead, batch processing)                  │
│  TOTAL: ~15GB used / 24GB available (~63% utilization)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Simultaneous (NOT Hot-Swap)
| Factor | Old (T4 16GB) | New (24GB) |
|--------|---------------|------------|
| Swap Latency | 2-3 seconds | **0 ms** |
| Code Complexity | High | **Low** |
| Decision | ❌ Rejected | ✅ **Selected** |

---

## 📊 Performance Targets (From Research_V7.tex)

### Latency Targets
| Component | Target |
|-----------|--------|
| Fast Agent | <100ms P95 |
| Reasoning Agent | 200-500ms P95 |
| Graph Query (Neo4j) | O(log n) |

### Accuracy Targets
| Metric | Target Range |
|--------|-------------|
| Log Annotation Accuracy | 90-95% |
| Metric Annotation Accuracy | 85-92% |
| Trace Annotation Accuracy | 85-90% |
| Overall Annotation Accuracy | 87-92% |
| RCA Accuracy | 85-90% |
| Average Resolution Time | <5 minutes |

### Compression & Efficiency
| Metric | Value |
|--------|-------|
| Token Compression Rate | 92% |
| Tool Sprawl Reduction | 93% |
| Telemetry Ingestion | 1.7M tokens/hour |

### Confidence Score Formula
```
C(a) = α · C_LLM(a) + β · C_hist(a) + γ · C_sim(a)

Where:
  α = 0.4  (LLM confidence weight)
  β = 0.35 (Historical success rate)
  γ = 0.25 (Similarity to past incidents)
```

---

## 🛡️ Constitutional AI Framework

### Authorization Matrix
| Confidence | Action | Human Review |
|------------|--------|--------------|
| >0.90 | AUTOMATIC | Audit only |
| 0.70-0.90 | APPROVAL_REQUIRED | Must approve |
| <0.70 | ALERT_ONLY | Notify only |

### Principle Tiers (12 Total)
| Tier | Principles | Violation Handling |
|------|------------|-------------------|
| **Tier 1 (Safety)** | P1.1-P1.4 | NEVER violate |
| **Tier 2 (Operational)** | P2.1-P2.4 | Require approval |
| **Tier 3 (Learning)** | P3.1-P3.4 | Soft guidelines |

#### Tier 1 - Safety Critical
- **P1.1**: No data deletion without confirmation
- **P1.2**: Maintain minimum 2 healthy service replicas
- **P1.3**: No cascade actions affecting >5 services
- **P1.4**: All actions reversible within 60 seconds

#### Tier 2 - Operational
- **P2.1**: Prefer minimal intervention
- **P2.2**: Require evidence-based decisions
- **P2.3**: Check historical precedent
- **P2.4**: Graceful degradation over shutdown

#### Tier 3 - Learning
- **P3.1**: Attribute outcomes to actions
- **P3.2**: Analyze failures systematically
- **P3.3**: Reinforce successful patterns
- **P3.4**: Maintain solution diversity

---

## 🧠 Graph-Episodic Memory (AriGraph-Inspired)

### Neo4j Configuration
| Setting | Value |
|---------|-------|
| Database | Neo4j 5.x |
| Retrieval Complexity | O(log n) |
| Embedding Dimensions | 384-dim vectors |
| Similarity Threshold | ≥0.70 cosine |

### Memory Architecture
- **Semantic Triplets**: `T = {(e₁, r, e₂) | e₁, e₂ ∈ Entities, r ∈ Relations}`
- **Hybrid Retrieval**: `score(e) = α · vector_sim(e) + (1-α) · graph_sim(e)`

### Graph Schema Redesign (v0.6.0 - 2026-01-25)
**Purpose**: Prevent "hairball" visualization in Graph Explorer

| Constant | Value | File | Purpose |
|----------|-------|------|---------|
| `SIMILAR_TO_THRESHOLD` | 0.75 | graph.py | Min similarity for episode edges |
| `MAX_SIMILAR_EDGES_PER_EPISODE` | 3 | graph.py | Degree cap per episode |
| `MIN_TRIPLET_CONFIDENCE` | 0.70 | episode_store.py | Filter low-quality triplets |
| `MAX_EDGES_PER_NODE` | 5 | graph.py | Global degree cap |
| `CHARGE_STRENGTH` | -800 | EpisodicGraphExplorer.tsx | Node repulsion |
| `CENTER_STRENGTH` | 0.2 | EpisodicGraphExplorer.tsx | Centering force |

**If resuming after context compaction**: Check `docs/SESSION_STATE.md` for current progress.

### Data Retention
| Store | Retention |
|-------|-----------|
| Logs (Loki) | 30 days |
| Traces (Tempo) | 7 days |
| Metrics (Mimir) | 90 days |

---

## 📚 Research Gaps Addressed (5 Critical)

| ID | Gap | Description |
|----|-----|-------------|
| **RG1** | Knowledge Extraction | Automated learning from historical incidents |
| **RG2** | Graph-Based Knowledge | Semantic + episodic memory integration |
| **RG3** | Observability Tokenization | Strategies optimized for structured telemetry |
| **RG4** | Constitutional AI | Graduated trust for LLM-driven infrastructure |
| **RG5** | Unified Observability | Multi-modal AI correlation (logs+metrics+traces) |

---

## 💰 Deployment Costs

| Deployment | Hardware | Cost | Use Case |
|------------|----------|------|----------|
| **Primary (Current)** | AWS g6.xlarge L4 24GB On-Demand | ~$0.80/hr while running (VM frozen when idle; EBS-only cost stopped) | Production |
| Historical | Jarvis Labs A5000 24GB | $0.49/hr | Development (decommissioned 2026-05) |
| Local Dev | No GPU (mock LLM) | Free | Testing |

**Note**: Production runs on **AWS** with vLLM; the VM is stopped between sessions (an idle-stop
alarm guards against unattended burn) and all state persists on EBS across freeze/thaw.

---

## 📁 Documentation Map

```
constitutional-aiops/
├── README.md                    # Quick Start (entry point)
├── CLAUDE.md                    # THIS FILE - Read first every session
├── docs/
│   ├── INDEX.md                 # Master documentation index
│   ├── KEY_METRICS.md           # ⭐ Camera-ready metrics (COMSYS 2026 final)
│   ├── BACKEND.md               # ⭐ Python backend reference (113 files, 21 routers)
│   ├── API.md                   # ⭐ REST API reference (openapi.json: 127 paths)
│   ├── FRONTEND.md              # ⭐ React frontend reference (144 files)
│   ├── ARCHITECTURE.md          # System architecture
│   ├── DEPLOYMENT.md            # Deployment overview
│   ├── CHECKLIST.md             # Development checklist
│   ├── ISSUES.md                # Issue tracker
│   ├── CHANGELOG.md             # Version history
│   ├── JARVIS_LABS_DEPLOYMENT.md # Jarvis Labs guide
│   ├── AWS_DEPLOYMENT.md        # AWS guide
│   └── research/                # Academic materials
│       ├── # IMP Current Research Documentation/
│       │   └── Research_V7.tex  # Main research paper (22 pages)
│       └── references.bib       # BibTeX citations
```

---

## 🔄 Session Lifecycle

### On Session START
1. Run the mandatory commands above
2. Check CHECKLIST.md for pending items
3. Check ISSUES.md for blockers
4. Continue from where last session left off

### On Session END (or before context compaction)
```bash
# Update these files with session progress:
# 1. CHECKLIST.md - Mark completed items
# 2. CHANGELOG.md - Add session entry
# 3. ISSUES.md - Add/resolve issues
```

**Session Log Format** (add to CHANGELOG.md):
```markdown
## [YYYY-MM-DD] - Session Summary
### Completed
- Item 1
- Item 2

### In Progress
- Item 3 (X% done)

### Next Steps
- Priority task 1
```

---

## 🔧 Technology Stack

### Models (architecture fixed; runtime now vLLM AWQ)
Context column = deployed vLLM `--max-model-len` (docker-compose.production.yml).
The Ollama-era design doc had 8K fast / 4K reasoning; production flips it so chat
(reasoning agent) fits tool results in context.
| Role | Model | Quantization | Port | Context |
|------|-------|--------------|------|---------|
| Fast Agent | Qwen3-4B | AWQ-marlin (vLLM) / Q4_K_M (Ollama local) | 8000 | 4K |
| Reasoning Agent | Qwen3-14B | AWQ-marlin (vLLM) / Q4_K_M (Ollama local) | 8001 | 8K |

### Infrastructure
| Component | Technology |
|-----------|------------|
| LLM Hosting | AWS g6.xlarge L4 24GB (production) / Jarvis Labs A5000 (local-dev) |
| LLM Runtime | vLLM AWQ-marlin (production) / Ollama (local) — both OpenAI-compatible |
| Graph Memory | Neo4j 5.x |
| Observability | LGTM (Loki, Grafana, Tempo, Prometheus) + OTel collector |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + TypeScript + Tailwind |
| Container | Docker Compose |

---

## ⚡ Quick Reference

### Environment Variables
```bash
# LLM Endpoints (production vLLM on-VM; colon-free model names auto-disable thinking)
FAST_AGENT_URL=http://localhost:8000/v1       # FAST_AGENT_MODEL=qwen3-4b
REASONING_AGENT_URL=http://localhost:8001/v1  # REASONING_AGENT_MODEL=qwen3-14b
# Local dev may instead point at a Jarvis/Ollama endpoint (model names use a colon)

# Neo4j (no hardcoded default in production; set via .env / .env.production)
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=<required-in-production>

# Constitutional AI Thresholds
CONFIDENCE_THRESHOLD_AUTO=0.90
CONFIDENCE_THRESHOLD_APPROVAL=0.70

# Action tools (fail-closed; both default OFF/empty)
AIOPS_ENABLE_ACTION_TOOLS=false          # master kill-switch for restart/scale
AIOPS_ACTION_CONTAINER_WHITELIST=        # comma-extra containers beyond the default whitelist
DEMO_REMOTE_CONTAINERS=nextcloud-db      # containers remediated via the remote demo agent

# Serving mode (Mode 1 default; Mode 2 needs the compose overlay too)
AIOPS_MODE=1
CHAT_AGENTIC_TOOL_LOOP=false             # opt-in agentic tool loop in chat
```

### Key Commands
```bash
# Local development (no GPU)
docker-compose -f docker/docker-compose.local.yml up -d

# GPU deployment
docker-compose -f docker/docker-compose.gpu.yml up -d

# Run tests
pytest tests/ -v

# Format code
black src/ && isort src/
```

### Model Router Pattern
```python
from src.agents.model_router import ModelRouter

router = ModelRouter()

# Fast agent (production vLLM at :8000)
fast_response = await router.fast_completion(prompt)

# Reasoning agent (production vLLM at :8001)
reasoning_response = await router.reasoning_completion(prompt)
```

---

## ✅ Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Core Architecture | ✅ COMPLETE |
| 2 | Intelligence Layer | ✅ COMPLETE |
| 3 | Dashboard & Polish | ✅ COMPLETE |
| 4 | Deployment Package | ✅ COMPLETE |
| 5 | Documentation | ✅ COMPLETE |
| 6 | Research Paper | ✅ COMPLETE |

**Overall Status**: 100% Core Complete

---

## ⚠️ Important Constraints

1. **Architecture is FINALIZED**: 24GB simultaneous dual-model
2. **Models are FIXED**: Qwen3-4B (fast) + Qwen3-14B (reasoning); runtime is vLLM AWQ-marlin
3. **Hardware**: AWS g6.xlarge L4 24GB (primary, vLLM) / Jarvis Labs A5000 (local-dev, Ollama)
4. **NO hot-swap**: Both models always loaded, direct port routing (8000 fast / 8001 reasoning)
5. **Constitutional AI is REQUIRED**: Every action through validator
6. **Update docs EVERY session**: Maintain continuity

---

## 👥 Project Team

**Project**: Constitutional AIOps
**Type**: Academic engineering research project

---

## 📄 File Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python | snake_case | `fast_annotator.py` |
| React | PascalCase | `IncidentTimeline.tsx` |
| Config | kebab-case | `docker-compose.yml` |
| Docs | UPPERCASE | `CHECKLIST.md` |

---

## 📎 Quick Links

- **Research Paper**: `docs/research/# IMP Current Research Documentation/Research_V7.tex`
- **Key Metrics**: `docs/KEY_METRICS.md`
- **API Reference**: `docs/API.md`
- **Backend Reference**: `docs/BACKEND.md`

---

**End of CLAUDE.md** | Version 5.2 | 2026-09-07
