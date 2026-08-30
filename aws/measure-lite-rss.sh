#!/usr/bin/env bash
# aws/measure-lite-rss.sh — measure steady-state RSS of the LITE stack ON the VM.
#
# The instance-size + cost gate (5c WS3) must follow a MEASUREMENT, not the
# placeholder memory limits in docker/docker-compose.lite.yml. Run this on the
# deployment VM AFTER the lite stack has settled:
#   docker compose -f docker/docker-compose.lite.yml up -d
#   # wait ~2-3 min past healthcheck (let the SPA + backend warm), then:
#   bash aws/measure-lite-rss.sh
#
# Samples `docker stats` and reports per-container + total memory, tracking the
# PEAK total across samples. Tunables: SAMPLES (default 5), INTERVAL sec (10).

set -eu

SAMPLES="${SAMPLES:-5}"
INTERVAL="${INTERVAL:-10}"

echo "Sampling docker stats ${SAMPLES}x every ${INTERVAL}s..."
peak=0
for i in $(seq 1 "$SAMPLES"); do
    echo "--- sample $i/${SAMPLES} ---"
    # {{.MemUsage}} renders as "123.4MiB / 1.5GiB"; awk field $2 is the used part.
    total=$(docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' | awk '
        function tomib(s,   n){ n=s+0;
            if (s ~ /GiB/) return n*1024;
            if (s ~ /MiB/) return n;
            if (s ~ /KiB/) return n/1024;
            if (s ~ /[0-9]B/) return n/1048576;
            return n }
        { mib=tomib($2); sum+=mib;
          printf "  %-24s %8.1f MiB\n", $1, mib > "/dev/stderr" }
        END { printf "%.1f", sum }')
    echo "  sample total: ${total} MiB"
    if awk -v a="$total" -v b="$peak" 'BEGIN{exit !(a>b)}'; then peak="$total"; fi
    [ "$i" -lt "$SAMPLES" ] && sleep "$INTERVAL"
done

peak_gib=$(awk -v p="$peak" 'BEGIN{printf "%.2f", p/1024}')
echo
echo "PEAK TOTAL RSS: ${peak} MiB (${peak_gib} GiB)"
echo "Size the lite instance from this + ~25-40% headroom + OS overhead."
echo "(t3/t4g.small = 2 GiB, .medium = 4 GiB — pick from the measured peak.)"
