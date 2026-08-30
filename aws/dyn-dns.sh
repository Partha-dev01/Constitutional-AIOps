#!/usr/bin/env bash
# aws/dyn-dns.sh — guest-side dynamic-DNS updater, runs ON the deployment VM.
#
# The lite tier has NO Elastic IP (that is the whole $2-3/mo, no-fixed-IP
# design), so the box gets a NEW public IPv4 on every wake. This oneshot UPSERTs
# the box's own A record to the current public IP so the CloudFront/Lambda front
# door can 302 a visitor straight to aiops-node.<domain> right after it wakes the
# box. Without it, the A record seeded at first launch goes stale on the next
# wake and the front door 302s to a dead address.
#
# Perms: the instance role (aiops-lite-role) is scoped to exactly
# route53:ChangeResourceRecordSets on HOSTED_ZONE_ID — nothing wider.
# IP source: IMDSv2 (token-authenticated) public-ipv4.
#
# Install ON the VM via aws/systemd/aiops-dyn-dns.service (runs once per boot,
# after the network is online). Safe to run by hand any time — the UPSERT is
# idempotent (a no-op when the record already matches the current IP).
#
# Tunables (env, all optional):
#   HOSTED_ZONE_ID   Route53 zone id          (REQUIRED — set for your deployment)
#   RECORD_NAME      FQDN A record to update  (REQUIRED — e.g. app-node.example.com)
#   RECORD_TTL       A record TTL, seconds    (default 60 — fast wake propagation)
#   AWS_DEFAULT_REGION                        (default us-east-1)
#   AIOPS_DYNDNS_LOG log file                 (default /var/log/aiops-dyn-dns.log)

set -eu

# Deployment-specific — override via env (see aiops-dyn-dns.service EnvironmentFile).
HOSTED_ZONE_ID="${HOSTED_ZONE_ID:-YOUR_ROUTE53_ZONE_ID}"
RECORD_NAME="${RECORD_NAME:-app-node.example.com}"
RECORD_TTL="${RECORD_TTL:-60}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
LOG="${AIOPS_DYNDNS_LOG:-/var/log/aiops-dyn-dns.log}"

log() { echo "$(date -Iseconds) $*" >> "$LOG" 2>/dev/null || true; echo "$*"; }

# --- IMDSv2: session token, then the current public IPv4.
TOKEN=$(curl -s --max-time 5 -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 300" || true)
if [ -z "${TOKEN:-}" ]; then
    log "FATAL: no IMDSv2 token — is this an EC2 instance?"
    exit 1
fi
PUBLIC_IP=$(curl -s --max-time 5 -H "X-aws-ec2-metadata-token: $TOKEN" \
    "http://169.254.169.254/latest/meta-data/public-ipv4" || true)
if ! printf '%s' "${PUBLIC_IP:-}" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    log "FATAL: no valid public IPv4 from IMDS (got '${PUBLIC_IP:-}') — not updating"
    exit 1
fi

log "public IPv4 = $PUBLIC_IP; UPSERT $RECORD_NAME A -> $PUBLIC_IP (zone $HOSTED_ZONE_ID ttl $RECORD_TTL)"

CHANGE_BATCH=$(cat <<JSON
{"Comment":"aiops dyn-dns on-boot update","Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"$RECORD_NAME","Type":"A","TTL":$RECORD_TTL,"ResourceRecords":[{"Value":"$PUBLIC_IP"}]}}]}
JSON
)

if OUT=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "$HOSTED_ZONE_ID" \
        --change-batch "$CHANGE_BATCH" \
        --region "$REGION" \
        --query "ChangeInfo.[Id,Status]" --output text 2>&1); then
    log "OK: route53 change submitted: $OUT"
else
    log "FATAL: route53 change failed: $OUT"
    exit 1
fi
