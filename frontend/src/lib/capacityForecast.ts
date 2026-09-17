/**
 * Pure helpers for the "Capacity forecast" widget (Track 2, no-LLM half).
 *
 * A naive least-squares linear fit over a utilization series (values in 0..100),
 * projected forward to estimate when it would reach a threshold. Deterministic
 * and side-effect free so the maths unit-tests without a DOM or an LLM. The
 * widget labels the projection as a linear extrapolation, never a guarantee.
 */
import type { SeriesPoint } from './anomalyScan'

export interface Forecast {
  /** Least-squares slope per sample (units of the metric per point). */
  slopePerSample: number
  /** Latest observed value. */
  current: number
  /** The threshold the projection targets. */
  threshold: number
  /** Samples until the trend reaches `threshold`, or null when not rising toward it. */
  samplesToThreshold: number | null
  /** Estimated milliseconds to threshold from the sample spacing, or null. */
  msToThreshold: number | null
  direction: 'rising' | 'falling' | 'flat'
}

export interface ForecastOptions {
  /** Utilization threshold to project toward. Default 90. */
  threshold?: number
  /** Minimum points before a fit runs at all. Default 8. */
  minSamples?: number
  /** Slope magnitude at or below which the trend reads flat. Default 1e-6. */
  epsilon?: number
}

/**
 * A utilization series: non-empty and every value within 0..100. Used to gate
 * the forecast so it only runs where a "reach 90%" projection is meaningful,
 * not on arbitrary counters where a linear target would be nonsense.
 */
export function isUtilizationSeries(points: SeriesPoint[]): boolean {
  return points.length > 0 && points.every((p) => p.value >= 0 && p.value <= 100)
}

/**
 * Fit a line to the series and project time-to-threshold. Returns null when the
 * series is too short or has no spread on x. Only a rising series that has not
 * already crossed the threshold gets a projection; everything else reports a
 * direction with null projections.
 */
export function forecastSeries(points: SeriesPoint[], opts: ForecastOptions = {}): Forecast | null {
  const threshold = opts.threshold ?? 90
  const minSamples = opts.minSamples ?? 8
  const epsilon = opts.epsilon ?? 1e-6
  const n = points.length
  if (n < minSamples) return null

  const xbar = (n - 1) / 2
  const ybar = points.reduce((sum, p) => sum + p.value, 0) / n
  let num = 0
  let den = 0
  for (let i = 0; i < n; i++) {
    const dx = i - xbar
    num += dx * (points[i].value - ybar)
    den += dx * dx
  }
  if (den <= 0) return null

  const slope = num / den
  const current = points[n - 1].value
  const direction: Forecast['direction'] =
    slope > epsilon ? 'rising' : slope < -epsilon ? 'falling' : 'flat'

  let samplesToThreshold: number | null = null
  let msToThreshold: number | null = null
  if (direction === 'rising' && current < threshold) {
    samplesToThreshold = Math.ceil((threshold - current) / slope)
    const first = Date.parse(points[0].timestamp)
    const last = Date.parse(points[n - 1].timestamp)
    if (Number.isFinite(first) && Number.isFinite(last) && last > first) {
      const avgInterval = (last - first) / (n - 1)
      msToThreshold = samplesToThreshold * avgInterval
    }
  }

  return { slopePerSample: slope, current, threshold, samplesToThreshold, msToThreshold, direction }
}
