# Constitutional AIOps - AWS Deployment Guide

Complete guide for deploying Constitutional AIOps on AWS with GPU support.

## Target Configuration

| Component | Specification |
|-----------|---------------|
| **Instance Type** | g6.xlarge (Spot recommended) |
| **GPU** | NVIDIA L4 24GB VRAM |
| **vCPU** | 4 cores |
| **RAM** | 16 GB |
| **Storage** | 100 GB gp3 |
| **Cost** | ~$0.35/hr (Spot) / ~$0.80/hr (On-Demand) |
| **Monthly (Spot)** | ~$250-300 |

## Prerequisites

- AWS Account with EC2 access
- AWS CLI configured (`aws configure`)
- SSH key pair created in target region
- Basic familiarity with EC2 and Security Groups

## Step 1: Launch EC2 Instance

### Using AWS Console

1. **Go to EC2 Dashboard** → Launch Instance

2. **Name**: `constitutional-aiops`

3. **AMI Selection**:
   - Search for: `Deep Learning AMI GPU PyTorch`
   - Select: **Deep Learning AMI GPU PyTorch 2.0 (Ubuntu 20.04)**
   - This AMI includes NVIDIA drivers and Docker

4. **Instance Type**: `g6.xlarge`
   - Alternative: `g5.xlarge` (A10G GPU, similar performance)

5. **Key Pair**: Select or create an SSH key pair

6. **Network Settings**:
   - VPC: Default or your VPC
   - Subnet: Public subnet
   - Auto-assign Public IP: **Enable**

7. **Security Group Rules**:
   ```
   SSH (22)        - Your IP
   HTTP (3000)     - 0.0.0.0/0 (Frontend)
   HTTP (8000)     - 0.0.0.0/0 (Backend API)
   HTTP (3001)     - Your IP (Grafana)
   HTTP (7474)     - Your IP (Neo4j Browser)
   Custom (7687)   - Your IP (Neo4j Bolt)
   Custom (8080)   - Your IP (llama-swap)
   Custom (8081)   - Your IP (Fast Agent)
   Custom (8082)   - Your IP (Reasoning Agent)
   ```

8. **Storage**: 100 GB gp3

9. **Advanced Details** (for Spot):
   - Request Spot Instances: **Yes**
   - Maximum price: Leave blank (uses on-demand price cap)

10. **Launch Instance**

### Using AWS CLI

```bash
# Create security group
aws ec2 create-security-group \
    --group-name constitutional-aiops-sg \
    --description "Constitutional AIOps Security Group"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
    --group-name constitutional-aiops-sg \
    --protocol tcp --port 22 --cidr YOUR_IP/32

aws ec2 authorize-security-group-ingress \
    --group-name constitutional-aiops-sg \
    --protocol tcp --port 3000 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name constitutional-aiops-sg \
    --protocol tcp --port 8000 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-name constitutional-aiops-sg \
    --protocol tcp --port 3001 --cidr YOUR_IP/32

aws ec2 authorize-security-group-ingress \
    --group-name constitutional-aiops-sg \
    --protocol tcp --port 7474 --cidr YOUR_IP/32

aws ec2 authorize-security-group-ingress \
    --group-name constitutional-aiops-sg \
    --protocol tcp --port 7687 --cidr YOUR_IP/32

# Launch Spot instance
aws ec2 run-instances \
    --image-id ami-0123456789abcdef0 \
    --instance-type g6.xlarge \
    --key-name your-key-pair \
    --security-groups constitutional-aiops-sg \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100,"VolumeType":"gp3"}}]' \
    --instance-market-options '{"MarketType":"spot"}' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=constitutional-aiops}]'
```

## Step 2: Connect and Setup

### SSH to Instance

```bash
# Connect to instance
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# Verify GPU is available
nvidia-smi
```

Expected output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.x     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA L4           Off  | 00000000:00:1E.0 Off |                    0 |
| N/A   30C    P8     9W /  72W |      0MiB / 23034MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

### Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (if not present)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Log out and back in for docker group
exit
```

## Step 3: Deploy Application

### Clone and Setup

```bash
# SSH back in
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# Clone repository
git clone https://github.com/your-repo/constitutional-aiops.git
cd constitutional-aiops

# Run installation wizard
chmod +x scripts/install.sh
./scripts/install.sh --gpu
```

The installation wizard will:
1. Detect NVIDIA L4 GPU (24GB)
2. Download Qwen3-4B (~2.5GB) and Qwen3-14B (~9GB) models
3. Create environment configuration
4. Start all services

### Manual Model Download (if needed)

```bash
# Create models directory
mkdir -p models

# Download Qwen3-4B
curl -L -o models/qwen3-4b-q4_k_m.gguf \
    "https://huggingface.co/Qwen/Qwen2.5-4B-Instruct-GGUF/resolve/main/qwen2.5-4b-instruct-q4_k_m.gguf"

# Download Qwen3-14B
curl -L -o models/qwen3-14b-q4_k_m.gguf \
    "https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf"
```

## Step 4: Verify Deployment

### Check Services

```bash
# All containers should be running
docker compose ps

