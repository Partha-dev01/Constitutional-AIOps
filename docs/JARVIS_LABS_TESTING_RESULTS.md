# Jarvis Labs Testing Results

> **Date**: 2025-12-20
> **Instance**: Ollama Template on A5000 24GB
> **API Endpoint**: https://251c243656751.notebooks.jarvislabs.net
> **SSH**: ssh -i .ssh/jarvis_labs_key -p 11014 root@sshg.jarvislabs.ai

---

## 1. Ollama Setup Findings

### Template Configuration
The Jarvis Labs Ollama template comes pre-configured with:
- **Ollama Version**: 0.13.5
- **OLLAMA_HOST**: 0.0.0.0:6006 (mapped to HTTPS endpoint)
- **OLLAMA_MODELS**: `/home/.ollama/models` (persistent!)
- **Context Length**: 4096 tokens default
- **GPU**: NVIDIA RTX A5000 (24GB VRAM)

### Pre-loaded Models (from template)
| Model | Size | Notes |
|-------|------|-------|
| llama3:70b | 39 GB | Pre-loaded |
| mixtral:text | 26 GB | Pre-loaded |
| llama3:8b | 4.7 GB | Pre-loaded |
| llava:7b-v1.6 | 4.7 GB | Pre-loaded |

### Data Persistence
**CRITICAL FINDING**: Only `/home` directory persists on Jarvis Labs!

| Directory | Persists? | Size Found |
|-----------|-----------|------------|
| `/home/.models/` | YES | 76 GB (pre-loaded models) |
| `/home/.ollama/` | YES | Template config |
| `/root/*` | NO | Lost on pause/resume |
| `/usr/share/ollama` | NO | Lost on pause/resume |

The Ollama template automatically stores models in `/home/.ollama/models`, which persists across pause/resume cycles.

---

## 2. Qwen3 Model Installation

### Models Pulled
| Model | Size | Download Time | Download Speed |
|-------|------|---------------|----------------|
| qwen3:4b | 2.5 GB | ~22 seconds | ~120 MB/s |
| qwen3:14b | 9.3 GB | ~80 seconds | ~120 MB/s |

### Verification
```
NAME             ID              SIZE      MODIFIED
qwen3:14b        bdbd181c33f2    9.3 GB    Fresh install
qwen3:4b         359d7dd4bcda    2.5 GB    Fresh install
```

---

## 3. Simultaneous Dual-Model Loading - CONFIRMED

### GPU Memory Status (Both Models Loaded)
```
memory.used: 12,900 MiB (~12.6 GB)
memory.total: 24,564 MiB (~24 GB)
memory.free: 11,224 MiB (~11 GB FREE)
```

### Model Loading Details
| Model | VRAM Used | Processor | Context | Keep-Alive |
|-------|-----------|-----------|---------|------------|
| qwen3:14b | 10 GB | 100% GPU | 4096 | 5 min TTL |
| qwen3:4b | 3.6 GB | 100% GPU | 4096 | 5 min TTL |

**KEY FINDING**: Both Qwen3 models CAN run simultaneously on A5000 24GB with ~11GB VRAM to spare!

---

## 4. Dual-LLM Performance Test

### Test 1: Fast Agent (qwen3:4b) - Telemetry Annotation
**Prompt**: Classify log entries and metrics
**Response Time**: ~3.2 seconds
**Tokens**: 409 (109 prompt + 300 completion)

Sample response (reasoning mode):
```
We are given two types of signals: Logs and Metrics.
We need to classify them into structured JSON...
```

### Test 2: Reasoning Agent (qwen3:14b) - Root Cause Analysis
**Prompt**: Perform RCA on classified telemetry
**Response Time**: ~11.8 seconds
**Tokens**: 788 (188 prompt + 600 completion)

Sample response:
```
### **1. Root Cause**
**Primary Cause:**
The database (`db-primary`) is experiencing **connection pool exhaustion**
due to excessive concurrent requests and **high CPU utilization (95%)**...

**Secondary Cause:**
The **high latency (32000ms)** reported by the `api-gateway` is likely
a consequence of the database's poor performance...
```

---

## 5. Performance Benchmarks

### Latency Summary
| Model | Purpose | Response Time | Tokens/sec |
|-------|---------|---------------|------------|
| qwen3:4b | Fast annotation | ~3.2s | ~94 tok/s |
| qwen3:14b | Deep reasoning | ~11.8s | ~51 tok/s |

### HTTPS API Overhead
- Jarvis Labs HTTPS endpoint adds minimal latency (~50-100ms)
- Direct HTTPS access (no SSH tunnel needed)
- API compatible with OpenAI format

---

