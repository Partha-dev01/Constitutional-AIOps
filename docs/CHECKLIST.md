# Constitutional AIOps - Development Checklist

> **Version**: 0.11.0
> **Last Updated**: 2026-05-13
> **Status**: Phase 4.2 complete — 431-case benchmark 88.6% accuracy. Phases 4.3/4.4/4.5/4.7 pending.
> **Architecture**: Simultaneous Dual-Model (Qwen3-4B + Qwen3-14B on 24GB VRAM)
> **Deployment**: AWS g6.xlarge L4 24GB (Stack A Ollama Q4_K_M)

---

## Recent Updates (2026-05-13) ✅

### v0.11.0 - Phase 4.2 Benchmark Complete + Graph Memory Fixed

#### Completed This Session
- [x] **Phase 4.2**: Main benchmark 431 cases — **88.6% overall** (382/431), annotation 82.6%, RCA 94.8%
- [x] **Graph memory fake context fixed**: `_build_sample_graph_context()` was injecting hardcoded fake incidents (EP-2024-087/134). Replaced with real async Neo4j cosine retrieval via `_build_real_graph_context()`
- [x] **OpsEval-remine 33 cases fixed**: severity KeyError patched + all 33 enriched with A/B/C/D option text recovered from raw OpsEval data — 0% → 100% accuracy
- [x] **`mine_opseval.py` fixed**: now embeds answer choices in question text and converts letter answers to option text for semantic matching
- [x] **`scripts/populate_neo4j.py`**: new Phase 4.4 population script (reads benchmark JSON, creates real Episode objects with 384-dim embeddings, idempotent MERGE)
- [x] **Gate §15**: Stack A P95 65.96s / Stack B P95 43.71s = 1.51× speedup → PASS
- [x] **CI golden smoke**: 22/22 tests passing (schema-only, no LLM required)
- [x] **Merged results**: `benchmark/results_aws/run_stackA_main431/results_merged.json` — authoritative 431-case results

#### OpenSSH 50% — Confirmed Not a Bug
All 20 failures are false positives: model flags isolated auth events; Loghub labels only brute-force campaigns as anomaly. 0 false negatives. Report as precision/recall tradeoff in paper Table 4.

#### Pending (in priority order)
- [ ] Phase 4.7: SOTA baselines (Llama 3.3 70B + DeepSeek R1 via Bedrock, ~110 min total from laptop)
- [ ] Phase 4.3: 7-config ablation on 400 cases (Stack A, overnight ~15 hrs on instance)
- [ ] Phase 4.4: Populate Neo4j — `python3 scripts/populate_neo4j.py` on instance
- [ ] Phase 4.5: Graph memory sub-experiments (4.5a heterogeneous, 4.5b LEMMA 5-fold, 4.5c cold-start)
- [ ] Phase 5: Bootstrap BCa CIs (10k resamples), McNemar tests, Cohen's h
- [ ] Phase 6: Paper update — Tables 1-9, Figure 4/5, 3 paragraph reframes, 12 new references

#### AWS State (2026-05-13)
- Instance: `i-091c4de0e95d63154` RUNNING, EIP 44.195.172.165
- Stack A (Ollama) active, Stack B (vLLM) stopped
- Budget: ~$12 / $120 ceiling (~10% used)

---

## Recent Updates (2026-03-01) ✅

### v0.10.1 - Dashboard Integration & Chat Fix
- [x] Added `load_dotenv()` to `src/config.py` for proper `.env` loading
- [x] Fixed chat `_build_runtime_context()` — always reports status even when Docker unavailable
- [x] Removed emoji from runtime context (token encoding issues)
- [x] Added fallback system prompt text when no runtime data available
- [x] LangGraph orchestration deployed to Jarvis Labs (v0.10.0)
- [x] Local dashboard verified end-to-end with Playwright screenshots
- [x] Neo4j graph populated (72 nodes, 97 edges, 9 episodes)
- [x] Both agents healthy via Jarvis Labs HTTPS

### v0.10.0 - LangGraph Orchestration Pipeline
- [x] Added mandatory LangGraph StateGraph pipeline (5 nodes, 2 conditional edges)
- [x] Talker-Reasoner architecture (System 1 → System 2 escalation)
- [x] Deployed to Jarvis Labs with both Qwen3 models
- [x] Benchmark: 100% annotation, 80% RCA on 5+5 smoke test

---

