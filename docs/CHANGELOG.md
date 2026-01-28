# Constitutional AIOps - Changelog

All notable changes to this project will be documented in this file.

## [0.6.1] - 2026-01-27

### Episode Generation via Reasoning Agent

**Feature**: New API endpoint to generate realistic demo episodes using the Reasoning Agent (Qwen3-14B) with template-based schemas.

#### New Endpoint: `POST /api/v1/graph/generate-episodes`

Generates realistic incident episodes for each service in the Constitutional AIOps architecture. The Reasoning Agent analyzes service templates and creates contextually appropriate incidents.

**Implementation Details**

**Backend (src/api/routes/graph.py)**
- Added `SERVICE_TEMPLATES` array defining 8 services with:
  - Name, type, port, description
  - Health endpoint, dependencies
  - Common issues for realistic incident generation
- Added `EPISODE_GENERATION_TEMPLATE` prompt for Qwen3-14B
- Added `GenerateEpisodesRequest` and `GenerateEpisodesResponse` models
- Added `/generate-episodes` endpoint that:
  1. Calls ReasoningAgent.chat() for each service
  2. Parses JSON response (handles `<think>` tags, markdown blocks)
  3. Stores in Neo4j with full graph schema

**Graph Schema Created**
| Node Type | Properties |
|-----------|------------|
| `:Episode` | episode_id, title, description, severity, category, root_cause, confidence, outcome, detected_at, resolved_at |
| `:Service` | name, type, port, description, health_endpoint, status, uptime_percent |
| `:RootCauseType` | id, name |
| `:Action` | id, name, success_rate |
| `:Entity` | name (causal chain elements) |

| Relationship | Pattern |
|--------------|---------|
| `INVOLVES` | Episode → Service |
| `CAUSED_BY` | Episode → RootCauseType |
| `RESOLVED_BY` | Episode → Action |
| `CAUSED` | Entity → Entity (causal chain) |

**Usage**
```bash
# Generate episodes for all services
curl -X POST "http://localhost:8000/api/v1/graph/generate-episodes" \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true, "count_per_service": 1}'

# Generate for specific services
curl -X POST "http://localhost:8000/api/v1/graph/generate-episodes" \
  -H "Content-Type: application/json" \
  -d '{"services": ["neo4j", "backend"], "count_per_service": 2}'
```

**Requirements**
- Jarvis Labs VM must be running with Ollama
- Both Qwen3-4B and Qwen3-14B models loaded
- Neo4j container healthy

#### Bug Fixes
- Fixed graph node click "fly off" behavior (removed zoom(2, 500))
- Adjusted physics settings for better service node distribution
- Removed duplicate `/graph` route (now only in Agents tab)

---

## [0.6.0] - 2026-01-25

### Graph Schema Redesign - Hairball Prevention

**Issue**: Graph visualization was a tangled mess ("hairball") with 2,450+ SIMILAR_TO edges due to O(n²) algorithm with 0.5 threshold, entity proliferation from LLM triplets without deduplication, and weak force simulation parameters.

#### Changes Made

**Backend (src/api/routes/graph.py)**
- `SIMILAR_TO_THRESHOLD`: 0.5 → 0.75 (94% edge reduction)
- Added `MAX_SIMILAR_EDGES_PER_EPISODE = 3` (degree capping)
- Added `MIN_TRIPLET_CONFIDENCE = 0.70` (quality filtering)
- Added `MAX_EDGES_PER_NODE = 5` (hairball prevention)
- New API query parameters: `min_similarity`, `min_confidence`, `include_similar_to`, `include_entities`, `max_edges_per_node`
- Added `_prune_edges()` function for server-side degree capping
- Added `/cleanup` endpoint for graph maintenance

**Backend (src/agents/fast_annotator.py)**
- Added `ENTITY_CANONICALIZATION` dictionary (30+ entity mappings)
- Added `canonicalize_entity()` function to map variants to canonical forms
- Example: "API Gateway", "api-gateway", "apigateway" all → "api_gateway"

**Backend (src/memory/episode_store.py)**
- Added `MIN_TRIPLET_CONFIDENCE = 0.70` constant
- Triplets below confidence threshold are now filtered out
- Added confidence field to RELATES edges

**Backend (src/memory/neo4j_client.py)**
- Added `cleanup_graph()` method for data maintenance
- Added `get_graph_stats()` method for monitoring

**Frontend (frontend/src/components/EpisodicGraphExplorer.tsx)**
- Charge strength: -300 → -800 (stronger node repulsion)
- Center strength: 0.05 → 0.2 (tighter centering)
- Variable link distance based on relationship type (50-150px)
- Added DAG/hierarchical layout mode option
- Added edge visibility toggles (Similar To, Entities)
- Added layout mode toggle (Force vs Hierarchy)

#### Expected Improvements
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| SIMILAR_TO edges | 2,450 | ~150 | 94% reduction |
| Entity nodes | 50+ | ~15 | 70% reduction |
| Total edges | 3,000+ | ~300 | 90% reduction |
| API response size | ~500KB | ~50KB | 90% reduction |

---

## [0.5.3] - 2026-01-23

### Neo4j Health Check Resilience Fix

**Issue**: Neo4j container becomes "unhealthy" after Docker Desktop restarts, blocking backend startup due to `depends_on: service_healthy` dependency.

#### Root Cause
1. `start_period: 60s` was too short for Neo4j cold start initialization
2. No `stop_grace_period` meant unclean shutdowns left stale PID files
3. Stale PIDs caused "Neo4j is already running" errors on restart

#### Fix Applied

**File**: `docker-compose.yml` (Neo4j service, lines 72-95)

```yaml
neo4j:
  ...
  stop_grace_period: 30s  # NEW: Ensures Neo4j shuts down cleanly
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:7474"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 120s  # CHANGED: Was 60s, increased for cold start
```

#### Recovery Commands (if issue persists)
```bash
# Clean restart (preserves data)
docker compose down && docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d

# Full reset (DELETES DATA - use only if corrupted)
docker compose down -v && docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d
```

#### Verification
```bash
docker ps --format "table {{.Names}}\t{{.Status}}" | grep neo4j
# Expected: aiops-neo4j ... (healthy)
```

---

## [0.5.2] - 2026-01-16

### Confidence Formula & Embeddings Implementation

**Session**: Implemented the composite confidence formula and vector embeddings from Research_V6.tex.

#### New Features

