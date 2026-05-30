# EBS Persistence + systemd Lifecycle (Gate 3)

How the Constitutional AIOps production stack keeps its state across instance
stop/start, and how the three systemd units bring it up in order. This is the
on-VM operations runbook; nothing here spends AWS money on its own.

> **Scope:** production only. Local dev (`docker-compose.local.yml`) still uses
> named Docker volumes and is unchanged.

---

## 1. Why bind-mounts instead of named volumes

The instance is **stopped when idle** (CloudWatch alarm + `aiops-idle-check.timer`)
to save GPU cost. Docker *named* volumes live under `/var/lib/docker/volumes` on
the **root** EBS volume; they do survive a stop/start, but they are invisible,
hard to snapshot selectively, and easy to lose on an AMI rebuild.

Instead, every stateful service binds to the dedicated **data EBS volume**
(`vol-0123456789abcdef0`) mounted at **`/mnt/data`**. State is then plainly
visible, independently snapshot-able, and decoupled from the root volume.

`docker/docker-compose.production.yml` no longer declares any top-level
`volumes:` — each service maps a `/mnt/data/...` host path directly.

### Data layout

```
/mnt/data/
├── neo4j/
│   ├── data/            -> /data   in aiops-neo4j     (graph-episodic memory)
│   │   └── backups/     -> neo4j-backup.sh dump target
│   └── logs/            -> /logs   in aiops-neo4j
├── loki/                -> /loki   in aiops-loki      (logs, 30-day retention)
├── prometheus/          -> /prometheus in aiops-prometheus (metrics, 30-day)
├── tempo/               -> /tmp/tempo  in aiops-tempo (traces, blocks + WAL)
├── grafana/             -> /var/lib/grafana in aiops-grafana (dashboards, state)
└── caddy/
    ├── data/            -> /data   in aiops-caddy     (Let's Encrypt certs!)
    └── config/          -> /config in aiops-caddy
```

> The `caddy/data` directory holds the issued Let's Encrypt certificates. Keeping
> it on EBS means a restart does **not** re-request certs and risk hitting LE rate
> limits. (Caddy mounts are wired up in Gate 6.)

---

## 2. One-time data-volume prep

A fresh bind-mount directory is owned by `root`, but the LGTM/Neo4j containers
run as non-root and need to write. `aws/init-data-dirs.sh` creates each directory
and `chown`s it to the uid the owning image runs as:

| Directory | Container | Runs as (uid:gid) |
|-----------|-----------|-------------------|
| `neo4j/data`, `neo4j/logs` | neo4j:5.15-community | `7474:7474` |
| `loki` | grafana/loki:2.9.3 | `10001:10001` |
| `tempo` | grafana/tempo:2.3.1 | `10001:10001` |
| `prometheus` | prom/prometheus:v2.48.0 | `65534:65534` (nobody) |
| `grafana` | grafana/grafana:10.2.3 | `472:472` |
| `caddy/data`, `caddy/config` | caddy:2-alpine | `0:0` (root) |

It is **idempotent** and runs automatically as `ExecStartPre` of
`aiops-app.service`. To run it by hand:

```bash
sudo AIOPS_DATA_ROOT=/mnt/data /opt/aiops/aws/init-data-dirs.sh
```

### Mounting the data volume (first boot only)

```bash
# Identify the data volume (the non-root one), then — only if it has no fs yet:
lsblk -f
sudo mkfs.ext4 /dev/nvme1n1          # SKIP if it already has data!
sudo mkdir -p /mnt/data
echo '/dev/nvme1n1 /mnt/data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
sudo mount -a
```

---

## 3. systemd units (replace ad-hoc `docker compose up` + crontab)

Repo is checked out at **`/opt/aiops`** with a git-ignored **`.env.production`**
alongside `docker-compose.yml`.

| Unit | Brings up | Notes |
|------|-----------|-------|
| `aiops-vllm.service` | `qwen3-4b`, `qwen3-14b` | GPU tier; stop/start independently for idle savings |
| `aiops-app.service` | neo4j, loki, promtail, prometheus, tempo, grafana, otel-collector, backend, frontend | `After=aiops-vllm`; `ExecStartPre=init-data-dirs.sh`; excludes the `nextcloud` demo |
| `aiops-caddy.service` | caddy | `After=aiops-app`; only public 80/443 (Gate 6) |
| `aiops-idle-check.service` + `.timer` | runs `aws/idle-check.sh` every 10 min | replaces the crontab entry |

Each `*.service` is a `Type=oneshot` + `RemainAfterExit=yes` wrapper around
`docker compose ... up -d <subset>`, so `systemctl start/stop` maps cleanly onto
the right containers and `systemctl status` reflects the tier.

### Install

```bash
sudo cp /opt/aiops/aws/systemd/aiops-*.service \
        /opt/aiops/aws/systemd/aiops-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aiops-vllm aiops-app aiops-caddy aiops-idle-check.timer
```

After an instance **start**, the units come up in order automatically
(`aiops-vllm` → `aiops-app` → `aiops-caddy`); no manual `docker compose` needed.

### Operate

```bash
systemctl status aiops-app
sudo systemctl restart aiops-caddy        # reload proxy without touching the GPU
sudo systemctl stop aiops-vllm            # free the GPU but keep app+data serving
journalctl -u aiops-app -f
systemctl list-timers aiops-idle-check.timer
```

---

## 4. Backups

1. **Primary — EBS snapshot** of the data volume: `aws/snapshot-vm.sh`
   (point-in-time, covers every store at once). Run before risky changes.
2. **Neo4j logical dump** — `docker exec aiops-neo4j /scripts/backup.sh`
   (`docker/configs/neo4j-backup.sh`) writes timestamped dumps to
   `/mnt/data/neo4j/data/backups/`, retaining the latest 7. Note: Neo4j Community
   requires the DB stopped for `neo4j-admin database dump`, so prefer the snapshot
   path for live backups and use this for maintenance-window exports.

## 5. Restore after a rebuild

1. Create the instance, attach the **existing** data volume at `/dev/sdf`
   (Terraform adopts it via `import` — it is never recreated).
2. `sudo mount -a` (fstab entry above) → `/mnt/data` reappears with all state.
3. `sudo systemctl start aiops-vllm aiops-app aiops-caddy`.
4. Caddy reuses the certs in `/mnt/data/caddy/data`; Grafana/Neo4j/Loki/Prom/Tempo
   reattach to their existing directories.

---

## 6. Verification (no AWS spend)

`docker compose config` validates the merged production file locally:

```bash
docker compose -f docker-compose.yml -f docker/docker-compose.production.yml \
  --env-file .env.production config >/dev/null && echo "compose OK"
```

`systemd-analyze verify aws/systemd/aiops-*.service` checks unit syntax (on a
Linux box). The real bring-up + container health checks happen in Gate 8.
