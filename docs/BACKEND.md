# Backend Architecture

> **Version**: 0.4.0
> **Last Updated**: 2025-12-30
> **Framework**: FastAPI (Python 3.11+)
> **Source of Truth**: [KEY_METRICS.md](KEY_METRICS.md)

---

## Overview

The Constitutional AIOps backend is a FastAPI application providing:

- **Dual-Agent LLM System**: Qwen3-4B (fast) + Qwen3-14B (reasoning)
- **Constitutional AI Validation**: 11 principles across 3 tiers
- **Graph-Episodic Memory**: Neo4j-based incident correlation
- **Real-time Events**: WebSocket streaming for UI updates
- **LGTM Stack Integration**: Loki, Grafana, Tempo, Prometheus

---

## Module Reference

### Core (src/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `main.py` | FastAPI app entry, lifespan management, WebSocket endpoint | `app`, `lifespan()` |
| `config.py` | Environment-based configuration classes | `Config`, `config` singleton |
| `__init__.py` | Package version (`0.1.0`) | `__version__` |

#### main.py Details
- **Lifespan**: Initializes ModelRouter, agents, validator, Neo4j, telemetry, MCP server
- **Routes**: 11 routers mounted at `/api/v1`
- **WebSocket**: `/ws` endpoint for real-time event streaming
- **CORS**: Configurable origins from environment

#### config.py Classes
| Class | Purpose |
|-------|---------|
| `LLMConfig` | Dual-model endpoints (ports 8081, 8082), timeouts, model names |
| `Neo4jConfig` | Graph database URI, credentials |
| `ObservabilityConfig` | LGTM stack URLs |
| `ConstitutionalConfig` | Confidence thresholds (0.90 auto, 0.70 approval) |
| `AppConfig` | Server host/port, logging, CORS |

---

### Agents (src/agents/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `base_agent.py` | Abstract base class for agents | `BaseAgent`, `AgentRole`, `ConfidenceLevel`, `AgentResponse` |
| `model_router.py` | Dual-endpoint HTTP routing | `ModelRouter` |
| `fast_annotator.py` | Telemetry annotation (Qwen3-4B) | `FastAnnotator` |
| `reasoning_agent.py` | RCA/planning/chat (Qwen3-14B) | `ReasoningAgent` |
| `__init__.py` | Module exports | All above |

#### base_agent.py Enums
```python
class AgentRole(Enum):
    FAST_ANNOTATOR = "fast_annotator"
    REASONING = "reasoning"
    CHAT = "chat"

class ConfidenceLevel(Enum):
    HIGH = "high"      # >0.90
    MEDIUM = "medium"  # 0.70-0.90
    LOW = "low"        # <0.70
```

#### model_router.py
- **No Hot-Swap**: Both models always loaded (24GB VRAM)
- **Fast Agent**: Port 8081, <100ms P95 latency, 512 max tokens
- **Reasoning Agent**: Port 8082, 200-500ms P95 latency, 2048 max tokens
- **Methods**: `fast_completion()`, `reasoning_completion()`, `health_check()`

#### fast_annotator.py
- **Model**: Qwen3-4B Q4_K_M
- **Purpose**: Telemetry annotation, anomaly detection, classification
- **Output Fields**: `anomaly_detected`, `severity`, `category`, `confidence`, `summary`, `needs_reasoning`, `key_indicators`
- **Statistics**: Tracks requests, latency, success/error rates

#### reasoning_agent.py
- **Model**: Qwen3-14B Q4_K_M
- **Modes**: RCA analysis, remediation planning, human chat
- **System Prompts**: 3 specialized prompts (RCA, CHAT, PLANNING)
- **Service Knowledge**: Pre-built context for 6 services
- **RCA Output**: `root_cause`, `causal_chain`, `impact`, `confidence`, `remediation_steps`
- **Planning Output**: `plan_name`, `steps[]`, `rollback_plan`, `success_criteria`

---

### API Routes (src/api/routes/)

| File | Prefix | Purpose |
|------|--------|---------|
| `health.py` | `/health` | System health, readiness, liveness probes |
| `chat.py` | `/chat` | Interactive chat, RCA/planning analysis |
| `incidents.py` | `/incidents` | Incident CRUD, RCA triggering |
| `actions.py` | `/actions` | Action validation, approval, execution |
| `tools.py` | `/tools` | MCP tools REST API |
| `agents.py` | `/agents` | Agent activity and statistics |
| `telemetry.py` | `/telemetry` | LGTM stack queries |
| `graph.py` | `/graph` | Neo4j episodic memory queries |
| `prompts.py` | `/prompts` | System prompt management |
| `infrastructure.py` | `/infrastructure` | Docker container monitoring |
| `demo.py` | `/demo` | Anomaly injection for demos |
| `__init__.py` | - | Route exports |