## Previous Updates (2026-01-30) ✅

### v0.7.1 - LEMMA-RCA Cloud Computing Integration
- [x] Added LEMMA-RCA Cloud Computing dataset from HuggingFace (~4.74GB)
- [x] Updated `requirements.txt` - Added datasets>=2.14.0, huggingface-hub>=0.17.0
- [x] Added `download_lemma_rca()` function to `benchmark/scripts/download_datasets.py`
- [x] Added `--skip-lemma` and `--lemma-only` CLI flags for download flexibility
- [x] Added `load_lemma_rca()` function to `benchmark/scripts/prepare_datasets.py`
- [x] Updated `create_rca_dataset()` to merge OpsEval (100) + LEMMA-RCA (100) = 200 RCA cases
- [x] Total benchmark cases: 200 annotation + 200 RCA = **400 test cases**
- [x] Updated all documentation (CHECKLIST, CHANGELOG, BENCHMARK.md)

---

## Previous Updates (2026-01-29) ✅

### v0.7.0 - Conference-Level Benchmarking System
- [x] Created `benchmark/` directory structure with datasets, scripts, results folders
- [x] Downloaded REAL datasets from OpsEval (8,920 QA) and Loghub (HDFS + BGL logs)
- [x] Created `benchmark/scripts/download_datasets.py` for automated dataset download
- [x] Created `benchmark/scripts/prepare_datasets.py` for data preprocessing
- [x] Created `benchmark/scripts/run_benchmark.py` with network latency compensation
- [x] Created `benchmark/scripts/evaluate_results.py` with BERTScore (DeBERTa-XLarge-MNLI)
- [x] Created `benchmark/scripts/export_metrics.py` for JSON/CSV/LaTeX export
- [x] Created `src/benchmark/runner.py` - BenchmarkRunner class
- [x] Created `src/benchmark/evaluator.py` - BenchmarkEvaluator with metrics
- [x] Created `src/api/routes/benchmark.py` - REST API endpoints (/models, /datasets, /run, /results, /compare, /export)
- [x] Created `frontend/src/pages/Benchmark.tsx` - Full benchmark UI (4 tabs: Datasets, Run, Results, Compare)
- [x] Updated `frontend/src/components/Layout.tsx` - Removed Demo Mode, added Benchmark nav
- [x] Updated `frontend/src/App.tsx` - Added /benchmark route
- [x] Updated `requirements.txt` - Added bert-score>=0.3.13, transformers>=4.30.0
- [x] Created `docs/BENCHMARK.md` - Comprehensive benchmark documentation
- [x] Updated all documentation files (README, INDEX, CHECKLIST, CHANGELOG, API)
- [x] Prepared 200 annotation test cases (100 HDFS + 100 BGL, balanced normal/anomaly)
- [x] Prepared 100 RCA test cases from OpsEval QA questions

---

## Previous Updates (2026-01-28) ✅

### v0.6.1 - Episode Generation via Reasoning Agent
- [x] Created `/api/v1/graph/generate-episodes` endpoint for LLM-based episode generation
- [x] Implemented SERVICE_TEMPLATES with 8 services (neo4j, prometheus, grafana, loki, tempo, otel-collector, backend, frontend)
- [x] Added EPISODE_GENERATION_TEMPLATE for Qwen3-14B prompts
- [x] Created `frontend/src/pages/Graph.tsx` - Dedicated graph visualization page
- [x] Added Graph page to sidebar navigation in Layout.tsx
- [x] Created `scripts/generate_real_episodes.py` for batch episode generation
- [x] Updated all documentation to v0.6.1

### v0.6.0 - Graph Schema Redesign (2026-01-25)
- [x] Implemented hairball prevention with degree capping
- [x] Added `SIMILAR_TO_THRESHOLD = 0.75` for episode similarity edges
- [x] Added `MAX_SIMILAR_EDGES_PER_EPISODE = 3` degree cap
- [x] Added `MIN_TRIPLET_CONFIDENCE = 0.70` for LLM-extracted triplet filtering
- [x] Added `MAX_EDGES_PER_NODE = 5` global degree cap
- [x] Created `src/confidence/calculator.py` with composite formula
- [x] Entity canonicalization (70+ variants → 15 canonical forms)
- [x] Created `src/memory/embedding_service.py` for 384-dim embeddings
- [x] Updated EpisodicGraphExplorer physics (CHARGE_STRENGTH=-300)

