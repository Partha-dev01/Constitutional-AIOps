#!/usr/bin/env bash
# docker/configs/neo4j-backup.sh — mounted read-only at /scripts/backup.sh inside
# the aiops-neo4j container. Neo4j Community has no hot online backup, so this takes
# an offline-consistent dump with neo4j-admin. Trigger it from the host on a schedule:
#
#     docker exec aiops-neo4j /scripts/backup.sh
#
# Dumps land in /data/backups, which is part of the /data bind-mount
# (/mnt/data/neo4j/data on the EBS volume), so they persist across instance restarts.
#
# NOTE: `neo4j-admin database dump` requires the target database to be stopped on
# Neo4j Community. For an always-on single-node box, prefer the EBS snapshot path
# (aws/snapshot-vm.sh) as the primary backup and use this script for ad-hoc exports
# during a maintenance window.
set -euo pipefail

STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="/data/backups"
DB="${NEO4J_BACKUP_DB:-neo4j}"
RETAIN="${NEO4J_BACKUP_RETAIN:-7}"

mkdir -p "$DEST"

echo "[neo4j-backup] dumping database '${DB}' -> ${DEST}/${DB}-${STAMP}.dump"
neo4j-admin database dump "$DB" --to-path="$DEST" --overwrite-destination=true

# neo4j-admin writes <db>.dump; stamp it so successive backups do not clobber.
if [ -f "${DEST}/${DB}.dump" ]; then
    mv "${DEST}/${DB}.dump" "${DEST}/${DB}-${STAMP}.dump"
fi

# Retain only the most recent N dumps.
ls -1t "${DEST}/${DB}"-*.dump 2>/dev/null | tail -n "+$((RETAIN + 1))" | xargs -r rm -f
echo "[neo4j-backup] done; retained $(ls -1 "${DEST}/${DB}"-*.dump 2>/dev/null | wc -l) dump(s) in ${DEST}"
