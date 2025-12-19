# Jarvis Labs + Qwen3 Deployment Plan

> **Created**: 2025-12-19
> **Status**: Ready for Implementation
> **Key Changes**: Qwen3 models, /home persistence, PowerShell support

---

## CRITICAL UPDATES FROM RESEARCH

### 1. Data Persistence (IMPORTANT!)
**Only `/home` directory persists between restarts!** Models stored elsewhere are LOST.

| Directory | Persists? | Action |
|-----------|-----------|--------|
| `/home/*` | YES | Store models here |
| `/root/*` | NO | Lost on pause/resume |
| `/usr/share/ollama` | NO | Default Ollama location - LOST |

**Solution**: Set `OLLAMA_MODELS=/home/ollama-models`

### 2. Model Upgrade: Qwen3 > Qwen2.5
Research confirms **Qwen3 is significantly better** for reasoning tasks:

| Benchmark | Qwen3-4B | Qwen2.5-7B | Winner |
|-----------|----------|-----------|--------|
| MMLU-Pro | 74 | 45.0 | Qwen3-4B |
| GPQA | 59 | 36.4 | Qwen3-4B |
| MATH | 90 | 49.8 | Qwen3-4B |

**Qwen3-4B beats Qwen2.5-7B in reasoning** - ideal for AIOps RCA!

### 3. VRAM Feasibility: CONFIRMED

```
Model                      VRAM Used
─────────────────────────────────────
Qwen3-14B (Q4_K_M)        ~9 GB
Qwen3-4B (Q4_K_M)         ~3 GB
KV Cache (8K context)     ~2-3 GB
System overhead           ~0.5-1 GB
─────────────────────────────────────
TOTAL                     ~15-16 GB
FREE VRAM                 ~8-9 GB
```

**A5000 24GB can run BOTH models simultaneously!**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR LOCAL MACHINE (Windows)                  │
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
│  API: https://[instance-id].notebooks.jarvislabs.net            │
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
└─────────────────────────────────────────────────────────────────┘
```

---

## Files Modified

| File | Changes |
|------|---------|
| `docs/JARVIS_LABS_DEPLOYMENT.md` | Added persistence warning, Qwen3 models, PowerShell commands |
| `scripts/setup-jarvis-ollama.sh` | Added OLLAMA_MODELS=/home, Qwen3 models |
| `docker/docker-compose.hybrid.yml` | Updated model names to qwen3:4b, qwen3:14b |
| `README.md` | Updated Qwen3 references |
| `docs/CHECKLIST.md` | Updated with Qwen3 model names |

---

## Next Phase: SSH Setup

Once Jarvis Labs VM is started:

1. **SSH into the instance**:
   ```bash
   ssh -i .ssh/jarvis_labs_key -p [PORT] root@sshg.jarvislabs.ai
   ```

2. **Run the setup script** to:
   - Configure /home/ollama-models persistence
   - Pull qwen3:4b (~2.5GB)
   - Pull qwen3:14b (~9.3GB)
   - Test both models
   - Verify persistence

3. **Get the API endpoint** from Jarvis Labs dashboard

4. **Test from local machine** (PowerShell):
   ```powershell
   $response = Invoke-RestMethod `
     -Uri "https://[ENDPOINT].notebooks.jarvislabs.net/api/tags"
   $response
   ```

5. **Configure local .env** and start Docker services

---

## Sources

- [Jarvis Labs Environment](https://docs.jarvislabs.ai/environment/) - /home persistence
- [Ollama Model Storage](https://dev.to/hamed0406/how-to-change-place-of-saving-models-on-ollama-4ko8)
- [Qwen3 Official Blog](https://qwenlm.github.io/blog/qwen3/)
- [Ollama Qwen3 Library](https://ollama.com/library/qwen3)
- [Qwen3 vs Qwen2.5 Comparison](https://blogs.novita.ai/qwen-3-and-qwen-2-5/)
