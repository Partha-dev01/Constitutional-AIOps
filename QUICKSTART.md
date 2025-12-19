# Constitutional AIOps - Quick Start Guide

Get Constitutional AIOps running in under 10 minutes.

## Prerequisites

- **Docker** 20.10+ with Docker Compose
- **8GB+ RAM** (16GB recommended for local mode)
- **NVIDIA GPU** with 24GB VRAM (for GPU mode, optional)

## Quick Install

### Option 1: One-Command Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-repo/constitutional-aiops.git
cd constitutional-aiops

# Run the installation wizard
./scripts/install.sh
```

The wizard will:
- ✅ Detect your hardware (GPU/CPU)
- ✅ Check prerequisites
- ✅ Configure environment
- ✅ Download models (GPU mode only)
- ✅ Start all services

### Option 2: Manual Setup

```bash
# Clone repository
git clone https://github.com/your-repo/constitutional-aiops.git
cd constitutional-aiops

# Copy environment template
cp .env.example .env

# Start in local mode (no GPU required)
docker compose -f docker-compose.yml -f docker/docker-compose.local.yml up -d

# OR start in GPU mode (requires NVIDIA GPU)
docker compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up -d
```

## Verify Installation

```bash
# Check all services are running
docker compose ps

# Test backend health
curl http://localhost:8000/health

# Test API endpoint
curl http://localhost:8000/api/v1/health
```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Neo4j Browser** | http://localhost:7474 | neo4j / constitutional_aiops_2025 |

### GPU Mode Only
| Service | URL |
|---------|-----|
| Fast Agent (Qwen3-4B) | http://localhost:8081/v1 |
| Reasoning Agent (Qwen3-14B) | http://localhost:8082/v1 |

## Deployment Modes

### Local Mode (Default)
- No GPU required
- Uses mock LLM server for testing
- Perfect for development and demos
- All features work except real LLM inference

```bash
./scripts/install.sh --local
```

### GPU Mode
- Requires NVIDIA GPU with 24GB+ VRAM
- Full LLM inference with Qwen3-4B and Qwen3-14B
- Both models loaded simultaneously
- Recommended: AWS g6.xlarge or equivalent

```bash
./scripts/install.sh --gpu
```

## First Steps After Installation

### 1. Create Your First Incident

```bash
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High CPU Usage on API Server",
    "description": "API server showing 95% CPU utilization",
    "severity": "high",
    "source": "prometheus"
  }'
```

### 2. View in Dashboard
Open http://localhost:3000 and navigate to the Incidents page.

### 3. Explore the Graph Memory
Open http://localhost:7474 and run:
```cypher
MATCH (n) RETURN n LIMIT 25
```

### 4. Check Observability
Open Grafana at http://localhost:3001 to view:
- System metrics
- Log aggregation
- Trace data

## Common Commands

```bash
# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v

# Update to latest
git pull && docker compose build && docker compose up -d
```

## Troubleshooting

### Services not starting?
```bash
# Check Docker is running
docker info

# Check for port conflicts
netstat -tulpn | grep -E '(3000|8000|7474|7687)'

# View detailed logs
docker compose logs --tail=100
```

### Backend not connecting to Neo4j?
```bash
# Wait for Neo4j to be fully ready (can take 30-60s)
docker compose logs neo4j

# Manually test Neo4j connection
curl http://localhost:7474
```

### GPU not detected?
```bash
# Check NVIDIA driver
nvidia-smi

# Check NVIDIA Container Toolkit
docker info | grep nvidia

# Run GPU test
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

## Next Steps

- 📖 Read the [Architecture Guide](docs/ARCHITECTURE.md)
- 🚀 Deploy to AWS with [AWS Deployment Guide](docs/AWS_DEPLOYMENT.md)
- 🛡️ Learn about [Constitutional AI Framework](docs/CONSTITUTIONAL_AI.md)
- 📊 Set up [Monitoring Dashboards](docs/MONITORING.md)

## Support

- **Issues**: https://github.com/your-repo/constitutional-aiops/issues
- **Discussions**: https://github.com/your-repo/constitutional-aiops/discussions

---

**Constitutional AIOps** - Autonomous Infrastructure with Safety Guarantees
