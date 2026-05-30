import { describe, it, expect } from 'vitest'

import { cn, formatDate, formatRelativeTime } from './utils'

describe('cn', () => {
  it('joins class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })

  it('drops falsy values', () => {
    expect(cn('x', false && 'y', undefined, 'z')).toBe('x z')
  })

  it('merges conflicting tailwind classes (last wins)', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
  })
})

describe('formatDate', () => {
  it('renders the year for a date string', () => {
    expect(formatDate('2025-01-15T10:00:00Z')).toContain('2025')
  })
})

describe('formatRelativeTime', () => {
  const ago = (ms: number) => new Date(Date.now() - ms)

  it('reports "just now" for <1 min', () => {
    expect(formatRelativeTime(ago(30_000))).toBe('just now')
  })

  it('reports minutes', () => {
    expect(formatRelativeTime(ago(5 * 60_000))).toBe('5m ago')
  })

  it('reports hours', () => {
    expect(formatRelativeTime(ago(3 * 3_600_000))).toBe('3h ago')
  })

  it('reports days', () => {
    expect(formatRelativeTime(ago(2 * 86_400_000))).toBe('2d ago')
  })
})