1. **Confidence Calculator Module** (`src/confidence/`)
   - Implements formula: `C(a) = 0.4·C_LLM + 0.35·C_hist + 0.25·C_sim`
   - Queries Neo4j for historical action success rates
   - Uses episode similarity for context-aware confidence
   - Falls back to neutral defaults (0.5) when data unavailable

2. **Embedding Service** (`src/memory/embedding_service.py`)
   - Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim)
   - Automatic CUDA detection for GPU acceleration (GTX 1650+)
   - Singleton pattern with lazy loading
   - Batch encoding support

3. **Hybrid Retrieval** (`src/memory/episode_store.py`)
   - Formula: `score = 0.6·vector_sim + 0.4·graph_sim`
   - On-the-fly embedding generation with callback notification
   - Stores embeddings as JSON array in Neo4j (Community compatible)

4. **New API Endpoints**
   - `GET /api/v1/actions/confidence/formula` - Get formula details
   - `GET /api/v1/graph/embedding/status` - Get embedding service status

#### Files Created

| File | Purpose |
|------|---------|
| `src/confidence/__init__.py` | Module init |
| `src/confidence/calculator.py` | ConfidenceCalculator class |
| `src/memory/embedding_service.py` | EmbeddingService with CUDA support |

#### Files Modified

| File | Changes |
|------|---------|
| `requirements.txt` | Added torch>=2.0.0, sentence-transformers>=2.2.0 |
| `src/main.py` | Initialize embedding service and confidence calculator |
| `src/memory/episode_store.py` | Integrate embeddings, hybrid similarity |
| `src/memory/__init__.py` | Export embedding service |
| `src/api/routes/actions.py` | Use composite confidence, add formula endpoint |
| `src/api/routes/graph.py` | Add embedding status endpoint |
| `docs/KEY_METRICS.md` | Document confidence formula and embeddings |
| `docs/BACKEND.md` | Document new modules |

#### GPU Installation

```bash
# NVIDIA GTX 1650+ with CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118
pip install sentence-transformers
```

---

## [0.5.1] - 2026-01-15

### Docker Service Recovery & Bug Fixes

**Session**: Fixed Docker services to properly recover after Docker Desktop restart, plus multiple backend bug fixes.

#### Docker Infrastructure Improvements

1. **Health Checks Added to All Services**
   - `loki`: `/ready` endpoint check
   - `prometheus`: `/-/healthy` endpoint check
   - `tempo`: `/ready` endpoint check
   - `grafana`: `/api/health` endpoint check
   - `frontend`: Root endpoint check
   - `otel-collector`: Health extension on port 13133

2. **Conditional Dependencies**
   - All `depends_on` now use `condition: service_healthy`
   - Services wait for dependencies to be truly ready before starting
   - Eliminates race conditions on Docker restart

3. **Neo4j Health Check Standardization**
   - Changed from `wget` to `curl` for consistency
   - Added `start_period: 60s` for proper startup time

#### Backend Bug Fixes

1. **Neo4j Query Method Fix** (`src/api/routes/graph.py`)
   - Fixed 7 locations using deprecated `execute_read()` method
   - Changed to standard `run()` method for Neo4j queries

2. **Fast Agent JSON Parsing** (`src/agents/fast_annotator.py`)
   - Added brace-matching fallback parser for malformed JSON
   - Handles LLM responses with extra text before/after JSON

3. **Model Router System Prompt** (`src/agents/model_router.py`)
   - Added system prompt for strict JSON output
   - Improves determinism and parsing reliability

4. **Episode Compaction** (`src/telemetry/background_processor.py`)
   - Implemented episode deduplication using similarity matching
   - Reduces graph clutter from repeated similar incidents

#### Files Changed

| File | Changes |
|------|---------|
| `docker-compose.yml` | Health checks, conditional dependencies |
| `src/api/routes/graph.py` | Neo4j query method fix |
| `src/agents/fast_annotator.py` | JSON brace-matching parser |
| `src/agents/model_router.py` | System prompt addition |
| `src/telemetry/background_processor.py` | Episode compaction |

---

## [0.5.0] - 2026-01-11

### Graphiti-Style Force-Directed Graph Visualization

**Session**: Implemented interactive force-directed graph for Neo4j episodic memory visualization

#### New Features

1. **EpisodicGraphExplorer Component** (`frontend/src/components/EpisodicGraphExplorer.tsx`)
   - Force-directed graph using `react-force-graph-2d` library
   - Interactive pan, zoom, and node dragging
   - Physics simulation with pause/resume capability
   - Responsive container with ResizeObserver

2. **Graph Controls**
   - Zoom In/Out buttons
   - Fit to View (auto-zoom to show all nodes)
   - Pause/Resume animation
   - Reset view
   - Refresh data button

3. **Node Visualization**
   - 5 node types: service, episode, incident, action, root_cause
   - Color-coded by status: healthy (green), warning (amber), critical (red)
   - Icon labels: S (Service), E (Episode), ! (Incident), A (Action), R (Root Cause)
   - Glow effect on hover/selection
   - Details panel showing confidence, severity, timestamp

4. **Edge Visualization**
   - 5 relationship types: depends_on, affects, caused_by, resolved_by, similar_to
   - Directional arrows at midpoint
   - Color-coded by relationship type
   - Labels shown at high zoom levels

5. **Filtering**
   - Dropdown filter by node type
   - Real-time node/edge count display
   - Color legend for status types

#### Technical Details

- Added `react-force-graph-2d` dependency (v1.25.0)
- Created custom TypeScript declarations (`frontend/src/types/react-force-graph-2d.d.ts`)
- Fixed TypeScript issues with ForceGraphMethods ref type
- Added type assertions for callback parameters

#### Files Changed
- `frontend/src/components/EpisodicGraphExplorer.tsx` (NEW - 456 lines)
- `frontend/src/types/react-force-graph-2d.d.ts` (NEW - 135 lines)
- `frontend/src/pages/Agents.tsx` (updated Graph Explorer tab)
- `frontend/package.json` (added react-force-graph-2d)

#### Infrastructure Updates
- Updated Jarvis Labs SSH port to 11114 (ssho.jarvislabs.ai)
- Fixed docker-compose hybrid configuration for production use

---

## [0.4.8] - 2026-01-09

### Architecture Fix: TelemetryCollector Compliance with Research_V6.tex

**Session**: Fixed architecture violation where BackgroundProcessor bypassed TelemetryCollector

#### Critical Fix

The previous implementation incorrectly bypassed the `TelemetryCollector` with direct HTTP queries to Loki/Prometheus/Tempo. This violated the Research_V6.tex architecture:

```
LGTM Stack → TelemetryCollector → BackgroundProcessor → Fast Agent
```

