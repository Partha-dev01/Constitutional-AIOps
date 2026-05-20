# Ablation Study Results

> Generated: 2026-02-10T14:11:30.387192
> N=150 per configuration

| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Cos Sim | Term Ov. | Avg Latency | Delta vs Full |
|--------------|---------|---------|---------|---------|---------|----------|-------------|---------------|
| Full System (Hybrid dual-agent baseline) | 89.0% | 98.0% | 92.0% | 0.459 | 0.308 | 0.433 | 5917ms | - |
| Single Agent - Qwen3-4B for both annotation and RCA | 89.0% | 94.0% | 90.7% | 0.457 | 0.309 | 0.401 | 6033ms | -1.3% |
| Single Agent - Qwen3-14B for both annotation and RCA | 89.0% | 88.0% | 88.7% | 0.458 | 0.306 | 0.427 | 5988ms | -3.3% |
| No Structured Output - raw text, no JSON metadata extraction | 89.0% | 96.0% | 91.3% | 0.457 | 0.302 | 0.383 | 6157ms | -0.7% |
| No System Prompt - empty system message, raw user query only | 45.0% | 92.0% | 60.7% | 0.389 | 0.288 | 0.780 | 11018ms | -31.3% |
| With Graph Context - historical episode context injected (RAG) | 89.0% | 90.0% | 89.3% | 0.454 | 0.288 | 0.335 | 6430ms | -2.7% |
| No Constitutional AI - skip validation (overhead measurement) | 89.0% | 96.0% | 91.3% | 0.457 | 0.307 | 0.420 | 6110ms | -0.7% |
