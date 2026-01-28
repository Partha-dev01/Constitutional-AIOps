# CLAUDE.md - Constitutional AIOps Development Instructions

> **Version**: 3.1
> **Last Updated**: 2026-01-03
> **Architecture**: Simultaneous Dual-Model (24GB VRAM)
> **Status**: 100% Core Complete

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
- **Implementation**: 100% core complete
- **Deployment**: Jarvis Labs A5000 24GB (primary)
- **Research Paper**: `docs/research/# IMP Current Research Documentation/Research_V6.tex`

### Key Files Inventory
| Category | Count | Location |
|----------|-------|----------|
| Backend Python | 43 files | `src/` |
| Frontend React | 23 files | `frontend/src/` |
| API Endpoints | 50+ | FastAPI routes |
| Documentation | 15+ files | `docs/` |

### Observability Stack
| Component | Version | Retention |
|-----------|---------|-----------|
| Loki | v2.9 | 30 days |
| Grafana | v10.2 | - |
| Tempo | v2.3 | 7 days |
| Mimir | v2.16 | 90 days |

### Models (Always Loaded Simultaneously)
| Agent | Model | Port | VRAM |
|-------|-------|------|------|
| Fast Agent | Qwen3-4B Q4_K_M | 8081 | ~4GB |
| Reasoning Agent | Qwen3-14B Q4_K_M | 8082 | ~11GB |

**⚠️ ALWAYS run session start commands before continuing work!**

---

## 📋 Project Overview

**Constitutional AIOps** is an autonomous infrastructure management system combining:
- **Dual-agent LLM architecture** (Qwen3-4B + Qwen3-14B running simultaneously)
- **Constitutional AI safety framework** (12 principles, 3 tiers)
- **Graph-episodic memory** (Neo4j) for incident correlation
- **Human-in-the-loop workflows** for uncertain actions

**Target**: Self-hosted B.Tech final year project with research paper
**Hardware**: Jarvis Labs A5000 24GB (primary) / AWS g6.xlarge L4 24GB (alternative)
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
│  │  FAST AGENT (Port 8081)                                   │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-4B Q4_K_M (~2.5GB + 1GB KV = ~4GB)         │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  │  Context: 8K tokens | Latency: <100ms P95 | TTL: -1      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8082)                              │  │
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

## 📊 Performance Targets (From Research_V6.tex)

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
| **Primary (Current)** | Jarvis Labs A5000 24GB | $0.49/hr (~$36/month) | Development |
| Alternative | AWS g6.xlarge L4 24GB Spot | $0.35/hr (~$252/month continuous) | Production |
| Local Dev | No GPU (mock LLM) | Free | Testing |

**Note**: Currently using **Jarvis Labs** for development with Ollama endpoints.

---

## 📁 Documentation Map

```
constitutional-aiops/
├── README.md                    # Quick Start (entry point)
├── CLAUDE.md                    # THIS FILE - Read first every session
├── docs/
│   ├── INDEX.md                 # Master documentation index (93+ files)
│   ├── KEY_METRICS.md           # ⭐ Exportable metrics for paper
│   ├── BACKEND.md               # ⭐ Python backend reference (43 files)
│   ├── API.md                   # ⭐ REST API reference (50+ endpoints)
│   ├── FRONTEND.md              # ⭐ React frontend reference (23 files)
│   ├── ARCHITECTURE.md          # System architecture
│   ├── DEPLOYMENT.md            # Deployment overview
│   ├── CHECKLIST.md             # Development checklist
│   ├── ISSUES.md                # Issue tracker
│   ├── CHANGELOG.md             # Version history
│   ├── JARVIS_LABS_DEPLOYMENT.md # Jarvis Labs guide
│   ├── AWS_DEPLOYMENT.md        # AWS guide
│   └── research/                # Academic materials
│       ├── # IMP Current Research Documentation/
│       │   └── Research_V6.tex  # Main research paper (22 pages)
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

### Models (FIXED - Do Not Change)
| Role | Model | Quantization | Port | Context |
|------|-------|--------------|------|---------|
| Fast Agent | Qwen3-4B | Q4_K_M | 8081 | 8K |
| Reasoning Agent | Qwen3-14B | Q4_K_M | 8082 | 4K |

### Infrastructure
| Component | Technology |
|-----------|------------|
| LLM Hosting | Jarvis Labs Ollama (A5000 24GB) |
| LLM Runtime | Ollama with OpenAI-compatible API |
| Graph Memory | Neo4j 5.x |
| Observability | LGTM (Loki, Grafana, Tempo, Mimir) |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + TypeScript + Tailwind |
| Container | Docker Compose |

---

## ⚡ Quick Reference

### Environment Variables
```bash
# LLM Endpoints (Jarvis Labs)
FAST_AGENT_URL=https://[endpoint].notebooks.jarvislabs.net/v1
REASONING_AGENT_URL=https://[endpoint].notebooks.jarvislabs.net/v1

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=constitutional_aiops_2025

# Constitutional AI Thresholds
CONFIDENCE_THRESHOLD_AUTO=0.90
CONFIDENCE_THRESHOLD_APPROVAL=0.70
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

# Fast agent (always available at :8081)
fast_response = await router.fast_completion(prompt)

# Reasoning agent (always available at :8082)
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
2. **Models are FIXED**: Qwen3-4B (fast) + Qwen3-14B (reasoning)
3. **Hardware**: Jarvis Labs A5000 (primary) / AWS L4 (alternative)
4. **NO hot-swap**: Both models always loaded, direct port routing
5. **Constitutional AI is REQUIRED**: Every action through validator
6. **Update docs EVERY session**: Maintain continuity

---

## 👥 Project Team

**Project**: Constitutional AIOps
**Type**: B.Tech Final Year Project
**Institution**: [redacted]
**Advisor**: [redacted]

**Team**: [redacted], [redacted], [redacted], [redacted]

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

- **Research Paper**: `docs/research/# IMP Current Research Documentation/Research_V6.tex`
- **Key Metrics**: `docs/KEY_METRICS.md`
- **API Reference**: `docs/API.md`
- **Backend Reference**: `docs/BACKEND.md`

---

**End of CLAUDE.md** | Version 3.0 | 2025-12-30
