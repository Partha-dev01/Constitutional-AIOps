import json, statistics
from pathlib import Path
p = Path(r"c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\main_benchmark\results.json")
recs = json.loads(p.read_text(encoding="utf-8"))
keep = [r for r in recs if r.get("task_type") in ("annotation", "rca")]
print(f"end-to-end excluding qa_mcq: n={len(keep)}")
xs = sorted([r["inference_latency_ms"] for r in keep])
n = len(xs)
P50 = xs[n // 2]; P95 = xs[min(int(n * 0.95), n - 1)]; P99 = xs[min(int(n * 0.99), n - 1)]
avg = statistics.mean(xs); mn = xs[0]; mx = xs[-1]
print(f"  P50={P50/1000:.2f}s, P95={P95/1000:.2f}s, P99={P99/1000:.2f}s, avg={avg/1000:.2f}s, range={mn/1000:.2f}-{mx/1000:.2f}s")
