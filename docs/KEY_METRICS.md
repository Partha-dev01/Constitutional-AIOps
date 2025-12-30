# Key Metrics Reference

> **Version**: 0.4.0
> **Last Updated**: 2025-12-30
> **Purpose**: Single source of truth for all metrics in Research_V5.tex
> **Usage**: Export this file to update research paper metrics

---

## Architecture Metrics

### Dual-Agent Configuration

| Component | Specification |
|-----------|---------------|
| Fast Agent Model | Qwen3-4B Q4_K_M |
| Fast Agent VRAM | ~4GB (2.5GB + 1GB KV) |
| Fast Agent Port | 8081 |
| Fast Agent Context | 8K tokens |
| Fast Agent Latency | <100ms P95 |
| Fast Agent CPU | 2 cores |
| Fast Agent RAM | 8GB |
| Reasoning Agent Model | Qwen3-14B Q4_K_M |
| Reasoning Agent VRAM | ~11GB (9GB + 1.5GB KV) |
| Reasoning Agent Port | 8082 |
| Reasoning Agent Context | 4K tokens |
| Reasoning Agent Latency | 200-500ms P95 |
| Reasoning Agent CPU | 4 cores |
| Reasoning Agent RAM | 12GB |

### VRAM Allocation

| Metric | Value |
|--------|-------|
| Total VRAM Used | ~15GB |
| Total VRAM Available | 24GB |
| VRAM Utilization | ~63% |
| Free VRAM | ~9GB |

---

## Constitutional AI Metrics

### Principle Structure

| Metric | Value |
|--------|-------|
| Total Principles | 11 |
| Tier 1 (Safety) | 4 principles (P1.1-P1.4) |
| Tier 2 (Operational) | 4 principles (P2.1-P2.4) |
| Tier 3 (Learning) | 3 principles (P3.1-P3.3) |

### Authorization Thresholds

| Threshold | Value | Action |
|-----------|-------|--------|
| Auto-Execute | >0.90 | AUTOMATIC |
| Approval Required | 0.70-0.90 | APPROVAL_REQUIRED |
| Alert-Only | <0.70 | ALERT_ONLY |

### Confidence Formula

```
C(a) = α · C_LLM(a) + β · C_hist(a) + γ · C_sim(a)

Where:
  α = 0.4  (LLM confidence weight)
  β = 0.35 (Historical success rate weight)
  γ = 0.25 (Similarity to past incidents weight)

  C_LLM(a)  = Reasoning agent's self-reported confidence (0.0-1.0)
  C_hist(a) = successful_executions / total_executions
  C_sim(a)  = max(cosine_similarity(current, past_resolutions))
```

---

## Performance Metrics

### Annotation Accuracy Targets

| Telemetry Type | Target Range |
|----------------|-------------|
| Log Annotation | 90-95% |
| Metric Annotation | 85-92% |
| Trace Annotation | 85-90% |
| **Overall Average** | **87-92%** |

### RCA Performance Targets

| Metric | Target |
|--------|--------|
| RCA Accuracy | 85-90% |
| Average Resolution Time | <5 minutes |

### Latency Targets

| Component | Target |
|-----------|--------|
| Fast Agent (Qwen3-4B) | <100ms P95 |
| Reasoning Agent (Qwen3-14B) | 200-500ms P95 |
| Graph Query (Neo4j) | O(log n) |

### Efficiency Metrics

| Metric | Value |
|--------|-------|
| Token Compression Rate | 92% |
| Tool Sprawl Reduction | 93% |

---

## Telemetry Metrics

### Ingestion Rates

| Metric | Value |
|--------|-------|
| Raw Telemetry Ingestion | 1.7M tokens/hour |
| Log Entries/Day | 4M |
| Avg Tokens/Log Entry | 42 |
| Metric Points/Hour | 850K |
| Avg Tokens/Metric Point | 15 |
| Trace Spans/Hour | 120K |
| Avg Spans/Trace | 8 |

### Batch Processing

