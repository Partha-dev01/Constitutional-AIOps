/**
 * Pure helpers for the "Metric correlation" widget (Track 2, no-LLM half).
 *
 * Pairwise Pearson correlation over the metric series in a window, surfacing
 * series that move together as a hypothesis for a shared cause or dependency.
 * Deterministic and side-effect free so the maths unit-tests without a DOM. The
 * widget is explicit that correlation is not causation.
 */
import type { SeriesPoint } from './anomalyScan'

export interface CorrelationPair {
  a: string
  b: string
  /** Pearson correlation coefficient over the overlapping tail, -1..1. */
  r: number
  /** Number of aligned samples the coefficient was computed over. */
  n: number
}

/**
 * Pearson correlation over the leading min(len) values of two arrays. Returns
 * null when there are fewer than two aligned points or either side is flat
 * (zero variance), so a constant series never yields a spurious coefficient.
 */
export function pearson(x: number[], y: number[]): number | null {
  const n = Math.min(x.length, y.length)
  if (n < 2) return null
  let sx = 0
  let sy = 0
  for (let i = 0; i < n; i++) {
    sx += x[i]
    sy += y[i]
  }
  const mx = sx / n
  const my = sy / n
  let num = 0
  let dx2 = 0
  let dy2 = 0
  for (let i = 0; i < n; i++) {
    const dx = x[i] - mx
    const dy = y[i] - my
    num += dx * dy
    dx2 += dx * dx
    dy2 += dy * dy
  }
  if (dx2 <= 0 || dy2 <= 0) return null
  return num / Math.sqrt(dx2 * dy2)
}

export interface CorrelationOptions {
  /** |r| at or above this counts as correlated. Default 0.8. */
  threshold?: number
  /** Minimum aligned samples before a pair is considered. Default 8. */
  minSamples?: number
  /** Cap on returned pairs (strongest first). Default 6. */
  max?: number
}

/**
 * Correlate every pair of series over their overlapping tail. Returns pairs
 * whose |r| meets the threshold, strongest first, capped to `max`. Series are
 * aligned by taking the last min(lenA, lenB) values of each.
 */
export function correlateSeries(
  series: Map<string, SeriesPoint[]>,
  opts: CorrelationOptions = {},
): CorrelationPair[] {
  const threshold = opts.threshold ?? 0.8
  const minSamples = opts.minSamples ?? 8
  const max = opts.max ?? 6
  const names = [...series.keys()]
  const pairs: CorrelationPair[] = []

  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      const A = series.get(names[i])
      const B = series.get(names[j])
      if (!A || !B) continue
      const n = Math.min(A.length, B.length)
      if (n < minSamples) continue
      const xa = A.slice(A.length - n).map((p) => p.value)
      const xb = B.slice(B.length - n).map((p) => p.value)
      const r = pearson(xa, xb)
      if (r === null) continue
      if (Math.abs(r) >= threshold) pairs.push({ a: names[i], b: names[j], r, n })
    }
  }

  pairs.sort((p, q) => Math.abs(q.r) - Math.abs(p.r))
  return pairs.slice(0, Math.max(0, max))
}
