# Jarvis Labs Deployment Guide

> **Template**: Ollama
> **GPU**: A5000 (24GB VRAM) - $0.49/hr
> **Storage**: 100GB recommended
> **Setup Time**: ~15 minutes
> **Models**: Qwen3-4B + Qwen3-14B (simultaneous)

This guide explains how to run Constitutional AIOps with LLMs on Jarvis Labs while keeping all other services (frontend, backend, Neo4j, monitoring) running locally for easy debugging.

---

## CRITICAL: Data Persistence

**Only `/home` directory persists between pause/resume!** All other data is LOST.

| Directory | Persists? | Notes |
|-----------|-----------|-------|
| `/home/*` | YES | Store models here |
| `/root/*` | NO | Lost on pause/resume |
| `/usr/share/ollama` | NO | Default Ollama location - LOST |

**The setup script configures models to be stored in `/home/ollama-models` for persistence.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR LOCAL MACHINE (Windows)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Frontend   │  │   Backend   │  │   Neo4j     │              │
│  │ :3000       │  │  :8000      │  │  :7474      │              │
│  │ Debug here! │  │  API here!  │  │  Graph DB   │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
│                          │                                       │
│                    HTTPS requests                                │
│                          │                                       │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           JARVIS LABS - Ollama Template (A5000 24GB)            │
│                                                                 │
│  API Endpoint: https://[id].notebooks.jarvislabs.net            │
│                                                                 │
│  Models stored in: /home/ollama-models (PERSISTS!)              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     Ollama Server                       │    │
│  │  ┌─────────────────┐  ┌─────────────────────┐          │    │
│  │  │ qwen3:4b        │  │ qwen3:14b           │          │    │
│  │  │ (Fast Agent)    │  │ (Reasoning Agent)   │          │    │
│  │  │ ~3GB VRAM       │  │ ~9GB VRAM           │          │    │
│  │  └─────────────────┘  └─────────────────────┘          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Total VRAM: ~15GB used / 24GB available                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**No SSH tunnel needed!** The Ollama template provides a direct HTTPS API endpoint.

---

## Models

| Role | Model | VRAM | Download Size |
|------|-------|------|---------------|
| Fast Agent | qwen3:4b | ~3 GB | ~2.5 GB |
| Reasoning Agent | qwen3:14b | ~9 GB | ~9.3 GB |

**Why Qwen3?** Research shows Qwen3-4B outperforms Qwen2.5-7B on reasoning benchmarks:
- MMLU-Pro: 74 vs 45
- GPQA: 59 vs 36.4
- MATH: 90 vs 49.8

---

## Prerequisites

- Docker Desktop installed locally
- $10-20 credits on Jarvis Labs account
- Git repository cloned locally
- Windows PowerShell or Git Bash for testing

---

## Step 1: Create Jarvis Labs Account (FREE)

1. Go to https://jarvislabs.ai
2. Sign up or login
3. Add credits ($10-20 for testing)

---

## Step 2: Add SSH Key (FREE)

Add your SSH public key to access the instance terminal.

1. Go to **Settings** → **SSH Keys**
2. Click **Add SSH Key**
3. Paste this public key:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAUpDdcM1oSEwI9o+dsVbA9TDiTSoc5VvWd9hRuL7wp9 constitutional-aiops-jarvis
```

4. Give it a name (e.g., "Constitutional AIOps")
5. Click Save

---

## Step 3: Launch Ollama Instance (BILLING STARTS)

1. Go to **Dashboard** → **Create Instance**
2. Select template: **Ollama**
3. Select GPU: **A5000** ($0.49/hr)
4. Storage: **100GB**
5. Click **Launch**
6. Wait ~90 seconds for instance to start

### Important: Copy These Values
After launch, from the dashboard:
- **SSH Command**: For terminal access (e.g., `ssh -p 11114 root@sshn.jarvislabs.ai`)
- **API Endpoint**: For API access (e.g., `https://62d7ad3655361.notebooks.jarvislabs.net`)

---