| Metric | Value |
|--------|-------|
| Fast Agent Batch Size | 8 observations |
| Batch Timeout | 10 seconds |
| Batch Items | 5000 |

---

## Memory System Metrics

### Neo4j Configuration

| Metric | Value |
|--------|-------|
| Graph Database | Neo4j 5.x |
| Retrieval Complexity | O(log n) |
| Embedding Model | sentence-transformers/all-MiniLM-L6-v2 |
| Embedding Dimensions | 384 |
| Similarity Threshold | ≥0.70 cosine |
| Similar Incident Limit | Top 5 |

### Data Retention

| Store | Retention |
|-------|-----------|
| Logs (Loki) | 30 days |
| Traces (Tempo) | 7 days |
| Metrics (Mimir) | 90 days |

---

## Observability Stack Versions

| Component | Version | Purpose |
|-----------|---------|---------|
| Loki | v2.9 | Log aggregation |
| Grafana | v10.2 | Visualization & alerting |
| Tempo | v2.3 | Distributed tracing |
| Mimir | v2.16 | Long-term metrics storage |
| OpenTelemetry Collector | v0.131.0 | Telemetry collection |

---

## Research Gaps Addressed

| ID | Gap | Description | Status |
|----|-----|-------------|--------|
| RG1 | Automated Knowledge Extraction | Learning from historical incident data | Addressed |
| RG2 | Graph-Based Operational Knowledge | Semantic + episodic memory in Neo4j | Addressed |
| RG3 | Observability-Specific Tokenization | Optimized for structured telemetry | Addressed |
| RG4 | Constitutional AI for Autonomous Operations | Graduated trust mechanisms | Addressed |
| RG5 | Comprehensive AI-Enhanced Observability | Unified multi-modal (logs+metrics+traces) | Addressed |

---

## Formulas Reference

### Semantic Triplets

```
T = {(e₁, r, e₂) | e₁, e₂ ∈ Entities, r ∈ Relations}

Examples:
- (api-gateway, EXPERIENCED, connection_timeout)
- (database, CAUSED, service_unavailable)
```

### Hybrid Retrieval Score

```
score(e) = α · vector_sim(e) + (1-α) · graph_sim(e)

Where α is a configurable weighting parameter
```

### Authorization Decision

```
Action =
  AUTOMATIC           if C(a) > 0.90
  APPROVAL_REQUIRED   if 0.70 ≤ C(a) ≤ 0.90
  ALERT_ONLY          if C(a) < 0.70
```

---

## Deployment Costs

| Deployment | Hardware | Hourly | Monthly (Typical) |
|------------|----------|--------|-------------------|
| Jarvis Labs (Primary) | A5000 24GB | $0.49/hr | ~$36/month |
| AWS Spot | g6.xlarge L4 24GB | $0.35/hr | ~$252/month (continuous) |
| Local Development | No GPU | Free | Free |

---

## MCP Tools

| Tool | Purpose |
|------|---------|
| find_similar_incidents | Neo4j top-5 similarity retrieval |
| get_component_dependencies | Graph traversal for impact analysis |
| restart_service | Docker restart with health validation |
| scale_service | Kubernetes replica scaling |
| analyze_time_series_anomaly | Z-score and seasonal decomposition |

---

## API Statistics

| Metric | Count |
|--------|-------|
| Total API Endpoints | 50+ |
| Backend Python Files | 43 |
| Frontend React Files | 23 |
| API Route Files | 12 |

---

## Version Comparison: Traditional vs Constitutional AIOps

| Metric | Traditional | Constitutional AIOps | Improvement |
|--------|-------------|---------------------|-------------|
| Detection Time | 5-15 min | <1 second | 300-900x faster |
| Initial Classification | 10-30 min | <100ms | 6000-18000x faster |
| RCA Time | 1-4 hours | 5-10 minutes | 6-48x faster |
| Alert Fatigue Reduction | - | 70-90% | Significant |
| Tool Sprawl Reduction | - | 93% | Significant |

---

**Last Verified Against Research_V5.tex**: 2025-12-30