---

## Previous Updates (2026-01-15) ✅

### v0.5.1 - Docker Service Recovery & Bug Fixes
- [x] Added health checks to all docker-compose services (loki, prometheus, tempo, grafana, frontend, otel-collector)
- [x] Added conditional dependencies (`service_healthy`) to ensure proper startup order
- [x] Standardized Neo4j health check to use curl (was wget)
- [x] Fixed services recovering properly after Docker Desktop restart
- [x] Fixed Neo4j query method in `graph.py` (execute_read → run, 7 locations)
- [x] Fixed Fast Agent JSON parsing with brace-matching fallback in `fast_annotator.py`
- [x] Added system prompt for strict JSON output in `model_router.py`
- [x] Implemented episode compaction to reduce graph clutter in `background_processor.py`

---

## Previous Updates

### v0.5.0 - Graphiti-Style Force-Directed Graph Visualization (2026-01-11)
- [x] Created `EpisodicGraphExplorer.tsx` - Force-directed graph with `react-force-graph-2d`
- [x] Added custom TypeScript declarations for `react-force-graph-2d` library
- [x] Interactive controls: Zoom In/Out, Fit to View, Pause/Resume Animation, Reset View
- [x] Node filtering by type: Services, Episodes, Incidents, Actions
- [x] Color-coded nodes by status: Healthy (green), Warning (amber), Critical (red)
- [x] Edge rendering with directional arrows and relationship labels
- [x] Node details panel on click with confidence, severity, timestamp
- [x] Fixed edge display bug - now correctly shows service dependencies
- [x] Updated Jarvis Labs SSH port to 11114 (ssho.jarvislabs.ai)

---

## Previous Updates

### v0.4.8 - Architecture Compliance Fix (2026-01-09)
- [x] Fixed `TelemetryCollector.query_logs()` to use correct Loki label `{job="containerlogs"}`
- [x] Fixed `TelemetryCollector.query_metrics()` to query generic Prometheus metrics
- [x] Removed HTTP bypass from `BackgroundTelemetryProcessor` - now uses TelemetryCollector
- [x] Architecture compliant with Research_V7.tex: `LGTM → TelemetryCollector → BackgroundProcessor → Fast Agent`

### v0.4.7 - Background Telemetry Processor
- [x] Created `src/telemetry/background_processor.py` - Continuous Fast Agent scanning (System 1)
- [x] Processes telemetry every 30 seconds via TelemetryCollector
- [x] Escalates to Reasoning Agent when `needs_reasoning=true`
- [x] Stores annotations and episodes in Neo4j graph
- [x] Added `/api/v1/telemetry/processor/status` endpoint

### v0.4.6 - Infrastructure Fixes
- [x] Removed hardcoded Jarvis Labs URLs from docker-compose.yml
- [x] Fixed Neo4j health check (curl → wget)
- [x] Added Chat UI typewriter effect + thinking indicator
- [x] Added Nextcloud to docker-compose.yml

---

## Codebase Synchronization (2025-12-30) ✅

All codebase files now match documentation (Research_V7.tex, KEY_METRICS.md).

### Backend Updates ✅
- [x] `src/agents/fast_annotator.py` - Latency: <50ms P99 → <100ms P95
- [x] `src/agents/reasoning_agent.py` - Latency: <200ms P99 → 200-500ms P95
- [x] `src/main.py` - Version: 0.2.0 → 0.4.0
- [x] `src/config.py` - Added MemoryConfig, PerformanceConfig classes
- [x] `src/memory/episode_store.py` - Added embedding constants
- [x] `src/memory/retrieval.py` - Documented hybrid retrieval formula
- [x] `src/validation/constants.py` - NEW: Centralized validation constants

### Frontend Updates ✅
- [x] `frontend/package.json` - Version: 0.1.0 → 0.4.0
- [x] `frontend/src/pages/Settings.tsx` - Latency: <50ms → <100ms P95, <200ms → 200-500ms P95
- [x] `frontend/src/pages/Dashboard.tsx` - Latency: 42ms/156ms → <100ms P95/200-500ms P95

### New Validation Module ✅
Created `src/validation/constants.py` with:
- PerformanceTargets (latency, resolution time)
- AccuracyTargets (annotation, RCA)
- CompressionMetrics (token compression, tool sprawl)
- MemorySystemConfig (embeddings, similarity, retrieval)
- ConstitutionalAIConfig (thresholds, weights, principles)
- VRAMConfig (model allocations)
- ObservabilityVersions (stack versions, retention)
- ResearchGaps (RG1-RG5 definitions)

