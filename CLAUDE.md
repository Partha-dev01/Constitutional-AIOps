# CLAUDE.md - Constitutional AIOps Development Instructions

> **Version**: 2.2
> **Last Updated**: 2025-12-28
> **Architecture**: Simultaneous Dual-Model (24GB VRAM)

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
cat docs/INDEX.md
```

---

## 📋 Project Overview

**Constitutional AIOps** is an autonomous infrastructure management system combining:
- **Dual-agent LLM architecture** (Qwen3-4B + Qwen3-14B running simultaneously)
- **Constitutional AI safety framework** (11 principles, 3 tiers)
- **Graph-episodic memory** (Neo4j) for incident correlation
- **Human-in-the-loop workflows** for uncertain actions

**Target**: Self-hosted B.Tech final year project with research paper
**Hardware**: AWS g6.xlarge (NVIDIA L4 24GB) - ~$36/month
**License**: Academic/Research

---

## 🏛️ Architecture (FINALIZED - DO NOT CHANGE)

### Simultaneous Dual-Model Configuration
```
┌─────────────────────────────────────────────────────────────────┐
│                 L4 24GB VRAM - BOTH ALWAYS LOADED               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST AGENT (Port 8081)                                   │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-4B Q4_K_M (~2.5GB + 1GB KV = ~4GB)         │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  │  Context: 8K tokens | Latency: <50ms | TTL: -1           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8082)                              │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-14B Q4_K_M (~9GB + 1.5GB KV = ~11GB)       │  │
│  │  Purpose: RCA, remediation planning, human chat           │  │
│  │  Context: 4K tokens | Latency: <200ms | TTL: -1          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  FREE VRAM: ~9GB (overhead, batch processing)                  │
│  TOTAL: ~15GB used / 24GB available                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Simultaneous (NOT Hot-Swap)
| Factor | Old (T4 16GB) | New (L4 24GB) |
|--------|---------------|---------------|
| Swap Latency | 2-3 seconds | **0 ms** |
| Code Complexity | High (timeout mgmt) | **Low (direct routing)** |
| Monthly Cost | ~$14 | ~$28 |
| Decision | ❌ Rejected | ✅ **Selected** |

**+$14/month is justified by: zero latency, simpler code, better UX**

---

## 📁 Documentation Map

```
constitutional-aiops/
├── README.md                    # Quick Start (entry point)
├── CLAUDE.md                    # THIS FILE - Read first every session
├── docs/
│   ├── INDEX.md                 # Master documentation index (93+ files)
│   ├── BACKEND.md               # ⭐ Python backend reference (43 files)
│   ├── API.md                   # ⭐ REST API reference (50+ endpoints)
│   ├── FRONTEND.md              # ⭐ React frontend reference (23 files)
│   ├── ARCHITECTURE.md          # System architecture
│   ├── DEPLOYMENT.md            # Deployment overview
│   ├── JARVIS_LABS_DEPLOYMENT.md # Detailed Jarvis Labs guide
│   ├── AWS_DEPLOYMENT.md        # Detailed AWS guide
│   └── research/                # Academic materials
│       ├── references.bib       # BibTeX citations
│       └── diagrams/            # Architecture diagrams
```

---

## 🔄 Session Lifecycle

### On Session START
1. Run the mandatory commands above
2. Identify `[IN PROGRESS]` or `0%` items in CHECKLIST.md
3. Check for `[BLOCKER]` tags in ISSUES.md
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

### Blocked
- Issue description

### Next Steps
- Priority task 1
- Priority task 2
```

---

## 🔧 Technology Stack

### Models (FIXED - Do Not Change)
| Role | Model | Quantization | Port |
|------|-------|--------------|------|
| Fast Agent | Qwen3-4B | Q4_K_M | 8081 |
| Reasoning Agent | Qwen3-14B | Q4_K_M | 8082 |

### Infrastructure
| Component | Technology |
|-----------|------------|
| LLM Hosting | Jarvis Labs Ollama (A5000 24GB) |
| LLM Runtime | Ollama with OpenAI-compatible API |
| Graph Memory | Neo4j 5.x |
| Observability | Grafana, Loki, Tempo, Prometheus |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + TypeScript + Tailwind |
| Container | Docker Compose |

### AWS Configuration
| Setting | Value |
|---------|-------|
| Instance | g6.xlarge (Spot) |
| GPU | NVIDIA L4 24GB |
| Spot Price | ~$0.35/hr |
| Storage | 100GB gp3 |
| Ports | 22, 3000, 8080, 8081, 8082, 7474, 7687 |

---

## ⚡ Quick Reference

### Environment Variables
```bash
# LLM Endpoints
FAST_AGENT_URL=http://localhost:8081/v1
REASONING_AGENT_URL=http://localhost:8082/v1

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=constitutional_aiops_2025

# Constitutional AI
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

# Download models
./scripts/download-models.sh
```

### Model Router Pattern (NOT ModelManager)
```python
# Simple dual-endpoint routing (no swap logic needed)
from src.agents.model_router import ModelRouter

router = ModelRouter()

# Fast agent (always available at :8081)
fast_response = await router.fast_completion(prompt)

# Reasoning agent (always available at :8082)
reasoning_response = await router.reasoning_completion(prompt)
```

---

## 🛡️ Constitutional AI Framework

### Authorization Matrix
| Confidence | Action | Human Review |
|------------|--------|--------------|
| >90% | AUTOMATIC | Audit only |
| 70-90% | APPROVAL_REQUIRED | Must approve |
| <70% | ALERT_ONLY | Notify only |

### Principle Tiers
- **Tier 1 (Safety)**: P1.1-P1.4 - NEVER violate
- **Tier 2 (Operational)**: P2.1-P2.4 - Require approval to violate
- **Tier 3 (Learning)**: P3.1-P3.3 - Soft guidelines

---

## 📊 Development Phases

| Phase | Focus | Timeline | Status |
|-------|-------|----------|--------|
| 1 | Core Architecture | Week 1-2 | ⬅️ CURRENT |
| 2 | Intelligence Layer | Week 3 | Not Started |
| 3 | Dashboard & Polish | Week 4 | Not Started |
| 4 | Deployment Package | Week 5 | Not Started |

---

## ⚠️ Important Constraints

1. **Architecture is FINALIZED**: 24GB simultaneous dual-model is the decision
2. **Models are FIXED**: Qwen3-4B (fast) + Qwen3-14B (reasoning)
3. **Hardware is SET**: AWS g6.xlarge (L4 24GB)
4. **NO hot-swap**: Both models always loaded, direct port routing
5. **Constitutional AI is REQUIRED**: Every action goes through validator
6. **Update docs EVERY session**: Maintain continuity

---

## 👥 Project Team

**Project**: Constitutional AIOps
**Type**: B.Tech Final Year Project
**Institution**: [redacted]
**Advisor**: [redacted]

**Team**: Par (Lead), [redacted], [redacted], [redacted]

---

## 📄 File Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python | snake_case | `fast_annotator.py` |
| React | PascalCase | `IncidentTimeline.tsx` |
| Config | kebab-case | `llama-swap.yaml` |
| Docs | UPPERCASE | `CHECKLIST.md` |

---

**End of CLAUDE.md**