#### Changes Made

1. **Fixed TelemetryCollector.query_logs()** (`src/telemetry/collector.py`)
   - Changed Loki query from `{service="{service}"}` to `{job="containerlogs"}`
   - Loki uses `job="containerlogs"` label (configured in promtail)
   - Added service filtering with LogQL pattern matching

2. **Fixed TelemetryCollector.query_metrics()** (`src/telemetry/collector.py`)
   - Changed from service-specific metrics to generic Prometheus metrics
   - Queries: `go_goroutines`, `go_memstats_alloc_bytes`, `process_cpu_seconds_total`, `up`

3. **Removed HTTP Bypass from BackgroundProcessor** (`src/telemetry/background_processor.py`)
   - Removed direct HTTP client and hardcoded URLs
   - Removed `_query_loki_logs()`, `_query_prometheus_metrics()`, `_query_tempo_traces()`
   - Now uses `self.telemetry_collector.collect_window()` as designed

#### Architecture Compliance

Now properly follows Research_V6.tex Section 4.1:
- TelemetryCollector is the **single interface** to LGTM stack
- BackgroundProcessor delegates to TelemetryCollector
- No direct HTTP calls to observability backends

#### Verification
```bash
curl http://localhost:8000/api/v1/telemetry/processor/status
# Response: {"running":true,"total_cycles":2,"telemetry_processed":2,...}
```

---

## [0.4.7] - 2026-01-07

### Background Telemetry Processor - Continuous Fast Agent Scanning

**Session**: Implementing continuous telemetry processing as described in Research_V6.tex

#### Major Changes

1. **Created Background Telemetry Processor** (`src/telemetry/background_processor.py`)
   - Implements "System 1" continuous scanning from research paper
   - Processes telemetry every 30 seconds from Loki/Prometheus/Tempo
   - Fast Agent annotates anomalies automatically
   - Escalates to Reasoning Agent when `needs_reasoning=true`
   - Stores annotations and episodes in Neo4j graph

2. **Updated Main Application** (`src/main.py`)
   - Background processor starts on application startup
   - Graceful shutdown of processor on application stop
   - Logs processor activity for debugging

3. **Added Processor Status API** (`src/api/routes/telemetry.py`)
   - New endpoint: `GET /api/v1/telemetry/processor/status`
   - Returns: running status, total cycles, anomalies detected, escalations, etc.

#### Services Monitored
- `aiops-backend`
- `nextcloud`
- `aiops-frontend`
- `aiops-neo4j`

#### Research Paper Reference
From Research_V6.tex:
> "Fast Annotation Agent (System 1): A 4B parameter model optimized for sub-100ms pattern recognition. It continuously scans OpenTelemetry streams to tag anomalies."

---

## [0.4.6] - 2026-01-05

### Container Fixes, Chat UI Enhancements & Infrastructure Updates

**Session**: Hardcoded URL removal, Chat typewriter effect, Neo4j health fix, Nextcloud integration

#### Major Changes

1. **Removed Hardcoded Jarvis Labs URLs** (`docker-compose.yml`)
   - Changed `FAST_AGENT_URL` and `REASONING_AGENT_URL` from hardcoded fallbacks to read from `JARVIS_OLLAMA_URL` in `.env`
   - Old: `${FAST_AGENT_URL:-https://96c3f93672471.notebooks.jarvislabs.net/v1}` (hardcoded!)
   - New: `${JARVIS_OLLAMA_URL}/v1` (reads from .env)
   - **Benefit**: When Jarvis Labs endpoint changes, only update `.env` file

2. **Fixed Neo4j Health Check** (`docker-compose.yml`)
   - Changed from `curl` to `wget` (curl not installed in Neo4j container)
   - Old: `["CMD", "curl", "-f", "http://localhost:7474"]`
   - New: `["CMD-SHELL", "wget -q --spider http://localhost:7474 || exit 1"]`

3. **Added Nextcloud to Docker Compose** (`docker-compose.yml`)
   - Nextcloud now auto-starts with the project for Phase B metrics extraction
   - Port: 8080:80
   - Volume: nextcloud-data

4. **Chat UI Enhancements** (`frontend/src/pages/Chat.tsx`)
   - Added typewriter effect: Text appears gradually (3 chars at 15ms intervals)
   - Added thinking indicator: Collapsible "Thinking..." dropdown with animated dots
   - Added blinking cursor while typing
   - Better UX for LLM response visualization

#### Container Status (Post-Fix)
| Container | Status | Notes |
|-----------|--------|-------|
| aiops-backend | ✅ Healthy | Both agents connecting to Jarvis Labs |
| aiops-frontend | ✅ Healthy | Chat UI with typewriter effect |
| aiops-neo4j | ✅ Healthy | wget health check working |
| nextcloud | ✅ Running | Now part of project stack |
| All LGTM | ✅ Running | Observability stack operational |

#### Files Modified
| File | Changes |
|------|---------|
| `docker-compose.yml` | Removed hardcoded URLs, fixed Neo4j health check, added nextcloud |
| `frontend/src/pages/Chat.tsx` | Typewriter effect + thinking indicator |

---

## [0.4.5] - 2026-01-05

### Environment & Container Fixes

**Session**: Debugging agent offline status and container issues

#### Bug Fixes
- **`.env`**: Updated `JARVIS_OLLAMA_URL` to correct Jarvis Labs endpoint (`https://96c3f93672471.notebooks.jarvislabs.net`)
- **`docker/configs/otel-collector.yaml`**: Fixed loki exporter config syntax
  - Changed invalid `labels.attributes` to `default_labels_enabled` format
  - Resolved otel-collector restart loop

#### Environment Issues Resolved
| Issue | Root Cause | Resolution |
|-------|------------|------------|
| Agents showing offline | Wrong Jarvis Labs endpoint in container env | Updated `.env` with correct endpoint |
| Docker not reading .env | Git Bash/Windows env handling | Use explicit `export VAR=value` before compose |
| otel-collector restart loop | Invalid loki exporter config | Fixed to use `default_labels_enabled` format |
| nginx 502 Bad Gateway | Stale DNS resolution | Restart frontend container |

#### Container Status (Post-Fix)
- Backend: ✅ Healthy (Jarvis Labs `qwen3:4b` + `qwen3:14b` responding)
- Frontend: ✅ Healthy (nginx proxy working)
- otel-collector: ✅ Running
- Neo4j: ✅ Running (API responds at 7474/7687)
- Loki, Prometheus, Tempo, Grafana: ✅ Running

---

## [0.4.4] - 2026-01-04

