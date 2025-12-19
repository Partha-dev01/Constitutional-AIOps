# Constitutional AIOps - Complete Project Summary & Requirements

> **Document Version**: 1.0
> **Last Updated**: 2025-12-14
> **Purpose**: Complete project context for development continuity across Claude Code sessions

---

## 🎯 QUICK START FOR CLAUDE CODE

**Read these files in order on EVERY session start:**
1. `CLAUDE.md` - Development instructions and conventions
2. `docs/CHECKLIST.md` - Current progress and next tasks
3. `docs/ISSUES.md` - Active blockers

**Start building command:**
```bash
# Check current status
cat docs/CHECKLIST.md | grep -A2 "IN PROGRESS\|0%"
```

---

## 📖 Project History & Evolution

### Session 1: Initial Vision (Dec 6, 2025 - Early Morning)
**Goal**: Create a Claude Code mega prompt for B.Tech final year AIOps research project

**Original Requirements**:
- Build autonomous IT operations management system using LLMs
- Implement Constitutional AI principles for safe autonomous actions
- Use graph-episodic memory (Neo4j) for context retention
- Integrate with LGTM observability stack
- Target: Self-hosted on limited hardware (student budget)
- Deliverable: Research paper for academic submission

### Session 2: Enterprise Research (Dec 6, 2025 - Morning)
**Research Areas**:
1. **Telemetry Volumes**: Enterprise benchmarks → 1.7M tokens/hr from 50-node cluster
2. **GPU Costs**: AWS pricing analysis → g4dn, g5, g6 instances compared
3. **Model Selection**: MoE vs Dense → Qwen3 family chosen (open weights)
4. **Fine-tuning Datasets**: LogHub, AIOpsLab, FailureBench identified
5. **Patent Landscape**: IBM, Google, ServiceNow AIOps patents analyzed
6. **Compliance**: HIPAA, ISO 27001, SOC2 requirements documented

**Key Decisions Made**:
- Qwen3 family selected for strong instruction following
- Self-hosted on consumer/prosumer GPUs feasible
- Token compression essential (92% reduction target)

### Session 3: Architecture Finalization (Dec 6, 2025 - Late Morning)
**Dual-Agent Architecture Defined**:
- Fast Agent: Qwen3-8B for annotation, classification
- Reasoning Agent: Qwen3-14B for complex analysis, chat

**Initial Hardware Target**:
- AWS g4dn.xlarge (T4 16GB) with hot-swap
- llama-swap for model management
- Budget: ~$14/month Spot pricing

### Session 4: Documentation Package (Dec 10, 2025 - Morning)
**Files Created (11 files, 220KB)**:
- CLAUDE.md, MEGA_PROMPT (3 parts), CHECKLIST.md
- CHANGELOG.md, ISSUES.md, Simplified_AIOps_Documentation_v6.md

**Constitutional AI Framework Defined**:
- Tier 1 (Safety-Critical): P1.1-P1.4 - Never violate
- Tier 2 (Operational): P2.1-P2.4 - Require approval
- Tier 3 (Learning): P3.1-P3.3 - Soft guidelines

### Session 5: 24GB GPU Research (Dec 10, 2025 - Later)
**Research Question**: Can both models run simultaneously?

**VRAM Calculations**:
| Model | VRAM (Q4_K_M) |
|-------|---------------|
| Qwen3-4B | ~4GB (model + KV cache) |
| Qwen3-14B | ~11GB (model + KV cache) |
| **Total** | **~15GB / 24GB** |

**Recommendation**: Migrate to L4/A10G 24GB for simultaneous loading

### Session 6: Architecture Migration (Dec 14, 2025)
**Changes Implemented**:
1. Fast Agent: Qwen3-8B → **Qwen3-4B** (smaller, faster)
2. Hardware: T4 16GB → **L4 24GB** (simultaneous loading)
3. Code: ModelManager → **ModelRouter** (simplified)

**Research Deliverables Created**:
- references.bib (40+ citations)
- 3 SVG architecture diagrams
- Project_Report_Constitutional_AIOps.docx

---

## 🏛️ Final Architecture (v2.0)

### Hardware Specification
| Component | Specification | Cost (Spot) |
|-----------|---------------|-------------|
| GPU | NVIDIA L4 24GB (AWS g6.xlarge) | $0.35/hr |
| CPU | 4 vCPUs | Included |
| RAM | 16GB system memory | Included |
| Storage | 100GB SSD (gp3) | ~$8/mo |
| **Monthly Total** | 4hr/day × 20 days | **~$36/mo** |

