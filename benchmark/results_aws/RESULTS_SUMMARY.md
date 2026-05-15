# Benchmark Results Summary
_Generated: 2026-05-15 13:37_

## Table 7 — SOTA Baseline Comparison

| System | Annotation | RCA | Overall | Latency | Notes |
|--------|-----------|-----|---------|---------|-------|
| Constitutional AIOps (Ours) | 180/218 (82.6%) | 202/213 (94.8%) | 382/431 (88.6%) | — | Stack A, Ollama Q4_K_M, 431 cases, L4 24GB |
| Llama 3.3-70B (Bedrock) | 186/202 (92.1%) | 116/198 (58.6%) | 302/400 (75.5%) | — | SOTA baseline, 400 cases |
| DeepSeek V3.2 (Bedrock) | 183/202 (90.6%) | 113/198 (57.1%) | 296/400 (74.0%) | — | SOTA baseline, 400 cases |

## RCA Gap vs SOTA

- **Llama 3.3-70B (Bedrock)**: Our RCA 94.8% vs 58.6% = **+36.2pp**
- **DeepSeek V3.2 (Bedrock)**: Our RCA 94.8% vs 57.1% = **+37.8pp**

## LaTeX Snippet (Table 7)

```latex
\begin{table}[t]
\caption{SOTA Baseline Comparison (400 cases, same system prompt)}\label{tab:sota}
\begin{tabular}{lccccc}
\toprule
System & Ann. & RCA & Overall & $\Delta$ RCA \\
\midrule
Constitutional AIOps (Ours) & 82.6\% & 94.8\% & 88.6\% & — \\
Llama 3.3-70B (Bedrock) & 92.1\% & 58.6\% & 75.5\% & $+36.2$pp \\
DeepSeek V3.2 (Bedrock) & 90.6\% & 57.1\% & 74.0\% & $+37.8$pp \\
\bottomrule
\end{tabular}
\end{table}
```