### Playwright MCP Testing & API Route Fixes

**Testing Session**: Full frontend and backend verification using Playwright MCP

#### Bug Fixes
- **src/api/routes/metrics.py**: Fixed all route paths causing 404 errors
  - Changed `/metrics` → `""` (base route)
  - Changed `/metrics/latency` → `/latency`
  - Changed `/metrics/history` → `/history`
  - Changed `/metrics/export` → `/export`
  - Changed `/metrics/clear` → `/clear`
  - Changed `/metrics/benchmark` → `/benchmark`
  - Changed `/metrics/validate/determinism` → `/validate/determinism`
  - Changed `/metrics/validation/report` → `/validation/report`
  - Root cause: Routes had redundant `/metrics` prefix since router was already mounted at `/api/v1/metrics`

#### Testing Coverage (Playwright MCP)
| Page | Tests Passed | Key Checks |
|------|-------------|------------|
| Dashboard | ✅ | Stats cards, model status, sidebar navigation |
| Agents | ✅ | 6 tabs (Fast, Reasoning, Telemetry, Graph, MCP Tools, Infrastructure) |
| Incidents | ✅ | List, search, filters, create modal |
| Chat | ✅ | Input, send button, response handling |
| Metrics | ✅ | 4 tabs (Overview, Benchmark, Validation, Export) |
| Settings | ✅ | 5 tabs (Constitutional AI, Notifications, Telemetry, Models, Prompts) |

#### Compliance Verification
- Fast Agent Temperature: 0.0 ✅
- Reasoning Agent Temperature: 0.0 (analysis mode) ✅
- Chat Temperature: 0.5 ✅
- Seed Method: hash(prompt) % 2^32 ✅
- Constitutional Principles: 12 (4+4+4) ✅

#### Services Verified
- Backend: http://localhost:8000 ✅
- Frontend: http://localhost:3000 ✅
- Neo4j: bolt://localhost:7687 ✅
- Grafana: http://localhost:3001 ✅
- Prometheus: http://localhost:9090 ✅
- Loki: http://localhost:3100 ✅
- Jarvis Labs LLM: https://96c3f93672471.notebooks.jarvislabs.net ✅

---

## [0.4.3] - 2026-01-03

### Full Codebase Compliance Verification

**Verification Scope**: Research_V6.tex → docs/ → src/ → frontend/src/

#### Files Modified (Backend)
- **src/agents/fast_annotator.py**:
  - Fixed V5→V6 reference in docstring
  - Fixed temperature 0.1→0.0 for deterministic annotation
- **src/agents/reasoning_agent.py**:
  - Fixed V5→V6 reference in docstring
  - Fixed "11 principles"→"12 principles (4+4+4)"
  - Fixed temperature to be mode-based (0.0 for RCA/planning, 0.5 for chat)
- **src/config.py**: Fixed 3× V5→V6 references
- **src/validation/constants.py**: Fixed 8× V5→V6 references
- **src/validation/__init__.py**: Fixed 2× V5→V6 references
- **src/memory/episode_store.py**: Fixed 2× V5→V6 references
- **src/memory/retrieval.py**: Fixed 2× V5→V6 references
- **src/main.py**: Fixed "11 principles"→"12 principles (4+4+4)"
- **src/api/routes/actions.py**: Fixed "11 principles"→"12 principles"

#### Verification Results
| Area | Files Checked | Status |
|------|---------------|--------|
| Research_V6.tex | 1 (22 pages) | ✅ No changes needed |
| docs/ | 13+ files | ✅ Already compliant |
| frontend/src/ | 23+ files | ✅ Already compliant |
| src/ | 48 files | ✅ Fixed (17 changes in 9 files) |

**Total Changes**: 17 edits across 9 backend files

---

## [0.4.2] - 2026-01-03

### Research Paper V6 Complete
- **Research_V6.tex**: Final research paper version (22 pages)
  - Added Determinism Analysis section with mathematical proofs
  - Enhanced Confidence-Based Authorization with justifications
  - Fixed Kubernetes→Docker Compose references (current deployment)
  - Clarified 12 Constitutional Principles (4+4+4 across 3 tiers)
  - Added Bounded Determinism claims (temperature=0, seed=hash(prompt))

### Documentation Verification
- **ARCHITECTURE.md**: Fixed mismatches with V6
  - 11 Principles → 12 Principles
  - Neo4j 5.15 → Neo4j 5.x
  - OpenTelemetry 0.91 → OpenTelemetry 0.131.0
- **CHECKLIST.md**: Updated V5→V6 references
- **KEY_METRICS.md**: Complete overhaul with implementation details
  - Added metric collection API endpoints and commands
  - Added research paper tables mapping
  - Documented test dataset requirements for accuracy validation
  - Added complete metrics collection workflow

### V6 Critical Values (Verified Across All Docs)
- Principles: 12 (4+4+4), not 11
- Fast Agent: <100ms P95
- Reasoning Agent: 200-500ms P95
- Auto threshold: >0.90
- Approval threshold: 0.70-0.90
- Confidence weights: α=0.4, β=0.35, γ=0.25
- Embedding: 384-dim
- Similarity: ≥0.70 cosine
- Hybrid retrieval: α=0.6 vector, 0.4 graph
- VRAM: 4GB + 11GB = 15GB
- Compression: 92%

---

## [0.4.1] - 2025-12-30

### Changed
- **Codebase Synchronization**: All codebase files now match Research_V6.tex and documentation
- **Latency Targets**: Updated all files to use correct values
  - fast_annotator.py: <50ms P99 → <100ms P95
  - reasoning_agent.py: <200ms P99 → 200-500ms P95
  - Settings.tsx, Dashboard.tsx: Updated latency displays
- **Version Numbers**: Synchronized across codebase
  - main.py: 0.2.0 → 0.4.0
  - frontend/package.json: 0.1.0 → 0.4.0

### Added
- **src/validation/constants.py**: NEW centralized validation constants module
  - PerformanceTargets: Latency and resolution time targets
  - AccuracyTargets: Annotation and RCA accuracy ranges
  - CompressionMetrics: Token compression and tool sprawl rates
  - MemorySystemConfig: Embeddings, similarity threshold, retrieval alpha
  - ConstitutionalAIConfig: Thresholds, weights, principle counts
  - VRAMConfig: Model memory allocations and ports
  - ObservabilityVersions: LGTM stack versions and retention
  - ResearchGaps: RG1-RG5 definitions