---

## Project Completion Summary

| Phase | Focus | Status | Completion |
|-------|-------|--------|------------|
| Phase 1 | Core Architecture | ✅ Complete | 100% |
| Phase 2 | Intelligence Layer | ✅ Complete | 100% |
| Phase 3 | Dashboard & Polish | ✅ Complete | 100% |
| Phase 4 | Deployment Package | ✅ Complete | 100% |
| Phase 5 | Documentation | ✅ Complete | 100% |
| Phase 6 | Research Paper | ✅ Complete | 100% |

**Overall Status**: 100% Core Complete

---

## Component Status

### Backend (47+ Python files) ✅

#### Core Modules
- [x] `src/main.py` - FastAPI entry point with lifespan management
- [x] `src/config.py` - Environment-based configuration

#### Agents Module (src/agents/)
- [x] `model_router.py` - Dual-endpoint HTTP routing
- [x] `base_agent.py` - Base agent class
- [x] `fast_annotator.py` - Qwen3-4B agent (<100ms P95)
- [x] `reasoning_agent.py` - Qwen3-14B agent (200-500ms P95)

#### Constitutional AI (src/constitutional/)
- [x] `principles.py` - 12 principles, 3 tiers
- [x] `validator.py` - Action validation engine

#### Confidence (src/confidence/) - NEW v0.6.0
- [x] `calculator.py` - Composite confidence: C(a) = α·C_LLM + β·C_hist + γ·C_sim

#### Benchmark (src/benchmark/) - NEW v0.7.0
- [x] `runner.py` - BenchmarkRunner class for multi-model evaluation
- [x] `evaluator.py` - BenchmarkEvaluator with BERTScore metrics

#### Memory System (src/memory/)
- [x] `neo4j_client.py` - Neo4j async client
- [x] `episode_store.py` - Episodic memory storage with triplet filtering
- [x] `embedding_service.py` - 384-dim sentence embeddings (NEW v0.6.0)
- [x] `retrieval.py` - RAG context retrieval

#### Telemetry (src/telemetry/)
- [x] `collector.py` - LGTM stack integration
- [x] `compressor.py` - 92% token compression
- [x] `aggregator.py` - Health scoring

#### API Routes (src/api/routes/)
- [x] `health.py` - Kubernetes probes
- [x] `chat.py` - Interactive chat
- [x] `incidents.py` - Incident CRUD + RCA
- [x] `actions.py` - Action validation + approval
- [x] `tools.py` - MCP tools REST API
- [x] `agents.py` - Agent statistics
- [x] `telemetry.py` - LGTM queries
- [x] `graph.py` - Neo4j queries
- [x] `prompts.py` - System prompts
- [x] `infrastructure.py` - Docker monitoring
- [x] `demo.py` - Anomaly injection

#### MCP (src/mcp/)
- [x] `server.py` - Model Context Protocol server
- [x] 5 MCP tools implemented

#### Utils (src/utils/)
- [x] `logging.py` - Logging configuration
- [x] `audit.py` - Audit trail
- [x] `websocket.py` - Real-time events

---

### Frontend (26+ React files) ✅

#### Pages
- [x] `Dashboard.tsx` - Overview with real-time updates
- [x] `Incidents.tsx` - Incident list with CRUD
- [x] `Chat.tsx` - Interactive chat interface
- [x] `Agents.tsx` - Agent management (6 tabs)
- [x] `Graph.tsx` - Dedicated episodic graph page (NEW v0.6.1)
- [x] `Metrics.tsx` - LGTM observability metrics
- [x] `Benchmark.tsx` - LLM benchmarking interface (NEW v0.7.0)
- [x] `Settings.tsx` - Configuration (5 tabs)

#### Components
- [x] `Layout.tsx` - Navigation and structure
- [x] `EpisodicGraphExplorer.tsx` - Force-directed graph (NEW v0.5.0)
- [x] `IncidentTimeline.tsx` - Event timeline
- [x] `DependencyGraph.tsx` - Service dependencies

#### Libraries
- [x] `api.ts` - Type-safe API client
- [x] `websocket.ts` - WebSocket hook

---

### Infrastructure ✅