### Model Configuration
```
┌─────────────────────────────────────────────────────────────────┐
│              L4 24GB VRAM - SIMULTANEOUS LOADING                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST AGENT (Port 8081)                                   │  │
│  │  Model: Qwen3-4B Q4_K_M                                   │  │
│  │  VRAM: ~2.5GB model + ~1GB KV cache = ~4GB               │  │
│  │  Context: 8K tokens | Latency: <50ms                      │  │
│  │  TTL: -1 (never unload)                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8082)                              │  │
│  │  Model: Qwen3-14B Q4_K_M                                  │  │
│  │  VRAM: ~9GB model + ~1.5GB KV cache = ~11GB              │  │
│  │  Context: 4K tokens | Latency: <200ms                     │  │
│  │  TTL: -1 (never unload)                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  FREE VRAM: ~9GB (for batch processing, overhead)              │
│  TOTAL USED: ~15GB / 24GB available                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Software Stack
| Layer | Technology | Purpose |
|-------|------------|---------|
| LLM Runtime | llama.cpp (llama-server × 2) | Model inference |
| Model Mgmt | llama-swap | Process management |
| Memory | Neo4j | Graph-episodic memory |
| Observability | Grafana, Loki, Tempo, Mimir | LGTM stack |
| Backend | FastAPI (Python 3.11+) | API server |
| Frontend | React 18 + TypeScript | Dashboard |
| Deployment | Docker Compose | Container orchestration |

---

## 📋 Complete Requirements Specification

### Functional Requirements
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR1 | Ingest telemetry from LGTM stack (logs, metrics, traces) | P0 | Not Started |
| FR2 | Classify alerts with Fast Agent (Qwen3-4B) | P0 | Not Started |
| FR3 | Perform root cause analysis with Reasoning Agent (Qwen3-14B) | P0 | Not Started |
| FR4 | Execute remediation actions via MCP tools | P0 | Not Started |
| FR5 | Maintain conversation context with graph-episodic memory | P0 | Not Started |
| FR6 | Enforce Constitutional AI principles on all actions | P0 | Not Started |
| FR7 | Provide chat interface for human operators | P1 | Not Started |
| FR8 | Learn from operator feedback and corrections | P2 | Not Started |
| FR9 | Display real-time incident timeline | P1 | Not Started |
| FR10 | Support approval workflows for uncertain actions | P0 | Not Started |

### Non-Functional Requirements
| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR1 | Fast Agent latency | <50ms | p99 response time |
| NFR2 | Reasoning Agent latency | <200ms | p99 response time |
| NFR3 | Token compression ratio | 92% | Input vs output tokens |
| NFR4 | Log classification accuracy | 94.2% | F1 score |
| NFR5 | Metric classification accuracy | 91.8% | F1 score |
| NFR6 | Trace classification accuracy | 89.3% | F1 score |
| NFR7 | VRAM usage | <20GB | Peak usage |
| NFR8 | Monthly infrastructure cost | ~$36 | AWS Spot + storage |
| NFR9 | System uptime | 99.5% | Availability |
| NFR10 | Time to first response | <100ms | User-perceived latency |

### Constitutional AI Principles
**Tier 1 - Safety-Critical (NEVER violate)**:
- P1.1: Never execute actions that could cause data loss
- P1.2: Never take actions during active incidents without approval
- P1.3: Never exceed resource limits that could cause cascade failures
- P1.4: Never modify security configurations without explicit approval

**Tier 2 - Operational (Require approval to violate)**:
- P2.1: Prefer minimal intervention (smallest effective action)
- P2.2: Require evidence before action (telemetry correlation)
- P2.3: Log all actions for audit trail
- P2.4: Escalate uncertainty to humans

**Tier 3 - Learning (Soft guidelines)**:
- P3.1: Track outcomes for continuous improvement
- P3.2: Learn from human corrections
- P3.3: Optimize for long-term system health

### Authorization Matrix
| Confidence | Action Type | Human Review |
|------------|-------------|--------------|
| >90% | AUTOMATIC | Audit only |
| 70-90% | APPROVAL_REQUIRED | Must approve |
| <70% | ALERT_ONLY | Notify only |

---

## 🗂️ Project Structure

```
constitutional-aiops/
├── CLAUDE.md                          # AI development instructions
├── PROJECT_SUMMARY.md                 # THIS FILE - Complete context
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Dev dependencies
├── pyproject.toml                     # Project config
├── docker-compose.yml                 # Main compose file
├── .env.example                       # Environment template
│
├── docs/                              # Documentation
│   ├── CHECKLIST.md                   # Development progress
│   ├── CHANGELOG.md                   # Version history
│   ├── ISSUES.md                      # Issue tracker
│   ├── ARCHITECTURE.md                # Architecture details
│   ├── DEPLOYMENT.md                  # Deployment guide
│   ├── MEGA_PROMPT.md                 # Part 1 - Overview
│   ├── MEGA_PROMPT_PART2.md           # Part 2 - Backend
│   ├── MEGA_PROMPT_PART3.md           # Part 3 - Frontend
│   ├── Simplified_AIOps_Documentation_v6.md  # Academic doc
│   └── research/                      # Research materials
│       ├── references.bib             # BibTeX citations
│       └── diagrams/                  # SVG diagrams
│
├── src/                               # Source code
│   ├── __init__.py
│   ├── main.py                        # FastAPI entry point
│   ├── config.py                      # Configuration
│   │
│   ├── agents/                        # LLM agents
│   │   ├── __init__.py
│   │   ├── base_agent.py              # Base agent class
│   │   ├── fast_annotator.py          # Qwen3-4B agent
│   │   ├── reasoning_agent.py         # Qwen3-14B agent
│   │   └── model_router.py            # Dual-endpoint router
│   │
│   ├── constitutional/                # Constitutional AI
│   │   ├── __init__.py
│   │   ├── principles.py              # Principle definitions
│   │   ├── validator.py               # Action validator
│   │   └── authorization.py           # Auth matrix
│   │
│   ├── memory/                        # Graph-episodic memory
│   │   ├── __init__.py
│   │   ├── neo4j_client.py            # Neo4j connection
│   │   ├── episode_store.py           # Episode storage
│   │   └── retrieval.py               # Context retrieval
│   │
│   ├── telemetry/                     # Telemetry processing
│   │   ├── __init__.py
│   │   ├── collector.py               # OTEL collection
│   │   ├── compressor.py              # Token compression
│   │   └── aggregator.py              # Data aggregation
│   │
│   ├── mcp/                           # MCP tools
│   │   ├── __init__.py
│   │   ├── server.py                  # MCP server
│   │   └── tools/                     # Individual tools
│   │       ├── __init__.py
│   │       ├── find_similar.py
│   │       ├── get_dependencies.py
│   │       ├── restart_service.py
│   │       ├── scale_service.py
│   │       └── analyze_logs.py
│   │
│   ├── api/                           # API routes
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                # Chat endpoints
│   │   │   ├── incidents.py           # Incident endpoints
│   │   │   ├── actions.py             # Action endpoints
│   │   │   └── health.py              # Health checks
│   │   └── schemas/                   # Pydantic models
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       ├── incident.py
│   │       └── action.py
│   │
│   └── utils/                         # Utilities
│       ├── __init__.py
│       ├── logging.py                 # Logging config
│       └── metrics.py                 # Prometheus metrics
│
├── frontend/                          # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── types/
│
├── docker/                            # Docker configs
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.local.yml       # Local dev (no GPU)
│   ├── docker-compose.gpu.yml         # GPU deployment
│   └── configs/
│       ├── llama-swap.yaml            # Model config
│       ├── otel-collector.yaml        # OTEL config
│       ├── loki-config.yaml
│       ├── tempo-config.yaml
│       └── prometheus.yml
│
├── scripts/                           # Utility scripts
│   ├── setup.sh                       # Initial setup
│   ├── download-models.sh             # Model downloader
│   ├── aws-start.sh                   # Start AWS instance
│   ├── aws-stop.sh                    # Stop AWS instance
│   ├── inject-anomaly.sh              # Test anomaly injection
│   └── backup-neo4j.sh                # Memory backup
│
├── tests/                             # Test files
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agents/
│   ├── test_constitutional/
│   ├── test_memory/
│   └── test_api/
│
└── configs/                           # Runtime configs
    ├── constitutional-principles.yaml  # Principle definitions
    ├── authorization-matrix.yaml       # Auth rules
    └── prompts/                        # Prompt templates
        ├── fast-annotator.txt
        ├── reasoning-rca.txt
        └── reasoning-chat.txt