- **config.py**: Added MemoryConfig and PerformanceConfig classes
- **episode_store.py**: Added embedding model constants (EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, SIMILARITY_THRESHOLD)
- **retrieval.py**: Documented hybrid retrieval formula with RETRIEVAL_ALPHA constant

### Fixed
- Dashboard.tsx: Removed hardcoded fake latency values (42ms, 156ms)
- Settings.tsx: Fixed incorrect latency target displays
- validation/__init__.py: Added exports for all new constants

---

## [0.3.2] - 2025-12-27

### Documentation Restructure
- **ARCHITECTURE.md**: Complete rewrite with correct specs (Qwen3-4B/14B, Jarvis Labs, no hot-swap)
- **DEPLOYMENT.md**: Complete rewrite with Jarvis Labs Hybrid as primary deployment option
- **INDEX.md**: New master documentation index with update tracking
- **DOCUMENTATION_SCHEMA.md**: New guidelines for maintaining documentation
- **CLAUDE.md**: Updated to v2.1 with correct documentation map
- **README.md**: Updated technology stack and documentation references

### Removed (Outdated/Redundant Files)
- `MEGA_PROMPT.md`, `MEGA_PROMPT_PART2.md`, `MEGA_PROMPT_PART3.md` - Contained outdated code examples (InfluxDB, T4)
- `PROJECT_SUMMARY.md` - Historical document, no longer needed
- `QUICKSTART.md` - Merged into README.md
- `Cloud_provider_discussions.md` - Historical research notes
- `JARVIS_LABS_TESTING_RESULTS.md` - Test results, not documentation
- `Simplified_AIOps_Documentation_v6.md` - Old consolidated draft
- `docs/plans/jarvis-labs-qwen3-deployment.md` - Obsolete plan file

### Fixed
- Removed all T4 16GB / hot-swap / llama-swap references (incorrect architecture)
- Removed all Qwen3-8B references (correct model is Qwen3-4B)
- Removed InfluxDB references (only Neo4j is used for memory)
- Updated all documentation to reflect Jarvis Labs Ollama as primary LLM host

---

## [0.3.1] - 2025-12-21

### Deployment
- **Full Container Rebuild**: All Docker containers rebuilt with `docker compose build --no-cache`
- **Verified Working**:
  - Frontend nginx proxy correctly routes `/api/v1/*` to backend
  - LLM agents (qwen3:4b, qwen3:14b) healthy via Jarvis Labs endpoint
  - Backend health check: `{"status":"degraded","components":[fast_agent: healthy, reasoning_agent: healthy]}`
  - Incidents API: Returns proper JSON via both direct and proxied routes

### Fixed
- **Success Rate Display**: Changed from "N/A" to "100%" by default when no actions exist - decreases from 100% when failures occur
- **New Incident Button**: Added functional "New Incident" button with full create incident modal form
- **Incidents Empty State**: Shows "All Systems Operational" with green checkmark when no incidents, replacing plain "No incidents found" text
- **Demo Mode Real Incidents**: Demo mode now creates actual incidents in the incident store with RCA analysis, instead of just logging

### Added
- **CreateIncidentModal Component**: Full form for creating incidents with title, description, severity, category, affected service, and auto-analyze option
- **Demo Incident Generation**: Demo mode creates 5 real incidents (CPU Stress, Memory Pressure, Disk I/O, Network Latency, Service Crash) with appropriate severity and category

---

## [0.3.0] - 2025-12-21

### Fixed
- **CRITICAL: Incidents Page NetworkError**: Removed hardcoded `VITE_API_URL=http://localhost:8000` from docker-compose.yml - frontend now uses relative `/api/v1` path which nginx proxies correctly
- **Infrastructure Tab "Unknown" Status**: Running containers without HEALTHCHECK directive now show as "healthy" instead of "unknown" (grafana, loki, prometheus, nextcloud)
- **Dashboard Hardcoded 45min**: Replaced mock MTTR value with actual LLM response latency from health endpoint
- **Dashboard Empty States**: Remediation Performance section shows appropriate empty state messages
- **Graph Explorer No Edges**: Added default service dependencies that are always shown (frontend→backend, backend→neo4j/loki/prometheus, etc.)
- **Service Availability Bars**: Fixed health status mapping - running containers now display green bars

### Added
- **Promtail Log Shipping**: Added Promtail container to ship Docker container logs to Loki (LGTM stack)
- **Jarvis Labs LLM Integration**: docker-compose.yml now defaults to Jarvis Labs Ollama endpoint for qwen3:4b and qwen3:14b models

### Changed
- **Dashboard Metrics Labels**: Changed "Mean time to resolve" to "LLM response latency" for clarity
- **DashboardStats Interface**: `mttr_minutes` now accepts `number | null` type

### Added
- **Agents Page** (`/agents`): New comprehensive agent management interface with 5 tabs:
  - Fast Agent Activity: Real-time telemetry annotation stream
  - Reasoning Agent Activity: RCA and planning results
  - Telemetry Viewer: Logs, metrics, traces from LGTM stack
  - Graph Explorer: Neo4j episodic memory visualization
  - MCP Tools: Tool configuration and execution interface
- **Backend API Endpoints**:
  - `/api/v1/agents/fast/activity` - Fast agent activity stream
  - `/api/v1/agents/reasoning/activity` - Reasoning agent activity stream
  - `/api/v1/telemetry/logs` - Log queries from Loki
  - `/api/v1/telemetry/metrics` - Metrics from Prometheus
  - `/api/v1/telemetry/traces` - Traces from Tempo
  - `/api/v1/graph/episodes` - Neo4j episodic memory
  - `/api/v1/graph/services` - Service dependency graph
  - `/api/v1/prompts/` - System prompt management
- **System Prompts Tab** in Settings: View and customize prompts for Fast/Reasoning agents
- Navigation link to Agents page in sidebar

### Fixed
- **CRITICAL: Layout.tsx Hardcoded Agent Status**: Bottom-left sidebar now shows dynamic health status instead of always "Online"
- **Incidents.tsx Mock Data**: Removed fallback mock data array, now shows empty state on API errors
- **Dashboard.tsx Mock Activity**: Removed hardcoded "Recent Activity" items, now shows proper empty state
- **Error Messages**: Improved error display with proper styling (red for errors instead of yellow)

### Changed
- Jarvis Labs hybrid deployment support
  - `docker/docker-compose.hybrid.yml` for local + remote LLM architecture
  - `scripts/setup-jarvis-ollama.sh` for model setup on Jarvis Labs
  - `docs/JARVIS_LABS_DEPLOYMENT.md` complete setup guide
