#!/usr/bin/env bash
# aws/init-data-dirs.sh — idempotent prep of the EBS data volume so the
# observability containers (which run as NON-root) can write their bind-mounts.
#
# Each LGTM/Neo4j image runs its main process as a fixed uid:gid; a fresh
# bind-mount is owned by root and the container then fails to write. This script
# creates every data directory under /mnt/data and chowns it to the right uid.
#
# Run automatically as ExecStartPre of aiops-app.service; also safe to run by hand:
#     sudo AIOPS_DATA_ROOT=/mnt/data aws/init-data-dirs.sh
#
# See aws/EBS_PERSISTENCE.md for the uid table and the rationale.
set -euo pipefail

DATA_ROOT="${AIOPS_DATA_ROOT:-/mnt/data}"

# Directory (relative to DATA_ROOT) -> uid:gid the owning container runs as.
#   neo4j   : 7474   (neo4j:5.15-community)
#   loki    : 10001  (grafana/loki:2.9.3)
#   tempo   : 10001  (grafana/tempo:2.3.1)
#   prom    : 65534  (prom/prometheus:v2.48.0 — "nobody")
#   grafana : 472    (grafana/grafana:10.2.3)
#   caddy   : 0      (caddy:2-alpine runs as root)
declare -A OWN=(
  ["neo4j/data"]="7474:7474"
  ["neo4j/logs"]="7474:7474"
  ["neo4j/data/backups"]="7474:7474"
  ["loki"]="10001:10001"
  ["tempo"]="10001:10001"
  ["prometheus"]="65534:65534"
  ["grafana"]="472:472"
  ["caddy/data"]="0:0"
  ["caddy/config"]="0:0"
)

for sub in "${!OWN[@]}"; do
  dir="${DATA_ROOT}/${sub}"
  mkdir -p "$dir"
  chown -R "${OWN[$sub]}" "$dir"
done

echo "[init-data-dirs] prepared ${DATA_ROOT} for the AIOps stack"
