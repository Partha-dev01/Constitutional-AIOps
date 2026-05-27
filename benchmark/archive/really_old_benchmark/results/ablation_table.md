# Ablation Study Results

> Generated: 2026-02-06T12:34:39.772129

| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Avg Latency | Delta vs Full |
|--------------|---------|---------|---------|---------|-------------|---------------|
| Full System (Hybrid dual-agent baseline) | 100.0% | 80.0% | 90.0% | 0.424 | 8485ms | - |
| Single Agent - Qwen3-4B for both annotation and RCA | 100.0% | 80.0% | 90.0% | 0.425 | 8504ms | +0.0% |
| Single Agent - Qwen3-14B for both annotation and RCA | 100.0% | 80.0% | 90.0% | 0.417 | 9161ms | +0.0% |
| No Structured Output - raw text, no JSON metadata extraction | 100.0% | 100.0% | 100.0% | 0.420 | 8444ms | +10.0% |
