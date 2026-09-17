/**
 * metrics1h - a shared fetch of the last hour of telemetry metrics for the
 * dashboard insight widgets.
 *
 * Several widgets read the same GET /telemetry/metrics?range=1h on mount: the
 * anomaly scan, the capacity forecast and the metric correlation. On the lite
 * tier that scrape is serialized server-side (Docker-socket fallback, no
 * Prometheus), so three independent calls stack up and the last widget can sit
 * on a spinner for ~18s. Collapsing them into one in-flight request (plus a
 * short result window for mounts that land a beat apart) keeps every widget on
 * a single call. A failed fetch is never cached, so the next mount retries.
 */
import { api, type TelemetryMetricPoint } from './api'

/** How long a resolved result is reused before a fresh fetch is made. */
const SHARE_WINDOW_MS = 5_000

let inflight: Promise<TelemetryMetricPoint[]> | null = null
let cached: { at: number; points: TelemetryMetricPoint[] } | null = null

/**
 * Return the last hour of metric points, sharing one request across concurrent
 * callers. Resolves to an empty array when the instance has no metrics.
 */
export async function fetchMetrics1h(): Promise<TelemetryMetricPoint[]> {
  if (cached && Date.now() - cached.at < SHARE_WINDOW_MS) return cached.points
  if (inflight) return inflight
  inflight = api.telemetry
    .metrics({ range: '1h' })
    .then((res) => {
      const points = res?.metrics ?? []
      cached = { at: Date.now(), points }
      return points
    })
    .finally(() => {
      inflight = null
    })
  return inflight
}

/** Clear the shared state (test helper; not used in the app). */
export function __resetMetrics1h(): void {
  inflight = null
  cached = null
}
