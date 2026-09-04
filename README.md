# Constitutional AIOps

> Autonomous Infrastructure Management with Constitutional AI Safety

**Version**: 1.0.0 | **Status**: Production deployed (AWS lite tier) | **Last Updated**: 2026-09-04

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)]()

## Overview

Constitutional AIOps is an autonomous infrastructure management system that combines:

- **Dual-Agent LLM Architecture**: a fast annotation agent and a reasoning agent, each pointed at any OpenAI-compatible endpoint (vLLM, Ollama, AWS Bedrock, OpenAI, ...). Both can share one endpoint for a minimal setup; the research reference config runs Qwen3-4B (fast) + Qwen3-14B (reasoning) on a single 24GB GPU.
- **Constitutional AI Safety**: 12 principles across 3 tiers ensuring safe autonomous actions
- **Graph-Episodic Memory**: Neo4j-based incident correlation and context retention (optional; omitted in the lite profile)
- **Human-in-the-Loop**: Approval workflows for uncertain actions

## Architecture

The recommended deployment is the **lite** profile: the backend and frontend plus
your own OpenAI-compatible LLM endpoint. No GPU, no bundled models, no Neo4j. The
diagram below is the **research reference config** (both models co-resident on one
24GB GPU), not a requirement for self-hosting.

```
┌─────────────────────────────────────────────────────────────────┐
│                 L4 24GB VRAM - BOTH ALWAYS LOADED               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST AGENT (Port 8000)                                   │  │
│  │  Model: Qwen3-4B Q4_K_M | Latency: <100ms P95             │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8001)                              │  │
│  │  Model: Qwen3-14B Q4_K_M | Latency: 200-500ms P95         │  │
│  │  Purpose: RCA, remediation planning, human chat           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  TOTAL: ~15GB used / 24GB available                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

The recommended self-host is the **lite** profile: backend + frontend + your own
OpenAI-compatible LLM endpoint. No GPU, no bundled models, no Neo4j. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full guide.

### Prerequisites

- Docker & Docker Compose v2
- An OpenAI-compatible LLM endpoint (vLLM, Ollama, AWS Bedrock, OpenAI, ...)
- ~2GB RAM, ~20GB disk

### Lite Self-Host (no GPU)

```bash
# Clone
git clone https://github.com/Partha-dev01/Constitutional-AIOps.git constitutional-aiops
cd constitutional-aiops

# Configure your LLM endpoint (both agents may share one URL + model)
cp .env.example .env
#   set FAST_AGENT_URL / REASONING_AGENT_URL / *_MODEL, and LLM_API_KEY if the
#   endpoint needs a bearer token.

# Start (self-contained)
docker compose -f docker/docker-compose.lite.yml up -d