# Expected output:
# NAME                IMAGE                              STATUS
# aiops-backend       constitutional-aiops-backend       Up (healthy)
# aiops-frontend      constitutional-aiops-frontend      Up
# aiops-neo4j         neo4j:5.15-community               Up (healthy)
# aiops-llama-swap    ghcr.io/mostlygeek/llama-swap      Up (healthy)
# aiops-grafana       grafana/grafana:10.2.3             Up
# aiops-loki          grafana/loki:2.9.3                 Up
# aiops-prometheus    prom/prometheus:v2.48.0            Up
# aiops-tempo         grafana/tempo:2.3.1                Up
```

### Test Endpoints

```bash
# Backend health
curl http://localhost:8000/health

# API health
curl http://localhost:8000/api/v1/health

# LLM Fast Agent
curl http://localhost:8081/v1/models

# LLM Reasoning Agent
curl http://localhost:8082/v1/models

# Test LLM inference
curl http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-4b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### GPU Memory Usage

```bash
# Check GPU memory
nvidia-smi

# Expected: ~15GB used (4GB + 11GB for both models)
```

## Step 5: Access Application

From your local machine, access:

| Service | URL |
|---------|-----|
| Frontend | http://YOUR_INSTANCE_IP:3000 |
| Backend API | http://YOUR_INSTANCE_IP:8000 |
| API Docs | http://YOUR_INSTANCE_IP:8000/docs |
| Grafana | http://YOUR_INSTANCE_IP:3001 |
| Neo4j | http://YOUR_INSTANCE_IP:7474 |

## Production Considerations

### Enable HTTPS (Recommended)

```bash
# Install Caddy as reverse proxy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
    sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
    sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Create Caddyfile
sudo tee /etc/caddy/Caddyfile << 'EOF'
your-domain.com {
    reverse_proxy localhost:3000
}

api.your-domain.com {
    reverse_proxy localhost:8000
}
EOF

# Start Caddy
sudo systemctl enable caddy
sudo systemctl start caddy
```

### Setup Auto-Start on Reboot

```bash
# Create systemd service
sudo tee /etc/systemd/system/constitutional-aiops.service << 'EOF'
[Unit]
Description=Constitutional AIOps
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/constitutional-aiops
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker/docker-compose.gpu.yml up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable constitutional-aiops
```

### Monitoring & Alerts

1. **CloudWatch Alarms**:
   - CPU Utilization > 80%
   - GPU Memory > 90%
   - Disk Usage > 80%

2. **Spot Instance Interruption**:
   ```bash
   # Check for interruption notice
   curl -s http://169.254.169.254/latest/meta-data/spot/instance-action
   ```

### Backup Neo4j Data

```bash
# Create backup
docker exec aiops-neo4j neo4j-admin database dump neo4j --to-path=/backups
docker cp aiops-neo4j:/backups/neo4j.dump ./backups/

# Upload to S3
aws s3 cp ./backups/neo4j.dump s3://your-bucket/backups/
```

## Cost Optimization

### Spot Instance Strategy

- Use Spot for development/testing (~60% savings)
- Set up Spot Fleet for production resilience
- Consider Reserved Instances for long-term (>1 year)

### Storage Optimization

```bash
# Clean Docker resources weekly
docker system prune -af --volumes

# Compress old logs
find /var/log -name "*.log" -mtime +7 -exec gzip {} \;
```

### Right-sizing

| Use Case | Instance | Cost/Month |
|----------|----------|------------|
| Development | g6.xlarge Spot | ~$250 |
| Production | g6.xlarge On-Demand | ~$580 |
| High Availability | 2x g6.xlarge Spot | ~$500 |

## Troubleshooting

### Models Not Loading

```bash
# Check llama-swap logs
docker compose logs llama-swap

# Verify model files
ls -la models/

# Check GPU memory
nvidia-smi
```

### Container Won't Start

```bash
# Check Docker logs
docker compose logs --tail=50

# Rebuild containers
docker compose build --no-cache
docker compose up -d
```

### Network Issues

```bash
# Check security group
aws ec2 describe-security-groups --group-names constitutional-aiops-sg

# Check instance public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

## Architecture on AWS

```
                    Internet
                        │
                        ▼
             ┌─────────────────────┐
             │   Security Group    │
             │  (Ports: 22,3000,   │
             │   8000,3001,7474)   │
             └─────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │         g6.xlarge Instance         │
        │  ┌─────────────────────────────┐  │
        │  │      Docker Compose         │  │
        │  │  ┌───────┐  ┌───────────┐  │  │
        │  │  │Frontend│  │  Backend  │  │  │
        │  │  │ :3000  │  │   :8000   │  │  │
        │  │  └───────┘  └───────────┘  │  │
        │  │  ┌───────┐  ┌───────────┐  │  │
        │  │  │ Neo4j │  │  Grafana  │  │  │
        │  │  │ :7474 │  │   :3001   │  │  │
        │  │  └───────┘  └───────────┘  │  │
        │  │  ┌─────────────────────┐   │  │
        │  │  │    llama-swap       │   │  │
        │  │  │ :8081 (4B) :8082(14B)│  │  │
        │  │  └─────────────────────┘   │  │
        │  └─────────────────────────────┘  │
        │  ┌─────────────────────────────┐  │
        │  │    NVIDIA L4 24GB GPU       │  │
        │  │  Qwen3-4B + Qwen3-14B       │  │
        │  └─────────────────────────────┘  │
        └───────────────────────────────────┘
```

---

**Need Help?** Open an issue at https://github.com/your-repo/constitutional-aiops/issues
