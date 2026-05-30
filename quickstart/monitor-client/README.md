# Monitor a container running on a client machine

This answers: *"there is another container on a client — how do I monitor it from
the AWS AIOps stack?"*

## How it works (one agent per host, not per container)

You run **one** [Grafana Alloy](https://grafana.com/docs/alloy/) agent on the
**client machine** (the box whose container you want watched). That single agent:

- discovers **every** Docker container on that host through the Docker socket, and
  ships their stdout/stderr **logs → Loki**;
- collects **host + per-container metrics** (node exporter + cAdvisor) **→ Prometheus**;
- accepts **OTLP traces** on `:4317`/`:4318` and forwards them **→ Tempo**;
- stamps everything with `edge=<label>` so each client stays distinguishable.

So the "other container" is picked up **automatically** — you don't configure
anything per container. Onboard the *host*, and all its containers (current and
future) appear in your AWS Grafana. The AIOps backend reasons over that telemetry
with no change required.

```
  CLIENT machine (anywhere)                    AWS VM (aiops.imaginaerium.in)
 ┌───────────────────────────┐                ┌──────────────────────────────┐
 │ your-app container         │   logs+metrics │  Caddy  /ingest/* (TLS+auth) │
 │ other container  ──────────┼── over TLS ───▶│   ├─ /ingest/loki → Loki      │
 │        ▲                   │   + basic_auth │   ├─ /ingest/prom → Prometheus│
 │   ┌────┴─────┐             │                │   └─ /ingest/otlp → Tempo     │
 │   │  Alloy   │ (this agent)│                │        backend reasons over it │
 │   └──────────┘             │                └──────────────────────────────┘
 └───────────────────────────┘
```

> The agent is **Linux-only** (it bind-mounts `/var/run/docker.sock`, `/`, `/proc`,
> `/sys`). Run it on a Linux Docker host. A Windows laptop can't host it.

## Option A — one command from your laptop (recommended)

From Git Bash, with SSH access to the client:

```bash
cd quickstart/monitor-client
./onboard-client.sh ubuntu@<client-ip> ~/.ssh/<key>.pem <edge-label> tRNeQ9RPkji07Uzb
```

It installs Docker (if missing), copies the agent, writes `.env`, and starts it.
The ingest password is the `edge` machine credential
(`INGEST_BASIC_AUTH_*` in the VM's `.env.production`; `tRNeQ9RPkji07Uzb` for the
current deployment).

## Option B — manually, on the client itself

```bash
# copy the agent to the client, e.g. with scp or git clone, then on the client:
cd monitoring-agent
cp .env.example .env
#   set EDGE_LABEL, INGEST_USER=edge, INGEST_PASS=<the ingest password>;
#   leave the three *_URL as-is (they already point at aiops.imaginaerium.in/ingest)
docker compose up -d
docker compose logs -f alloy        # expect no 401/403 on push
```

(The full agent reference is in [`../../monitoring-agent/README.md`](../../monitoring-agent/README.md).)

## Verify

In Grafana → **https://aiops.imaginaerium.in/grafana/** (log in with the Grafana
admin creds), then:

- **Loki** (Explore): `{edge="<edge-label>"}` → the client's container logs.
- **Prometheus**: `up{edge="<edge-label>"}` → 1 per target; `node_*` / `container_*` series.
- **Tempo**: traces appear only if an app on the client emits OTLP to its `:4318`.

## Stop / remove monitoring

```bash
ssh -i ~/.ssh/<key>.pem ubuntu@<client-ip> 'cd ~/aiops-monitoring && sudo docker compose down'
```

This was validated end-to-end on 2026-05-30 against a throwaway host
(`edge="edge-t3micro-smoke"` showed up in both Loki and Prometheus).