## Step 4: Setup Models via SSH

SSH into the instance and run the setup script:

```bash
# SSH into the instance (use the port from dashboard - currently 11114)
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai

# Or run the setup script directly
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai 'bash -s' < scripts/setup-jarvis-ollama.sh
```

### Manual Setup (if not using script)

```bash
# 1. Configure persistent storage (CRITICAL!)
export OLLAMA_MODELS=/home/ollama-models
mkdir -p /home/ollama-models
echo 'export OLLAMA_MODELS=/home/ollama-models' >> ~/.bashrc

# 2. Restart Ollama with new path
pkill ollama
OLLAMA_MODELS=/home/ollama-models ollama serve &
sleep 5

# 3. Pull Fast Agent model (~2.5GB, ~1-2 min)
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:4b

# 4. Pull Reasoning Agent model (~9.3GB, ~5-8 min)
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:14b

# 5. Verify models are installed
OLLAMA_MODELS=/home/ollama-models ollama list

# 6. Verify persistence
ls -la /home/ollama-models/
```

---

## Step 4b: Setup Benchmark Dependencies (Optional)

If you plan to run the benchmark evaluation on Jarvis Labs (recommended for GPU-accelerated BERTScore and cosine similarity metrics):

```bash
# Run the benchmark setup script
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai 'bash -s' < scripts/setup-jarvis-benchmark.sh
```

This installs:
- `sentence-transformers` (all-MiniLM-L6-v2 for 384-dim cosine similarity)
- `bert-score` (microsoft/deberta-xlarge-mnli for BERTScore F1)
- Pre-downloads model weights (~2GB total)

### Running Benchmark on Jarvis Labs

Running the benchmark ON Jarvis Labs is recommended because:
1. **Zero network latency** - Ollama calls are localhost instead of HTTPS
2. **GPU-accelerated metrics** - BERTScore and sentence-transformers use A5000 GPU
3. **All 4 metrics populate** - rule_score, BERTScore F1, cosine similarity, term overlap

```bash
# SSH into instance
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai

# Clone/update repo in /home (persists on pause/resume)
cd /home && git clone <repo-url> constitutional-aiops
cd constitutional-aiops

# Install Python project dependencies
pip install -r requirements.txt

# Quick test (5 annotation + 5 RCA)
python benchmark/scripts/test_5plus5.py --ann=5 --rca=5

# Full benchmark (100 annotation + 50 RCA, ~20 min)
python benchmark/scripts/test_5plus5.py

# Ablation study (all 4 configs, quick test)
python benchmark/scripts/run_ablation.py --config all --ann 5 --rca 5

# Full ablation study (~1.5 hours)
python benchmark/scripts/run_ablation.py --config all

# Export paper tables
python benchmark/scripts/export_metrics.py
```

The scripts auto-detect Jarvis Labs (via `/home/.ollama/models`) and switch to `localhost:6006` (Ollama template binds to port 6006).

---

## Data Transfer: Local Machine ↔ Jarvis Labs

### Uploading Code to Jarvis Labs

Since only `/home` persists on Jarvis Labs, and you need the benchmark scripts and source code to run benchmarks directly on the instance:

#### Step 1: Create a tarball (excluding large raw datasets and old results)

```bash
# From the project root on your local machine (Git Bash)
cd /c/Users/partha/Downloads/"files AIOPS NEW"/constitutional-aiops

# Create tarball excluding raw datasets, node_modules, and results
tar czf /tmp/aiops_code.tar.gz \
  --exclude='benchmark/datasets/raw' \
  --exclude='benchmark/results' \
  --exclude='frontend/node_modules' \
  --exclude='frontend/dist' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  -C .. constitutional-aiops
```

**Size**: ~60MB (includes processed datasets, source code, scripts)

#### Step 2: Upload to Jarvis Labs via SCP

```bash
# SCP the tarball to Jarvis Labs
scp -i .ssh/jarvis_labs_key -P 11114 \
  /tmp/aiops_code.tar.gz \
  root@sshn.jarvislabs.ai:/home/
```

