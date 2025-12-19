# Constitutional AIOps - Mega Development Prompt

> **Version**: 0.1.0-alpha
> **Created**: 2025-12-06
> **Purpose**: Comprehensive development guide for implementing the Constitutional AIOps system

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Development Environment](#2-development-environment)
3. [Project Structure](#3-project-structure)
4. [Docker Configurations](#4-docker-configurations)
5. [Backend Implementation](#5-backend-implementation)
6. [Agent Framework](#6-agent-framework)
7. [Frontend Implementation](#7-frontend-implementation)
8. [Testing](#8-testing)
9. [AWS Deployment](#9-aws-deployment)
10. [Operational Scripts](#10-operational-scripts)

---

## 1. Project Overview

### 1.1 System Description

Constitutional AIOps is an autonomous infrastructure management system that:

1. **Monitors** infrastructure via OpenTelemetry (logs, metrics, traces)
2. **Analyzes** telemetry using Qwen3-4B (Q4_K_M) for fast annotation
3. **Reasons** about complex issues using Qwen3-14B (Q4_K_M) for deep analysis
4. **Validates** all actions against Constitutional AI safety principles
5. **Executes** approved actions via MCP tools
6. **Learns** from outcomes via graph-episodic memory
7. **Interacts** with humans via chat interface for oversight

**Dual-Model Architecture**: Both models run simultaneously on 24GB VRAM (AWS g6.xlarge L4 or g5.xlarge A10G), eliminating hot-swap latency and simplifying the codebase.

### 1.2 Core Principles

```
SAFETY FIRST: No action that could cause data loss or cascade failures
EVIDENCE BASED: All decisions backed by telemetry data
HUMAN IN LOOP: Uncertain actions require human approval
MINIMAL INTERVENTION: Prefer smallest effective action
CONTINUOUS LEARNING: Track outcomes for improvement
```

### 1.3 Model Architecture

**Target Hardware**: AWS g6.xlarge (NVIDIA L4 24GB) or g5.xlarge (NVIDIA A10G 24GB)

```
┌─────────────────────────────────────────────────────────────────┐
│              L4/A10G 24GB VRAM - SIMULTANEOUS LOADING           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ALWAYS LOADED (No Hot-Swapping):                               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FAST ANNOTATION AGENT                                    │  │
│  │  ─────────────────────                                    │  │
│  │  Model: Qwen3-4B Q4_K_M                                   │  │
│  │  VRAM: ~2.5GB model + ~1GB KV cache (8K ctx) = ~4GB      │  │
│  │  Port: 8081                                               │  │
│  │  Purpose: High-throughput telemetry annotation            │  │
│  │  Latency: <50ms                                           │  │
│  │  TTL: -1 (never unload)                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REASONING & CHAT AGENT                                   │  │
│  │  ────────────────────────                                 │  │
│  │  Model: Qwen3-14B Q4_K_M                                  │  │
│  │  VRAM: ~9GB model + ~1.5GB KV cache (4K ctx) = ~11GB     │  │
│  │  Port: 8082                                               │  │
│  │  Purpose: Complex RCA, remediation planning, chat         │  │
│  │  Latency: <200ms                                          │  │
│  │  TTL: -1 (never unload)                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FREE VRAM: ~9GB                                          │  │
│  │  Purpose: Extended context, batch processing, overhead    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  TOTAL: ~15GB used / 24GB available                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Quantization Selection Rationale**:
- **Q4_K_M** chosen for optimal balance of quality and size
- Better quality than Q4_0/Q4_1 with minimal size increase
- Maintains >95% of full precision accuracy for instruction-following
- Enables 8K context for fast agent, 4K for reasoning within VRAM budget

**Why 24GB Simultaneous vs 16GB Hot-Swap**:
| Factor | T4 16GB (Hot-Swap) | L4 24GB (Simultaneous) |
|--------|-------------------|------------------------|
| Swap Latency | 2-3 seconds | **0 ms** |
| Architecture Complexity | High | **Low** |
| Code Simplicity | Timeout management needed | **Direct routing** |
| Spot Price | $0.18/hr | $0.35/hr |
| Monthly (4hr×20 days) | ~$14 | ~$28 |
| Extra Cost | - | +$14/mo |

### 1.4 Data Flow

```
[Nextcloud Services]
        │
        ▼
[OpenTelemetry Collector]
        │
        ├──► [Loki] ──────► Logs
        ├──► [Tempo] ─────► Traces
        └──► [Prometheus] ► Metrics
                │
                ▼
        [Telemetry Aggregator]
                │
                ▼
        [Fast Annotator - Qwen3-4B @ :8081]
                │
        ┌───────┴───────┐
        ▼               ▼
[High Confidence]  [Low Confidence]
        │               │
        ▼               ▼
[Constitutional     [Reasoning Agent - Qwen3-14B @ :8082]
 Validator]               │
        │                 ▼
        │         [Constitutional
        │          Validator]
        │               │
        ▼               ▼
[MCP Action Server] ◄───┘
        │
        ▼
[Service Actions]
        │
        ▼
[Graph-Episodic Memory]
```

**Key Architecture Benefits**:
- Both models always loaded → Zero routing latency
- Direct port-based routing → No model manager complexity
- Fast agent handles 95% of telemetry → Efficient resource use
- Reasoning agent for complex RCA → Higher accuracy when needed

---

## 2. Development Environment

### 2.1 Local Development Setup

**Requirements (Local - No GPU)**:
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git
- 16GB RAM minimum
- 50GB disk space

**Purpose**: Code development, unit testing, frontend development

```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node dependencies
cd frontend
npm install

# Start local services (no GPU needed)
docker-compose -f docker/docker-compose.local.yml up -d
```

### 2.2 AWS GPU Testing Setup

**Recommended Instance: g6.xlarge (NVIDIA L4 24GB)**
- 1x NVIDIA L4 24GB GDDR6
- 4 vCPUs
- 16GB RAM
- 250GB NVMe SSD
- ~$0.35/hr (Spot), ~$0.805/hr (On-Demand)

**Alternative: g5.xlarge (NVIDIA A10G 24GB)**
- 1x NVIDIA A10G 24GB GDDR6
- 4 vCPUs
- 16GB RAM
- 250GB NVMe SSD
- ~$0.41/hr (Spot), ~$1.006/hr (On-Demand)

**Why 24GB over 16GB (T4)**:
- Both models loaded simultaneously (no hot-swapping)
- Zero model switch latency
- Simpler codebase (no swap logic)
- Worth extra ~$14/month for development

**Purpose**: Model testing, integration testing, performance validation

```bash
# Setup script for AWS g6.xlarge instance
#!/bin/bash
set -e

# Update system
sudo apt update && sudo apt upgrade -y

# Install NVIDIA drivers (L4 requires 535+)
sudo apt install -y nvidia-driver-535

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU (should show L4 with 24GB)
nvidia-smi
```

### 2.3 Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LOCAL MACHINE                        AWS GPU INSTANCE          │
│  ─────────────                        ────────────────          │
│                                                                 │
│  1. Write code                        5. Deploy via script      │
│  2. Run unit tests                    6. Run GPU tests          │
│  3. Test frontend                     7. Integration tests      │
│  4. Commit to git ──────────────────► 8. Performance tests      │
│                                       9. Debug issues           │
│                                       10. Stop instance!        │
│                    ◄──────────────────                          │
│  11. Review results                                             │
│  12. Iterate                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Project Structure

```
constitutional-aiops/
├── CLAUDE.md                           # AI assistant instructions
├── README.md                           # Project overview
├── LICENSE.md                          # License file
├── requirements.txt                    # Python dependencies
├── requirements-dev.txt                # Dev dependencies
├── pyproject.toml                      # Python project config
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
│
├── docs/                               # Documentation
│   ├── CHECKLIST.md                    # Development progress
│   ├── CHANGELOG.md                    # Version history
│   ├── ISSUES.md                       # Issue tracker
│   ├── ARCHITECTURE.md                 # System design
│   ├── API.md                          # API reference
│   ├── DEPLOYMENT.md                   # Deployment guide
│   ├── RESEARCH.md                     # Research notes
│   └── MEGA_PROMPT.md                  # This file
│
├── src/                                # Python source code
│   ├── __init__.py
│   ├── main.py                         # Application entry point
│   ├── config.py                       # Configuration management
│   │
│   ├── agents/                         # LLM agents
│   │   ├── __init__.py
│   │   ├── base.py                     # Base agent class
│   │   ├── fast_annotator.py           # 4B fast agent (Qwen3-4B)
│   │   ├── reasoning_agent.py          # 14B reasoning agent (Qwen3-14B)
│   │   ├── model_router.py             # Direct dual-endpoint routing
│   │   └── prompts/                    # Prompt templates
│   │       ├── __init__.py
│   │       ├── annotation.py
│   │       ├── rca.py
│   │       └── chat.py
│   │
│   ├── constitutional/                 # Constitutional AI
│   │   ├── __init__.py
│   │   ├── principles.py               # Safety principles
│   │   ├── validator.py                # Validation engine
│   │   └── authorization.py            # Auth matrix
│   │
│   ├── memory/                         # Graph-episodic memory
│   │   ├── __init__.py
│   │   ├── neo4j_client.py             # Neo4j interface
│   │   ├── models.py                   # Data models
│   │   └── queries.py                  # Query templates
│   │
│   ├── mcp/                            # MCP action server
│   │   ├── __init__.py
│   │   ├── server.py                   # MCP server
│   │   └── tools/                      # Tool implementations
│   │       ├── __init__.py
│   │       ├── find_similar.py
│   │       ├── get_dependencies.py
│   │       ├── restart_service.py
│   │       ├── scale_service.py
│   │       └── analyze_anomaly.py
│   │
│   ├── telemetry/                      # Telemetry processing
│   │   ├── __init__.py
│   │   ├── collector.py                # Data collection
│   │   ├── aggregator.py               # Data aggregation
│   │   └── models.py                   # Data models
│   │
│   ├── api/                            # FastAPI backend
│   │   ├── __init__.py
│   │   ├── app.py                      # FastAPI app
│   │   ├── routes/                     # API routes
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── chat.py
│   │   │   ├── telemetry.py
│   │   │   ├── incidents.py
│   │   │   ├── actions.py
│   │   │   └── status.py
│   │   ├── websocket/                  # WebSocket handlers
│   │   │   ├── __init__.py
│   │   │   └── chat.py
│   │   └── middleware/                 # Middleware
│   │       ├── __init__.py
│   │       ├── logging.py
│   │       └── auth.py
│   │
│   └── utils/                          # Utilities
│       ├── __init__.py
│       ├── logging.py
│       └── helpers.py
│
├── frontend/                           # React frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       │
│       ├── components/                 # React components
│       │   ├── Layout/
│       │   ├── Chat/
│       │   ├── Dashboard/
│       │   ├── Incidents/
│       │   └── common/
│       │
│       ├── pages/                      # Page components
│       │   ├── ChatPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── IncidentsPage.tsx
│       │   └── SettingsPage.tsx
│       │
│       ├── hooks/                      # Custom hooks
│       │   ├── useWebSocket.ts
│       │   └── useApi.ts
│       │
│       ├── services/                   # API services
│       │   └── api.ts
│       │
│       └── types/                      # TypeScript types
│           └── index.ts
│
├── docker/                             # Docker configurations
│   ├── docker-compose.local.yml        # Local dev (no GPU)
│   ├── docker-compose.gpu.yml          # GPU testing
│   ├── docker-compose.prod.yml         # Production
│   │
│   ├── Dockerfile.backend              # Backend image
│   ├── Dockerfile.frontend             # Frontend image
│   │
│   └── configs/                        # Service configs
│       ├── otel-collector.yaml
│       ├── prometheus.yml
│       ├── loki.yaml
│       ├── tempo.yaml
│       ├── grafana/
│       └── llama-swap.yaml
│
├── configs/                            # Application configs
│   ├── llama-swap.yaml                 # Model swap config
│   ├── constitutional.yaml             # Safety principles
│   └── logging.yaml                    # Logging config
│
├── scripts/                            # Utility scripts
│   ├── setup-local.sh                  # Local setup
│   ├── setup-aws.sh                    # AWS setup
│   ├── aws-start.sh                    # Start AWS instance
│   ├── aws-stop.sh                     # Stop AWS instance
│   ├── deploy-aws.sh                   # Deploy to AWS
│   ├── download-models.sh              # Download models
│   ├── precache-models.sh              # Pre-cache in RAM
│   ├── inject-anomaly.py               # Anomaly injection
│   └── run-tests.sh                    # Run test suite
│
├── tests/                              # Test files
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures
│   │
│   ├── unit/                           # Unit tests
│   │   ├── test_fast_annotator.py
│   │   ├── test_reasoning_agent.py
│   │   ├── test_constitutional.py
│   │   ├── test_model_manager.py
│   │   └── test_mcp_tools.py
│   │
│   ├── integration/                    # Integration tests
│   │   ├── test_telemetry_flow.py
│   │   ├── test_chat_flow.py
│   │   └── test_action_flow.py
│   │
│   └── e2e/                            # End-to-end tests
│       └── test_full_incident.py
│
└── models/                             # Model storage (gitignored)
    ├── .gitkeep
    ├── qwen3-8b-q4_k_m.gguf
    └── qwen3-14b-q4_k_m.gguf
```

---

## 4. Docker Configurations

### 4.1 Local Development Stack (No GPU)

```yaml
# docker/docker-compose.local.yml
version: '3.8'

services:
  # ============================================
  # NEXTCLOUD TEST ENVIRONMENT
  # ============================================
  
  nextcloud:
    image: nextcloud:latest
    container_name: nextcloud-app
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      - MYSQL_HOST=nextcloud-db
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=nextcloud_password
      - REDIS_HOST=nextcloud-redis
    volumes:
      - nextcloud_data:/var/www/html
    depends_on:
      - nextcloud-db
      - nextcloud-redis
    labels:
      - "otel.service.name=nextcloud-app"
    networks:
      - aiops-network

  nextcloud-db:
    image: mariadb:10.6
    container_name: nextcloud-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=nextcloud_password
    volumes:
      - nextcloud_db:/var/lib/mysql
    labels:
      - "otel.service.name=nextcloud-db"
    networks:
      - aiops-network

  nextcloud-redis:
    image: redis:alpine
    container_name: nextcloud-redis
    restart: unless-stopped
    labels:
      - "otel.service.name=nextcloud-redis"
    networks:
      - aiops-network

  nextcloud-cron:
    image: nextcloud:latest
    container_name: nextcloud-cron
    restart: unless-stopped
    entrypoint: /cron.sh
    volumes:
      - nextcloud_data:/var/www/html
    depends_on:
      - nextcloud
    labels:
      - "otel.service.name=nextcloud-cron"
    networks:
      - aiops-network

  # ============================================
  # OBSERVABILITY STACK (LGTM)
  # ============================================

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    restart: unless-stopped
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./configs/otel-collector.yaml:/etc/otel-collector-config.yaml:ro
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
    networks:
      - aiops-network

  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - ./configs/loki.yaml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - aiops-network

  tempo:
    image: grafana/tempo:latest
    container_name: tempo
    restart: unless-stopped
    ports:
      - "3200:3200"   # Tempo
      - "9095:9095"   # Tempo gRPC
    volumes:
      - ./configs/tempo.yaml:/etc/tempo.yaml:ro
      - tempo_data:/tmp/tempo
    command: ["-config.file=/etc/tempo.yaml"]
    networks:
      - aiops-network

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - aiops-network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - loki
      - tempo
      - prometheus
    networks:
      - aiops-network

  # ============================================
  # MEMORY STORES
  # ============================================

  neo4j:
    image: neo4j:5-community
    container_name: neo4j
    restart: unless-stopped
    ports:
      - "7474:7474"   # HTTP
      - "7687:7687"   # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password123
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
    networks:
      - aiops-network

  influxdb:
    image: influxdb:2.7
    container_name: influxdb
    restart: unless-stopped
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password123
      - DOCKER_INFLUXDB_INIT_ORG=aiops
      - DOCKER_INFLUXDB_INIT_BUCKET=telemetry
    volumes:
      - influxdb_data:/var/lib/influxdb2
    networks:
      - aiops-network

  # ============================================
  # APPLICATION (Local - Mock LLM)
  # ============================================

  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    container_name: aiops-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=local
      - OPENAI_API_BASE=http://mock-llm:8080/v1
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_PASSWORD=password123
      - LOKI_URL=http://loki:3100
      - TEMPO_URL=http://tempo:3200
      - PROMETHEUS_URL=http://prometheus:9090
    volumes:
      - ../src:/app/src:ro
    depends_on:
      - neo4j
      - loki
    networks:
      - aiops-network

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
    container_name: aiops-frontend
    restart: unless-stopped
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000
    volumes:
      - ../frontend/src:/app/src:ro
    networks:
      - aiops-network

  # Mock LLM for local testing (returns canned responses)
  mock-llm:
    image: python:3.11-slim
    container_name: mock-llm
    restart: unless-stopped
    ports:
      - "8081:8080"
    volumes:
      - ../scripts/mock_llm.py:/app/mock_llm.py:ro
    command: python /app/mock_llm.py
    networks:
      - aiops-network

volumes:
  nextcloud_data:
  nextcloud_db:
  loki_data:
  tempo_data:
  prometheus_data:
  grafana_data:
  neo4j_data:
  influxdb_data:

networks:
  aiops-network:
    driver: bridge
```

### 4.2 GPU Testing Stack (AWS)

```yaml
# docker/docker-compose.gpu.yml
version: '3.8'

services:
  # ============================================
  # LLM INFERENCE (GPU)
  # ============================================

  llama-swap:
    image: ghcr.io/mostlygeek/llama-swap:cuda
    container_name: llama-swap
    restart: unless-stopped
    runtime: nvidia
    ports:
      - "8080:8080"
    volumes:
      - ../models:/models:ro
      - ../configs/llama-swap.yaml:/app/config.yaml:ro
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - aiops-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Include all services from local stack
  # (Nextcloud, LGTM, Neo4j, etc.)
  # ... (same as local, but backend points to llama-swap)

  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    container_name: aiops-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=gpu-testing
      - OPENAI_API_BASE=http://llama-swap:8080/v1
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_PASSWORD=password123
      - MODEL_TIMEOUT_SECONDS=60
    depends_on:
      - llama-swap
      - neo4j
    networks:
      - aiops-network

networks:
  aiops-network:
    driver: bridge
```

### 4.3 llama-swap Configuration (Simultaneous Dual-Model)

```yaml
# configs/llama-swap.yaml
# SIMULTANEOUS DUAL-MODEL CONFIGURATION
# Both models always loaded on 24GB VRAM - no hot-swapping needed

models:
  # Fast Annotation Agent - Always loaded
  fast-agent:
    cmd: >
      llama-server
      --model /models/qwen3-4b-q4_k_m.gguf
      --alias fast-agent
      --ctx-size 8192
      --n-gpu-layers 99
      --flash-attn
      --threads 4
      --port 8081
    proxy: http://localhost:8081
    aliases:
      - "qwen3-4b"
      - "fast"
      - "annotator"
    # CRITICAL: Never unload - simultaneous operation
    ttl: -1
    
  # Reasoning Agent - Always loaded
  reasoning-agent:
    cmd: >
      llama-server
      --model /models/qwen3-14b-q4_k_m.gguf
      --alias reasoning-agent
      --ctx-size 4096
      --n-gpu-layers 99
      --flash-attn
      --threads 4
      --port 8082
    proxy: http://localhost:8082
    aliases:
      - "qwen3-14b"
      - "reasoning"
      - "chat"
    # CRITICAL: Never unload - simultaneous operation
    ttl: -1

# Health check configuration
healthcheck:
  enabled: true
  interval: 30
  timeout: 10

# Logging
log_level: info
log_format: json

# VRAM Budget (L4/A10G 24GB):
# - Qwen3-4B Q4_K_M: ~2.5GB model + ~1GB KV = ~4GB
# - Qwen3-14B Q4_K_M: ~9GB model + ~1.5GB KV = ~11GB
# - Total: ~15GB, leaving ~9GB headroom
```

### 4.3.1 Alternative: Direct Dual llama-server (Without llama-swap)

If preferred, run two independent llama-server processes directly:

```yaml
# docker-compose.gpu-direct.yml excerpt
services:
  fast-agent:
    image: ghcr.io/ggerganov/llama.cpp:server-cuda
    container_name: fast-agent
    runtime: nvidia
    ports:
      - "8081:8081"
    volumes:
      - ./models:/models:ro
    command: >
      --model /models/qwen3-4b-q4_k_m.gguf
      --ctx-size 8192
      --n-gpu-layers 99
      --flash-attn
      --port 8081
      --host 0.0.0.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]

  reasoning-agent:
    image: ghcr.io/ggerganov/llama.cpp:server-cuda
    container_name: reasoning-agent
    runtime: nvidia
    ports:
      - "8082:8082"
    volumes:
      - ./models:/models:ro
    command: >
      --model /models/qwen3-14b-q4_k_m.gguf
      --ctx-size 4096
      --n-gpu-layers 99
      --flash-attn
      --port 8082
      --host 0.0.0.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
```

### 4.4 OpenTelemetry Collector Configuration

```yaml
# docker/configs/otel-collector.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  # Docker stats for container metrics
  docker_stats:
    endpoint: unix:///var/run/docker.sock
    collection_interval: 10s

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000

  # Add service name attribute
  resource:
    attributes:
      - key: service.namespace
        value: constitutional-aiops
        action: upsert

exporters:
  # Logs to Loki
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      attributes:
        service.name: "service_name"
        service.namespace: "service_namespace"

  # Traces to Tempo
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  # Metrics to Prometheus
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: aiops

  # Debug output
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/tempo, logging]
    
    metrics:
      receivers: [otlp, docker_stats]
      processors: [batch, resource]
      exporters: [prometheus]
    
    logs:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [loki, logging]
```

---

*Continued in next section...*
