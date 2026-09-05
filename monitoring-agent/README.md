# Edge Monitoring Agent (Grafana Alloy)

A single-container [Grafana Alloy](https://grafana.com/docs/alloy/) agent that runs
on **any remote host** and ships that host's Docker telemetry into the Constitutional
AIOps LGTM stack on AWS. The AIOps backend then reasons over it through its existing
read-only `TelemetryCollector` — **no backend change is required to onboard a host.**

```
 remote host                                     AWS VM (aiops.example.com)
┌──────────────────────────┐                    ┌───────────────────────────────┐
│ your Docker containers    │  logs/metrics/     │  Caddy  /ingest/* (basic_auth)│
│        │ stdout, /metrics │  traces over TLS   │    ├─ /ingest/loki -> Loki     │
│        ▼                  │  + basic_auth      │    ├─ /ingest/prom -> Prometheus│
│   ┌──────────┐  ───────────────────────────▶  │    └─ /ingest/otlp -> Tempo     │
│   │  Alloy   │            │                    │           │                    │
│   └──────────┘            │                    │     backend TelemetryCollector │
└──────────────────────────┘                    └───────────────────────────────┘
```

## What it collects

| Signal | Source | Destination |
|--------|--------|-------------|
| Logs | every Docker container (`discovery.docker` + `loki.source.docker`) | Loki |
| Host metrics | node/`unix` exporter (CPU, mem, disk, net) | Prometheus |
| Container metrics | in-process cAdvisor (`docker_only`) | Prometheus |
| Traces | local OTLP receiver on `:4317`/`:4318` | Tempo |

Every stream is stamped with an `edge=<EDGE_LABEL>` label so multiple monitored
hosts stay distinguishable in Grafana and to the backend.

## Prerequisites

- Docker + Docker Compose on the remote host.
- Network egress to `https://aiops.example.com` (443).
- The **ingest credential**: ask the AIOps admin for the plaintext `INGEST_PASS`
  (the server stores only its bcrypt hash, see below).

## Setup

```bash
cp .env.example .env
# edit .env: set EDGE_LABEL, INGEST_USER/INGEST_PASS, and (only if your domain
# differs) the three *_URL endpoints.

# optional but recommended — check the config parses + is well-formatted first
# (-t / --test exits non-zero on a parse error or formatting drift):
docker run --rm -v "$PWD/config.alloy:/c.alloy" grafana/alloy:v1.5.1 fmt -t /c.alloy

docker compose up -d
docker compose logs -f alloy        # watch for successful pushes
```

Inspect the agent locally via its UI (loopback only):
`ssh -L 12345:127.0.0.1:12345 <remote-host>` then open `http://localhost:12345`.

## Server side (already wired by Gate 6 + Gate 7)

The AWS `.env.production` carries the matching machine credential as a **bcrypt
hash** (never the plaintext). Generate it on the server from the SAME plaintext the
agent uses:

```bash
docker run --rm caddy:2.8-alpine caddy hash-password --plaintext 'the-INGEST_PASS'
# put the result in INGEST_BASIC_AUTH_HASH, escaping every $ as $$
```

Caddy then exposes the path-routed, auth-gated ingestion endpoints and Prometheus
runs with `--web.enable-remote-write-receiver` so it accepts the remote_write push.

## Verify end to end

1. `docker compose logs alloy` shows no 401/403 on push (credential OK).
2. In Grafana (`https://aiops.example.com/grafana/`):
   - **Loki**: `{edge="<EDGE_LABEL>"}` returns this host's container logs.
   - **Prometheus**: `up{edge="<EDGE_LABEL>"}` and `node_*` / `container_*` series.
   - **Tempo**: traces appear if your app emits OTLP to this host's `:4318`.
3. The AIOps backend annotates incidents sourced from the remote telemetry.

## Hardening notes / caveats

- **Rate limiting:** the stock `caddy:2.8-alpine` image has no `rate_limit`
  directive (it lives in a plugin). The `/ingest/*` routes instead cap request body
  size (10 MB) and require basic_auth over TLS. To add true rate-limiting, build a
  custom Caddy with the `caddy-ratelimit` module and add a `rate_limit` block.
- **cAdvisor:** the in-process exporter needs the host mounts in `docker-compose.yml`
  (`/`, `/proc`, `/sys`, `/dev/disk`). On some kernels/distros it can be noisy — if
  so, comment the `prometheus.exporter.cadvisor` block in `config.alloy` and remove
  it from `prometheus.scrape.edge.targets`; logs and host metrics keep flowing.
- **Credential rotation:** change `INGEST_PASS` here and the bcrypt
  `INGEST_BASIC_AUTH_HASH` on the server together, then restart both.
- The Alloy version tag is pinned for reproducibility; bump it deliberately.
