#!/usr/bin/env python3
"""
Constitutional AIOps - t3 chaos/remediation control agent.

A tiny, dependency-free HTTP agent that runs ON the remote t3 host (next to the
nextcloud + nextcloud-db containers) with the host docker socket mounted. The
AIOps backend (on a different host) cannot reach this docker daemon directly, so
it calls this agent over HTTP to (a) inject chaos scenarios and (b) remediate by
restarting containers.

STDLIB ONLY (http.server, json, subprocess, os, hmac). The docker CLI is provided
by the base image (docker:27-cli).

Security:
  - Every endpoint except nothing-public is bearer-token gated. The token comes
    from env DEMO_AGENT_TOKEN and is compared with hmac.compare_digest.
  - The agent REFUSES TO START if DEMO_AGENT_TOKEN is empty.
  - /remediate/restart only accepts containers on the DEMO_AGENT_CONTAINERS
    whitelist (default: nextcloud,nextcloud-db).

HTTP API (all JSON; bearer-gated unless noted):
  GET  /health                       -> {"ok":true,"version":"1","docker":<bool>}
  GET  /status                       -> {"scenarios":{...},"containers":{...}}
  POST /chaos/{scenario}/start       -> {"scenario","action","success","detail"}
  POST /chaos/{scenario}/heal        -> {"scenario","action","success","detail"}
  POST /remediate/restart {container}-> {"container","action":"restart","success"}
"""

import hmac
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1"

# ---------------------------------------------------------------------------
# Configuration (env)
# ---------------------------------------------------------------------------

DEMO_AGENT_TOKEN = os.getenv("DEMO_AGENT_TOKEN", "")
DEMO_AGENT_PORT = int(os.getenv("DEMO_AGENT_PORT", "8889"))

NEXTCLOUD_CONTAINER = os.getenv("NEXTCLOUD_CONTAINER", "nextcloud")
NEXTCLOUD_DB_CONTAINER = os.getenv("NEXTCLOUD_DB_CONTAINER", "nextcloud-db")


def _whitelist() -> set:
    """Containers this agent may act on (restart/exec). Default: the two NC ones."""
    raw = os.getenv(
        "DEMO_AGENT_CONTAINERS",
        f"{NEXTCLOUD_CONTAINER},{NEXTCLOUD_DB_CONTAINER}",
    )
    return {name.strip() for name in raw.split(",") if name.strip()}


# The five chaos scenarios this agent understands.
SCENARIOS = ("db_down", "cpu_stress", "mem_stress", "bad_config_5xx", "disk_fill")


# ---------------------------------------------------------------------------
# Pure helpers (unit-testable without a server)
# ---------------------------------------------------------------------------

def is_authorized(header: str) -> bool:
    """Constant-time check of an ``Authorization: Bearer <token>`` header.

    Returns False if the agent token is empty (the agent refuses to start in that
    case, but we still fail closed here), if the header is missing/malformed, or
    if the token does not match.
    """
    if not DEMO_AGENT_TOKEN:
        return False
    if not header or not isinstance(header, str):
        return False
    prefix = "Bearer "
    if not header.startswith(prefix):
        return False
    presented = header[len(prefix):].strip()
    if not presented:
        return False
    return hmac.compare_digest(presented, DEMO_AGENT_TOKEN)


