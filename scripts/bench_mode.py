#!/usr/bin/env python3
"""Constitutional AIOps - Mode benchmark replay tool (Phase 0 of the Mode 2 plan).

Replays a FIXED request set against a LIVE deployment and writes one
timestamped JSON result file, so serving-stack changes (Mode 1 vs Mode 2,
engine upgrades, prompt-layout work) can be compared run-over-run with the
same ruler.

Workloads (in order):
  A. Single-shot reasoning calls — N chat turns (default 10), each in a FRESH
     conversation, cycling a fixed set of 10 realistic AIOps prompts.
  B. Multi-turn conversation replay — one scripted 5-turn conversation reusing
     the SAME conversation_id (this is the workload automatic prefix caching
     is expected to improve in later phases; today it baselines Mode 1).
  C. Server-side micro-benchmark — POST /api/v1/metrics/benchmark for the
     fast and reasoning agents (skipped gracefully if the endpoint errors).

Around the workloads it snapshots GET /api/v1/metrics (before AND after) so
the server-side avg/p50/p95/p99 + total_tokens deltas are captured alongside
the client-side wall times, and records the backend version from
GET /api/v1/health.

Usage:
    python scripts/bench_mode.py --base-url https://<your-deployment> \
        --label mode1-baseline [--out-dir data/state/bench] \
        [--single-shot 10] [--benchmark-iterations 5] [--timeout 180]

Auth (all via environment; NEVER hardcode credentials):
  * Reverse-proxy (Caddy) basic auth:  E2E_USER / E2E_PASS
  * In-app login (POST /api/v1/auth/login): E2E_APP_USER / E2E_APP_PASS
    (falls back to E2E_USER / E2E_PASS, mirroring the live-e2e convention).
    The tool first reads GET /api/v1/auth/config; when auth_required is
    false the login step is skipped entirely (graceful degradation for
    local/dev deployments).
  * When basic auth is in use, the Authorization header must stay "Basic ..."
    for the proxy, so the in-app session rides the httpOnly session cookie
    (kept by the HTTP client's cookie jar). Without basic auth, the session
    token is ALSO sent as "Authorization: Bearer <token>" — the API accepts
    either — which keeps plain-HTTP targets working (the session cookie is
    flagged Secure and would not be re-sent over http).

Safety: the run is read-only EXCEPT that it creates chat conversations (one
per single-shot call + one for the replay) and appends latency records to the
in-memory metrics history. It never calls action tools, never deletes, never
changes settings. Safe to run repeatedly.

Output schema (one JSON file per run, "bench_<label>_<UTC>.json"):
  {
    "schema_version": 1,
    "label": str,                      # e.g. "mode1-baseline" (run comparability key)
    "started_at": str, "finished_at": str,   # UTC ISO-8601
    "backend": {"version": str|null, "status": str|null, "auth_required": bool|null},
    "engine": {"version": null, "note": str},   # TODO hook, see fetch_engine_version()
    "config": {"single_shot_calls": int, "conversation_turns": int,
               "benchmark_iterations": int, "timeout_s": float},
    "metrics_before": <GET /api/v1/metrics body>|null,
    "metrics_after":  <GET /api/v1/metrics body>|null,
    "single_shot": {
        "calls": [{"prompt_id": str, "wall_ms": float, "status_code": int|null,
                   "ok": bool, "confidence": float|null, "tokens_used": int|null,
                   "timings": {"context_build_ms","tools_ms","llm_ms","total_ms"}|null,
                   "content_chars": int|null, "error": str|null}, ...],
        "summary": {"count","ok","avg_ms","p50_ms","p95_ms","min_ms","max_ms"}
    },
    "conversation": {
        "conversation_id": str|null,
        "turns": [<same per-call shape, plus "turn": int>, ...],
        "summary": {<same as above>}
    },
    "server_benchmark": {"fast": <endpoint body|{"error": str}>,
                         "reasoning": <endpoint body|{"error": str}>}
  }
Notes:
  * The target base URL is deliberately NOT stored in the output (public-repo
    hygiene: results may be committed as numbers-only baselines).
  * "timings" is the per-stage breakdown added to chat metadata in Phase 0;
    it is null against older backends (the tool tolerates its absence).
  * Server-side metrics history is in-memory and resets on backend restart —
    capture baselines within one backend lifetime (see metrics_before/after).

Dependencies: stdlib + httpx (already a project dependency). No src/ imports,
so the script can run from any machine that can reach the deployment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

# Session cookie name used by the backend (src/auth/tokens.py COOKIE_NAME).
# Duplicated here on purpose: this script must not import src/.
_SESSION_COOKIE = "aiops_session"

# ---------------------------------------------------------------------------
# Fixed workloads (do not edit between runs you intend to compare)
# ---------------------------------------------------------------------------

# Workload A: 10 realistic single-shot AIOps prompts. They name monitored
# services so the chat path exercises its telemetry/tool routing, mirroring
# real operator traffic (reasoning-agent calls, the latency that matters).
SINGLE_SHOT_PROMPTS: list[tuple[str, str]] = [
    ("SS01", "Analyze the recent error logs for the nextcloud service and summarize the dominant failure pattern."),
    ("SS02", "What are the upstream and downstream dependencies of the backend service?"),
    ("SS03", "Is neo4j healthy right now? Check its current status and any recent errors."),
    ("SS04", "Have there been any similar past incidents involving high memory usage on nextcloud?"),
    ("SS05", "Summarize the current CPU and memory metrics for the prometheus container."),
    ("SS06", "What could cause intermittent 502 errors from the frontend, and what should I check first?"),
    ("SS07", "Loki is ingesting logs slowly and grafana dashboards are lagging. Give me a quick root cause assessment."),
    ("SS08", "Which containers are currently running, and are any of them unhealthy?"),
    ("SS09", "Recommend safe, reversible remediation steps for sustained high disk usage on the loki container."),
    ("SS10", "Explain how an outage of neo4j would impact incident correlation in this system."),
]

# Workload B: one scripted 5-turn incident-investigation conversation. All
# turns share ONE conversation_id so the growing shared history exposes
# prefix-caching effects once the serving stack supports exploiting them.
CONVERSATION_TURNS: list[str] = [
    "We are seeing elevated error rates on nextcloud. Analyze the recent logs and tell me what stands out.",
    "Which services depend on nextcloud? What is the blast radius if it degrades further?",
    "Have we seen similar incidents before? What was the root cause then?",
    "Given everything so far, what is your best root-cause hypothesis right now?",
    "Propose a safe, reversible remediation plan for this incident.",
]

# Workload C: the existing server-side micro-benchmark endpoint, with its
# default classification prompt (fixed for comparability).
BENCHMARK_PROMPT = "Classify this log: ERROR Connection timeout"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _percentile(sorted_data: list[float], p: float) -> float:
    """Same interpolation as ModelRouter.get_latency_stats (comparable numbers)."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    if c == f:
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _summarize(calls: list[dict[str, Any]]) -> dict[str, Any]:
    ok_calls = [c for c in calls if c.get("ok")]
    lats = sorted(float(c["wall_ms"]) for c in ok_calls)
    if not lats:
        return {"count": len(calls), "ok": 0, "avg_ms": 0.0, "p50_ms": 0.0,
                "p95_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}
    return {
        "count": len(calls),
        "ok": len(ok_calls),
        "avg_ms": round(sum(lats) / len(lats), 2),
        "p50_ms": round(_percentile(lats, 50), 2),
        "p95_ms": round(_percentile(lats, 95), 2),
        "min_ms": round(lats[0], 2),
        "max_ms": round(lats[-1], 2),
    }


def fetch_engine_version(client: httpx.Client) -> Optional[str]:
    """Engine (vLLM) version hook — intentionally a no-op in Phase 0.

    TODO(Phase 1, Mode 2 plan): once GET /api/v1/health/serving exists and
    proxies the LLM engine's /version + /v1/models, read the engine version
    here and store it in the output's "engine" block. In Mode 1 the vLLM
    /version endpoint is only reachable from inside the VM (ports 8000/8001
    are not exposed through the proxy), so there is nothing to query from a
    remote bench client yet.
    """
    _ = client  # unused until the serving health endpoint lands
    return None


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------


def build_client(base_url: str, timeout_s: float) -> httpx.Client:
    auth: Optional[httpx.BasicAuth] = None
    user = os.environ.get("E2E_USER") or ""
    password = os.environ.get("E2E_PASS") or ""
    if user and password:
        auth = httpx.BasicAuth(user, password)
    return httpx.Client(
        base_url=base_url.rstrip("/"),
        auth=auth,
        timeout=httpx.Timeout(timeout_s, connect=15.0),
        follow_redirects=True,
        headers={"User-Agent": "aiops-bench-mode/1.0"},
    )


def app_login(client: httpx.Client) -> Optional[bool]:
    """In-app login when the deployment enforces it.

    Returns the deployment's auth_required flag (None if unknown). Raises
    SystemExit with a clear message when auth is required but no credentials
    were provided (running the workloads would only produce 401 noise).
    """
    auth_required: Optional[bool] = None
    try:
        resp = client.get("/api/v1/auth/config")
        resp.raise_for_status()
        auth_required = bool(resp.json().get("auth_required"))
    except Exception as exc:  # noqa: BLE001 - endpoint may predate auth
        print(f"[bench] WARNING: could not read /api/v1/auth/config ({exc}); "
              "continuing without in-app login")
        return None

    if not auth_required:
        print("[bench] in-app auth not enforced; skipping login")
        return False

    app_user = os.environ.get("E2E_APP_USER") or os.environ.get("E2E_USER") or ""
    app_pass = os.environ.get("E2E_APP_PASS") or os.environ.get("E2E_PASS") or ""
    if not app_user or not app_pass:
        raise SystemExit(
            "[bench] ERROR: deployment enforces in-app auth but no credentials "
            "were provided. Set E2E_APP_USER / E2E_APP_PASS (or E2E_USER / "
            "E2E_PASS) in the environment."
        )

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": app_user, "password": app_pass},
    )
    if resp.status_code != 200:
        raise SystemExit(
            f"[bench] ERROR: in-app login failed with HTTP {resp.status_code}: "
            f"{resp.text[:200]}"
        )

    # Session rides the httpOnly cookie (kept by the client's cookie jar).
    # Without proxy basic auth the Authorization header is free, so ALSO send
    # the token as a Bearer (the API accepts either; this keeps plain-HTTP
    # targets working where the Secure cookie would not be re-sent).
    token = client.cookies.get(_SESSION_COOKIE)
    if token and client.auth is None:
        client.headers["Authorization"] = f"Bearer {token}"
    print(f"[bench] logged in as '{app_user}' (session established)")
    return True