See [API.md](API.md) for endpoint documentation.

---

### API Schemas (src/api/schemas/)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `chat.py` | Chat request/response models | `ChatRequest`, `ChatResponse`, `AnalysisRequest`, `ConversationHistory` |
| `incident.py` | Incident lifecycle models | `Incident`, `IncidentCreate`, `RCAResult`, `RemediationPlan` |
| `action.py` | Action workflow models | `Action`, `ActionCreate`, `ActionApproval`, `ConstitutionalValidation` |
| `__init__.py` | Schema exports | All above |

#### Key Enums
```python
# incident.py
class IncidentSeverity(Enum): critical, high, medium, low, info
class IncidentStatus(Enum): detecting, analyzing, pending_approval, remediating, resolved, closed
class IncidentCategory(Enum): performance, error, security, resource, availability, configuration, unknown

# action.py
class ActionType(Enum): restart_service, scale_up, scale_down, rollback, modify_config, clear_cache, kill_process, block_ip, rotate_credentials, custom
class ActionStatus(Enum): pending, validating, approved, rejected, awaiting_approval, executing, completed, failed, cancelled, expired
class AuthorizationLevel(Enum): automatic, approval_required, alert_only
```

---

### Constitutional AI (src/constitutional/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `principles.py` | 11 principles, 3 tiers | `Principle`, `PrincipleTier`, `ALL_PRINCIPLES`, `get_principle()` |
| `validator.py` | Action validation engine | `ConstitutionalValidator`, `ValidationReport`, `AuthorizationLevel` |
| `__init__.py` | Module exports | All above |

#### Principle Tiers

| Tier | Violation Action | Principles |
|------|------------------|------------|
| **Tier 1 (Safety)** | BLOCK | P1.1 Data Protection, P1.2 Active Incident Safety, P1.3 Cascade Prevention, P1.4 Security Integrity |
| **Tier 2 (Operational)** | REQUIRE_APPROVAL | P2.1 Minimal Intervention, P2.2 Evidence-Based Actions, P2.3 Audit Trail, P2.4 Uncertainty Escalation |
| **Tier 3 (Learning)** | LOG_WARNING | P3.1 Outcome Tracking, P3.2 Human Correction Learning, P3.3 Long-term Optimization |

#### Authorization Matrix
| Confidence | Authorization Level | Action |
|------------|---------------------|--------|
| ≥0.90 | AUTOMATIC | Execute without approval |
| 0.70-0.89 | APPROVAL_REQUIRED | Human must approve |
| <0.70 | ALERT_ONLY | Notify only, no execution |

---

### Memory (src/memory/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `neo4j_client.py` | Graph database operations | `Neo4jClient`, `get_neo4j_client()` |
| `episode_store.py` | Episodic memory for incidents | `Episode`, `EpisodeStore` |
| `retrieval.py` | RAG context retrieval | `RetrievalContext`, `ContextRetriever` |
| `__init__.py` | Module exports | All above |

#### neo4j_client.py Operations
- **Incident**: `create_incident()`, `update_incident()`, `find_similar_incidents()`
- **Action**: `create_action()`, `link_action_to_incident()`, `record_action_outcome()`
- **Service Graph**: `create_service_dependency()`, `get_service_dependencies()`, `get_affected_by_service()`
- **Analytics**: `get_incident_stats()`, `get_action_success_rate()`

#### episode_store.py
- **Episode Dataclass**: Complete incident lifecycle (detection → resolution)
- **Similarity Matching**: Category (30%) + Service overlap (40%) + Root cause type (30%)
- **Hybrid Storage**: In-memory + Neo4j with fallback

#### retrieval.py (RAG)
- **retrieve_for_incident()**: Full context for incident analysis
- **retrieve_for_rca()**: Formatted context for RCA prompt injection
- **retrieve_for_planning()**: Previously successful actions + impact assessment

---

### Telemetry (src/telemetry/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `collector.py` | LGTM stack data collection | `TelemetryCollector`, `LogEntry`, `MetricPoint`, `TraceSpan`, `TelemetryWindow` |
| `compressor.py` | Token compression for LLM context | `TokenCompressor`, `CompressedTelemetry` |
| `aggregator.py` | Health scoring, incident context | `TelemetryAggregator`, `AggregatedMetrics`, `ServiceHealth`, `IncidentContext` |
| `__init__.py` | Module exports | All above |

#### collector.py Methods
- `query_logs()`: Loki LogQL queries (nanosecond precision)
- `query_metrics()`: Prometheus PromQL (rate, p99, error_rate, memory, CPU)
- `query_traces()`: Tempo trace search by service/tags
- `collect_window()`: Gather logs + metrics + traces for time range

