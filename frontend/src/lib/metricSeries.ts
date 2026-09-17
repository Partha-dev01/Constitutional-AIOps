/**
 * metricSeries - shared helpers for the client-side metric-insight widgets.
 *
 * Turns the flat telemetry metric points into per-series {timestamp, value}
 * lists (input order preserved), so widgets like the capacity forecast and the
 * correlation scan share one bucketing definition. Pure and side-effect free.
 */
import type { TelemetryMetricPoint } from './api'
import type { SeriesPoint } from './anomalyScan'

/** Series name for a point: service + metric when present, else the label. */
export function seriesKey(p: TelemetryMetricPoint): string {
  if (p.service && p.metric) return `${p.service} · ${p.metric}`
  return p.label
}

/** Bucket raw points into per-series {timestamp, value} lists, order kept. */
export function groupSeries(points: TelemetryMetricPoint[]): Map<string, SeriesPoint[]> {
  const groups = new Map<string, SeriesPoint[]>()
  for (const p of points) {
    const key = seriesKey(p)
    const point: SeriesPoint = { timestamp: p.timestamp, value: p.value }
    const bucket = groups.get(key)
    if (bucket) bucket.push(point)
    else groups.set(key, [point])
  }
  return groups
}
