import { describe, it, expect } from 'vitest'

import { forecastSeries, isUtilizationSeries } from './capacityForecast'
import type { SeriesPoint } from './anomalyScan'

/** Points one minute apart from the epoch, given the values. */
const pts = (values: number[], stepMs = 60_000): SeriesPoint[] =>
  values.map((v, i) => ({ timestamp: new Date(i * stepMs).toISOString(), value: v }))

describe('isUtilizationSeries', () => {
  it('accepts a 0..100 series and rejects out-of-range or empty', () => {
    expect(isUtilizationSeries(pts([0, 50, 100]))).toBe(true)
    expect(isUtilizationSeries(pts([50, 120]))).toBe(false)
    expect(isUtilizationSeries([])).toBe(false)
  })
})

describe('forecastSeries', () => {
  it('projects a rising series to the threshold', () => {
    const f = forecastSeries(pts([50, 52, 54, 56, 58, 60, 62, 64, 66, 68]))
    expect(f).not.toBeNull()
    expect(f?.direction).toBe('rising')
    expect(f?.slopePerSample).toBeCloseTo(2, 5)
    // current 68 -> 90 at +2/sample = ceil(22/2) = 11 samples.
    expect(f?.samplesToThreshold).toBe(11)
    // 60s spacing -> 11 * 60_000 ms.
    expect(f?.msToThreshold).toBe(11 * 60_000)
  })

  it('returns a flat direction with no projection for a flat series', () => {
    const f = forecastSeries(pts([50, 50, 50, 50, 50, 50, 50, 50, 50, 50]))
    expect(f?.direction).toBe('flat')
    expect(f?.samplesToThreshold).toBeNull()
  })

  it('does not project a falling series', () => {
    const f = forecastSeries(pts([68, 66, 64, 62, 60, 58, 56, 54, 52, 50]))
    expect(f?.direction).toBe('falling')
    expect(f?.samplesToThreshold).toBeNull()
  })

  it('does not project once the series is already at the threshold', () => {
    const f = forecastSeries(pts([82, 84, 86, 88, 90, 92, 94, 96, 98, 100]))
    expect(f?.direction).toBe('rising')
    expect(f?.samplesToThreshold).toBeNull()
  })

  it('returns null for a too-short series', () => {
    expect(forecastSeries(pts([50, 60, 70]))).toBeNull()
  })
})
