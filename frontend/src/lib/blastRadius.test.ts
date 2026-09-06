import { describe, it, expect } from 'vitest'
import { computeBlastRadius, directDependents, type BlastEdge } from './blastRadius'

describe('computeBlastRadius', () => {
  it('groups a linear chain by hop and stops at maxDepth', () => {
    const edges: BlastEdge[] = [
      { source: 'a', target: 'b' },
      { source: 'b', target: 'c' },
      { source: 'c', target: 'd' },
    ]
    const { levels, total } = computeBlastRadius(edges, 'a', 2)
    expect(levels).toEqual([['b'], ['c']])
    expect(total).toBe(2)
  })

  it('dedupes a diamond to the shortest hop', () => {
    const edges: BlastEdge[] = [
      { source: 'a', target: 'b' },
      { source: 'a', target: 'c' },
      { source: 'b', target: 'd' },
      { source: 'c', target: 'd' },
    ]
    const { levels, total } = computeBlastRadius(edges, 'a', 3)
    expect(levels).toEqual([['b', 'c'], ['d']])
    expect(total).toBe(3)
  })

  it('terminates on a cycle instead of looping forever', () => {
    const edges: BlastEdge[] = [
      { source: 'a', target: 'b' },
      { source: 'b', target: 'c' },
      { source: 'c', target: 'a' },
    ]
    const { levels, total } = computeBlastRadius(edges, 'a', 10)
    expect(levels).toEqual([['b'], ['c']])
    expect(total).toBe(2)
  })

  it('clamps depth (default 2) so deeper hops are excluded', () => {
    const edges: BlastEdge[] = [
      { source: 'a', target: 'b' },
      { source: 'b', target: 'c' },
      { source: 'c', target: 'd' },
      { source: 'd', target: 'e' },
    ]
    expect(computeBlastRadius(edges, 'a').levels).toEqual([['b'], ['c']])
    expect(computeBlastRadius(edges, 'a', 1).levels).toEqual([['b']])
  })

  it('returns empty for no edges', () => {
    expect(computeBlastRadius([], 'a')).toEqual({ levels: [], total: 0 })
  })

  it('returns empty for an unknown focus', () => {
    const edges: BlastEdge[] = [{ source: 'a', target: 'b' }]
    expect(computeBlastRadius(edges, 'zzz')).toEqual({ levels: [], total: 0 })
  })

  it('returns empty for a leaf focus with nothing downstream', () => {
    const edges: BlastEdge[] = [{ source: 'a', target: 'b' }]
    expect(computeBlastRadius(edges, 'b')).toEqual({ levels: [], total: 0 })
  })
})

describe('directDependents', () => {
  it('lists only the first-hop dependents', () => {
    const edges: BlastEdge[] = [
      { source: 'a', target: 'b' },
      { source: 'a', target: 'c' },
      { source: 'b', target: 'd' },
    ]
    expect(directDependents(edges, 'a')).toEqual(['b', 'c'])
  })

  it('is empty when nothing depends on the focus', () => {
    expect(directDependents([{ source: 'a', target: 'b' }], 'b')).toEqual([])
  })
})
