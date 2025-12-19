# Constitutional AIOps

> Autonomous Infrastructure Management with Constitutional AI Safety

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)]()

## Overview

Constitutional AIOps is an autonomous infrastructure management system that combines:

- **Dual-Agent LLM Architecture**: Qwen3-4B (fast) + Qwen3-14B (reasoning) running simultaneously
- **Constitutional AI Safety**: 11 principles across 3 tiers ensuring safe autonomous actions
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
│  │  Model: Qwen3-4B Q4_K_M | Latency: <50ms                  │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT (Port 8082)                              │  │
│  │  Model: Qwen3-14B Q4_K_M | Latency: <200ms                │  │
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

## Project Structure

```
constitutional-aiops/
├── CLAUDE.md                # AI assistant instructions (READ FIRST)
├── PROJECT_SUMMARY.md       # Complete requirements history
├── src/                     # Python backend
│   ├── agents/              # LLM agents (FastAnnotator, ReasoningAgent)
│   ├── constitutional/      # Constitutional AI framework
│   ├── memory/              # Neo4j graph-episodic memory
│   ├── telemetry/           # OTEL integration
│   └── api/                 # FastAPI routes
├── frontend/                # React dashboard
├── docker/                  # Docker configurations
├── docs/                    # Documentation
│   ├── CHECKLIST.md         # Development progress
│   ├── CHANGELOG.md         # Version history
│   └── MEGA_PROMPT.md       # Detailed implementation guide
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

## Technology Stack

| Component | Technology |
|-----------|------------|
| LLM Runtime | llama.cpp (llama-server × 2) |
| Model Mgmt | llama-swap (TTL: -1) |
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

- **CLAUDE.md**: Instructions for AI assistants (read first on every session)
- **PROJECT_SUMMARY.md**: Complete requirements and history
- **docs/MEGA_PROMPT.md**: Detailed implementation guide
- **docs/CHECKLIST.md**: Development progress tracker
- **docs/CHANGELOG.md**: Version history

## Team

**Project**: Constitutional AIOps - B.Tech Final Year Project
**Institution**: [redacted]
**Advisor**: [redacted]

**Team Members**:
- Par (Project Lead)
- [redacted]
- [redacted]
- [redacted]

## License

Proprietary - All rights reserved.

---

## For Claude Code Users

When starting a new session, always read:
1. `CLAUDE.md` - Development instructions
2. `docs/CHECKLIST.md` - Current progress
3. `docs/ISSUES.md` - Active blockers

The architecture is **FINALIZED**:
- 24GB VRAM simultaneous dual-model (not hot-swap)
- Qwen3-4B (fast) + Qwen3-14B (reasoning)
- AWS g6.xlarge target hardware