- `docs/plans/` folder for sub-implementation plans
  - `docs/plans/jarvis-labs-qwen3-deployment.md` - Qwen3 migration plan

### Fixed
- **Config Environment Variables**: Model names now read from `FAST_AGENT_MODEL` and `REASONING_AGENT_MODEL` environment variables instead of being hardcoded
- **httpx URL Resolution**: Changed absolute paths (`/chat/completions`) to relative paths (`chat/completions`) in model_router.py for correct URL resolution with base_url
- **Health Check Endpoint**: Updated docker-compose.yml healthcheck from `/health` to `/api/v1/health`
- **Chat API Hardcoded Responses**: Removed mock response functions (`_mock_chat_response`, `_mock_analysis_response`) that could mask real LLM errors. Now raises HTTP 503 with clear error messages when agent unavailable.
- **Frontend HealthResponse Type Mismatch**: Fixed type definition in `api.ts` - changed from object structure to array to match backend response format. Added `isComponentHealthy()` helper function.
- **Frontend Mock Data Fallback**: Removed mock data fallbacks from Dashboard.tsx and Chat.tsx. Now shows proper error messages when API calls fail.
- **Frontend Agent Status Display**: Fixed Dashboard.tsx and Settings.tsx to correctly show agents as "online" when healthy using the new helper function.

### Changed
- **Model Upgrade**: Migrated from Qwen2.5 to Qwen3 models
  - Fast Agent: qwen2.5:3b → qwen3:4b (better reasoning benchmarks)
  - Reasoning Agent: qwen2.5:14b → qwen3:14b
  - Research: Qwen3-4B outperforms Qwen2.5-7B (MMLU-Pro: 74 vs 45)
- **Data Persistence Fix**: Models now stored in `/home/ollama-models`
  - Only `/home` directory persists on Jarvis Labs pause/resume
  - Setup script configures OLLAMA_MODELS environment variable
- Updated deployment strategy from AWS-only to hybrid (Jarvis Labs + Local)
- Added Windows PowerShell commands (Invoke-RestMethod) to documentation
- Updated API endpoint format to `.notebooks.jarvislabs.net`
- Added SSH private key protection to `.gitignore`
- Updated README.md with hybrid deployment instructions
- Updated CHECKLIST.md with Jarvis Labs testing tasks

---

## [0.3.0-alpha] - 2025-12-19 (Phase 4 - Deployment Package)

### Added

#### Deployment Scripts
- **scripts/install.sh**: One-command installation wizard
  - Hardware auto-detection (GPU, memory, CPU)
  - Prerequisites checking (Docker, Docker Compose, curl)
  - Automatic deployment mode selection
  - Environment file generation
  - Model download for GPU mode
  - Service startup with health verification

- **scripts/detect_hardware.py**: Python hardware detection
  - Cross-platform support (Linux, macOS, Windows)
  - GPU detection with NVIDIA Container Toolkit check
  - JSON output mode for automation
  - Deployment recommendations

- **scripts/inject_anomaly.py**: Anomaly injection for testing
  - CPU spike, memory leak, DB connection issues
  - Latency spike, error rate spike, disk warning
  - Cascading failure scenario
  - Load test scenario

#### Docker Configurations
- **docker/docker-compose.production.yml**: Production deployment
  - Resource limits and reservations
  - Security hardening (internal-only ports)
  - Logging configuration with rotation
  - Health checks for all services

- **docker/docker-compose.hybrid.yml**: Jarvis Labs hybrid mode
  - Disables llama-swap (uses remote Ollama)
  - Configures backend for JARVIS_OLLAMA_URL

- **docker/Dockerfile.mock-llm**: Mock LLM server image

#### Documentation
- **QUICKSTART.md**: Quick start guide
- **docs/AWS_DEPLOYMENT.md**: AWS deployment guide
- **docs/JARVIS_LABS_DEPLOYMENT.md**: Jarvis Labs deployment guide
- **docs/Cloud_provider_discussions.md**: Cloud provider research

#### Phase 2 Features (MCP, WebSocket, Audit)
- **src/mcp/server.py**: MCP Action Server with 5 tools
  - find_similar, get_dependencies, restart_service, scale_service, analyze_logs
- **src/api/routes/tools.py**: Tools API endpoint
- **src/utils/websocket.py**: WebSocket connection manager
- **src/utils/audit.py**: Comprehensive audit logging
- **frontend/src/lib/api.ts**: Type-safe API client
- **frontend/src/lib/websocket.ts**: React WebSocket hook

#### Phase 3 Features (Visualization)
- **frontend/src/components/IncidentTimeline.tsx**: Incident event timeline
- **frontend/src/components/DependencyGraph.tsx**: Service dependency visualization
- **frontend/src/pages/Settings.tsx**: Enhanced settings with 4 tabs

### Changed
- Updated mock_llm_server.py with health proxy and /v1/models endpoints
- Updated frontend pages with API integration and real-time updates
- Updated main.py with WebSocket endpoint

### Milestone
**Phase 4: Deployment Package - Files Ready (Jarvis Labs testing pending)**

---

## [0.2.0-alpha] - 2025-12-15 (Phase 1 Complete)

### Added

#### Memory Integration
- **src/memory/neo4j_client.py**: Async Neo4j client
  - Schema initialization (nodes: Service, Incident, Action, Episode)
  - Incident and action CRUD operations
  - Service dependency graph queries
  - Action success rate calculations
  - Graceful fallback with `NEO4J_AVAILABLE` flag

- **src/memory/episode_store.py**: Episode storage system
  - `Episode` dataclass with full incident lifecycle
  - In-memory store with Neo4j sync capability
  - Similarity search using cosine distance on signatures
  - Pattern extraction from successful remediations
  - Service-based incident lookup

- **src/memory/retrieval.py**: Context retrieval for RAG
  - `RetrievalContext` with similar incidents, dependencies, patterns
  - `ContextRetriever` for incident, RCA, and planning contexts
  - Caching with 5-minute TTL
  - Service reliability scoring
  - Prompt-ready context formatting

#### Telemetry Processing
- **src/telemetry/collector.py**: LGTM stack integration
  - `TelemetryCollector` for Loki, Prometheus, Tempo
  - `LogEntry`, `MetricPoint`, `TraceSpan` dataclasses
  - `TelemetryWindow` for time-windowed collection
  - Health check for telemetry backends
  - Configurable endpoints

- **src/telemetry/compressor.py**: Token compression
  - `TokenCompressor` with configurable target tokens
  - `CompressedTelemetry` with deduplication stats
  - Log deduplication and pattern extraction
  - Error/warning prioritization
  - Fast agent (500 tokens) and reasoning agent (1500 tokens) modes