# Open http://localhost:3000  (backend http://localhost:8000/docs)
```

### Local Development (mock LLM)

```bash
docker compose -f docker-compose.yml -f docker/docker-compose.local.yml up -d
# Backend hot-reload:  cd src && uvicorn main:app --reload
# Frontend hot-reload: cd frontend && npm install && npm run dev
```

### Full GPU Stack (research reference config)

Both models on one 24GB GPU (vLLM AWQ): Qwen3-4B (fast, :8000) + Qwen3-14B
(reasoning, :8001), plus Neo4j and the LGTM observability stack.

```bash
cp .env.production.example .env   # set NEO4J_PASSWORD, AUTH_*, WS_TOKEN, ...
docker compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up -d
curl http://localhost:8000/health   # fast agent
curl http://localhost:8001/health   # reasoning agent
```

## Deployment Options

| Mode | GPU | LLM | Best for |
|------|-----|-----|----------|
| **Lite self-host** | None | Your own OpenAI-compatible endpoint | Most self-hosters |
| **Local development** | None | Mock (no external calls) | Working on the code |
| **Full GPU stack** | One 24GB GPU | Two co-resident models (research reference) | Reproducing the paper |

The lite profile is what the hosted instance runs. It has no fixed running cost
beyond a small always-on VM, since compute sleeps when idle.

## Project Structure

```
constitutional-aiops/
├── README.md                # Quick Start (this file)
├── CLAUDE.md                # AI assistant instructions
├── src/                     # Python backend
│   ├── agents/              # LLM agents (FastAnnotator, ReasoningAgent)
│   ├── constitutional/      # Constitutional AI framework
│   ├── memory/              # Neo4j graph-episodic memory
│   ├── telemetry/           # OTEL integration
│   ├── benchmark/           # Benchmark runner and evaluator
│   └── api/                 # FastAPI routes
├── frontend/                # React dashboard
├── docker/                  # Docker configurations
├── docs/                    # Documentation
│   ├── INDEX.md             # Documentation index
│   ├── BENCHMARK.md         # Benchmark documentation
│   ├── ARCHITECTURE.md      # System design
│   ├── DEPLOYMENT.md        # Deployment guide
│   ├── CHECKLIST.md         # Development progress
│   └── CHANGELOG.md         # Version history
└── tests/                   # Test suite
```

## Constitutional AI Framework

### Authorization Matrix

| Confidence | Action | Human Review |
|------------|--------|--------------|
| >90% | AUTOMATIC | Audit only |
| 70-90% | APPROVAL_REQUIRED | Must approve |
| <70% | ALERT_ONLY | Notify only |

### Principle Tiers

**Tier 1 (Safety-Critical)** - NEVER violate:
- P1.1: Data Protection
- P1.2: Active Incident Safety
- P1.3: Cascade Prevention
- P1.4: Security Integrity

**Tier 2 (Operational)** - Require approval to violate:
- P2.1: Minimal Intervention
- P2.2: Evidence-Based Actions
- P2.3: Audit Trail
- P2.4: Uncertainty Escalation

**Tier 3 (Learning)** - Soft guidelines:
- P3.1: Outcome Tracking
- P3.2: Human Correction Learning
- P3.3: Long-term Optimization

## Performance Targets

| Metric | Target |
|--------|--------|
| Fast Agent Latency | <100ms P95 |
| Reasoning Agent Latency | 200-500ms P95 |
| Annotation Accuracy | 87-92% |
| RCA Accuracy | 85-90% |
| Token Compression Rate | 92% |
| Resolution Time | <5 minutes |

### Confidence Formula

```
C(a) = 0.4 · C_LLM + 0.35 · C_hist + 0.25 · C_sim
```

See [KEY_METRICS.md](docs/KEY_METRICS.md) for complete metrics reference.

## Benchmarking System

The Benchmark page has two jobs. The **Your setup** tab runs a few sample cases
through the exact agents the app uses, against the LLM endpoint you configured,
so you can check whether your model is good enough before trusting it. The
**Research run** tab reproduces the paper's evaluation.

### Research reference datasets

The app ships a small synthetic sample so the page works out of the box. The
research evaluation used the datasets below; bring your own by replacing the
files under `data/benchmark/` in the same shape.

| Dataset | Source | Cases | Purpose |
|---------|--------|-------|---------|
| **Annotation Test** | Loghub HDFS + BGL | 200 | Log classification (normal vs anomaly) |
| **RCA Test** | OpsEval | 100 | Root cause analysis questions |

### Models Evaluated

| Model | Type | VRAM |
|-------|------|------|
| Constitutional AIOps | Hybrid (Qwen3-4B + Qwen3-14B) | ~15GB |
| llama3:70b | Single | ~40GB |
| llama3:8b | Single | ~5GB |
| qwen3:4b | Single | ~4GB |
| qwen3:14b | Single | ~11GB |

### Quick Benchmark Commands

The app ships a small **synthetic sample** dataset so the Benchmark page works
out of the box. Regenerate it (or use it as a template for your own data) with:

```bash
# (Re)seed the synthetic sample datasets under data/benchmark/
python scripts/seed_benchmark_data.py
```

**Bring your own dataset:** replace the JSON files under
`data/benchmark/intermediate/datasets/` with your own cases in the same shape,
then start a run from the Benchmark page (requires a configured LLM endpoint).

### Evaluation Metrics

- **Annotation Accuracy**: Exact match on log classification
- **RCA Accuracy**: Partial match + BERTScore F1
- **BERTScore**: Semantic similarity using DeBERTa-XLarge-MNLI
- **Latency**: P50, P95, P99 with network compensation

## Research Gaps Addressed

This project addresses 5 critical research gaps in AI-enhanced observability:

| ID | Research Gap | Solution |
|----|--------------|----------|
| RG1 | Automated Knowledge Extraction | Graph-episodic memory with incident correlation |
| RG2 | Graph-Based Operational Knowledge | Neo4j semantic + episodic hybrid retrieval |
| RG3 | Observability-Specific Tokenization | 92% compression via dedup + aggregation |
| RG4 | Constitutional AI for Operations | 12 principles across 3 tiers |
| RG5 | Comprehensive AI-Enhanced Observability | Dual-agent LGTM integration |

The research paper behind this project is maintained separately and is not part of this repository.

## Technology Stack

| Component | Technology |
|-----------|------------|
| LLM Hosting | Bring your own (vLLM, Ollama, AWS Bedrock, OpenAI, ...) |
| LLM Runtime | Any OpenAI-compatible endpoint |
| Graph Memory | Neo4j 5.x |
| Observability | Grafana, Loki, Tempo, Prometheus |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 18 + TypeScript + Tailwind |
| Container | Docker Compose |

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agents/test_model_router.py -v
```

### Code Quality

```bash
# Format code
black src/ && isort src/

# Type checking
mypy src/

# Linting
ruff src/
```

## Configuration

Key environment variables (see `.env.example`):

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

## Documentation

- **[CLAUDE.md](CLAUDE.md)**: Instructions for AI assistants (read first on every session)
- **[docs/INDEX.md](docs/INDEX.md)**: Master documentation index (100+ files)
- **[docs/KEY_METRICS.md](docs/KEY_METRICS.md)**: Performance metrics reference
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System architecture
- **[docs/BACKEND.md](docs/BACKEND.md)**: Python backend (45+ files)
- **[docs/API.md](docs/API.md)**: REST API reference (55+ endpoints)
- **[docs/FRONTEND.md](docs/FRONTEND.md)**: React frontend (25+ files)
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Deployment overview
- **[docs/CHECKLIST.md](docs/CHECKLIST.md)**: Development progress tracker
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)**: Version history

## About

Constitutional AIOps is an academic engineering research project.

## License

Licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0). See
[LICENSE](LICENSE) for the full text.

Copyright (C) 2026 Partha-dev01.

Because this project is AGPL-licensed, if you run a modified version as a network
service, you must offer its users the corresponding source of your modified version.

---

## For Claude Code Users

When starting a new session, always read:
1. `CLAUDE.md` - Development instructions
2. `docs/INDEX.md` - Documentation index
3. `docs/CHECKLIST.md` - Current progress
4. `docs/ISSUES.md` - Active blockers

The research reference configuration:
- 24GB VRAM simultaneous dual-model (not hot-swap)
- Qwen3-4B (fast) + Qwen3-14B (reasoning)
- Self-hosters instead point both agents at any OpenAI-compatible endpoint (see the lite profile)
