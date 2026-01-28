# API Reference

> **Version**: 0.6.1
> **Last Updated**: 2026-01-27
> **Base URL**: `/api/v1`

---

## Overview

The Constitutional AIOps API provides REST endpoints for:
- System health monitoring
- Incident management with RCA
- Action validation and approval workflows
- Interactive chat with Reasoning Agent
- Telemetry queries (LGTM stack)
- Graph memory exploration
- Infrastructure monitoring

---

## Authentication

Currently no authentication required (development mode). Production should add:
- API key authentication
- JWT tokens for user sessions
- RBAC for action approvals

---

## Endpoints

### Health (`/health`)

#### GET /health
Comprehensive system health check.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-12-27T10:00:00Z",
  "version": "0.1.0",
  "components": {
    "fast_agent": {"healthy": true, "latency_ms": 45},
    "reasoning_agent": {"healthy": true, "latency_ms": 180},
    "neo4j": {"healthy": true, "latency_ms": 12}
  },
  "uptime_seconds": 3600
}
```

#### GET /health/ready
Kubernetes readiness probe.

**Response** `200 OK`
```json
{
  "ready": true,
  "checks_passed": ["fast_agent", "reasoning_agent"],
  "checks_failed": []
}
```

#### GET /health/live
Kubernetes liveness probe.

**Response** `200 OK`
```json
{
  "alive": true,
  "timestamp": "2025-12-27T10:00:00Z"
}
```

#### GET /health/agents
Detailed agent configuration and status.

**Response** `200 OK`
```json
{
  "fast_agent": {
    "model": "qwen3:4b",
    "url": "http://localhost:8081/v1",
    "status": "healthy",
    "latency_ms": 45
  },
  "reasoning_agent": {
    "model": "qwen3:14b",
    "url": "http://localhost:8082/v1",
    "status": "healthy",
    "latency_ms": 180
  }
}
```

---

### Chat (`/chat`)

#### POST /chat
Send message to Reasoning Agent.

**Request**
```json
{
  "message": "What caused the database slowdown?",
  "conversation_id": "conv-123",
  "context": {"incident_id": "INC-2025-001"},
  "enable_thinking": false
}
```

**Response** `200 OK`
```json
{
  "conversation_id": "conv-123",
  "message": "Based on the telemetry data, the database slowdown was caused by...",
  "confidence": 0.85,
  "suggested_actions": ["restart_service", "scale_up"],
  "related_incidents": ["INC-2025-002"],
  "metadata": {"tokens_used": 450, "latency_ms": 1200}
}
```

#### POST /chat/analyze
Run RCA or planning analysis.

**Request**
```json
{
  "mode": "rca",
  "data": {
    "logs": ["ERROR: Connection timeout..."],
    "metrics": {"cpu": 95, "memory": 80},
    "affected_services": ["backend", "database"]
  },
  "enable_thinking": true
}
```

**Response** `200 OK`
```json
{
  "analysis_id": "ana-456",
  "mode": "rca",
  "result": {
    "root_cause": "Database connection pool exhaustion",
    "causal_chain": ["High traffic", "Connection pool full", "Timeout errors"],
    "confidence": 0.88,
    "remediation_steps": [
      {"action": "Increase connection pool size", "risk": "low"},
      {"action": "Add read replicas", "risk": "medium"}
    ]
  },
  "processing_time_ms": 2500,
  "requires_approval": false
}
```

#### GET /chat/conversations
List all conversations.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 20 | Max results |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`
```json
{
  "conversations": [
    {"id": "conv-123", "created_at": "...", "message_count": 5}
  ],
  "total": 15
}
```

#### GET /chat/conversations/{id}
Get full conversation history.

#### DELETE /chat/conversations/{id}
Delete conversation.

---

### Incidents (`/incidents`)

#### POST /incidents
Create new incident.

**Request**
```json
{
  "title": "Database connection timeout",
  "description": "Multiple services reporting database timeouts",
  "severity": "critical",
  "category": "performance",
  "affected_services": [
    {"name": "backend", "namespace": "production"}
  ],
  "source": "prometheus-alert",
  "auto_analyze": true
}
```

