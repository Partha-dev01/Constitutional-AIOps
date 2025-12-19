# Constitutional AIOps - Deployment Guide

> **Version**: 0.1.0-alpha
> **Last Updated**: 2025-12-06

---

## Table of Contents

1. [Overview](#1-overview)
2. [Local Development Setup](#2-local-development-setup)
3. [AWS GPU Testing Setup](#3-aws-gpu-testing-setup)
4. [Production Deployment](#4-production-deployment)
5. [Configuration Reference](#5-configuration-reference)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Overview

### 1.1 Deployment Environments

| Environment | Purpose | GPU Required | Typical Use |
|-------------|---------|--------------|-------------|
| Local | Development, unit tests | No | Daily coding |
| AWS GPU | Integration tests, GPU testing | Yes (T4 16GB) | Weekly testing |
| Production | Customer deployment | Yes (16GB+ VRAM) | Final deployment |

### 1.2 Development Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LOCAL MACHINE                        AWS GPU INSTANCE              │
│  ─────────────                        ────────────────              │
│                                                                     │
│  1. Write/edit code                   6. Deploy code                │
│  2. Run linters                       7. Run GPU tests              │
│  3. Run unit tests                    8. Test model swapping        │
│  4. Test frontend                     9. Performance tests          │
│  5. Commit changes ──────────────────►10. Debug issues              │
│                                       11. STOP INSTANCE! 💰         │
│                    ◄──────────────────                              │
│  12. Review results                                                 │
│  13. Iterate                                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Local Development Setup

### 2.1 Prerequisites

**Required Software**:
- Python 3.11+
- Node.js 20+
- Docker Desktop (with Docker Compose v2)
- Git

**Hardware**:
- RAM: 16GB minimum (32GB recommended)
- Disk: 50GB free space
- CPU: 4+ cores

### 2.2 Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/constitutional-aiops.git
cd constitutional-aiops

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node dependencies
cd frontend
npm install
cd ..

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2.3 Start Local Services

```bash
# Start infrastructure (Nextcloud, LGTM, Neo4j, etc.)
docker-compose -f docker/docker-compose.local.yml up -d

# Verify services are running
docker-compose -f docker/docker-compose.local.yml ps

# Check logs if needed
docker-compose -f docker/docker-compose.local.yml logs -f
```

### 2.4 Run Backend (Development Mode)

```bash
# Activate virtual environment
source venv/bin/activate

# Run with hot reload
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use the convenience script
./scripts/run-backend.sh
```

### 2.5 Run Frontend (Development Mode)

```bash
# In a new terminal
cd frontend
npm run dev

# Frontend will be available at http://localhost:5173
```

### 2.6 Local Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_constitutional.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run linters
black src/ --check
isort src/ --check
flake8 src/
mypy src/
```

### 2.7 Stop Local Services

```bash
# Stop all services
docker-compose -f docker/docker-compose.local.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker/docker-compose.local.yml down -v
```

---

## 3. AWS GPU Testing Setup

### 3.1 AWS Prerequisites

**Required**:
- AWS Account with EC2 permissions
- AWS CLI configured locally
- SSH key pair for EC2 access
- Understanding of Spot instances

**Recommended Instance**:
- Type: g4dn.xlarge
- GPU: 1x NVIDIA T4 (16GB)
- vCPU: 4
- RAM: 16GB
- Storage: 125GB NVMe SSD
- Cost: ~$0.16-0.20/hour (Spot)

### 3.2 One-Time AWS Setup

#### Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
    --group-name aiops-gpu-sg \
    --description "Security group for AIOps GPU testing"

# Allow SSH
aws ec2 authorize-security-group-ingress \
    --group-name aiops-gpu-sg \
    --protocol tcp --port 22 --cidr 0.0.0.0/0

# Allow application ports
aws ec2 authorize-security-group-ingress \
    --group-name aiops-gpu-sg \
    --protocol tcp --port 3000 --cidr 0.0.0.0/0  # Grafana
aws ec2 authorize-security-group-ingress \
    --group-name aiops-gpu-sg \
    --protocol tcp --port 5173 --cidr 0.0.0.0/0  # Frontend
aws ec2 authorize-security-group-ingress \
    --group-name aiops-gpu-sg \
    --protocol tcp --port 8000 --cidr 0.0.0.0/0  # Backend
aws ec2 authorize-security-group-ingress \
    --group-name aiops-gpu-sg \
    --protocol tcp --port 8080 --cidr 0.0.0.0/0  # llama-swap
```

#### Create Spot Instance Request

```bash
# Request Spot instance
aws ec2 request-spot-instances \
    --instance-count 1 \
    --type "persistent" \
    --launch-specification '{
        "ImageId": "ami-0c7217cdde317cfec",
        "InstanceType": "g4dn.xlarge",
        "KeyName": "your-key-name",
        "SecurityGroupIds": ["sg-xxxxxxxx"],
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": 100,
                    "VolumeType": "gp3",
                    "DeleteOnTermination": false
                }
            }
        ]
    }'
```

### 3.3 Instance Setup (First Time)

```bash
# SSH to instance
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>

# Run setup script
curl -sSL https://raw.githubusercontent.com/your-org/constitutional-aiops/main/scripts/setup-aws.sh | bash

# Log out and back in for Docker group
exit
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>

# Verify GPU
nvidia-smi

# Clone repository
git clone https://github.com/your-org/constitutional-aiops.git
cd constitutional-aiops

# Download models (one-time, ~15GB)
./scripts/download-models.sh

# Pre-cache models in RAM
./scripts/precache-models.sh
```

### 3.4 Daily GPU Testing Workflow

**On your local machine**:

```bash
# Set environment variables
export AWS_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
export AWS_INSTANCE_IP="x.x.x.x"
export SSH_KEY_FILE="~/.ssh/your-key.pem"

# Start instance
./scripts/aws-start.sh

# Wait for instance to be ready (~2 minutes)
# The script will output the public IP

# Deploy latest code
./scripts/deploy-aws.sh
```

**On the AWS instance**:

```bash
# SSH to instance
ssh -i ~/.ssh/your-key.pem ubuntu@<instance-ip>

# Navigate to project
cd constitutional-aiops

# Pre-cache models (if not already done)
./scripts/precache-models.sh

# Start GPU stack
docker-compose -f docker/docker-compose.gpu.yml up -d

# Check services
docker-compose -f docker/docker-compose.gpu.yml ps

# View logs
docker-compose -f docker/docker-compose.gpu.yml logs -f llama-swap

# Run GPU tests
pytest tests/integration/ -v -m gpu

# Test model swapping manually
curl http://localhost:8080/v1/models

# Check VRAM usage
nvidia-smi -l 1
```

**When done (IMPORTANT!)**:

```bash
# Stop services on instance
docker-compose -f docker/docker-compose.gpu.yml down

# Exit SSH
exit

# Stop instance to save money
./scripts/aws-stop.sh
```

### 3.5 Cost Management

| Activity | Duration | Cost (Spot) |
|----------|----------|-------------|
| Quick test | 1 hour | ~$0.18 |
| Half day | 4 hours | ~$0.72 |
| Full day | 8 hours | ~$1.44 |
| Week (4hr/day) | 20 hours | ~$3.60 |
| Month (moderate) | 80 hours | ~$14.40 |

**Cost Saving Tips**:
1. Always stop instance when not in use
2. Use Spot instances (60-70% savings)
3. Store models on persistent EBS volume
4. Use auto-stop script with timeout

```bash
# Auto-stop after 30 minutes of inactivity
# Add to crontab on instance
*/5 * * * * /home/ubuntu/constitutional-aiops/scripts/check-idle.sh
```

---

## 4. Production Deployment

### 4.1 Hardware Requirements

**Minimum**:
- GPU: 16GB VRAM (NVIDIA T4, RTX 4060 Ti 16GB)
- RAM: 32GB
- Storage: 100GB SSD
- CPU: 4 cores

**Recommended**:
- GPU: 24GB VRAM (RTX 4090, A10)
- RAM: 64GB
- Storage: 250GB NVMe SSD
- CPU: 8 cores

### 4.2 Quick Start (Single Command)

```bash
# Clone repository
git clone https://github.com/your-org/constitutional-aiops.git
cd constitutional-aiops

# Run installer (handles everything)
./scripts/install.sh

# Start system
docker-compose up -d

# Access dashboard
open http://localhost:5173
```

### 4.3 Manual Installation

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# 3. Clone repository
git clone https://github.com/your-org/constitutional-aiops.git
cd constitutional-aiops

# 4. Download models
./scripts/download-models.sh

# 5. Configure environment
cp .env.example .env
nano .env  # Edit as needed

# 6. Start services
docker-compose -f docker/docker-compose.prod.yml up -d

# 7. Verify
docker-compose -f docker/docker-compose.prod.yml ps
curl http://localhost:8000/health
```

### 4.4 Configuration

Edit `.env` file:

```bash
# Environment
ENVIRONMENT=production

# Security (CHANGE THESE!)
JWT_SECRET=your-secure-secret-here
NEO4J_PASSWORD=your-neo4j-password
INFLUXDB_PASSWORD=your-influxdb-password

# Model Configuration
MODEL_TIMEOUT_SECONDS=60
CONFIDENCE_HIGH=0.9
CONFIDENCE_MEDIUM=0.7

# Logging
LOG_LEVEL=INFO
```

### 4.5 SSL/TLS Setup

```bash
# Using Let's Encrypt with Caddy
# Edit Caddyfile
your-domain.com {
    reverse_proxy localhost:5173
    
    handle /api/* {
        reverse_proxy localhost:8000
    }
}

# Start Caddy
docker-compose -f docker/docker-compose.prod.yml --profile ssl up -d
```

### 4.6 Backup & Recovery

```bash
# Backup Neo4j
docker exec neo4j neo4j-admin dump --database=neo4j --to=/backup/neo4j.dump

# Backup configuration
tar -czf config-backup.tar.gz .env configs/

# Restore Neo4j
docker exec neo4j neo4j-admin load --database=neo4j --from=/backup/neo4j.dump
```

---

## 5. Configuration Reference

### 5.1 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `local` | Environment: local, gpu-testing, production |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `OPENAI_API_BASE` | `http://localhost:8080/v1` | llama-swap endpoint |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_PASSWORD` | `password123` | Neo4j password |
| `MODEL_TIMEOUT_SECONDS` | `60` | Seconds before 14B model unloads |
| `CONFIDENCE_HIGH` | `0.9` | Threshold for automatic action |
| `CONFIDENCE_MEDIUM` | `0.7` | Threshold for requiring approval |

### 5.2 Docker Compose Profiles

```bash
# Local development (no GPU)
docker-compose -f docker/docker-compose.local.yml up -d

# GPU testing
docker-compose -f docker/docker-compose.gpu.yml up -d

# Production
docker-compose -f docker/docker-compose.prod.yml up -d

# Production with SSL
docker-compose -f docker/docker-compose.prod.yml --profile ssl up -d
```

### 5.3 llama-swap Configuration

```yaml
# configs/llama-swap.yaml
models:
  fast-agent:
    cmd: llama-server --model /models/qwen3-8b-q4_k_m.gguf ...
    ttl: -1  # Never unload
    
  reasoning-agent:
    cmd: llama-server --model /models/qwen3-14b-q4_k_m.gguf ...
    ttl: 60  # Unload after 60s inactivity

default: fast-agent
swap_strategy: graceful
```

---

## 6. Troubleshooting

### 6.1 Common Issues

#### Docker Permission Denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in
exit
# reconnect
```

#### GPU Not Detected

```bash
# Verify NVIDIA driver
nvidia-smi

# Verify Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check NVIDIA Container Toolkit
nvidia-ctk --version
```

#### Model Loading Fails

```bash
# Check available VRAM
nvidia-smi

# Verify model files
ls -la models/
md5sum models/*.gguf

# Check llama-swap logs
docker logs llama-swap
```

#### Out of Memory (OOM)

```bash
# Reduce context size in llama-swap.yaml
# Change --ctx-size 8192 to --ctx-size 4096

# Or reduce batch size
# Add --batch-size 256
```

#### Slow Model Swap

```bash
# Pre-cache models in RAM
./scripts/precache-models.sh

# Verify cache status
vmtouch models/*.gguf
```

### 6.2 Log Locations

| Service | Log Location |
|---------|--------------|
| Backend | `docker logs aiops-backend` |
| Frontend | Browser console |
| llama-swap | `docker logs llama-swap` |
| Neo4j | `docker logs neo4j` |
| All services | `docker-compose logs -f` |

### 6.3 Health Checks

```bash
# Check all services
curl http://localhost:8000/health

# Check model status
curl http://localhost:8000/api/status/models

# Check llama-swap
curl http://localhost:8080/health

# Check Neo4j
curl http://localhost:7474

# Check Grafana
curl http://localhost:3000/api/health
```

### 6.4 Performance Debugging

```bash
# Monitor GPU usage
nvidia-smi -l 1

# Monitor Docker stats
docker stats

# Profile model inference
curl -X POST http://localhost:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "fast-agent", "messages": [{"role": "user", "content": "test"}]}' \
    -w "\n\nTime: %{time_total}s\n"
```

---

## Appendix: Quick Reference Commands

```bash
# Local Development
docker-compose -f docker/docker-compose.local.yml up -d    # Start
docker-compose -f docker/docker-compose.local.yml down     # Stop
docker-compose -f docker/docker-compose.local.yml logs -f  # Logs
pytest tests/ -v                                           # Test

# AWS GPU
./scripts/aws-start.sh                                     # Start instance
./scripts/deploy-aws.sh                                    # Deploy code
./scripts/aws-stop.sh                                      # STOP INSTANCE!

# On AWS Instance
docker-compose -f docker/docker-compose.gpu.yml up -d      # Start
docker-compose -f docker/docker-compose.gpu.yml down       # Stop
nvidia-smi -l 1                                            # GPU monitor
./scripts/precache-models.sh                               # Pre-cache

# Production
./scripts/install.sh                                       # Install
docker-compose -f docker/docker-compose.prod.yml up -d     # Start
docker-compose -f docker/docker-compose.prod.yml down      # Stop
```

---

**Last Updated**: 2025-12-06
**Version**: 0.1.0-alpha
