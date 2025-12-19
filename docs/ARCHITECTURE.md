# Constitutional AIOps - System Architecture

> **Version**: 0.1.0-alpha
> **Last Updated**: 2025-12-06

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow](#3-data-flow)
4. [Model Architecture](#4-model-architecture)
5. [Memory Architecture](#5-memory-architecture)
6. [API Architecture](#6-api-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Deployment Architecture](#8-deployment-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONSTITUTIONAL AIOPS SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INFRASTRUCTURE LAYER                            │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │Nextcloud │ │ MariaDB  │ │  Redis   │ │  Nginx   │ │   Cron   │  │   │
│  │  │   App    │ │    DB    │ │  Cache   │ │  Proxy   │ │  Worker  │  │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │   │
│  │       │            │            │            │            │         │   │
│  │       └────────────┴────────────┴────────────┴────────────┘         │   │
│  │                              │                                       │   │
│  │                    OpenTelemetry SDK                                 │   │
│  └──────────────────────────────┼───────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────┴───────────────────────────────────────┐   │
│  │                     OBSERVABILITY LAYER (LGTM)                        │   │
│  │  ┌──────────────────────────────────────────────────────────────┐    │   │
│  │  │              OpenTelemetry Collector                          │    │   │
│  │  │         (Receive, Process, Export telemetry)                  │    │   │
│  │  └────────┬─────────────────┬─────────────────┬─────────────────┘    │   │
│  │           │                 │                 │                       │   │
│  │  ┌────────▼────┐   ┌────────▼────┐   ┌────────▼────┐                 │   │
│  │  │    Loki     │   │    Tempo    │   │ Prometheus  │                 │   │
│  │  │   (Logs)    │   │  (Traces)   │   │  (Metrics)  │                 │   │
│  │  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                 │   │
│  │         └─────────────────┼─────────────────┘                        │   │
│  │                           │                                          │   │
│  │                   ┌───────▼───────┐                                  │   │
│  │                   │    Grafana    │                                  │   │
│  │                   │ (Visualization)│                                  │   │
│  │                   └───────────────┘                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────┴───────────────────────────────────────┐   │
│  │                      INTELLIGENCE LAYER                               │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │                   TELEMETRY AGGREGATOR                       │     │   │
│  │  │         (Collect, normalize, prepare for analysis)           │     │   │
│  │  └────────────────────────────┬────────────────────────────────┘     │   │
│  │                               │                                       │   │
│  │  ┌────────────────────────────▼────────────────────────────────┐     │   │
│  │  │              FAST ANNOTATOR (Qwen3-8B)                       │     │   │
│  │  │     • Anomaly detection (<100ms latency)                     │     │   │
│  │  │     • Classification & severity scoring                      │     │   │
│  │  │     • Confidence calculation                                 │     │   │
│  │  │     • Routing decision (direct action vs reasoning)          │     │   │
│  │  └─────────────┬─────────────────────────────┬─────────────────┘     │   │
│  │                │                             │                        │   │
│  │    ┌───────────▼───────────┐     ┌───────────▼───────────┐           │   │
│  │    │   HIGH CONFIDENCE     │     │    LOW CONFIDENCE     │           │   │
│  │    │   (≥70%, simple)      │     │   (<70% or complex)   │           │   │
│  │    └───────────┬───────────┘     └───────────┬───────────┘           │   │
│  │                │                             │                        │   │
│  │                │                 ┌───────────▼───────────┐           │   │
│  │                │                 │  REASONING AGENT      │           │   │
│  │                │                 │    (Qwen3-14B)        │           │   │
│  │                │                 │  • Deep RCA analysis  │           │   │
│  │                │                 │  • Human chat mode    │           │   │
│  │                │                 │  • /think toggle      │           │   │
│  │                │                 └───────────┬───────────┘           │   │
│  │                │                             │                        │   │
│  │    ┌───────────▼─────────────────────────────▼───────────┐           │   │
│  │    │            CONSTITUTIONAL VALIDATOR                  │           │   │
│  │    │   Tier 1 (Safety) → Tier 2 (Ops) → Tier 3 (Learn)   │           │   │
│  │    └─────────────────────────┬───────────────────────────┘           │   │
│  │                              │                                        │   │
│  └──────────────────────────────┼────────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────┴───────────────────────────────────────┐   │
│  │                        ACTION LAYER                                   │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │                   MCP ACTION SERVER                          │     │   │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │     │   │
│  │  │  │find_similar│ │get_depends │ │  restart   │               │     │   │
│  │  │  └────────────┘ └────────────┘ └────────────┘               │     │   │
│  │  │  ┌────────────┐ ┌────────────┐                              │     │   │
│  │  │  │   scale    │ │  analyze   │                              │     │   │
│  │  │  └────────────┘ └────────────┘                              │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  │                              │                                        │   │
│  └──────────────────────────────┼────────────────────────────────────────┘   │
│                                 │                                           │
│  ┌──────────────────────────────┴───────────────────────────────────────┐   │
│  │                       MEMORY LAYER                                    │   │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                 │   │
│  │  │       Neo4j         │     │      InfluxDB       │                 │   │
│  │  │  (Graph Memory)     │     │   (Time Series)     │                 │   │
│  │  │  • Services         │     │  • Metrics history  │                 │   │
│  │  │  • Incidents        │     │  • Anomaly scores   │                 │   │
│  │  │  • Dependencies     │     │  • Action outcomes  │                 │   │
│  │  │  • Resolutions      │     │                     │                 │   │
│  │  └─────────────────────┘     └─────────────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      INTERFACE LAYER                                  │   │
│  │  ┌─────────────────────┐     ┌─────────────────────┐                 │   │
│  │  │   React Dashboard   │     │    FastAPI Backend  │                 │   │
│  │  │  • Real-time chat   │◄───►│  • REST endpoints   │                 │   │
│  │  │  • Incident view    │     │  • WebSocket chat   │                 │   │
│  │  │  • Service topology │     │  • Auth & logging   │                 │   │
│  │  │  • Configuration    │     │                     │                 │   │
│  │  └─────────────────────┘     └─────────────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

1. **Safety First**: All actions validated against Constitutional AI principles
2. **Evidence Based**: Decisions backed by telemetry data
3. **Human in Loop**: Uncertain actions require human approval
4. **Minimal Intervention**: Prefer smallest effective action
5. **Continuous Learning**: Track outcomes for improvement

---

## 2. Component Architecture

### 2.1 Core Components

| Component | Technology | Purpose | Port |
|-----------|------------|---------|------|
| Fast Annotator | Qwen3-8B via llama.cpp | Real-time anomaly detection | 8081 |
| Reasoning Agent | Qwen3-14B via llama.cpp | Complex RCA & chat | 8082 |
| Model Proxy | llama-swap | Model hot-swapping | 8080 |
| Backend API | FastAPI | REST & WebSocket API | 8000 |
| Frontend | React + Vite | User interface | 5173 |
| Graph Memory | Neo4j | Incident correlation | 7474/7687 |
| Time Series | InfluxDB | Metrics storage | 8086 |

### 2.2 Observability Components

| Component | Technology | Purpose | Port |
|-----------|------------|---------|------|
| Collector | OpenTelemetry | Telemetry aggregation | 4317/4318 |
| Logs | Loki | Log storage & query | 3100 |
| Traces | Tempo | Distributed tracing | 3200 |
| Metrics | Prometheus | Metrics collection | 9090 |
| Visualization | Grafana | Dashboards | 3000 |

### 2.3 Test Environment

| Component | Technology | Purpose | Port |
|-----------|------------|---------|------|
| Nextcloud App | Nextcloud | Test application | 8080 |
| Database | MariaDB | Test database | 3306 |
| Cache | Redis | Test cache | 6379 |
| Proxy | Nginx | (bundled) | - |
| Background | Cron | Test worker | - |

---

## 3. Data Flow

### 3.1 Telemetry Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TELEMETRY FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SERVICE                    COLLECTOR              STORAGE          │
│  ───────                    ─────────              ───────          │
│                                                                     │
│  Nextcloud ─┐                                                       │
│  MariaDB  ──┼─► OTLP ─────► OpenTelemetry ─────┬─► Loki (logs)     │
│  Redis    ──┤    Protocol    Collector         ├─► Tempo (traces)  │
│  Nginx    ──┤                   │              └─► Prometheus      │
│  Cron     ──┘                   │                  (metrics)       │
│                                 │                                   │
│                                 ▼                                   │
│                          Batch Processing                           │
│                          (5s batches)                               │
│                                 │                                   │
│                                 ▼                                   │
│                       Telemetry Aggregator                          │
│                                 │                                   │
│                                 ▼                                   │
│                        Fast Annotator (8B)                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ANALYSIS FLOW                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TELEMETRY              FAST AGENT (8B)           RESULT            │
│  ─────────              ───────────────           ──────            │
│                                                                     │
│  {                      ┌─────────────────┐                         │
│    logs: [...],         │ Anomaly Check   │                         │
│    metrics: {...},  ───►│ Classification  │───► confidence ≥ 0.7?  │
│    traces: [...]        │ Confidence Calc │           │             │
│  }                      └─────────────────┘           │             │
│                                                       │             │
│                         ┌─────────────────────────────┼─────────┐   │
│                         │                             │         │   │
│                         ▼                             ▼         │   │
│                  ┌──────────────┐            ┌──────────────┐   │   │
│                  │ Direct Route │            │ Reasoning    │   │   │
│                  │ to Validator │            │ Agent (14B)  │   │   │
│                  └──────────────┘            └──────────────┘   │   │
│                         │                             │         │   │
│                         │                             │         │   │
│                         └──────────────┬──────────────┘         │   │
│                                        │                        │   │
│                                        ▼                        │   │
│                              Constitutional Validator           │   │
│                                        │                        │   │
│                         ┌──────────────┼──────────────┐         │   │
│                         ▼              ▼              ▼         │   │
│                    APPROVED      NEEDS APPROVAL   REJECTED      │   │
│                         │              │              │         │   │
│                         ▼              ▼              ▼         │   │
│                    Execute       Queue for        Log &         │   │
│                    Action        Human Review     Alert         │   │
│                                                                 │   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Chat Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CHAT FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  USER                  BACKEND                  REASONING AGENT     │
│  ────                  ───────                  ───────────────     │
│                                                                     │
│  "Why is the          WebSocket               Record Activity       │
│   database slow?"  ──► Connection ──────────► (keeps 14B loaded)   │
│                            │                                        │
│                            ▼                                        │
│                     Complexity Check                                │
│                            │                                        │
│               ┌────────────┴────────────┐                          │
│               ▼                         ▼                          │
│         Simple Query              Complex Query                     │
│         /no_think                 /think                           │
│               │                         │                          │
│               └────────────┬────────────┘                          │
│                            │                                        │
│                            ▼                                        │
│                    Reasoning Agent (14B)                           │
│                            │                                        │
│               ┌────────────┴────────────┐                          │
│               ▼                         ▼                          │
│         Direct Response         Thinking Process                    │
│         (~500ms)                + Response (2-10s)                 │
│               │                         │                          │
│               └────────────┬────────────┘                          │
│                            │                                        │
│                            ▼                                        │
│                     WebSocket Response                              │
│                            │                                        │
│  {                         │                                        │
│    thinking: "...",   ◄────┘                                        │
│    response: "The database is slow because..."                     │
│  }                                                                  │
│                                                                     │
│  ─────────────────────────────────────────────────────────────     │
│  TIMEOUT: 1 minute after last message → swap back to 8B            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Model Architecture

### 4.1 VRAM Allocation Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    T4 16GB VRAM ALLOCATION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NORMAL STATE (95% of operation time):                              │
│  ════════════════════════════════════                              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    VRAM (16GB)                              │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  Qwen3-8B Q4_K_M          │  KV Cache    │     FREE        │    │
│  │      (~5.5GB)             │  (~1GB)      │   (~9.5GB)      │    │
│  │                           │  8K context  │                 │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Purpose: Fast annotation, anomaly detection                        │
│  Latency: <100ms per inference                                      │
│                                                                     │
│  ─────────────────────────────────────────────────────────────     │
│                                                                     │
│  RCA/CHAT STATE (on-demand, ~5% of time):                          │
│  ════════════════════════════════════════                          │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    VRAM (16GB)                              │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  Qwen3-14B Q4_K_M              │  KV Cache  │    FREE      │    │
│  │      (~9.5GB)                  │  (~1.5GB)  │   (~5GB)     │    │
│  │                                │ 4K context │              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Purpose: Complex RCA, human chat                                   │
│  Latency: ~500ms (no think), 2-10s (with think)                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────     │
│                                                                     │
│  RAM PRE-CACHE (always):                                           │
│  ══════════════════════                                            │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    RAM (32GB)                               │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  Qwen3-14B (mmap)  │    OS    │        Buffer             │    │
│  │     (~9GB)         │  (~8GB)  │       (~15GB)             │    │
│  │                    │          │                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Enables: ~2-3s swap time (vs 30s+ from disk)                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Model Swap Timing

| Transition | Time | Method |
|------------|------|--------|
| 8B → 14B | ~2-3s | Pre-cached in RAM |
| 14B → 8B | ~1s | Smaller model, faster |
| Cold start (disk) | ~30-60s | Avoided by pre-caching |

### 4.3 Thinking Mode Logic

```python
# Thinking mode is enabled for:
COMPLEX_PATTERNS = [
    "root cause",           # RCA queries
    "why.*fail",           # Failure analysis
    "cascade",             # Cascade failures
    "correlat",            # Correlation analysis
    "multiple.*service",   # Multi-service issues
    "explain.*step",       # Step-by-step explanations
    "compare",             # Comparisons
    "trade.?off",          # Trade-off analysis
    "plan|strategy",       # Planning
]

# Thinking mode is disabled for:
SIMPLE_PATTERNS = [
    "^(what|who|when|where)\\s+is\\b",  # Simple factual
    "^status",             # Status checks
    "^list",               # List commands
    "^show",               # Show commands
    "^restart",            # Action commands
    "^current",            # Current state
]

# Context triggers (override patterns):
if affected_services > 3:
    enable_thinking = True
if incident_severity == "critical":
    enable_thinking = True
```

---

## 5. Memory Architecture

### 5.1 Neo4j Graph Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NEO4J GRAPH SCHEMA                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NODE TYPES:                                                        │
│  ───────────                                                        │
│                                                                     │
│  (Service)                    (Incident)                            │
│  ├── name: string             ├── id: string                        │
│  ├── type: string             ├── timestamp: datetime               │
│  ├── criticality: int         ├── severity: string                  │
│  ├── replicas: int            ├── status: string                    │
│  └── metadata: map            ├── root_cause: string                │
│                               ├── resolution: string                │
│                               └── confidence: float                 │
│                                                                     │
│  (Action)                     (Metric)                              │
│  ├── id: string               ├── name: string                      │
│  ├── type: string             ├── value: float                      │
│  ├── timestamp: datetime      ├── timestamp: datetime               │
│  ├── confidence: float        └── service: string                   │
│  ├── outcome: string                                                │
│  └── rollback_available: bool                                       │
│                                                                     │
│  ─────────────────────────────────────────────────────────────     │
│                                                                     │
│  RELATIONSHIPS:                                                     │
│  ──────────────                                                     │
│                                                                     │
│  (Service)-[:DEPENDS_ON]->(Service)                                │
│      └── criticality: int                                          │
│                                                                     │
│  (Incident)-[:AFFECTS]->(Service)                                  │
│      └── impact_score: float                                       │
│                                                                     │
│  (Incident)-[:SIMILAR_TO]->(Incident)                              │
│      └── similarity: float                                         │
│                                                                     │
│  (Incident)-[:RESOLVED_BY]->(Action)                               │
│      └── effectiveness: float                                      │
│                                                                     │
│  (Action)-[:TARGETS]->(Service)                                    │
│                                                                     │
│  ─────────────────────────────────────────────────────────────     │
│                                                                     │
│  EXAMPLE GRAPH:                                                     │
│                                                                     │
│           ┌─────────────┐                                          │
│           │ nextcloud-  │                                          │
│           │    app      │                                          │
│           └──────┬──────┘                                          │
│                  │ DEPENDS_ON                                       │
│         ┌────────┼────────┐                                        │
│         ▼        ▼        ▼                                        │
│  ┌──────────┐ ┌──────┐ ┌──────────┐                               │
│  │nextcloud-│ │redis │ │nextcloud-│                               │
│  │   db     │ │      │ │  nginx   │                               │
│  └──────────┘ └──────┘ └──────────┘                               │
│         ▲                                                          │
│         │ AFFECTS                                                   │
│  ┌──────┴───────┐      ┌─────────────┐                            │
│  │ INC-20251206 │──────│ ACT-restart │                            │
│  │ DB Timeout   │ RESOLVED_BY        │                            │
│  └──────────────┘      └─────────────┘                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Query Patterns

```cypher
// Find similar incidents
MATCH (i:Incident)-[:AFFECTS]->(s:Service)<-[:AFFECTS]-(similar:Incident)
WHERE i.id = $incident_id
  AND similar.status = 'resolved'
RETURN similar, 
       count(s) as shared_services,
       similar.resolution as resolution
ORDER BY shared_services DESC
LIMIT 5

// Get service dependencies
MATCH path = (s:Service {name: $service_name})-[:DEPENDS_ON*1..3]->(dep:Service)
RETURN path

// Find effective resolutions
MATCH (i:Incident)-[:RESOLVED_BY]->(a:Action)
WHERE i.root_cause CONTAINS $pattern
  AND a.outcome = 'success'
RETURN a.type, count(*) as success_count
ORDER BY success_count DESC
```

---

## 6. API Architecture

### 6.1 REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness probe |
| GET | `/live` | Liveness probe |
| GET | `/api/status` | System status |
| GET | `/api/status/models` | Model status |
| POST | `/api/chat` | HTTP chat |
| WS | `/api/chat/ws/{session}` | WebSocket chat |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{id}` | Get incident |
| POST | `/api/actions` | Execute action |
| GET | `/api/telemetry/summary` | Telemetry summary |

### 6.2 WebSocket Protocol

```json
// Client → Server
{
  "type": "message",
  "content": "Why is the database slow?",
  "enable_thinking": true
}

// Server → Client (status)
{
  "type": "status",
  "content": "thinking"
}

// Server → Client (thinking)
{
  "type": "thinking",
  "content": "Analyzing database metrics..."
}

// Server → Client (response)
{
  "type": "response",
  "content": "The database is slow because...",
  "model": "reasoning-agent",
  "latency_ms": 1234.56
}

// Server → Client (error)
{
  "type": "error",
  "content": "Error message"
}
```

---

## 7. Security Architecture

### 7.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AUTHENTICATION:                                                    │
│  ───────────────                                                    │
│  • JWT tokens for API access                                        │
│  • Session management for WebSocket                                 │
│  • API key for service-to-service                                   │
│                                                                     │
│  AUTHORIZATION:                                                     │
│  ──────────────                                                     │
│  • Role-based access control (RBAC)                                │
│  • Roles: admin, operator, viewer                                  │
│  • Action approval based on confidence + role                       │
│                                                                     │
│  DATA PROTECTION:                                                   │
│  ────────────────                                                   │
│  • TLS 1.3 for all connections                                     │
│  • Encryption at rest for Neo4j/InfluxDB                           │
│  • No credential logging (P1.5 principle)                          │
│  • Audit trail for all actions                                     │
│                                                                     │
│  CONSTITUTIONAL SAFETY:                                             │
│  ──────────────────────                                            │
│  • Tier 1 principles never bypassed                                │
│  • All actions logged and auditable                                │
│  • Reversibility requirement enforced                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Compliance

| Standard | Status | Notes |
|----------|--------|-------|
| HIPAA | Ready | No PHI stored, audit trails |
| ISO 27001 | Ready | Security controls documented |
| SOC 2 | Partial | Requires external audit |
| GDPR | Ready | No personal data processed |

---

## 8. Deployment Architecture

### 8.1 Local Development

```
┌─────────────────────────────────────────────────────────────────────┐
│                  LOCAL DEVELOPMENT STACK                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  HOST MACHINE (No GPU required)                                     │
│  ─────────────────────────────                                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Docker Compose                            │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │Nextcloud │ │ MariaDB  │ │  Redis   │ │   Cron   │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │   Loki   │ │  Tempo   │ │Prometheus│ │ Grafana  │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │
│  │  │  Neo4j   │ │ InfluxDB │ │ Mock LLM │ ◄── Returns        │   │
│  │  └──────────┘ └──────────┘ └──────────┘     canned         │   │
│  │                                              responses      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  LOCAL PROCESSES:                                                   │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │ FastAPI      │  │ Vite (React) │                                │
│  │ (hot reload) │  │ (hot reload) │                                │
│  └──────────────┘  └──────────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 AWS GPU Testing

```
┌─────────────────────────────────────────────────────────────────────┐
│                  AWS GPU TESTING STACK                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AWS g4dn.xlarge (T4 16GB, 4 vCPU, 16GB RAM)                       │
│  ────────────────────────────────────────────                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Docker Compose (GPU)                      │   │
│  │                                                              │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │              llama-swap (GPU)                        │    │   │
│  │  │  ┌──────────────┐    ┌──────────────┐               │    │   │
│  │  │  │ Qwen3-8B     │◄──►│ Qwen3-14B    │               │    │   │
│  │  │  │ (fast-agent) │    │ (reasoning)  │               │    │   │
│  │  │  └──────────────┘    └──────────────┘               │    │   │
│  │  └─────────────────────────────────────────────────────┘    │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │Nextcloud │ │ MariaDB  │ │  Redis   │ │   Cron   │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │   Loki   │ │  Tempo   │ │Prometheus│ │ Grafana  │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  │                                                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │  Neo4j   │ │ InfluxDB │ │ Backend  │ │ Frontend │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  COST: ~$0.16-0.20/hour (Spot)                                     │
│  REMEMBER: Stop instance when not in use!                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Production Deployment

```
┌─────────────────────────────────────────────────────────────────────┐
│                 PRODUCTION DEPLOYMENT (Self-Hosted)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CUSTOMER HARDWARE REQUIREMENTS:                                    │
│  ───────────────────────────────                                   │
│  • GPU: 16GB VRAM minimum (T4, RTX 4060 Ti 16GB, RTX 3060 12GB)   │
│  • RAM: 32GB minimum                                               │
│  • Storage: 100GB SSD                                              │
│  • CPU: 4+ cores                                                   │
│                                                                     │
│  DEPLOYMENT:                                                        │
│  ───────────                                                        │
│  $ git clone https://github.com/org/constitutional-aiops           │
│  $ cd constitutional-aiops                                         │
│  $ ./scripts/install.sh    # Downloads models, configures system   │
│  $ docker-compose up -d    # Starts all services                   │
│                                                                     │
│  SINGLE DOCKER-COMPOSE:                                            │
│  ──────────────────────                                            │
│  • All services in one file                                        │
│  • Automatic hardware detection                                     │
│  • Self-contained (no external dependencies)                       │
│  • HIPAA/ISO 27001 compliant package                               │
│                                                                     │
│  CUSTOMER SUPPORT:                                                  │
│  ─────────────────                                                 │
│  • Installation documentation                                       │
│  • Troubleshooting guide                                           │
│  • Email/ticket support                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Hardware Compatibility Matrix

| GPU | VRAM | Compatible | Notes |
|-----|------|------------|-------|
| NVIDIA T4 | 16GB | ✅ Yes | Primary development target |
| NVIDIA RTX 4060 Ti | 16GB | ✅ Yes | Consumer option |
| NVIDIA RTX 3060 | 12GB | ⚠️ Limited | May need smaller context |
| NVIDIA RTX 4090 | 24GB | ✅ Yes | Can run both models |
| NVIDIA A10 | 24GB | ✅ Yes | Cloud option |
| NVIDIA A100 | 40/80GB | ✅ Yes | Enterprise option |
| AMD GPUs | Various | ❌ No | ROCm not tested |
| Apple Silicon | Various | ❌ No | Not supported |

## Appendix B: Port Reference

| Port | Service | Protocol |
|------|---------|----------|
| 3000 | Grafana | HTTP |
| 3100 | Loki | HTTP |
| 3200 | Tempo | HTTP/gRPC |
| 4317 | OTEL Collector | gRPC |
| 4318 | OTEL Collector | HTTP |
| 5173 | Frontend (dev) | HTTP |
| 7474 | Neo4j Browser | HTTP |
| 7687 | Neo4j Bolt | Bolt |
| 8000 | Backend API | HTTP/WS |
| 8080 | llama-swap | HTTP |
| 8081 | Fast Agent | HTTP |
| 8082 | Reasoning Agent | HTTP |
| 8086 | InfluxDB | HTTP |
| 9090 | Prometheus | HTTP |

---

**Last Updated**: 2025-12-06
**Version**: 0.1.0-alpha
