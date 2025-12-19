# Jarvis Labs Deployment Guide

> **Template**: Ollama
> **GPU**: A5000 (24GB VRAM) - $0.49/hr
> **Storage**: 100GB recommended
> **Setup Time**: ~10 minutes

This guide explains how to run Constitutional AIOps with LLMs on Jarvis Labs while keeping all other services (frontend, backend, Neo4j, monitoring) running locally for easy debugging.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR LOCAL MACHINE                            │
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
│  API Endpoint: https://[instance-id].jarvislabs.net             │
│                                                                 │
│  Models:                                                        │
│  • qwen2.5:3b   (Fast Agent - classification, annotation)       │
│  • qwen2.5:14b  (Reasoning Agent - RCA, planning, chat)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**No SSH tunnel needed!** The Ollama template provides a direct HTTPS API endpoint.

---

## Prerequisites

- Docker Desktop installed locally
- $10-20 credits on Jarvis Labs account
- Git repository cloned locally

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
- **SSH Address**: For terminal access (e.g., `root@ssh-xxx.jarvislabs.net`)
- **API Endpoint**: For API access (e.g., `https://xxx.jarvislabs.net`)

---

## Step 4: Pull LLM Models via SSH

SSH into the instance and pull the required models:

```bash
# Connect to Jarvis Labs instance
ssh -i .ssh/jarvis_labs_key root@[SSH-ADDRESS]

# Pull Fast Agent model (~2GB, ~1-2 min)
ollama pull qwen2.5:3b

# Pull Reasoning Agent model (~9GB, ~5-8 min)
ollama pull qwen2.5:14b

# Verify models are installed
ollama list
```

### Alternative: Run Setup Script
```bash
ssh root@[SSH-ADDRESS] 'bash -s' < scripts/setup-jarvis-ollama.sh
```

---

## Step 5: Test Ollama API

From your **local machine**, test the API endpoint:

```bash
# Test that Ollama is responding
curl https://[API-ENDPOINT]/api/tags

# Test Fast Agent
curl -X POST https://[API-ENDPOINT]/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

---

## Step 6: Configure Local Environment

Create or update your `.env` file:

```bash
# Jarvis Labs Ollama endpoint
JARVIS_OLLAMA_URL=https://[YOUR-API-ENDPOINT]

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

### Check Backend Health
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
3. Billing stops, data preserved

### Resume Instance
1. Click **Resume** on paused instance
2. Same API endpoint, models still loaded
3. Billing resumes

### Delete Instance (Data Lost)
- Use when completely done
- All data and models deleted
- Need to re-pull models next time

---

## Cost Breakdown

| Item | Cost |
|------|------|
| A5000 GPU | $0.49/hr |
| Storage (100GB) | ~$0.50/day |
| **1 hour session** | ~$0.50 |
| **8 hour day** | ~$4.50 |
| **Month (8hr/day × 20 days)** | ~$90 |

**Tip**: Always pause when not using!

---

## Troubleshooting

### "Connection refused" from local backend

1. Check JARVIS_OLLAMA_URL is set correctly in `.env`
2. Verify instance is running (not paused)
3. Test API directly: `curl https://[endpoint]/api/tags`

### Models not responding

SSH into instance and check:
```bash
ollama list              # Are models installed?
ollama ps                # Are models loaded?
cat /home/ollama.log     # Check logs
```

### Slow responses

- First request loads model into VRAM (~10-30s)
- Subsequent requests are fast
- 14B model is slower than 3B (expected)

### Backend can't reach Ollama

Check Docker environment:
```bash
docker compose logs backend | grep -i agent
```

Verify URL format: `https://xxx.jarvislabs.net/v1` (note the `/v1` path)

---

## Quick Reference

### SSH Command
```bash
ssh -i .ssh/jarvis_labs_key root@[SSH-ADDRESS]
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