#### Docker Configurations
- [x] `docker-compose.yml` - Main composition
- [x] `docker/docker-compose.gpu.yml` - GPU deployment
- [x] `docker/docker-compose.local.yml` - Local development
- [x] `docker/docker-compose.hybrid.yml` - Jarvis Labs hybrid
- [x] `docker/docker-compose.production.yml` - Production

#### Configuration Files
- [x] `docker/configs/prometheus.yml`
- [x] `docker/configs/otel-collector.yaml`
- [x] `docker/configs/tempo-config.yaml`

#### Scripts
- [x] `scripts/install.sh` - Installation wizard
- [x] `scripts/detect_hardware.py` - Hardware detection
- [x] `scripts/download-models.sh` - Model download
- [x] `scripts/mock_llm_server.py` - Mock LLM

---

### Documentation ✅

#### Root Files
- [x] `README.md` - Project overview
- [x] `CLAUDE.md` - Context compaction safe (v3.0)

#### docs/ Directory
- [x] `INDEX.md` - Master documentation index
- [x] `KEY_METRICS.md` - Exportable paper metrics
- [x] `BENCHMARK.md` - Benchmarking system documentation (NEW v0.7.0)
- [x] `ARCHITECTURE.md` - System architecture
- [x] `BACKEND.md` - Python backend reference
- [x] `API.md` - REST API reference
- [x] `FRONTEND.md` - React frontend reference
- [x] `DEPLOYMENT.md` - Deployment overview
- [x] `CHECKLIST.md` - This file
- [x] `ISSUES.md` - Issue tracker
- [x] `CHANGELOG.md` - Version history
- [x] `JARVIS_LABS_DEPLOYMENT.md` - Jarvis Labs guide
- [x] `AWS_DEPLOYMENT.md` - AWS guide

#### Research
- [x] `docs/research/# IMP Current Research Documentation/Research_V7.tex` - Main paper (22 pages)
- [x] `docs/research/references.bib` - BibTeX citations
- [x] `docs/research/Whitepaper_Combined.md` - Combined whitepaper

---

## Performance Targets (From Research_V7.tex)

| Metric | Target | Status |
|--------|--------|--------|
| Fast Agent Latency | <100ms P95 | ✅ |
| Reasoning Agent Latency | 200-500ms P95 | ✅ |
| Annotation Accuracy | 87-92% | ✅ |
| RCA Accuracy | 85-90% | ✅ |
| Token Compression | 92% | ✅ |
| Resolution Time | <5 minutes | ✅ |
| Tool Sprawl Reduction | 93% | ✅ |

---

## Research Gaps Addressed

| ID | Gap | Status |
|----|-----|--------|
| RG1 | Automated Knowledge Extraction | ✅ Addressed |
| RG2 | Graph-Based Operational Knowledge | ✅ Addressed |
| RG3 | Observability-Specific Tokenization | ✅ Addressed |
| RG4 | Constitutional AI for Autonomous Operations | ✅ Addressed |
| RG5 | Comprehensive AI-Enhanced Observability | ✅ Addressed |

---

## Pending Items (Optional Enhancements)

| Item | Priority | Status |
|------|----------|--------|
| User Authentication | Low | Not Started |
| Production SSL Setup | Low | Not Started |
| Performance Benchmarks | Medium | Pending |
| CI/CD Pipeline | Low | Not Started |

---

## Key Technical Specifications

### Constitutional AI
- **12 Principles** across 3 tiers (4+4+4)
- **Authorization**: >0.90 auto, 0.70-0.90 approval, <0.70 alert
- **Formula**: `C(a) = 0.4·C_LLM + 0.35·C_hist + 0.25·C_sim`

### Dual-Agent Architecture
- **Fast Agent**: Qwen3-4B, Port 8081, ~4GB VRAM, 8K context
- **Reasoning Agent**: Qwen3-14B, Port 8082, ~11GB VRAM, 4K context
- **Total VRAM**: ~15GB / 24GB (63% utilization)

### Memory System
- **Neo4j 5.x**: O(log n) retrieval
- **Embeddings**: 384-dim, ≥0.70 cosine similarity
- **Hybrid Retrieval**: `score = α·vector_sim + (1-α)·graph_sim`

---

## Quick Reference

See [KEY_METRICS.md](KEY_METRICS.md) for complete metrics reference.
See [CLAUDE.md](../CLAUDE.md) for session management.

---

**Last Updated**: 2026-01-29
**Version**: 0.7.0
