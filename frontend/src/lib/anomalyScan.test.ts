import { describe, it, expect } from 'vitest'
import { scanSeries, detectBurst, type SeriesPoint } from './anomalyScan'

/** Build a series of plain {timestamp, value} points from a list of values. */
function series(values: number[]): SeriesPoint[] {
  return values.map((value, i) => ({ timestamp: `2026-09-06T10:${String(i).padStart(2, '0')}:00Z`, value }))
}

describe('scanSeries', () => {
  it('flags nothing on a quiet, varying series', () => {
    const points = series([10, 11, 10, 11, 10, 11, 10, 11, 10, 11])
    expect(scanSeries(points)).toEqual([])
  })

  it('flags a single high outlier with direction high', () => {
    const points = series([10, 10, 10, 10, 10, 10, 10, 10, 10, 100])
    const found = scanSeries(points)
    expect(found).toHaveLength(1)
    expect(found[0].value).toBe(100)
    expect(found[0].direction).toBe('high')
    expect(found[0].z).toBeCloseTo(3.0, 5)
  })

  it('flags a low outlier with direction low', () => {
    const points = series([100, 100, 100, 100, 100, 100, 100, 100, 100, 10])
    const found = scanSeries(points)
    expect(found).toHaveLength(1)
    expect(found[0].value).toBe(10)
    expect(found[0].direction).toBe('low')
    expect(found[0].z).toBeCloseTo(-3.0, 5)
  })

  it('returns [] when the series is flat (stddev == 0)', () => {
    expect(scanSeries(series([5, 5, 5, 5, 5, 5, 5, 5, 5, 5]))).toEqual([])
  })

  it('returns [] below minSamples even with an obvious outlier', () => {
    expect(scanSeries(series([10, 10, 10, 100]))).toEqual([])
  })

  it('respects the threshold option', () => {
    const points = series([10, 10, 10, 10, 10, 10, 10, 10, 10, 100])
    // Outlier z is 3.0: caught at 2.5, missed at 3.5.
    expect(scanSeries(points, { threshold: 2.5 })).toHaveLength(1)
    expect(scanSeries(points, { threshold: 3.5 })).toEqual([])
  })
})

describe('detectBurst', () => {
  it('is true when the latest count exceeds factor times the preceding mean', () => {
    expect(detectBurst([1, 1, 1, 1, 10])).toBe(true)
  })

  it('is false when the latest count stays near the baseline', () => {
    expect(detectBurst([5, 5, 5, 5, 6])).toBe(false)
  })

  it('is false below minSamples', () => {
    expect(detectBurst([10, 100])).toBe(false)
  })

  it('is false when the baseline is all zero', () => {
    expect(detectBurst([0, 0, 0, 5])).toBe(false)
  })

  it('honors a custom factor', () => {
    expect(detectBurst([2, 2, 2, 2, 5], { factor: 2 })).toBe(true)
    expect(detectBurst([2, 2, 2, 2, 5], { factor: 3 })).toBe(false)
  })
})
