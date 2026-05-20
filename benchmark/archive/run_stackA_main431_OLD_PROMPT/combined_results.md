# Combined Benchmark Results

> Generated: 2026-05-13 (Phase 4.2 final — post BERTScore/cosine enrichment)

## constitutional_aiops

| Metric | Value |
|--------|-------|
| Model Type | hybrid |
| Fast Model | qwen3:4b-instruct |
| Reasoning Model | qwen3:14b |
| Annotation Accuracy | 82.6% (180/218) |
| RCA Accuracy | 94.8% (202/213) |
| Overall Accuracy | 88.6% (382/431) |
| BERTScore F1 (Annotation) | 0.822 |
| BERTScore F1 (RCA) | 0.7726 |
| BERTScore F1 (Overall) | 0.7975 |
| Cosine Similarity (Annotation) | 0.2041 |
| Cosine Similarity (RCA) | 0.3512 |
| Cosine Similarity (Overall) | 0.2756 |
| Term Overlap (Annotation) | 0.2121 |
| Term Overlap (RCA) | 0.5259 |
| P50 Latency | 4089ms |
| P95 Latency | 54343ms |
| Timestamp | 2026-05-13T10:40:40 (enriched) |

> Note: BERTScore uses roberta-large. Cosine uses all-MiniLM-L6-v2.
> Annotation cosine lower than RCA because expected outputs are JSON, not natural language.
