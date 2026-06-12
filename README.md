# Constitutional AIOps

> Autonomous Infrastructure Management with Constitutional AI Safety

**Version**: 0.7.0 | **Status**: Production Ready | **Last Updated**: 2026-01-29

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)]()

## Overview

Constitutional AIOps is an autonomous infrastructure management system that combines:

- **Dual-Agent LLM Architecture**: Qwen3-4B (fast) + Qwen3-14B (reasoning) running simultaneously
- **Constitutional AI Safety**: 12 principles across 3 tiers ensuring safe autonomous actions
- **Graph-Episodic Memory**: Neo4j-based incident correlation and context retention
- **Human-in-the-Loop**: Approval workflows for uncertain actions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 L4 24GB VRAM - BOTH ALWAYS LOADED               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST AGENT (Port 8081)                                   │  │
│  │  Model: Qwen3-4B Q4_K_M | Latency: <100ms P95             │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8082)                              │  │
│  │  Model: Qwen3-14B Q4_K_M | Latency: 200-500ms P95         │  │
│  │  Purpose: RCA, remediation planning, human chat           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  TOTAL: ~15GB used / 24GB available                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- NVIDIA GPU with 24GB VRAM (for production)

### Local Development (No GPU)

```bash
# Clone repository
git clone https://github.com/your-org/constitutional-aiops.git
cd constitutional-aiops

# Setup environment
cp .env.example .env
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start local stack (with mock LLM)
docker-compose -f docker-compose.yml -f docker/docker-compose.local.yml up -d

# Run backend
python -m uvicorn src.main:app --reload

# Run frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### GPU Deployment (AWS g6.xlarge)

```bash
# Download models (~12GB total)
./scripts/download-models.sh

# Start with GPU
docker-compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up -d

# Verify models loaded
curl http://localhost:8081/health  # Fast Agent
curl http://localhost:8082/health  # Reasoning Agent
```

### Hybrid Deployment (Jarvis Labs + Local)

Best for development: Run LLMs on Jarvis Labs GPU cloud, everything else locally.

```bash
# 1. Launch Ollama template on Jarvis Labs (A5000 $0.49/hr)
# 2. SSH in and run the setup script (stores models in /home for persistence):
ssh -i .ssh/jarvis_labs_key -p 11114 root@ssho.jarvislabs.ai 'bash -s' < scripts/setup-jarvis-ollama.sh

# 3. Set API endpoint in .env
echo "JARVIS_OLLAMA_URL=https://[your-endpoint].notebooks.jarvislabs.net" >> .env

# 4. Start local services
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d

# 5. Open http://localhost:3000
```

**Models**: Qwen3-4B (fast agent) + Qwen3-14B (reasoning agent) - both fit on A5000 24GB with 8GB free.

#### Rebuilding After Code Changes

After making changes to frontend or backend code, rebuild and restart:

```bash
# Stop current containers
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml down

# Rebuild with new code (force rebuild)
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml build --no-cache frontend backend

# Start services
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d

# Or quick rebuild and restart in one command:
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d --build
```

See [Jarvis Labs Deployment Guide](docs/JARVIS_LABS_DEPLOYMENT.md) for detailed instructions.

## Deployment Options

| Mode | GPU | Cost | Best For |
|------|-----|------|----------|
| **Local Development** | None | Free | Development with mock LLM |
| **Hybrid (Jarvis Labs)** | Remote | $0.49/hr | Development with real LLM |
| **AWS Full Stack** | Local | $0.35/hr | Production deployment |

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
├── benchmark/               # Benchmarking system
│   ├── datasets/            # OpsEval + Loghub datasets
│   ├── scripts/             # Download, prepare, run, evaluate
│   └── results/             # Benchmark outputs
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

Constitutional AIOps includes a comprehensive benchmarking system for evaluating LLM performance on AIOps tasks.

### Datasets (Real Data Only)

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

```bash
# Download and prepare datasets
python benchmark/scripts/download_datasets.py
python benchmark/scripts/prepare_datasets.py

# Run benchmarks (requires Ollama server)
python benchmark/scripts/run_benchmark.py

# Evaluate and export results
python benchmark/scripts/evaluate_results.py
python benchmark/scripts/export_metrics.py --format latex
```

### Evaluation Metrics

- **Annotation Accuracy**: Exact match on log classification
- **RCA Accuracy**: Partial match + BERTScore F1
- **BERTScore**: Semantic similarity using DeBERTa-XLarge-MNLI
- **Latency**: P50, P95, P99 with network compensation

See [docs/BENCHMARK.md](docs/BENCHMARK.md) for detailed benchmark documentation.

## Research Gaps Addressed

This project addresses 5 critical research gaps in AI-enhanced observability:

| ID | Research Gap | Solution |
|----|--------------|----------|
| RG1 | Automated Knowledge Extraction | Graph-episodic memory with incident correlation |
| RG2 | Graph-Based Operational Knowledge | Neo4j semantic + episodic hybrid retrieval |
| RG3 | Observability-Specific Tokenization | 92% compression via dedup + aggregation |
| RG4 | Constitutional AI for Operations | 11 principles across 3 tiers |
| RG5 | Comprehensive AI-Enhanced Observability | Dual-agent LGTM integration |

See [Research Paper](docs/research/# IMP Current Research Documentation/Research_V5.tex) for detailed analysis.

## Technology Stack

| Component | Technology |
|-----------|------------|
| LLM Hosting | Jarvis Labs Ollama (A5000 24GB) |
| LLM Runtime | Ollama with OpenAI-compatible API |
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
- **[docs/BENCHMARK.md](docs/BENCHMARK.md)**: Benchmarking system documentation
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

Proprietary - All rights reserved.

---

## For Claude Code Users

When starting a new session, always read:
1. `CLAUDE.md` - Development instructions
2. `docs/INDEX.md` - Documentation index
3. `docs/CHECKLIST.md` - Current progress
4. `docs/ISSUES.md` - Active blockers

The architecture is **FINALIZED**:
- 24GB VRAM simultaneous dual-model (not hot-swap)
- Qwen3-4B (fast) + Qwen3-14B (reasoning)
- Jarvis Labs Ollama (primary) or AWS g6.xlarge (alternative)