```

---

## 🔧 Key Configuration Files

### Environment Variables (.env)
```bash
# LLM Endpoints (Simultaneous Dual-Model)
FAST_AGENT_URL=http://localhost:8081/v1
REASONING_AGENT_URL=http://localhost:8082/v1

# Neo4j Graph Memory
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme_neo4j_password

# Observability
LOKI_URL=http://localhost:3100
TEMPO_URL=http://localhost:3200
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000

# Constitutional AI
CONFIDENCE_THRESHOLD_AUTO=0.90
CONFIDENCE_THRESHOLD_APPROVAL=0.70

# Application
LOG_LEVEL=INFO
DEBUG=false
```

### llama-swap Configuration (docker/configs/llama-swap.yaml)
```yaml
models:
  fast-agent:
    cmd: llama-server -m /models/qwen3-4b-q4_k_m.gguf -c 8192 -ngl 99 --port 8081
    proxy: http://localhost:8081
    ttl: -1  # Never unload
    
  reasoning-agent:
    cmd: llama-server -m /models/qwen3-14b-q4_k_m.gguf -c 4096 -ngl 99 --port 8082
    proxy: http://localhost:8082
    ttl: -1  # Never unload

healthcheck:
  enabled: true
  interval: 30s
```

---

## 📊 Development Phases

### Phase 1: Core Architecture (Week 1-2) ← CURRENT
- [ ] Project structure setup
- [ ] Docker Compose (Nextcloud + LGTM)
- [ ] Dual llama-server configuration
- [ ] Fast Annotator (Qwen3-4B) basic
- [ ] Reasoning Agent (Qwen3-14B) basic
- [ ] Model Router implementation
- [ ] Constitutional Validator (basic)
- [ ] Human Chat Interface (basic)

### Phase 2: Intelligence Layer (Week 3)
- [ ] MCP Action Server (5 tools)
- [ ] Graph-episodic memory (Neo4j)
- [ ] Anomaly injection scripts
- [ ] Approval workflow
- [ ] Audit logging

### Phase 3: Dashboard & Polish (Week 4)
- [ ] Full React dashboard
- [ ] Real-time visualization
- [ ] Incident timeline
- [ ] Configuration management

### Phase 4: Deployment Package (Week 5)
- [ ] Single docker-compose.yml
- [ ] Installation script
- [ ] Customer documentation
- [ ] Hardware detection

---

## 📚 Reference Documents

| Document | Purpose | Location |
|----------|---------|----------|
| CLAUDE.md | AI assistant instructions | `/CLAUDE.md` |
| MEGA_PROMPT.md | Architecture & overview | `/docs/MEGA_PROMPT.md` |
| MEGA_PROMPT_PART2.md | Backend implementation | `/docs/MEGA_PROMPT_PART2.md` |
| MEGA_PROMPT_PART3.md | Frontend & deployment | `/docs/MEGA_PROMPT_PART3.md` |
| CHECKLIST.md | Development progress | `/docs/CHECKLIST.md` |
| CHANGELOG.md | Version history | `/docs/CHANGELOG.md` |
| ISSUES.md | Issue tracker | `/docs/ISSUES.md` |
| references.bib | Research citations | `/docs/research/references.bib` |

---

## 👥 Project Information

**Project**: Constitutional AIOps - Autonomous Infrastructure Management System
**Type**: B.Tech Final Year Project + Research Paper
**Institution**: [redacted]
**Department**: Computer Science & Engineering

**Team**:
- Par (Project Lead)
- [redacted]
- [redacted]
- [redacted]

**Advisor**: [redacted]

---

## ⚠️ Important Notes for Claude Code

1. **Architecture is FINALIZED**: Do not revert to hot-swap or change model selections
2. **Both models run SIMULTANEOUSLY**: No swap latency, direct port routing
3. **Target Hardware**: AWS g6.xlarge (L4 24GB) - this is non-negotiable
4. **Cost is ACCEPTABLE**: ~$36/month for the full stack
5. **Constitutional AI is CORE**: Every action must pass through validator
6. **Update docs on EVERY session**: CHECKLIST.md, CHANGELOG.md, ISSUES.md

---

**Document End**