def build_commands(scenario: str, action: str) -> list:
    """Build the docker command(s) for a (scenario, action) pair.

    Returns a list of argv lists (each runnable via subprocess.run). Raises
    ``KeyError`` for an unknown scenario and ``ValueError`` for an unknown action.
    All commands are written to be idempotent (``|| true``, ``docker start`` is a
    no-op when already running) so repeated start/heal calls are safe.

    Scenario commands (run on the t3 via the mounted docker socket):
      - db_down:        stop/start the nextcloud-db container.
      - cpu_stress:     two self-expiring (~90s) busy loops inside nextcloud.
      - mem_stress:     a self-expiring (~90s) memory-growth loop inside nextcloud.
      - bad_config_5xx: toggle nextcloud maintenance mode (returns 503/errors).
      - disk_fill:      write a 512MB junk file + spam the nextcloud log; heal rm.
    """
    nc = NEXTCLOUD_CONTAINER
    db = NEXTCLOUD_DB_CONTAINER

    if action not in ("start", "heal"):
        raise ValueError(f"unknown action: {action}")

    if scenario == "db_down":
        if action == "start":
            return [["docker", "stop", db]]
        return [["docker", "start", db]]

    if scenario == "cpu_stress":
        if action == "start":
            # Two self-expiring busy loops (each times out after 90s).
            loop = "timeout 90 sh -c 'while :; do :; done'"
            one = ["docker", "exec", "-d", nc, "sh", "-c", loop]
            return [list(one), list(one)]
        # Best-effort kill of the busy loops.
        return [["docker", "exec", nc, "sh", "-c", "pkill -f 'while :' || true"]]

    if scenario == "mem_stress":
        if action == "start":
            # Self-expiring (~90s) memory growth: double a string until OOM/timeout.
            # `timeout 90` guarantees it releases the held allocation by itself even
            # if it never OOMs, so the host can't be wedged by a stuck demo.
            grow = (
                "timeout 90 sh -c 'a=; while :; do a=$a$a; done' "
                "2>/dev/null || true"
            )
            return [["docker", "exec", "-d", nc, "sh", "-c", grow]]
        # Best-effort kill of the growth loop.
        return [["docker", "exec", nc, "sh", "-c", "pkill -f 'a=$a$a' || true"]]

    if scenario == "bad_config_5xx":
        if action == "start":
            return [
                ["docker", "exec", "-u", "www-data", nc,
                 "php", "occ", "maintenance:mode", "--on"]
            ]
        return [
            ["docker", "exec", "-u", "www-data", nc,
             "php", "occ", "maintenance:mode", "--off"]
        ]

    if scenario == "disk_fill":
        if action == "start":
            fill = (
                "dd if=/dev/zero of=/var/www/html/data/chaos_fill.bin "
                "bs=1M count=512 2>/dev/null; "
                "for i in $(seq 1 500); do "
                "echo '{\"level\":3,\"app\":\"core\","
                "\"message\":\"disk pressure simulated\"}' "
                ">> /var/www/html/data/nextcloud.log; done"
            )
            return [["docker", "exec", nc, "sh", "-c", fill]]
        rm = "rm -f /var/www/html/data/chaos_fill.bin || true"
        return [["docker", "exec", nc, "sh", "-c", rm]]

    raise KeyError(f"unknown scenario: {scenario}")


# ---------------------------------------------------------------------------
# Docker helpers (impure — touch the daemon)
# ---------------------------------------------------------------------------

