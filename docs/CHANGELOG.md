# Constitutional AIOps - Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Jarvis Labs hybrid deployment support
  - `docker/docker-compose.hybrid.yml` for local + remote LLM architecture
  - `scripts/setup-jarvis-ollama.sh` for model setup on Jarvis Labs
  - `docs/JARVIS_LABS_DEPLOYMENT.md` complete setup guide

### Changed
- Updated deployment strategy from AWS-only to hybrid (Jarvis Labs + Local)
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

Current: **0.3.0-alpha** (Phase 4 files ready, Jarvis Labs testing pending)