#### compressor.py Strategies
- **Level 1**: Log deduplication (regex normalization, remove timestamps/UUIDs)
- **Level 2**: Metric aggregation (statistical summaries)
- **Level 3**: Trace sampling (top slow operations, error traces)
- **Token Targets**: Fast agent ~500, Reasoning agent ~1500

---

### MCP (src/mcp/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `server.py` | Model Context Protocol tool server | `MCPActionServer` |
| `tools/__init__.py` | Tool definitions | Tool schemas |
| `__init__.py` | Module exports | All above |

#### Available Tools
| Tool | Category | Requires Approval |
|------|----------|-------------------|
| `find_similar` | Query | No |
| `get_dependencies` | Query | No |
| `restart_service` | Action | Yes |
| `scale_service` | Action | Yes |
| `analyze_logs` | Analysis | No |

---

### Utils (src/utils/)

| File | Purpose | Key Exports |
|------|---------|-------------|
| `logging.py` | Logging configuration | `setup_logging()` |
| `audit.py` | Action audit trail tracking | Audit functions |
| `websocket.py` | Real-time event streaming | `WebSocketManager`, `EventType`, `WebSocketEvent` |
| `__init__.py` | Module exports | All above |

#### websocket.py Event Types
```python
class EventType(Enum):
    CONNECTED, PING, PONG
    INCIDENT_CREATED, INCIDENT_UPDATED, INCIDENT_RESOLVED, INCIDENT_DELETED
    ACTION_CREATED, ACTION_APPROVED, ACTION_REJECTED, ACTION_EXECUTED, ACTION_FAILED
    RCA_STARTED, RCA_COMPLETED, REMEDIATION_PLANNED
    SYSTEM_HEALTH, AGENT_STATUS, ALERT
```

---

## Startup Sequence

```python
# main.py lifespan()
1. ModelRouter() - Initialize dual-endpoint HTTP clients
2. FastAnnotator(router) - Create fast agent wrapper
3. ReasoningAgent(router) - Create reasoning agent wrapper
4. ConstitutionalValidator() - Load 11 principles
5. Neo4jClient() - Connect to graph database
6. EpisodeStore(neo4j) - Initialize episodic memory
7. ContextRetriever(store, neo4j) - Initialize RAG
8. TelemetryCollector() - Connect to LGTM stack
9. TokenCompressor() - Initialize compression
10. MCPActionServer() - Initialize tool server
11. WebSocketManager() - Initialize event streaming
12. Mount 11 routers at /api/v1
```

---

## Dependencies

### External Libraries
| Library | Purpose |
|---------|---------|
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| httpx | Async HTTP client |
| neo4j | Graph database driver |
| pydantic | Data validation |
| python-dotenv | Environment loading |
| loguru | Logging |
| docker | Container discovery |

### Internal Dependencies
```
main.py
├── config.py
├── agents/
│   ├── model_router.py
│   ├── fast_annotator.py (→ base_agent.py, model_router.py)
│   └── reasoning_agent.py (→ base_agent.py, model_router.py)
├── constitutional/
│   ├── principles.py
│   └── validator.py (→ principles.py, config.py)
├── memory/
│   ├── neo4j_client.py (→ config.py)
│   ├── episode_store.py (→ neo4j_client.py)
│   └── retrieval.py (→ episode_store.py, neo4j_client.py)
├── telemetry/
│   ├── collector.py (→ config.py)
│   ├── compressor.py
│   └── aggregator.py (→ collector.py)
├── mcp/
│   └── server.py (→ episode_store.py, neo4j_client.py, validator.py)
└── utils/
    ├── logging.py
    ├── audit.py
    └── websocket.py
```

---

## Configuration

### Environment Variables
```bash
# LLM Endpoints
FAST_AGENT_URL=http://localhost:8081/v1
REASONING_AGENT_URL=http://localhost:8082/v1
FAST_AGENT_MODEL=qwen3:4b
REASONING_AGENT_MODEL=qwen3:14b

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=constitutional_aiops_2025

# Observability
LOKI_URL=http://localhost:3100
PROMETHEUS_URL=http://localhost:9090
TEMPO_URL=http://localhost:3200

# Constitutional AI
CONFIDENCE_THRESHOLD_AUTO=0.90
CONFIDENCE_THRESHOLD_APPROVAL=0.70

# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

---

## Performance Targets (From Research_V5.tex)

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
C(a) = α · C_LLM(a) + β · C_hist(a) + γ · C_sim(a)

Where:
  α = 0.4  (LLM confidence weight)
  β = 0.35 (Historical success rate)
  γ = 0.25 (Similarity to past incidents)
```

---

**See Also**:
- [KEY_METRICS.md](KEY_METRICS.md) - Complete metrics reference
- [API.md](API.md) - REST API reference
- [FRONTEND.md](FRONTEND.md) - React frontend documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
