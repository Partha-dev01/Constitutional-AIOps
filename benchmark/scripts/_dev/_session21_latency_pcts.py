import json, statistics
from pathlib import Path
p = Path(r"c:\Users\partha\Downloads\files AIOPS NEW\constitutional-aiops\benchmark\final\main_benchmark\results.json")
recs = json.loads(p.read_text(encoding="utf-8"))
print(f"records total: {len(recs)}")

def pcts(xs, label):
    xs = sorted(xs)
    n = len(xs)
    if n == 0: return None
    out = {
        "n": n,
        "P50_ms": xs[n // 2],
        "P95_ms": xs[min(int(n * 0.95), n - 1)],
        "P99_ms": xs[min(int(n * 0.99), n - 1)],
        "avg_ms": round(statistics.mean(xs), 1),
        "min_ms": xs[0],
        "max_ms": xs[-1],
    }
    print(f"  {label}: n={out['n']}, P50={out['P50_ms']/1000:.2f}s, P95={out['P95_ms']/1000:.2f}s, P99={out['P99_ms']/1000:.2f}s, avg={out['avg_ms']/1000:.2f}s, range={out['min_ms']/1000:.2f}-{out['max_ms']/1000:.2f}s")
    return out

print()
print("=== INFERENCE latency (RTT-subtracted, what v1 + spec use) ===")
for key in ["inference_latency_ms", "total_latency_ms"]:
    print(f"\nfield: {key}")
    by_task = {}
    for r in recs:
        t = r.get("task_type"); l = r.get(key)
        if t and l is not None: by_task.setdefault(t, []).append(l)
    for tk in sorted(by_task.keys()):
        pcts(by_task[tk], tk)
    all_lat = [x for v in by_task.values() for x in v]
    pcts(all_lat, "end-to-end (all)")

print()
print("=== task_type bucket sizes ===")
buckets = {}
for r in recs:
    t = r.get("task_type"); buckets[t] = buckets.get(t, 0) + 1
print(buckets)
