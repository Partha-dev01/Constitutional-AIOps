# Ablation Study Results

> Generated: 2026-02-06T14:53:49.113812

| Configuration | Ann Acc | RCA Acc | Overall | BERT-F1 | Avg Latency | Delta vs Full |
|--------------|---------|---------|---------|---------|-------------|---------------|
| Full System (Hybrid dual-agent baseline) | 89.0% | 88.0% | 88.7% | 0.458 | 7208ms | - |
| Single Agent - Qwen3-4B for both annotation and RCA | 89.0% | 94.0% | 90.7% | 0.458 | 7250ms | +2.0% |
| Single Agent - Qwen3-14B for both annotation and RCA | 89.0% | 92.0% | 90.0% | 0.457 | 7582ms | +1.3% |
| No Structured Output - raw text, no JSON metadata extraction | 89.0% | 92.0% | 90.0% | 0.458 | 7467ms | +1.3% |