## 6. Architecture Validated

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE (Windows)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Frontend   │  │   Backend   │  │   Neo4j     │              │
│  │ :3000       │  │  :8000      │  │  :7474      │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
│                          │                                       │
│                    HTTPS requests                                │
│                          │                                       │
└──────────────────────────┼──────────────────────────────────────┘
                           │ Direct HTTPS (encrypted)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           JARVIS LABS - Ollama Template (A5000 24GB)            │
│                                                                 │
│  API: https://251c243656751.notebooks.jarvislabs.net            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     Ollama Server                       │    │
│  │  ┌─────────────────┐  ┌─────────────────────┐          │    │
│  │  │ qwen3:4b        │  │ qwen3:14b           │          │    │
│  │  │ Fast Agent      │  │ Reasoning Agent     │          │    │
│  │  │ 3.6 GB VRAM     │  │ 10 GB VRAM          │          │    │
│  │  │ ~3s latency     │  │ ~12s latency        │          │    │
│  │  └─────────────────┘  └─────────────────────┘          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  GPU Memory: 12.6 GB used / 24 GB total (11 GB FREE)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Key Findings Summary

### Confirmed Working
- [x] SSH connectivity to Jarvis Labs instance
- [x] HTTPS API endpoint accessible
- [x] Both Qwen3 models installed and persistent
- [x] Simultaneous dual-model loading on GPU
- [x] Fast Agent: ~3s response time
- [x] Reasoning Agent: ~12s response time
- [x] OpenAI-compatible API format
- [x] Models persist on pause/resume (in /home)

### Qwen3 Reasoning Mode
Both models use a "reasoning" mode where they show their thought process before answering. This can be controlled with:
- `/no_think` in prompt to suppress (may not fully work)
- `"reasoning"` field appears in API response

### Cost Efficiency
- A5000 instance: $0.49/hr
- Storage: ~$0.50/day
- **Total for 1-hour session**: ~$0.50

---

## 8. End-to-End Integration - COMPLETED

### Fixes Applied (2025-12-20)

1. **Config Environment Variables Fix** ([src/config.py](../src/config.py)):
   - Model names were hardcoded (`qwen3-4b`) instead of reading from env vars
   - Fixed to read `FAST_AGENT_MODEL` and `REASONING_AGENT_MODEL` from environment
   - Also fixed timeout values to read from environment

2. **httpx URL Resolution** ([src/agents/model_router.py](../src/agents/model_router.py)):
   - Changed absolute paths (`/chat/completions`) to relative paths (`chat/completions`)
   - Added trailing slash to base URL for correct resolution

3. **Health Check Endpoint** ([docker-compose.yml](../docker-compose.yml)):
   - Fixed healthcheck from `/health` to `/api/v1/health`

### Integration Test Results
```
Health Check Response:
{
  "status": "healthy",
  "components": [
    {"name": "fast_agent", "healthy": true, "latency_ms": 445.8},
    {"name": "reasoning_agent", "healthy": true, "latency_ms": 176.2},
    {"name": "neo4j", "healthy": true, "latency_ms": 2.68}
  ]
}

Chat API Test:
POST /api/v1/chat/
{"message": "What is your primary function?"}
→ 200 OK, Full AIOps response received
```

### Services Running
| Service | Port | Status |
|---------|------|--------|
| Frontend | 3000 | Healthy |
| Backend | 8000 | Healthy |
| Neo4j | 7474/7687 | Running |
| Grafana | 3001 | Running |
| Prometheus | 9090 | Running |
| Loki | 3100 | Running |

---

## 9. Quick Start Commands

1. **Configure Local Environment**:
   ```bash
   echo "JARVIS_OLLAMA_URL=https://251c243656751.notebooks.jarvislabs.net" >> .env
   ```

2. **Start Local Docker Services**:
   ```bash
   docker compose -f docker-compose.yml -f docker/docker-compose.hybrid.yml up -d
   ```

3. **Verify End-to-End**:
   - Open http://localhost:3000
   - Test chat functionality
   - Verify LLM responses

4. **Remember**: Pause the Jarvis Labs instance when not using to save costs!

---

## Appendix: Raw Commands Used

### SSH Test
```bash
ssh -i .ssh/jarvis_labs_key -p 11014 root@sshg.jarvislabs.ai "echo 'SSH OK' && hostname"
```

### Pull Models
```bash
ssh -i .ssh/jarvis_labs_key -p 11014 root@sshg.jarvislabs.ai "ollama pull qwen3:4b"
ssh -i .ssh/jarvis_labs_key -p 11014 root@sshg.jarvislabs.ai "ollama pull qwen3:14b"
```

### Check GPU Memory
```bash
ssh -i .ssh/jarvis_labs_key -p 11014 root@sshg.jarvislabs.ai "nvidia-smi --query-gpu=memory.used,memory.total,memory.free --format=csv && ollama ps"
```

### Test API
```bash
curl -X POST "https://251c243656751.notebooks.jarvislabs.net/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3:4b", "messages": [{"role": "user", "content": "Hello"}]}'
```
