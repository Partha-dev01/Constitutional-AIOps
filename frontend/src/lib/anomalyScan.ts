/**
 * Pure helpers for the Dashboard "Anomaly scan" widget (Track 2, the free/no-LLM
 * half of the Anomaly-to-Hypothesis Feed). A client-side z-score pass over a
 * telemetry metric series that flags points sitting far from the series mean.
 * Deterministic and side-effect-free at module scope, no LLM involved, so the
 * maths stays unit testable and the widget is only a view over existing data.
 */

export interface SeriesPoint {
  timestamp: string
  value: number
}

export interface Anomaly {
  timestamp: string
  value: number
  z: number
  direction: 'high' | 'low'
}

export interface ScanOptions {
  /** |z| at or above this flags a point. Default 2.5. */
  threshold?: number
  /** Minimum points before a scan runs at all. Default 8. */
  minSamples?: number
}

/**
 * Flag points at least `threshold` population standard deviations from the
 * series mean. Returns [] when the series is too short (< minSamples) or flat
 * (stddev == 0), so a quiet or tiny series never yields phantom anomalies.
 * z = (value - mean) / stddev; direction is 'high' when z > 0 else 'low'.
 * Results keep input order.
 */
export function scanSeries(points: SeriesPoint[], opts: ScanOptions = {}): Anomaly[] {
  const threshold = opts.threshold ?? 2.5
  const minSamples = opts.minSamples ?? 8
  const n = points.length
  if (n < minSamples) return []
  const mean = points.reduce((sum, p) => sum + p.value, 0) / n
  const variance = points.reduce((sum, p) => sum + (p.value - mean) ** 2, 0) / n
  const stddev = Math.sqrt(variance)
  if (stddev <= 0) return []
  const out: Anomaly[] = []
  for (const p of points) {
    const z = (p.value - mean) / stddev
    if (Math.abs(z) >= threshold) {
      out.push({ timestamp: p.timestamp, value: p.value, z, direction: z > 0 ? 'high' : 'low' })
    }
  }
  return out
}

export interface BurstOptions {
  /** Latest count must exceed this multiple of the preceding mean. Default 3. */
  factor?: number
  /** Minimum counts (latest included) before a burst can be called. Default 4. */
  minSamples?: number
}

/**
 * True when the latest count spikes past `factor` times the mean of the counts
 * before it. Needs at least minSamples counts and a positive baseline, so a
 * cold start or an all-zero window never reads as a burst.
 */
export function detectBurst(counts: number[], opts: BurstOptions = {}): boolean {
  const factor = opts.factor ?? 3
  const minSamples = opts.minSamples ?? 4
  const n = counts.length
  if (n < minSamples) return false
  const latest = counts[n - 1]
  const preceding = counts.slice(0, n - 1)
  const mean = preceding.reduce((sum, c) => sum + c, 0) / preceding.length
  if (mean <= 0) return false
  return latest > factor * mean
}