- **src/telemetry/aggregator.py**: Telemetry aggregation
  - `TelemetryAggregator` for service health analysis
  - `ServiceHealth` with health score calculation
  - `IncidentContext` with anomaly detection
  - Health score formula: weighted average (error rate, latency, availability)
  - Trend analysis (improving/degrading/stable)

#### Tests
- **tests/test_api/test_routes.py**: Comprehensive API tests
  - TestHealthRoutes: liveness, readiness probes
  - TestChatRoutes: conversation creation, continuation
  - TestIncidentRoutes: CRUD, filtering, updates
  - TestActionRoutes: validation workflow, approvals
  - TestSchemas: Pydantic validation
  - TestMemoryComponents: episode store, similarity
  - TestTelemetryComponents: compression, health scoring

- **tests/conftest.py**: Additional fixtures
  - `mock_model_router`, `mock_neo4j_client`
  - `sample_incident_create`, `sample_action_create`
  - `sample_episode`, `constitutional_context`

### Changed
- **src/main.py**: Full lifespan management
  - Initialize Neo4j with fallback to in-memory
  - Initialize all telemetry components
  - Health checks for LLM servers and telemetry backends
  - Proper shutdown cleanup for all connections

- **src/memory/__init__.py**: Export all memory components
- **src/telemetry/__init__.py**: Export all telemetry components

### Milestone
**Phase 1: Core Architecture - 100% COMPLETE**

---

## [0.1.1-alpha] - 2025-12-15

### Added

#### API Routes
- **src/api/routes/health.py**: Comprehensive health endpoints
  - `GET /api/v1/health` - System health with component status
  - `GET /api/v1/health/ready` - Kubernetes readiness probe
  - `GET /api/v1/health/live` - Kubernetes liveness probe
  - `GET /api/v1/health/agents` - Detailed LLM agent status

