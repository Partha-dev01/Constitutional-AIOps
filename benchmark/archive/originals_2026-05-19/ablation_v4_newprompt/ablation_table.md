# Ablation Study Results

> Generated: 2026-05-17T01:16:58.097887
> N=431 per configuration

| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Cos Sim | Term Ov. | Avg Latency | Delta vs Full |
|--------------|---------|---------|---------|---------|---------|----------|-------------|---------------|
| Full System (Hybrid dual-agent baseline) | 83.0% | 92.0% | 87.5% | 0.000 | 0.333 | 0.513 | 17634ms | - |
| Single Agent - Qwen3-4B for both annotation and RCA | 82.6% | 99.1% | 90.7% | 0.000 | 0.318 | 0.497 | 5401ms | +3.2% |
| Single Agent - Qwen3-14B for both annotation and RCA | 84.4% | 91.1% | 87.7% | 0.000 | 0.306 | 0.567 | 33717ms | +0.2% |
| No Structured Output - raw text, no JSON metadata extraction | 82.6% | 58.2% | 70.5% | 0.000 | 0.328 | 0.620 | 10055ms | -16.9% |
| No System Prompt - empty system message, raw user query only | 48.6% | 78.9% | 63.6% | 0.000 | 0.310 | 0.569 | 29641ms | -23.9% |
| With Graph Context - historical episode context injected (RAG) | 82.6% | 92.0% | 87.2% | 0.000 | 0.327 | 0.517 | 17908ms | -0.2% |
| No Constitutional AI - skip validation (overhead measurement) | 89.5% | 41.3% | 65.7% | 0.000 | 0.339 | 0.388 | 12641ms | -21.8% |
| LangGraph Orchestrator - full pipeline (annotate->reason->validate->plan) | 82.6% | 93.0% | 87.7% | 0.000 | 0.322 | 0.522 | 17705ms | +0.2% |