def _run(cmd: list, timeout: int = 60) -> tuple:
    """Run a command, returning (returncode, stdout, stderr). Never raises."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def docker_available() -> bool:
    """True when the docker CLI + daemon are reachable."""
    rc, _, _ = _run(["docker", "info"], timeout=10)
    return rc == 0


def container_running(name: str) -> bool:
    """True when the named container exists and is in the running state."""
    rc, out, _ = _run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name], timeout=10,
    )
    return rc == 0 and out.strip() == "true"


def scenario_active(scenario: str) -> bool:
    """Best-effort liveness check for a scenario (used by /status).

    These are heuristics, not guarantees — they reflect the observable side
    effect of each scenario.
    """
    nc = NEXTCLOUD_CONTAINER
    db = NEXTCLOUD_DB_CONTAINER

    if scenario == "db_down":
        return not container_running(db)

    if scenario == "cpu_stress":
        rc, out, _ = _run(
            ["docker", "exec", nc, "sh", "-c", "pgrep -f 'while :' || true"],
            timeout=10,
        )
        return rc == 0 and bool(out.strip())

    if scenario == "mem_stress":
        rc, out, _ = _run(
            ["docker", "exec", nc, "sh", "-c", "pgrep -f 'a=$a$a' || true"],
            timeout=10,
        )
        return rc == 0 and bool(out.strip())

    if scenario == "bad_config_5xx":
        rc, out, _ = _run(
            ["docker", "exec", "-u", "www-data", nc,
             "php", "occ", "maintenance:mode"],
            timeout=15,
        )
        return rc == 0 and "enabled" in out.lower()

    if scenario == "disk_fill":
        rc, _, _ = _run(
            ["docker", "exec", nc, "sh", "-c",
             "test -f /var/www/html/data/chaos_fill.bin"],
            timeout=10,
        )
        return rc == 0

    return False


def run_scenario(scenario: str, action: str) -> tuple:
    """Execute all commands for a (scenario, action). Returns (success, detail)."""
    commands = build_commands(scenario, action)
    details = []
    success = True
    # db_down is a single authoritative docker stop/start, so a non-zero rc there
    # is a genuine failure. The exec-based scenarios are best-effort/idempotent
    # (`|| true`, detached) so a non-zero rc shouldn't flip the whole op — but we
    # still surface stderr for debugging.
    strict = scenario == "db_down"
    for cmd in commands:
        rc, out, err = _run(cmd)
        if rc != 0:
            if strict:
                success = False
            snippet = (err or out).strip()[:200]
            if snippet:
                details.append(f"rc={rc}: {snippet}")
    detail = "; ".join(details) if details else f"{scenario} {action} ok"
    return success, detail


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class _Handler(BaseHTTPRequestHandler):
    server_version = f"DemoAgent/{VERSION}"

    # Silence default noisy logging; route through stderr concisely.
    def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
        sys.stderr.write("[demo-agent] " + (fmt % args) + "\n")

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return is_authorized(self.headers.get("Authorization", ""))

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:  # noqa: BLE001
            return {}

    # -- GET ---------------------------------------------------------------
    def do_GET(self):  # noqa: N802 - stdlib signature
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/health":
            # Health is bearer-gated too (keeps the surface uniformly closed).
            if not self._authorized():
                self._send(401, {"error": "unauthorized"})
                return
            self._send(200, {"ok": True, "version": VERSION, "docker": docker_available()})
            return

        if path == "/status":
            if not self._authorized():
                self._send(401, {"error": "unauthorized"})
                return
            scenarios = {s: {"active": scenario_active(s)} for s in SCENARIOS}
            containers = {
                NEXTCLOUD_CONTAINER: {"running": container_running(NEXTCLOUD_CONTAINER)},
                NEXTCLOUD_DB_CONTAINER: {"running": container_running(NEXTCLOUD_DB_CONTAINER)},
            }
            self._send(200, {"scenarios": scenarios, "containers": containers})
            return

        self._send(404, {"error": "not found"})

    # -- POST --------------------------------------------------------------
    def do_POST(self):  # noqa: N802 - stdlib signature
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if not self._authorized():
            self._send(401, {"error": "unauthorized"})
            return

        parts = [p for p in path.split("/") if p]

        # /chaos/{scenario}/start | /chaos/{scenario}/heal
        if len(parts) == 3 and parts[0] == "chaos" and parts[2] in ("start", "heal"):
            scenario = parts[1]
            action = parts[2]
            if scenario not in SCENARIOS:
                self._send(404, {"error": f"unknown scenario: {scenario}"})
                return
            success, detail = run_scenario(scenario, action)
            self._send(200, {
                "scenario": scenario,
                "action": action,
                "success": success,
                "detail": detail,
            })
            return

        # /remediate/restart
        if parts == ["remediate", "restart"]:
            body = self._read_json()
            container = body.get("container")
            if not isinstance(container, str) or not container.strip():
                self._send(400, {"error": "container required"})
                return
            container = container.strip()
            if container not in _whitelist():
                self._send(403, {
                    "container": container,
                    "action": "restart",
                    "success": False,
                    "error": "container not in whitelist",
                })
                return
            rc, _, err = _run(["docker", "restart", container])
            self._send(200, {
                "container": container,
                "action": "restart",
                "success": rc == 0,
                "detail": (err or "").strip()[:200] if rc != 0 else "restarted",
            })
            return

        self._send(404, {"error": "not found"})


def main() -> int:
    if not DEMO_AGENT_TOKEN:
        sys.stderr.write(
            "[demo-agent] FATAL: DEMO_AGENT_TOKEN is empty. Refusing to start.\n"
        )
        return 2
    server = ThreadingHTTPServer(("0.0.0.0", DEMO_AGENT_PORT), _Handler)
    sys.stderr.write(f"[demo-agent] listening on 0.0.0.0:{DEMO_AGENT_PORT}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
