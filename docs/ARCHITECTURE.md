# Constitutional AIOps - System Architecture

> **Version**: 0.4.0
> **Last Updated**: 2025-12-30
> **Status**: Production Ready
> **Source of Truth**: [KEY_METRICS.md](KEY_METRICS.md)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Architecture](#2-component-architecture)
3. [LLM Architecture](#3-llm-architecture)
4. [Data Flow](#4-data-flow)
5. [Memory Architecture](#5-memory-architecture)
6. [API Architecture](#6-api-architecture)
7. [Deployment Architecture](#7-deployment-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONSTITUTIONAL AIOPS SYSTEM                          │
│                      (Simultaneous Dual-Model Architecture)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INFRASTRUCTURE LAYER                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │
│  │  │Nextcloud │ │ Backend  │ │ Frontend │ │  Neo4j   │               │   │
│  │  │   App    │ │  :8000   │ │  :3000   │ │  :7687   │               │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   OBSERVABILITY LAYER (LGTM + Promtail)              │   │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐    │   │
│  │  │  Loki  │ │ Tempo  │ │Prometheus│ │ Grafana │ │  Promtail   │    │   │
│  │  │ :3100  │ │ :3200  │ │  :9090   │ │  :3001  │ │ (log ship)  │    │   │
│  │  └────────┘ └────────┘ └──────────┘ └─────────┘ └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INTELLIGENCE LAYER                              │   │
│  │              (Jarvis Labs A5000 24GB - Both Models Loaded)           │   │
│  │                                                                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐   │   │
│  │  │                JARVIS LABS OLLAMA ENDPOINT                     │   │   │
│  │  │          https://[instance].notebooks.jarvislabs.net/v1        │   │   │
│  │  │                                                                 │   │   │
│  │  │  ┌─────────────────────┐     ┌─────────────────────┐          │   │   │
│  │  │  │   FAST AGENT        │     │   REASONING AGENT   │          │   │   │
│  │  │  │   Qwen3-4B (~4GB)   │     │   Qwen3-14B (~11GB) │          │   │   │
│  │  │  │   8K context        │     │   4K context        │          │   │   │
│  │  │  │   <100ms P95        │     │   200-500ms P95     │          │   │   │
│  │  │  │                     │     │                     │          │   │   │
│  │  │  │   Purpose:          │     │   Purpose:          │          │   │   │
│  │  │  │   • Annotation      │     │   • RCA Analysis    │          │   │   │
│  │  │  │   • Classification  │     │   • Planning        │          │   │   │
│  │  │  │   • Confidence      │     │   • Human Chat      │          │   │   │
│  │  │  └─────────────────────┘     └─────────────────────┘          │   │   │
│  │  │                                                                 │   │   │
│  │  │  VRAM: ~15GB used / 24GB available (both always loaded)        │   │   │
│  │  │  NO HOT-SWAP - Direct routing, zero latency                    │   │   │
│  │  └───────────────────────────────────────────────────────────────┘   │   │
│  │                                                                       │   │
│  │  ┌───────────────────────────────────────────────────────────────┐   │   │
│  │  │            CONSTITUTIONAL VALIDATOR                            │   │   │
│  │  │   Tier 1 (Safety) → Tier 2 (Ops) → Tier 3 (Learning)          │   │   │
│  │  │   11 Principles | 3 Tiers | Authorization Matrix               │   │   │
│  │  └───────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

1. **Safety First**: All actions validated against Constitutional AI principles
2. **Simultaneous Loading**: Both models always loaded - zero swap latency
3. **Human in Loop**: Uncertain actions (70-90% confidence) require approval
4. **Evidence Based**: Decisions backed by telemetry data
5. **Minimal Intervention**: Prefer smallest effective action

---

## 2. Component Architecture

### 2.1 Core Components

| Component | Technology | Purpose | Port |
|-----------|------------|---------|------|
| Backend API | FastAPI | REST & WebSocket API | 8000 |
| Frontend | React + Vite + Tailwind | User interface | 3000 |
| Graph Memory | Neo4j 5.15 | Incident correlation | 7474/7687 |
| Fast Agent | Qwen3-4B via Ollama | Telemetry annotation | (Jarvis Labs) |
| Reasoning Agent | Qwen3-14B via Ollama | RCA & human chat | (Jarvis Labs) |

### 2.2 Observability Stack (LGTM + Promtail)

| Component | Technology | Purpose | Port |
|-----------|------------|---------|------|
| Logs | Loki 2.9.3 | Log aggregation | 3100 |
| Traces | Tempo 2.3.1 | Distributed tracing | 3200 |
| Metrics | Prometheus 2.48 | Metrics collection | 9090 |
| Visualization | Grafana 10.2.3 | Dashboards | 3001 |
| Log Shipping | Promtail 2.9.3 | Container logs → Loki | - |
| Collector | OpenTelemetry 0.91 | Telemetry pipeline | 4317/4318 |

### 2.3 LLM Configuration (from `src/config.py`)

```python
# Fast Agent (Qwen3-4B) - Always loaded
fast_agent_url: str = "https://[instance].notebooks.jarvislabs.net/v1"
fast_agent_model: str = "qwen3:4b"
fast_agent_context: int = 8192  # 8K context window
fast_agent_timeout: float = 30  # seconds

# Reasoning Agent (Qwen3-14B) - Always loaded
reasoning_agent_url: str = "https://[instance].notebooks.jarvislabs.net/v1"
reasoning_agent_model: str = "qwen3:14b"
reasoning_agent_context: int = 4096  # 4K context window
reasoning_agent_timeout: float = 120  # seconds
```

---

## 3. LLM Architecture

### 3.1 Simultaneous Dual-Model (NOT Hot-Swap)

```
┌─────────────────────────────────────────────────────────────────┐
│             JARVIS LABS A5000 24GB - BOTH ALWAYS LOADED         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST AGENT                                               │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-4B Q4_K_M (~2.5GB + 1GB KV = ~4GB)         │  │
│  │  Purpose: Telemetry annotation, classification            │  │
│  │  Context: 8K tokens | Latency: <100ms P95 | TTL: -1      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING AGENT                                          │  │
│  │  ─────────────────────────────────────────────────────    │  │
│  │  Model: Qwen3-14B Q4_K_M (~9GB + 1.5GB KV = ~11GB)       │  │
│  │  Purpose: RCA, remediation planning, human chat           │  │
│  │  Context: 4K tokens | Latency: 200-500ms P95 | TTL: -1   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  FREE VRAM: ~9GB (overhead, batch processing)                  │
│  TOTAL: ~15GB used / 24GB available                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Why Simultaneous (NOT Hot-Swap)

| Factor | Old (T4 16GB Hot-Swap) | Current (24GB Simultaneous) |
|--------|------------------------|----------------------------|
| Swap Latency | 2-3 seconds | **0 ms** |
| Code Complexity | High (timeout mgmt) | **Low (direct routing)** |
| Monthly Cost | ~$14 | ~$36 (Jarvis Labs) |
| User Experience | Noticeable delays | **Instant responses** |
| Decision | ❌ Rejected | ✅ **Selected** |

**+$22/month is justified by: zero latency, simpler code, better UX**

### 3.3 Model Router (from `src/agents/model_router.py`)

```python
class ModelRouter:
    """
    Routes requests to appropriate LLM endpoint.
    Both models run simultaneously on 24GB VRAM.
    No swap latency, no timeout management - just direct routing.
    """

    async def fast_completion(self, prompt: str, **kwargs) -> dict:
        """Fast agent (Qwen3-4B) for annotation, classification."""
        ...

    async def reasoning_completion(self, prompt: str, **kwargs) -> dict:
        """Reasoning agent (Qwen3-14B) for RCA, planning, chat."""
        ...
```

---

## 4. Data Flow

### 4.1 Telemetry Flow

```
Container Logs ──► Promtail ──► Loki ──► Backend API
                                              │
Metrics ─────────► Prometheus ────────────────┤
                                              │
Traces ──────────► Tempo ─────────────────────┤
                                              │
                                              ▼
                                    Telemetry Aggregator
                                              │
                                              ▼
                                    Fast Agent (Qwen3-4B)
                                      Classification
                                              │
                            ┌─────────────────┴─────────────────┐
                            ▼                                   ▼
                    HIGH CONFIDENCE                     LOW CONFIDENCE
                    (≥70%, simple)                     (<70% or complex)
                            │                                   │
                            │                    ┌──────────────┴──────────────┐
                            │                    ▼                             │
                            │           Reasoning Agent (Qwen3-14B)            │
                            │                    │                             │
                            └────────────────────┴─────────────────────────────┘
                                                 │
                                                 ▼
                                    Constitutional Validator
                                                 │
                            ┌────────────────────┼────────────────────┐
                            ▼                    ▼                    ▼
                        APPROVED           NEEDS APPROVAL         REJECTED
                        (≥90%)              (70-90%)              (<70%)
                            │                    │                    │
                            ▼                    ▼                    ▼
                        Execute            Queue for              Log &
                        Action             Human Review           Alert
```

### 4.2 Authorization Matrix

| Confidence | Action | Human Review |
|------------|--------|--------------|
| ≥90% | AUTOMATIC | Audit only |
| 70-90% | APPROVAL_REQUIRED | Must approve |
| <70% | ALERT_ONLY | Notify only |

---

## 5. Memory Architecture

### 5.1 Neo4j Graph Schema

```
NODE TYPES:
───────────

(Service)                    (Incident)
├── name: string             ├── id: string
├── type: string             ├── timestamp: datetime
├── criticality: int         ├── severity: string
└── metadata: map            ├── status: string
                             ├── root_cause: string
                             └── confidence: float

(Action)                     (Episode)
├── id: string               ├── incident_id: string
├── type: string             ├── telemetry_summary: string
├── timestamp: datetime      ├── analysis: string
├── confidence: float        ├── resolution: string
├── outcome: string          └── outcome: string
└── rollback_available: bool

RELATIONSHIPS:
──────────────

(Service)-[:DEPENDS_ON]->(Service)
(Incident)-[:AFFECTS]->(Service)
(Incident)-[:SIMILAR_TO]->(Incident)
(Incident)-[:RESOLVED_BY]->(Action)
(Action)-[:TARGETS]->(Service)
```

### 5.2 Query Patterns

```cypher
// Find similar incidents
MATCH (i:Incident)-[:AFFECTS]->(s:Service)<-[:AFFECTS]-(similar:Incident)
WHERE i.id = $incident_id AND similar.status = 'resolved'
RETURN similar, similar.resolution
LIMIT 5

// Get service dependencies
MATCH path = (s:Service {name: $name})-[:DEPENDS_ON*1..3]->(dep:Service)
RETURN path

// Find effective resolutions
MATCH (i:Incident)-[:RESOLVED_BY]->(a:Action)
WHERE i.root_cause CONTAINS $pattern AND a.outcome = 'success'
RETURN a.type, count(*) as success_count
ORDER BY success_count DESC
```

---

## 6. API Architecture

### 6.1 REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | System health with component status |
| GET | `/api/v1/health/ready` | Kubernetes readiness probe |
| GET | `/api/v1/health/live` | Kubernetes liveness probe |
| POST | `/api/v1/chat` | Send message to reasoning agent |
| POST | `/api/v1/chat/analyze` | Run RCA or planning analysis |
| GET | `/api/v1/incidents` | List incidents with filters |
| POST | `/api/v1/incidents` | Create incident |
| GET | `/api/v1/incidents/{id}` | Get incident details |
| POST | `/api/v1/incidents/{id}/analyze` | Trigger RCA |
| GET | `/api/v1/actions` | List actions |
| POST | `/api/v1/actions/{id}/approve` | Human approval |
| GET | `/api/v1/infrastructure/services` | Docker containers |
| GET | `/api/v1/graph/services` | Service dependency graph |
| POST | `/api/v1/demo/start` | Start demo mode |

### 6.2 WebSocket Endpoint

```
WS /ws - Real-time updates for incidents, actions, RCA results
```

---

## 7. Deployment Architecture

### 7.1 Primary: Jarvis Labs Hybrid (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                    JARVIS LABS HYBRID DEPLOYMENT                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LOCAL MACHINE (Docker Compose)          JARVIS LABS (Cloud)   │
│  ─────────────────────────────           ──────────────────    │
│                                                                 │
│  ┌─────────────────────┐                ┌─────────────────────┐│
│  │ Frontend    :3000   │                │ Ollama Server       ││
│  │ Backend     :8000   │───HTTPS────────│ A5000 24GB GPU      ││
│  │ Neo4j       :7687   │                │                     ││
│  │ Loki        :3100   │                │ ┌─────────────────┐ ││
│  │ Prometheus  :9090   │                │ │ Qwen3-4B (4GB)  │ ││
│  │ Tempo       :3200   │                │ │ Qwen3-14B (11GB)│ ││
│  │ Grafana     :3001   │                │ └─────────────────┘ ││
│  │ Promtail           │                │                     ││
│  │ OTel Collector     │                │ Cost: $0.49/hr      ││
│  └─────────────────────┘                └─────────────────────┘│
│                                                                 │
│  COST: ~$36/month (average 73 hours/month)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Alternative: AWS g6.xlarge

```
AWS g6.xlarge (L4 24GB, 4 vCPU, 16GB RAM)
Cost: ~$0.35/hr (Spot)
Use for: Self-contained deployment when Jarvis Labs unavailable
```

### 7.3 Local Development (No GPU)

```
docker-compose -f docker-compose.yml -f docker/docker-compose.local.yml up
- Uses mock LLM server
- Full observability stack
- No GPU required
```

---

## Appendix A: Port Reference

| Port | Service | Protocol |
|------|---------|----------|
| 3000 | Frontend | HTTP |
| 3001 | Grafana | HTTP |
| 3100 | Loki | HTTP |
| 3200 | Tempo | HTTP/gRPC |
| 4317 | OTEL Collector | gRPC |
| 4318 | OTEL Collector | HTTP |
| 7474 | Neo4j Browser | HTTP |
| 7687 | Neo4j Bolt | Bolt |
| 8000 | Backend API | HTTP/WS |
| 9090 | Prometheus | HTTP |

## Appendix B: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FAST_AGENT_URL` | Jarvis Labs URL | Fast agent endpoint |
| `REASONING_AGENT_URL` | Jarvis Labs URL | Reasoning agent endpoint |
| `FAST_AGENT_MODEL` | `qwen3:4b` | Fast agent model name |
| `REASONING_AGENT_MODEL` | `qwen3:14b` | Reasoning agent model |
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j connection |
| `NEO4J_PASSWORD` | `constitutional_aiops_2025` | Neo4j password |
| `CONFIDENCE_THRESHOLD_AUTO` | `0.90` | Auto-execute threshold |
| `CONFIDENCE_THRESHOLD_APPROVAL` | `0.70` | Require approval threshold |

---

---

## Appendix C: Performance Metrics (From Research_V5.tex)

See [KEY_METRICS.md](KEY_METRICS.md) for complete metrics reference.

### Key Targets
| Metric | Target |
|--------|--------|
| Fast Agent Latency | <100ms P95 |
| Reasoning Agent Latency | 200-500ms P95 |
| Annotation Accuracy | 87-92% |
| RCA Accuracy | 85-90% |
| Token Compression | 92% |
| Resolution Time | <5 minutes |

### Confidence Formula
```
C(a) = 0.4 · C_LLM + 0.35 · C_hist + 0.25 · C_sim
```

---

**Last Updated**: 2025-12-30
**Version**: 0.4.0
