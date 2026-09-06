import { describe, it, expect } from 'vitest'
import {
  parseViews,
  addView,
  removeView,
  normalizeQuery,
  viewsKey,
  type SavedView,
} from './savedViews'

const VIEWS: SavedView[] = [
  { id: 'a', name: 'Critical open', query: 'status=pending_approval&severity=critical' },
  { id: 'b', name: 'All resolved', query: 'status=resolved' },
]

describe('viewsKey', () => {
  it('namespaces per scope', () => {
    expect(viewsKey('incidents')).toBe('aiops.savedViews.incidents')
  })
})

describe('normalizeQuery', () => {
  it('strips a single leading question mark', () => {
    expect(normalizeQuery('?status=open')).toBe('status=open')
    expect(normalizeQuery('status=open')).toBe('status=open')
    expect(normalizeQuery('')).toBe('')
  })
})

describe('parseViews', () => {
  it('returns [] for null / empty / non-json / non-array', () => {
    expect(parseViews(null)).toEqual([])
    expect(parseViews('')).toEqual([])
    expect(parseViews('not json')).toEqual([])
    expect(parseViews('{"a":1}')).toEqual([])
  })

  it('keeps only well-shaped entries and normalizes their query', () => {
    const raw = JSON.stringify([
      { id: 'x', name: 'X', query: '?status=open' },
      { id: 'bad', name: 'no query' }, // dropped (missing query)
      { id: 5, name: 'wrong id type', query: 'a=1' }, // dropped (id not string)
    ])
    expect(parseViews(raw)).toEqual([{ id: 'x', name: 'X', query: 'status=open' }])
  })
})

describe('addView', () => {
  it('appends a new named view with a generated id', () => {
    const next = addView(VIEWS, 'Warnings', 'severity=warning')
    expect(next).toHaveLength(3)
    const added = next[next.length - 1]
    expect(added.name).toBe('Warnings')
    expect(added.query).toBe('severity=warning')
    expect(added.id).toBeTruthy()
    // originals untouched (pure)
    expect(VIEWS).toHaveLength(2)
  })

  it('overwrites a same-name view case-insensitively rather than duplicating', () => {
    const next = addView(VIEWS, 'critical open', 'status=analyzing')
    expect(next).toHaveLength(2)
    const match = next.filter((v) => v.name.toLowerCase() === 'critical open')
    expect(match).toHaveLength(1)
    expect(match[0].query).toBe('status=analyzing')
  })

  it('trims the name and strips a leading ? from the query', () => {
    const next = addView([], '  Trimmed  ', '?q=x')
    expect(next[0].name).toBe('Trimmed')
    expect(next[0].query).toBe('q=x')
  })

  it('is a no-op for an empty / whitespace name', () => {
    expect(addView(VIEWS, '   ', 'a=1')).toBe(VIEWS)
  })
})

describe('removeView', () => {
  it('drops the matching id and leaves the rest', () => {
    const next = removeView(VIEWS, 'a')
    expect(next.map((v) => v.id)).toEqual(['b'])
  })

  it('is a no-op for an unknown id', () => {
    expect(removeView(VIEWS, 'nope')).toHaveLength(2)
  })
})
