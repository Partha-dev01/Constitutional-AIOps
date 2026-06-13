# t3 chaos/remediation control agent

A tiny, dependency-free (Python stdlib only) HTTP agent that runs **on the t3
host** next to the `nextcloud` and `nextcloud-db` containers. The AIOps backend
runs in a container on a **different** host (the GPU VM) and cannot reach the
t3's docker daemon directly, so it calls this agent over HTTP to:

- inject chaos scenarios (for the demo), and
- remediate by restarting a remote container.

The agent shells out to the `docker` CLI against the **mounted host docker
socket**, so it can stop/start/exec the Nextcloud containers.

## Deploy (on the t3)

```bash
# 1. Copy this directory to the t3 (e.g. scp -r demo-agent t3:~/demo-agent)
scp -r demo-agent ec2-user@<T3_HOST>:~/demo-agent

# 2. On the t3:
cd ~/demo-agent
cp .env.example .env
#   Edit .env: set DEMO_AGENT_TOKEN to a long random secret.
#   It MUST be IDENTICAL to the backend's DEMO_AGENT_TOKEN env var.

# 3. Build + run
docker compose up -d

# 4. Smoke test (token-gated):
curl -H "Authorization: Bearer $DEMO_AGENT_TOKEN" http://localhost:8889/health
# -> {"ok":true,"version":"1","docker":true}
```

The agent **refuses to start** if `DEMO_AGENT_TOKEN` is empty.

## Security group rule (REQUIRED)

The agent listens on TCP **8889**. Open it in the t3's security group **only**
from the GPU VM's public IP, as a `/32`:

| Type       | Protocol | Port | Source                  |
|------------|----------|------|-------------------------|
| Custom TCP | TCP      | 8889 | `<GPU_VM_PUBLIC_IP>/32` |

Do **not** open 8889 to `0.0.0.0/0`. The bearer token is the only other line of
defense; the SG `/32` restriction is mandatory.

## Token rotation

1. Generate a new secret (e.g. `openssl rand -hex 32`).
2. Update `DEMO_AGENT_TOKEN` in the t3's `demo-agent/.env` **and** the backend's
   env (`DEMO_AGENT_TOKEN`) so they match.
3. `docker compose up -d` on the t3 (recreates the container with the new token)
   and restart/redeploy the backend so it picks up the new value.

Because the token check uses `hmac.compare_digest`, a stale token simply yields
`401 unauthorized` until both sides match again.

## Configuration (`.env`)

| Var                     | Default                 | Meaning                                             |
|-------------------------|-------------------------|-----------------------------------------------------|
| `DEMO_AGENT_TOKEN`      | *(required)*            | Shared bearer token; must equal backend's value.    |
| `DEMO_AGENT_PORT`       | `8889`                  | Published host port (container always listens 8889).|
| `DEMO_AGENT_CONTAINERS` | `nextcloud,nextcloud-db`| Whitelist of containers `/remediate/restart` allows.|
| `NEXTCLOUD_CONTAINER`   | `nextcloud`             | Name of the Nextcloud app container.                |
| `NEXTCLOUD_DB_CONTAINER`| `nextcloud-db`          | Name of the Nextcloud DB container.                 |

## HTTP API

All endpoints are bearer-gated (`Authorization: Bearer <DEMO_AGENT_TOKEN>`);
a missing/wrong token returns `401`.

| Method | Path                       | Body                  | Response                                          |
|--------|----------------------------|-----------------------|---------------------------------------------------|
| GET    | `/health`                  | —                     | `{"ok":true,"version":"1","docker":<bool>}`       |
| GET    | `/status`                  | —                     | `{"scenarios":{...},"containers":{...}}`           |
| POST   | `/chaos/{scenario}/start`  | —                     | `{"scenario","action","success","detail"}`        |
| POST   | `/chaos/{scenario}/heal`   | —                     | `{"scenario","action","success","detail"}`        |
| POST   | `/remediate/restart`       | `{"container":"..."}` | `{"container","action":"restart","success",...}`  |

Unknown scenario → `404`. A container not on the whitelist → `403`.

## Chaos scenarios

All starts/heals are **idempotent** and **self-expiring** where applicable, so a
demo can't wedge the host.

| Scenario         | Start                                                                                                  | Heal                                                | Self-expires |
|------------------|--------------------------------------------------------------------------------------------------------|-----------------------------------------------------|--------------|
| `db_down`        | `docker stop nextcloud-db`                                                                              | `docker start nextcloud-db`                          | No (manual)  |
| `cpu_stress`     | two detached busy loops in `nextcloud`, each `timeout 90`                                               | `pkill -f 'while :'` (best-effort)                   | ~90s         |
| `mem_stress`     | detached memory-growth loop in `nextcloud` (`a=$a$a`), wrapped in `timeout 90`                          | `pkill -f 'a=$a$a'` (best-effort)                    | ~90s         |
| `bad_config_5xx` | `php occ maintenance:mode --on` (as `www-data`) → Nextcloud serves 503/maintenance errors              | `php occ maintenance:mode --off`                    | No (manual)  |
| `disk_fill`      | write a 512MB `chaos_fill.bin` under `…/data` + append 500 error lines to `nextcloud.log`               | `rm -f …/data/chaos_fill.bin` (best-effort)         | No (manual)  |

### `mem_stress` design note

The start command is
`timeout 90 sh -c 'a=; while :; do a=$a$a; done' 2>/dev/null || true`. Doubling a
shell variable grows memory geometrically and creates real memory pressure; the
outer `timeout 90` guarantees the allocation is released after ~90s even if the
shell is OOM-killed first or never trips OOM, so the host can never be wedged by
a stuck demo. The `|| true` keeps the detached exec from reporting a hard failure
when `timeout`/OOM ends it.

> Note: the agent's `mem_stress` / `cpu_stress` **heal** is best-effort `pkill`;
> the scenarios self-expire after ~90s regardless.