#### Step 3: Extract on Jarvis Labs

```bash
# SSH into Jarvis Labs
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai

# Extract (overwrites existing code)
cd /home && tar xzf aiops_code.tar.gz && rm aiops_code.tar.gz

# Install Python dependencies
cd /home/constitutional-aiops
pip install -r requirements.txt
```

#### Step 4: Run Benchmarks on Jarvis Labs

```bash
# Quick 5+5 verification test
python benchmark/scripts/test_5plus5.py --ann=5 --rca=5

# Full 150-test benchmark (~20 min)
python benchmark/scripts/test_5plus5.py

# Full ablation study, all 4 configs (~1.5 hours)
python benchmark/scripts/run_ablation.py --config all
```

### Copying Results Back to Local Machine

After benchmarks complete, copy the results directory back to your local machine:

```bash
# From your local machine (Git Bash), copy results back
scp -r -i .ssh/jarvis_labs_key -P 11114 \
  root@sshn.jarvislabs.ai:/home/constitutional-aiops/benchmark/results/ \
  benchmark/results/
```

This copies:
- `combined_results.json` - Full benchmark summary
- `ablation_results.json` - All ablation config results
- `all_tables.md` / `paper_tables.md` - Auto-generated paper tables
- `constitutional_aiops/results.json` - Per-test detailed results
- `ablation_*/summary.json` - Per-config ablation summaries

### Quick Reference: Full Transfer Cycle

```bash
# 1. Create tarball (local)
tar czf /tmp/aiops_code.tar.gz --exclude='benchmark/datasets/raw' --exclude='benchmark/results' --exclude='frontend/node_modules' --exclude='.git' --exclude='__pycache__' -C .. constitutional-aiops

# 2. Upload to Jarvis (local → remote)
scp -i .ssh/jarvis_labs_key -P 11114 /tmp/aiops_code.tar.gz root@sshn.jarvislabs.ai:/home/

# 3. Extract + install (on Jarvis)
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai 'cd /home && tar xzf aiops_code.tar.gz && rm aiops_code.tar.gz && cd constitutional-aiops && pip install -r requirements.txt'

# 4. Run benchmark (on Jarvis)
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai 'cd /home/constitutional-aiops && python benchmark/scripts/test_5plus5.py'

# 5. Copy results back (remote → local)
scp -r -i .ssh/jarvis_labs_key -P 11114 root@sshn.jarvislabs.ai:/home/constitutional-aiops/benchmark/results/ benchmark/results/
```

---

## Step 5: Test Ollama API

### From Windows PowerShell (Local Machine)

```powershell
# Test that Ollama is responding
$response = Invoke-RestMethod `
  -Uri "https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/api/tags" `
  -Method GET
$response.models | Format-Table name, size

# Test Fast Agent
$body = @{
    model = "qwen3:4b"
    messages = @(@{role = "user"; content = "Say hello"})
} | ConvertTo-Json -Depth 3

$response = Invoke-RestMethod `
  -Uri "https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/v1/chat/completions" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

$response.choices[0].message.content

# Test Reasoning Agent
$body = @{
    model = "qwen3:14b"
    messages = @(@{role = "user"; content = "What is root cause analysis in IT operations?"})
} | ConvertTo-Json -Depth 3

$response = Invoke-RestMethod `
  -Uri "https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/v1/chat/completions" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

$response.choices[0].message.content
```

### From Git Bash / Linux

```bash
# Test that Ollama is responding
curl https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/api/tags

# Test Fast Agent
curl -X POST https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3:4b", "messages": [{"role": "user", "content": "Say hello"}]}'

# Test Reasoning Agent
curl -X POST https://[YOUR-ENDPOINT].notebooks.jarvislabs.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3:14b", "messages": [{"role": "user", "content": "What is RCA?"}]}'
```

---

## Step 6: Configure Local Environment

Create or update your `.env` file:

```bash
# Jarvis Labs Ollama endpoint (replace with your actual endpoint)
JARVIS_OLLAMA_URL=https://[YOUR-ENDPOINT].notebooks.jarvislabs.net

# Neo4j (local)
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=constitutional_aiops_2025

# Other settings (defaults are fine)
```

---

## Step 7: Start Local Services

```bash
# Start all local services (frontend, backend, Neo4j, monitoring)
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d

# Check services are running
docker compose ps
```

---

## Step 8: Verify Everything Works

### Check Backend Health (PowerShell)
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health"
$response | ConvertTo-Json
```

### Check Backend Health (Git Bash)
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "llm": {
    "fast_agent": true,
    "reasoning_agent": true
  }
}
```

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000/docs | - |
| Neo4j Browser | http://localhost:7474 | neo4j / password123 |
| Grafana | http://localhost:3001 | admin / admin |

---

## Cost Management

### Pause Instance (Billing Pauses)
When you're done developing:
1. Go to Jarvis Labs Dashboard
2. Click **Pause** on your instance
3. Billing stops, **data in /home preserved**

### Resume Instance
1. Click **Resume** on paused instance
2. Same API endpoint
3. Models still available in /home/ollama-models
4. Billing resumes

### Delete Instance (Data Lost)
- Use when completely done
- All data including /home deleted
- Need to re-pull models next time

---

## Cost Breakdown

| Item | Cost |
|------|------|
| A5000 GPU | $0.49/hr |
| Storage (100GB) | ~$0.50/day |
| **1 hour session** | ~$0.50 |
| **8 hour day** | ~$4.50 |
| **Month (8hr/day x 20 days)** | ~$90 |

**Tip**: Always pause when not using!

---

## Troubleshooting

### "Connection refused" from local backend

1. Check JARVIS_OLLAMA_URL is set correctly in `.env`
2. Verify instance is running (not paused)
3. Test API directly:
   ```powershell
   Invoke-RestMethod -Uri "https://[endpoint].notebooks.jarvislabs.net/api/tags"
   ```

### Models not responding

SSH into instance and check:
```bash
OLLAMA_MODELS=/home/ollama-models ollama list   # Are models installed?
OLLAMA_MODELS=/home/ollama-models ollama ps     # Are models loaded?
ls -la /home/ollama-models/                      # Check storage
```

### Models lost after pause/resume

Models were not stored in /home. Re-run the setup:
```bash
export OLLAMA_MODELS=/home/ollama-models
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:4b
OLLAMA_MODELS=/home/ollama-models ollama pull qwen3:14b
```

### Slow responses

- First request loads model into VRAM (~10-30s)
- Subsequent requests are fast
- 14B model is slower than 4B (expected)

### Backend can't reach Ollama

Check Docker environment:
```bash
docker compose logs backend | grep -i agent
```

Verify URL format: `https://xxx.notebooks.jarvislabs.net/v1` (note the `/v1` path)

### PowerShell curl doesn't work

PowerShell's `curl` is an alias for `Invoke-WebRequest`. Use `Invoke-RestMethod` instead:
```powershell
# Wrong (fails in PowerShell)
curl -X POST https://...

# Correct (PowerShell)
Invoke-RestMethod -Uri "https://..." -Method POST -ContentType "application/json" -Body $body
```

---

## Quick Reference

### SSH Command
```bash
ssh -i .ssh/jarvis_labs_key -p 11114 root@sshn.jarvislabs.ai
```

### Start Local Services
```bash
docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d
```

### Stop Local Services
```bash
docker compose down
```

### View Logs
```bash
docker compose logs -f backend
```

### Check Model Status (on Jarvis Labs)
```bash
OLLAMA_MODELS=/home/ollama-models ollama list
OLLAMA_MODELS=/home/ollama-models ollama ps
```

---

## Next Steps

After setup is complete:
1. Open http://localhost:3000
2. Create a test incident
3. Try the chat interface with the reasoning agent
4. Check Neo4j for the incident graph

For full documentation, see:
- [README.md](../README.md) - Project overview
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Full implementation plan