- **src/api/routes/chat.py**: Chat and analysis endpoints
  - `POST /api/v1/chat` - Send message to reasoning agent
  - `POST /api/v1/chat/analyze` - Run RCA or planning analysis
  - `GET /api/v1/chat/conversations` - List active conversations
  - `GET /api/v1/chat/conversations/{id}` - Get conversation history
  - `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

- **src/api/routes/incidents.py**: Incident management CRUD
  - `POST /api/v1/incidents` - Create incident with auto-analysis
  - `GET /api/v1/incidents` - List with pagination and filters
  - `GET /api/v1/incidents/stats` - Aggregated statistics
  - `GET /api/v1/incidents/{id}` - Get incident details
  - `PATCH /api/v1/incidents/{id}` - Update incident
  - `DELETE /api/v1/incidents/{id}` - Delete incident
  - `POST /api/v1/incidents/{id}/analyze` - Trigger RCA
  - `GET /api/v1/incidents/{id}/similar` - Find similar incidents

- **src/api/routes/actions.py**: Action management with Constitutional AI
  - `POST /api/v1/actions` - Create and validate action
  - `GET /api/v1/actions` - List with filters
  - `GET /api/v1/actions/pending` - Pending approvals summary
  - `GET /api/v1/actions/stats` - Action statistics
  - `GET /api/v1/actions/{id}` - Get action details
  - `POST /api/v1/actions/{id}/approve` - Human approval workflow
  - `POST /api/v1/actions/{id}/execute` - Execute approved action
  - `POST /api/v1/actions/{id}/cancel` - Cancel action

#### API Schemas
- **src/api/schemas/chat.py**: Chat-related Pydantic models
  - `ChatMessage`, `ChatRequest`, `ChatResponse`
  - `ConversationHistory`
  - `AnalysisRequest`, `AnalysisResponse`

- **src/api/schemas/incident.py**: Incident Pydantic models
  - `Incident`, `IncidentCreate`, `IncidentUpdate`
  - `IncidentSeverity`, `IncidentStatus`, `IncidentCategory`
  - `RCAResult`, `RemediationStep`, `RemediationPlan`
  - `ServiceInfo`, `TelemetrySnapshot`
  - `IncidentList`, `IncidentFilter`, `IncidentStats`

- **src/api/schemas/action.py**: Action Pydantic models
  - `Action`, `ActionCreate`, `ActionApproval`
  - `ActionType`, `ActionStatus`, `AuthorizationLevel`
  - `ConstitutionalValidation`, `ActionExecutionResult`
  - `ActionList`, `ActionFilter`, `ActionStats`, `PendingApprovals`

### Changed
- **src/main.py**: Updated to include all routers and initialize components
  - Added router imports and registrations
  - Initialize ModelRouter, agents, and validator in lifespan
  - Added proper shutdown cleanup
  - Updated root endpoint with API endpoint listing

- **src/api/routes/__init__.py**: Export all routers
- **src/api/schemas/__init__.py**: Export all schemas

### Fixed
- N/A

---

## [0.1.0-alpha] - 2025-12-14

### Added

#### Documentation
- **CLAUDE.md**: Complete AI development instructions with session lifecycle
- **PROJECT_SUMMARY.md**: Full requirements history across 6 sessions (Dec 6-14)
- **README.md**: Project overview with quick start guide
- **MEGA_PROMPT.md** (Parts 1-3): Detailed implementation guide (~120KB total)
- **references.bib**: 40+ BibTeX citations for research paper
- **Architecture diagrams**: 3 SVG diagrams (dual-agent, constitutional-ai, token-compression)

#### Core Backend
- **src/config.py**: Configuration management with environment variables
- **src/main.py**: FastAPI application with lifespan management
- **src/agents/model_router.py**: Dual-endpoint routing (no hot-swap)
- **src/agents/base_agent.py**: Abstract base class with confidence levels
- **src/agents/fast_annotator.py**: Qwen3-4B telemetry annotation agent
- **src/agents/reasoning_agent.py**: Qwen3-14B RCA and chat agent
- **src/constitutional/principles.py**: 11 principles across 3 tiers
- **src/constitutional/validator.py**: Action validation with authorization matrix
- **src/utils/logging.py**: Structured logging configuration

#### Docker & Deployment
- **docker-compose.yml**: Full stack composition (Neo4j, LGTM, backend, frontend)
- **docker/docker-compose.gpu.yml**: GPU deployment with llama-swap
- **docker/docker-compose.local.yml**: Local development with mock LLM
- **docker/Dockerfile.backend**: Python FastAPI container
- **docker/Dockerfile.frontend**: React production container
- **docker/configs/llama-swap.yaml**: Dual-model configuration (TTL: -1)
- **docker/configs/prometheus.yml**: Metrics collection
- **docker/configs/otel-collector.yaml**: OpenTelemetry pipeline
- **docker/configs/tempo-config.yaml**: Distributed tracing

#### Frontend
- **React 18 + TypeScript + Tailwind** setup
- **Dashboard page**: System overview with stats
- **Incidents page**: Incident list with filtering
- **Chat page**: Interactive chat with reasoning agent
- **Settings page**: Constitutional AI configuration
- **Layout component**: Sidebar navigation

#### Scripts
- **scripts/download-models.sh**: Model downloader for Qwen3 GGUF
- **scripts/setup.sh**: Initial environment setup
- **scripts/mock_llm_server.py**: Mock endpoints for local development

#### Tests
- **tests/conftest.py**: Pytest fixtures and configuration
- **tests/test_agents/test_model_router.py**: ModelRouter unit tests
- **tests/test_constitutional/test_validator.py**: Validator unit tests

### Changed

#### Architecture Migration (v2.0)
- **Models**: Qwen3-8B → **Qwen3-4B** for fast agent (smaller, faster)
- **Hardware**: T4 16GB → **L4 24GB** for simultaneous loading
- **Code**: ModelManager → **ModelRouter** (simplified, no swap logic)
- **Cost**: ~$14/mo → ~$28/mo (justified by zero latency)

### Fixed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- Hot-swap model management (replaced with simultaneous loading)
- Complex timeout management code

### Security
- Constitutional AI Tier 1 principles enforce safety-critical constraints
- All actions logged for audit trail
- Human approval required for uncertain actions (70-90% confidence)

---

## Session History

### Session 12: 2025-12-20 - Qwen3 Model Upgrade & Persistence Fix
- Researched Qwen3 vs Qwen2.5 models - Qwen3-4B significantly outperforms Qwen2.5-7B
  - MMLU-Pro: 74 vs 45, GPQA: 59 vs 36.4, MATH: 90 vs 49.8
- Discovered critical data persistence issue on Jarvis Labs (only /home persists)
- Created docs/plans/ folder for sub-implementation plans
- Created docs/plans/jarvis-labs-qwen3-deployment.md
- Updated all Jarvis Labs deployment files for Qwen3:
  - docker/docker-compose.hybrid.yml: qwen3:4b + qwen3:14b
  - scripts/setup-jarvis-ollama.sh: OLLAMA_MODELS=/home/ollama-models
  - docs/JARVIS_LABS_DEPLOYMENT.md: Complete rewrite with persistence fix
  - README.md: Updated hybrid deployment section
- Added Windows PowerShell commands (Invoke-RestMethod)
- VRAM verified: Both models fit on A5000 24GB with ~8-9GB free
- **QWEN3 MIGRATION COMPLETE - READY FOR JARVIS LABS TESTING**

### Session 11: 2025-12-19 - Jarvis Labs Hybrid Deployment
- Researched Jarvis Labs deployment options (Ollama template vs VM)
- Discovered Ollama template provides direct HTTPS API (no SSH tunnel!)
- Created docker/docker-compose.hybrid.yml for local + remote architecture
- Created scripts/setup-jarvis-ollama.sh for model setup
- Created docs/JARVIS_LABS_DEPLOYMENT.md complete guide
- Updated .gitignore with SSH private key protection
- Updated README.md with hybrid deployment section
- Updated CHECKLIST.md with Jarvis Labs testing tasks
- Generated SSH key pair for authentication
- **JARVIS LABS SETUP FILES READY**

### Session 10: 2025-12-18 - Cloud Provider Research & GitHub Setup
- Researched AWS quota issues (all G-family need approval)
- Explored alternative cloud providers (Jarvis Labs, Lambda Labs, Vast.ai)
- Created docs/Cloud_provider_discussions.md
- Pushed codebase to GitHub (Partha-dev01/Aiops_Final)
- Discussed hybrid architecture (local dev + remote GPU)

### Session 9: 2025-12-17 - Phase 4 Deployment Package
- Created scripts/install.sh (installation wizard)
- Created scripts/detect_hardware.py (hardware detection)
- Created docker/docker-compose.production.yml
- Created docker/Dockerfile.mock-llm
- Created QUICKSTART.md
- Created docs/AWS_DEPLOYMENT.md
- **PHASE 4: FILES READY**

### Session 8: 2025-12-15 - Phase 1 Complete (Memory, Telemetry, Tests)
- Implemented Neo4j async client with graceful fallback
- Implemented episode store with similarity search
- Implemented context retrieval for RAG patterns
- Implemented telemetry collector (Loki, Prometheus, Tempo)
- Implemented token compressor for LLM contexts
- Implemented telemetry aggregator with health scoring
- Updated main.py with full lifespan management
- Created comprehensive API tests
- Updated documentation
- **PHASE 1: 100% COMPLETE**

### Session 7: 2025-12-15 - API Routes & Schemas
- Implemented all API routes (health, chat, incidents, actions)
- Created comprehensive Pydantic schemas
- Updated main.py with router integration
- Constitutional AI validation workflow in actions API
- Mock responses for development without LLM

### Session 6: 2025-12-14 - Complete Project Setup
- Created comprehensive PROJECT_SUMMARY.md
- Updated all documentation for 24GB architecture
- Implemented core source files
- Set up Docker configurations
- Created React frontend
- Added tests

### Session 5: 2025-12-10 - 24GB GPU Research
- Analyzed simultaneous model loading feasibility
- VRAM calculations: ~15GB / 24GB
- Recommended L4/A10G migration

### Session 4: 2025-12-10 - Documentation Package
- Created 11 files, 220KB total
- MEGA_PROMPT parts 1-3
- CHECKLIST, CHANGELOG, ISSUES

### Session 3: 2025-12-06 - Architecture Finalization
- Defined dual-agent architecture
- Selected T4 16GB with hot-swap (later changed)
- Established Constitutional AI framework

### Session 2: 2025-12-06 - Enterprise Research
- Telemetry volume analysis
- GPU cost comparison
- Model selection (Qwen3 family)
- Compliance requirements

### Session 1: 2025-12-06 - Initial Vision
- B.Tech project requirements
- Constitutional AI concept
- Graph-episodic memory design

---

## Versioning

This project uses [Semantic Versioning](https://semver.org/):
- MAJOR: Incompatible API changes
- MINOR: Backward-compatible functionality
- PATCH: Backward-compatible bug fixes

Current: **0.4.5** (Environment & container fixes)
