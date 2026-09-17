import { describe, it, expect } from 'vitest'

import { pearson, correlateSeries } from './metricCorrelation'
import type { SeriesPoint } from './anomalyScan'

const sp = (values: number[]): SeriesPoint[] =>
  values.map((v, i) => ({ timestamp: String(i), value: v }))

describe('pearson', () => {
  it('is +1 for a perfect positive relationship', () => {
    expect(pearson([1, 2, 3, 4], [2, 4, 6, 8])).toBeCloseTo(1, 5)
  })

  it('is -1 for a perfect inverse relationship', () => {
    expect(pearson([1, 2, 3, 4], [8, 6, 4, 2])).toBeCloseTo(-1, 5)
  })

  it('is null when either side is flat (zero variance)', () => {
    expect(pearson([1, 1, 1], [1, 2, 3])).toBeNull()
  })

  it('is null with fewer than two aligned points', () => {
    expect(pearson([1], [1])).toBeNull()
  })
})

describe('correlateSeries', () => {
  const A = sp([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
  const B = sp([2, 4, 6, 8, 10, 12, 14, 16, 18, 20]) // r = +1 with A
  const C = sp([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]) // r = -1 with A
  const FLAT = sp([5, 5, 5, 5, 5, 5, 5, 5, 5, 5]) // no variance -> skipped

  it('returns strongly correlated pairs, strongest first, and skips flat series', () => {
    const map = new Map([
      ['a', A],
      ['b', B],
      ['c', C],
      ['flat', FLAT],
    ])
    const pairs = correlateSeries(map, { threshold: 0.9, max: 10 })
    // a-b (+1), a-c (-1), b-c (-1). flat pairs are dropped (pearson null).
    expect(pairs).toHaveLength(3)
    for (const p of pairs) expect(Math.abs(p.r)).toBeCloseTo(1, 5)
    expect(pairs.some((p) => p.a === 'flat' || p.b === 'flat')).toBe(false)
  })

  it('skips pairs with fewer than minSamples aligned points', () => {
    const short = sp([1, 2, 3])
    const map = new Map([
      ['a', A],
      ['short', short],
    ])
    expect(correlateSeries(map, { threshold: 0.5 })).toEqual([])
  })

  it('caps the result to max', () => {
    const map = new Map([
      ['a', A],
      ['b', B],
      ['c', C],
    ])
    expect(correlateSeries(map, { threshold: 0.9, max: 1 })).toHaveLength(1)
  })
})