def get_json(client: httpx.Client, path: str) -> Optional[dict[str, Any]]:
    try:
        resp = client.get(path)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001 - snapshots are best-effort
        print(f"[bench] WARNING: GET {path} failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Workloads
# ---------------------------------------------------------------------------


def _timed_chat_call(
    client: httpx.Client,
    message: str,
    conversation_id: Optional[str] = None,
) -> tuple[dict[str, Any], Optional[str]]:
    """POST one chat turn; return (per-call record, conversation_id)."""
    payload: dict[str, Any] = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id

    record: dict[str, Any] = {
        "wall_ms": 0.0, "status_code": None, "ok": False, "confidence": None,
        "tokens_used": None, "timings": None, "content_chars": None, "error": None,
    }
    conv_id: Optional[str] = conversation_id
    start = time.perf_counter()
    try:
        resp = client.post("/api/v1/chat/", json=payload)
        record["wall_ms"] = round((time.perf_counter() - start) * 1000, 2)
        record["status_code"] = resp.status_code
        if resp.status_code == 200:
            body = resp.json()
            record["ok"] = True
            record["confidence"] = body.get("confidence")
            conv_id = body.get("conversation_id") or conv_id
            meta = body.get("metadata") or {}
            record["tokens_used"] = meta.get("tokens_used")
            # Phase 0 stage breakdown; null against pre-Phase-0 backends.
            timings = meta.get("timings")
            record["timings"] = timings if isinstance(timings, dict) else None
            content = ((body.get("message") or {}).get("content")) or ""
            record["content_chars"] = len(content)
        else:
            record["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:  # noqa: BLE001 - keep replaying, record the failure
        record["wall_ms"] = round((time.perf_counter() - start) * 1000, 2)
        record["error"] = str(exc)[:300]
    return record, conv_id


def run_single_shot(client: httpx.Client, n_calls: int) -> dict[str, Any]:
    print(f"[bench] workload A: {n_calls} single-shot reasoning call(s)")
    calls: list[dict[str, Any]] = []
    for i in range(n_calls):
        prompt_id, prompt = SINGLE_SHOT_PROMPTS[i % len(SINGLE_SHOT_PROMPTS)]
        record, _ = _timed_chat_call(client, prompt, conversation_id=None)
        record = {"prompt_id": prompt_id, **record}
        calls.append(record)
        status = "ok" if record["ok"] else f"FAIL ({record['error']})"
        print(f"[bench]   {prompt_id}: {record['wall_ms']:.0f} ms  {status}")
    return {"calls": calls, "summary": _summarize(calls)}


def run_conversation(client: httpx.Client, turns: list[str]) -> dict[str, Any]:
    print(f"[bench] workload B: scripted {len(turns)}-turn conversation replay")
    conv_id: Optional[str] = None
    records: list[dict[str, Any]] = []
    for idx, message in enumerate(turns, start=1):
        record, conv_id = _timed_chat_call(client, message, conversation_id=conv_id)
        record = {"turn": idx, **record}
        records.append(record)
        status = "ok" if record["ok"] else f"FAIL ({record['error']})"
        print(f"[bench]   turn {idx}: {record['wall_ms']:.0f} ms  {status}")
    return {
        "conversation_id": conv_id,
        "turns": records,
        "summary": _summarize(records),
    }


def run_server_benchmark(client: httpx.Client, iterations: int) -> dict[str, Any]:
    print(f"[bench] workload C: POST /api/v1/metrics/benchmark "
          f"({iterations} iteration(s) per agent)")
    out: dict[str, Any] = {}
    for agent in ("fast", "reasoning"):
        try:
            resp = client.post(
                "/api/v1/metrics/benchmark",
                json={"agent": agent, "iterations": iterations,
                      "prompt": BENCHMARK_PROMPT},
            )
            resp.raise_for_status()
            out[agent] = resp.json()
            lat = (out[agent].get("latency") or {})
            print(f"[bench]   {agent}: status={out[agent].get('status')} "
                  f"avg={lat.get('avg_ms')} ms p95={lat.get('p95_ms')} ms")
        except Exception as exc:  # noqa: BLE001 - endpoint is optional
            out[agent] = {"error": str(exc)[:300]}
            print(f"[bench]   {agent}: SKIPPED ({exc})")
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _fmt_row(cols: list[str], widths: list[int]) -> str:
    return "  ".join(c.ljust(w) for c, w in zip(cols, widths))


def print_summary(result: dict[str, Any], out_path: Path) -> None:
    backend = result.get("backend") or {}
    print()
    print("=" * 72)
    print(f"BENCH SUMMARY  label={result['label']}  "
          f"backend v{backend.get('version') or '?'} ({backend.get('status') or '?'})")
    print("=" * 72)

    widths = [22, 6, 4, 10, 10, 10, 10]
    print(_fmt_row(["workload", "n", "ok", "avg_ms", "p50_ms", "p95_ms", "max_ms"], widths))
    print(_fmt_row(["-" * w for w in widths], widths))
    for name, block in (("single-shot chat", result.get("single_shot")),
                        ("5-turn conversation", result.get("conversation"))):
        if not block:
            continue
        s = block["summary"]
        print(_fmt_row(
            [name, str(s["count"]), str(s["ok"]), f"{s['avg_ms']:.0f}",
             f"{s['p50_ms']:.0f}", f"{s['p95_ms']:.0f}", f"{s['max_ms']:.0f}"],
            widths,
        ))

    # Server-side reasoning-agent delta (in-memory history: before vs after).
    before = (result.get("metrics_before") or {}).get("reasoning_agent") or {}
    after = (result.get("metrics_after") or {}).get("reasoning_agent") or {}
    if after:
        d_count = (after.get("count") or 0) - (before.get("count") or 0)
        d_tokens = (after.get("total_tokens") or 0) - (before.get("total_tokens") or 0)
        print()
        print(f"server-side reasoning agent: +{d_count} request(s), "
              f"+{d_tokens} token(s) this run; "
              f"cumulative avg={after.get('avg_ms')} ms p95={after.get('p95_ms')} ms")

    bench = result.get("server_benchmark") or {}
    for agent in ("fast", "reasoning"):
        blk = bench.get(agent) or {}
        lat = blk.get("latency") or {}
        if lat:
            print(f"server micro-bench [{agent}]: avg={lat.get('avg_ms')} ms "
                  f"p50={lat.get('p50_ms')} ms p95={lat.get('p95_ms')} ms")

    print()
    print(f"results written to: {out_path}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bench_mode.py",
        description=("Replay a fixed benchmark request set against a live "
                     "Constitutional AIOps deployment and write a timestamped "
                     "JSON result (see module docstring for the schema)."),
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AIOPS_BASE_URL", ""),
        help="Deployment base URL, e.g. https://aiops.example (or env AIOPS_BASE_URL)",
    )
    parser.add_argument(
        "--label", default="baseline",
        help="Run label for comparability, e.g. mode1-baseline (default: baseline)",
    )
    parser.add_argument(
        "--out-dir", default=os.path.join("data", "state", "bench"),
        help="Directory for result JSON files (default: data/state/bench)",
    )
    parser.add_argument(
        "--single-shot", type=int, default=len(SINGLE_SHOT_PROMPTS),
        help="Number of single-shot chat calls (cycles the fixed 10-prompt set)",
    )
    parser.add_argument(
        "--benchmark-iterations", type=int, default=5,
        help="Iterations per agent for POST /metrics/benchmark (default: 5)",
    )
    parser.add_argument(
        "--skip-server-benchmark", action="store_true",
        help="Skip workload C (the /metrics/benchmark endpoint)",
    )
    parser.add_argument(
        "--timeout", type=float, default=180.0,
        help="Per-request timeout in seconds (default: 180; reasoning calls are slow)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if not args.base_url:
        print("[bench] ERROR: --base-url (or env AIOPS_BASE_URL) is required",
              file=sys.stderr)
        return 2

    started_at = _utcnow_iso()
    client = build_client(args.base_url, args.timeout)

    result: dict[str, Any] = {
        "schema_version": 1,
        "label": args.label,
        "started_at": started_at,
        "finished_at": None,
        "backend": {"version": None, "status": None, "auth_required": None},
        "engine": {
            "version": None,
            "note": ("engine /version not reachable from a remote client in "
                     "Mode 1; TODO Phase 1: read GET /api/v1/health/serving"),
        },
        "config": {
            "single_shot_calls": args.single_shot,
            "conversation_turns": len(CONVERSATION_TURNS),
            "benchmark_iterations": args.benchmark_iterations,
            "timeout_s": args.timeout,
        },
        "metrics_before": None,
        "metrics_after": None,
        "single_shot": None,
        "conversation": None,
        "server_benchmark": None,
    }

    try:
        result["backend"]["auth_required"] = app_login(client)

        health = get_json(client, "/api/v1/health")
        if health:
            result["backend"]["version"] = health.get("version")
            result["backend"]["status"] = health.get("status")
            print(f"[bench] backend version {health.get('version')} "
                  f"status={health.get('status')}")
        result["engine"]["version"] = fetch_engine_version(client)

        result["metrics_before"] = get_json(client, "/api/v1/metrics")

        result["single_shot"] = run_single_shot(client, args.single_shot)
        result["conversation"] = run_conversation(client, CONVERSATION_TURNS)
        if args.skip_server_benchmark:
            print("[bench] workload C skipped (--skip-server-benchmark)")
        else:
            result["server_benchmark"] = run_server_benchmark(
                client, args.benchmark_iterations
            )

        result["metrics_after"] = get_json(client, "/api/v1/metrics")
    finally:
        client.close()

    result["finished_at"] = _utcnow_iso()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_label = "".join(c if c.isalnum() or c in "-_" else "-" for c in args.label)
    out_path = out_dir / f"bench_{safe_label}_{stamp}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print_summary(result, out_path)

    ss_ok = (result.get("single_shot") or {}).get("summary", {}).get("ok", 0)
    conv_ok = (result.get("conversation") or {}).get("summary", {}).get("ok", 0)
    if ss_ok + conv_ok == 0:
        print("[bench] ERROR: every chat call failed — check auth/URL/backend state",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