**Response** `201 Created`
```json
{
  "id": "INC-2025-001",
  "title": "Database connection timeout",
  "status": "analyzing",
  "severity": "critical",
  "created_at": "2025-12-27T10:00:00Z"
}
```

#### GET /incidents
List incidents with filtering.

**Query Parameters**
| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| status | string | detecting, analyzing, pending_approval, remediating, resolved, closed | Filter by status |
| severity | string | critical, high, medium, low, info | Filter by severity |
| category | string | performance, error, security, resource, availability, configuration | Filter by category |
| service | string | - | Filter by affected service |
| search | string | - | Search in title/description |
| limit | int | 20 | Max results |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`
```json
{
  "items": [...],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

#### GET /incidents/stats
Incident statistics.

**Response** `200 OK`
```json
{
  "by_status": {"open": 5, "resolved": 40},
  "by_severity": {"critical": 3, "high": 12, "medium": 20},
  "by_category": {"performance": 15, "error": 20},
  "mean_time_to_resolution": 1800,
  "auto_resolved_count": 25,
  "approval_required_count": 8
}
```

#### GET /incidents/{id}
Get incident details including RCA and remediation plan.

#### PATCH /incidents/{id}
Update incident fields.

**Request**
```json
{
  "status": "resolved",
  "resolution_notes": "Increased connection pool size"
}
```

#### DELETE /incidents/{id}
Soft delete incident.

#### POST /incidents/{id}/analyze
Trigger RCA analysis on existing incident.

**Response** `200 OK`
```json
{
  "incident_id": "INC-2025-001",
  "rca": {
    "root_cause": "...",
    "confidence": 0.85
  },
  "analysis_time_ms": 2100
}
```

#### GET /incidents/{id}/similar
Find similar incidents from Neo4j.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 5 | Max results |
| min_similarity | float | 0.5 | Minimum similarity score |

---

### Actions (`/actions`)

#### POST /actions
Create action with Constitutional AI validation.

**Request**
```json
{
  "action_type": "restart_service",
  "description": "Restart backend service to clear connection pool",
  "target_service": "backend",
  "target_instance": "backend-prod-1",
  "parameters": {"graceful": true},
  "incident_id": "INC-2025-001",
  "confidence": 0.85,
  "evidence": {"logs": [...], "metrics": {...}}
}
```

**Response** `201 Created`
```json
{
  "id": "ACT-2025-001",
  "status": "awaiting_approval",
  "requires_approval": true,
  "validation": {
    "passed": true,
    "authorization_level": "approval_required",
    "confidence": 0.85,
    "tier1_passed": true,
    "tier2_passed": true,
    "tier3_passed": true,
    "violations": [],
    "warnings": ["Action affects production service"],
    "explanation": "Medium confidence requires human approval"
  },
  "expires_at": "2025-12-27T14:00:00Z"
}
```

#### GET /actions
List actions with filters.

**Query Parameters**
| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| status | string | pending, approved, rejected, executing, completed, failed | Filter by status |
| action_type | string | restart_service, scale_up, etc. | Filter by type |
| target_service | string | - | Filter by target |
| incident_id | string | - | Filter by incident |
| requires_approval | bool | - | Filter approval-required |

#### GET /actions/pending
Get all actions awaiting approval.

**Response** `200 OK`
```json
{
  "count": 3,
  "actions": [...],
  "oldest_pending": "2025-12-27T09:00:00Z",
  "urgency_breakdown": {"critical": 1, "high": 2}
}
```

#### GET /actions/stats
Action statistics.

**Response** `200 OK`
```json
{
  "by_status": {"completed": 50, "failed": 5},
  "by_type": {"restart_service": 30, "scale_up": 15},
  "auto_executed": 35,
  "human_approved": 15,
  "rejected": 3,
  "success_rate": 0.91,
  "avg_execution_time_ms": 1500
}
```

#### GET /actions/{id}
Get action details.

#### POST /actions/{id}/approve
Approve or reject action.

**Request**
```json
{
  "approved": true,
  "approved_by": "operator@example.com",
  "comments": "Verified safe to proceed",
  "modifications": {"graceful": true, "timeout": 60}
}
```

#### POST /actions/{id}/execute
Execute approved action.

**Response** `200 OK`
```json
{
  "id": "ACT-2025-001",
  "status": "completed",
  "execution_result": {
    "success": true,
    "output": "Service restarted successfully",
    "started_at": "...",
    "completed_at": "...",
    "duration_ms": 1200,
    "rollback_available": true
  }
}
```

#### POST /actions/{id}/cancel
Cancel pending/awaiting action.

---

### Tools (`/tools`)

#### GET /tools
List available MCP tools.

**Response** `200 OK`
```json
{
  "tools": [
    {
      "name": "find_similar",
      "description": "Find similar incidents from episodic memory",
      "category": "query",
      "requires_approval": false,
      "risk_level": "low"
    },
    {
      "name": "restart_service",
      "description": "Restart a service instance",
      "category": "action",
      "requires_approval": true,
      "risk_level": "medium"
    }
  ],
  "total": 5
}
```

#### GET /tools/{tool_name}
Get tool definition with parameter schema.

#### POST /tools/call
Execute tool.

**Request**
```json
{
  "tool_name": "find_similar",
  "parameters": {"incident_id": "INC-2025-001", "limit": 5},
  "context": {"caller": "reasoning_agent"}
}
```

**Response** `200 OK`
```json
{
  "success": true,
  "data": {...},
  "execution_time_ms": 45,
  "metadata": {"source": "neo4j"}
}
```

---

### Telemetry (`/telemetry`)

#### GET /telemetry/logs
Query Loki logs.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 100 | Max results |
| level | string | - | Filter by level (ERROR, WARN, INFO) |
| service | string | - | Filter by service |
| query | string | - | Loki LogQL query |
| since_minutes | int | 60 | Time window |

**Response** `200 OK`
```json
{
  "logs": [
    {
      "timestamp": "2025-12-27T10:00:00Z",
      "level": "ERROR",
      "service": "backend",
      "message": "Connection timeout",
      "labels": {"pod": "backend-abc123"}
    }
  ],
  "total": 45,
  "query": "{service=\"backend\"} |= \"error\""
}
```

#### GET /telemetry/metrics
Query Prometheus metrics.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| range | string | 1h | Time range |
| step | string | 15s | Query step |
| query | string | - | PromQL query |
| metric | string | - | Metric name |
| service | string | - | Filter by service |

**Response** `200 OK`
```json
{
  "metrics": [
    {
      "timestamp": "2025-12-27T10:00:00Z",
      "value": 95.5,
      "labels": {"instance": "backend:8000"}
    }
  ],
  "range": "1h",
  "step": "15s"
}
```

#### GET /telemetry/traces
Query Tempo traces.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 20 | Max results |
| service | string | - | Filter by service |
| trace_id | string | - | Specific trace ID |
| min_duration_ms | int | - | Minimum duration |
| since_minutes | int | 60 | Time window |

#### GET /telemetry/health
Telemetry backend health check.

**Response** `200 OK`
```json
{
  "loki": true,
  "prometheus": true,
  "tempo": true
}
```

---

### Graph (`/graph`)

#### GET /graph/episodes
Get graph data for visualization.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 50 | Max episodes |
| since_hours | int | 168 | Time window (7 days) |
| min_similarity | float | 0.75 | Min similarity for SIMILAR_TO edges (v0.6.0) |
| min_confidence | float | 0.70 | Min confidence for entity edges (v0.6.0) |
| include_similar_to | bool | true | Include SIMILAR_TO edges (v0.6.0) |
| include_entities | bool | true | Include LLM-extracted entities (v0.6.0) |
| max_edges_per_node | int | 5 | Max edges per node (v0.6.0) |

**Response** `200 OK`
```json
{
  "services": [
    {"name": "backend", "type": "api", "status": "healthy"}
  ],
  "episodes": [
    {"id": "ep-123", "title": "...", "severity": "high"}
  ],
  "edges": [
    {"from": "backend", "to": "neo4j", "type": "DEPENDS_ON"}
  ],
  "stats": {
    "total_episodes": 50,
    "total_edges": 287,
    "critical_episodes": 3
  }
}
```

#### POST /graph/cleanup (v0.6.0)
Clean up graph data to prevent hairball visualization.

**Request Body**
```json
{
  "delete_similar_to": true,
  "merge_duplicate_entities": true,
  "delete_orphan_entities": true,
  "keep_episodes": 50
}
```

**Response** `200 OK`
```json
{
  "deleted_similar_to": 2450,
  "merged_entities": 35,
  "deleted_orphans": 12,
  "pruned_episodes": 5
}
```

#### POST /graph/generate-episodes (v0.6.1)
Generate realistic demo episodes using the Reasoning Agent (Qwen3-14B).

Uses template-based schemas for each service to create episodes that accurately reflect the Constitutional AIOps architecture. Each service template includes:
- Service metadata (name, type, port, description)
- Dependencies and health endpoints
- Common issues for realistic incident generation

**Request Body**
```json
{
  "services": ["neo4j", "backend"],
  "count_per_service": 1,
  "clear_existing": true
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| services | list[str] | null | Specific services to generate for. If null, generates for all 8 services |
| count_per_service | int | 1 | Episodes per service (1-3) |
| clear_existing | bool | true | Clear Neo4j before generating |

**Response** `200 OK`
```json
{
  "success": true,
  "episodes_created": 8,
  "services_processed": ["neo4j", "prometheus", "grafana", "loki", "tempo", "otel-collector", "backend", "frontend"],
  "errors": [],
  "message": "Generated 8 episodes for 8 services via Reasoning Agent (Qwen3-14B)"
}
```

**Service Templates**
| Service | Type | Port | Common Issues |
|---------|------|------|---------------|
| neo4j | database | 7687 | memory_pressure, connection_pool_exhaustion, slow_queries |
| prometheus | monitoring | 9090 | scrape_target_down, storage_full, query_timeout |
| grafana | visualization | 3001 | dashboard_load_timeout, datasource_error, auth_failure |
| loki | logging | 3100 | ingestion_backlog, storage_limit, rate_limiting |
| tempo | tracing | 3200 | trace_storage_full, span_drop, query_timeout |
| otel-collector | telemetry | 4317 | exporter_failure, pipeline_blocked, memory_limit |
| backend | api | 8000 | llm_timeout, api_latency, database_connection |
| frontend | ui | 3000 | api_unreachable, render_error, websocket_disconnect |

**Generated Graph Schema**
- `:Episode` nodes with title, description, severity, category, root_cause, confidence
- `:Service` nodes with type, port, description, health_endpoint, status
- `:RootCauseType` nodes for failure pattern tracking
- `:Action` nodes for remediation steps
- `:Entity` nodes for causal chain elements
- Relationships: `INVOLVES`, `CAUSED_BY`, `RESOLVED_BY`, `CAUSED`

#### GET /graph/services
List all services with dependencies.

#### GET /graph/services/{name}/dependencies
Get upstream/downstream dependencies.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| depth | int | 2 | Traversal depth |

**Response** `200 OK`
```json
{
  "service": "backend",
  "upstream": ["frontend"],
  "downstream": ["neo4j", "loki", "prometheus"],
  "depth": 2
}
```

#### GET /graph/episodes/{id}
Get episode details.

#### GET /graph/episodes/{id}/similar
Find similar episodes.

#### GET /graph/stats
Graph database statistics.

**Response** `200 OK`
```json
{
  "connected": true,
  "node_count": 150,
  "edge_count": 200,
  "episode_count": 45
}
```

---

### Agents (`/agents`)

#### GET /agents/fast/activity
Fast Agent activity log.

**Query Parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 50 | Max results |
| offset | int | 0 | Pagination offset |

**Response** `200 OK`
```json
{
  "activities": [
    {
      "id": "act-123",
      "timestamp": "2025-12-27T10:00:00Z",
      "type": "annotation",
      "input": "Log data...",
      "output": {"anomaly_detected": true, "severity": "high"},
      "latency_ms": 45,
      "model": "qwen3:4b",
      "status": "success"
    }
  ],
  "total": 100,
  "agent_type": "fast"
}
```

#### GET /agents/fast/stats
Fast Agent performance statistics.

**Response** `200 OK`
```json
{
  "total_requests": 1000,
  "success_count": 985,
  "error_count": 15,
  "avg_latency_ms": 42,
  "requests_per_minute": 5.2
}
```

#### GET /agents/reasoning/activity
Reasoning Agent activity log.

#### GET /agents/reasoning/stats
Reasoning Agent performance statistics.

---

### Prompts (`/prompts`)

#### GET /prompts
List all system prompts.

**Response** `200 OK`
```json
{
  "prompts": [
    {
      "name": "fast_annotator",
      "description": "Telemetry annotation prompt",
      "agent": "fast",
      "editable": true,
      "prompt": "You are a Fast Telemetry Annotator..."
    }
  ]
}
```

#### GET /prompts/{name}
Get specific prompt.

#### PUT /prompts/{name}
Update prompt.

**Request**
```json
{
  "prompt": "Updated prompt text..."
}
```

#### POST /prompts/reset
Reset all prompts to defaults.

#### POST /prompts/{name}/reset
Reset single prompt to default.

---

### Infrastructure (`/infrastructure`)

#### GET /infrastructure/containers
Real-time Docker container status.

**Response** `200 OK`
```json
{
  "containers": [
    {
      "name": "aiops-backend",
      "service": "backend",
      "status": "running",
      "health": "healthy",
      "port": "8000",
      "image": "aiops/backend:latest",
      "monitored": true
    }
  ],
  "total": 9,
  "healthy": 8,
  "unhealthy": 1
}
```

#### GET /infrastructure/containers/discover
Discover all Docker containers.

#### POST /infrastructure/containers/monitor
Add container to monitoring.

**Request**
```json
{
  "container_name": "nextcloud"
}
```

#### POST /infrastructure/monitor
Bulk monitor with initial telemetry collection.

#### DELETE /infrastructure/containers/{name}/monitor
Remove from monitoring.

#### GET /infrastructure/containers/monitored
List currently monitored containers.

#### GET /infrastructure/services
LLM service status.

---

### Demo (`/demo`)

#### GET /demo/status
Current demo mode status.

**Response** `200 OK`
```json
{
  "active": false,
  "started_at": null,
  "anomalies_triggered": 0,
  "container_name": "nextcloud"
}
```

#### POST /demo/start
Trigger 5 real anomalies in target container.

**Response** `200 OK`
```json
{
  "status": "started",
  "message": "Demo mode started",
  "anomalies": [
    {"name": "cpu_stress", "success": true, "message": "CPU stress started"},
    {"name": "memory_pressure", "success": true, "message": "Memory allocation started"},
    {"name": "disk_io", "success": true, "message": "Disk I/O generated"},
    {"name": "network_latency", "success": true, "message": "Network delay simulated"},
    {"name": "service_crash", "success": true, "message": "Process killed"}
  ]
}
```

#### POST /demo/reset
Stop demo and clean up.

#### POST /demo/set-container
Change target container.

**Request**
```json
{
  "container_name": "aiops-backend"
}
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "validation_error"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Action already in progress |
| 422 | Unprocessable Entity - Validation failed |
| 500 | Internal Server Error |
| 503 | Service Unavailable - LLM/Neo4j down |

---

## WebSocket Events

Connect to `/ws` for real-time events.

**Event Format**
```json
{
  "type": "INCIDENT_CREATED",
  "data": {...},
  "timestamp": "2025-12-27T10:00:00Z"
}
```

**Event Types**
| Event | Description |
|-------|-------------|
| `INCIDENT_CREATED` | New incident detected |
| `INCIDENT_UPDATED` | Incident status changed |
| `INCIDENT_RESOLVED` | Incident resolved |
| `ACTION_CREATED` | New action proposed |
| `ACTION_APPROVED` | Action approved by human |
| `ACTION_EXECUTED` | Action execution completed |
| `RCA_COMPLETED` | RCA analysis finished |
| `SYSTEM_HEALTH` | Health status update |
| `ALERT` | System alert |

---

**See Also**:
- [BACKEND.md](BACKEND.md) - Backend architecture
- [FRONTEND.md](FRONTEND.md) - Frontend documentation
