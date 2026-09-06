import { describe, it, expect } from 'vitest'
import {
  matchText,
  scoreCommand,
  rankCommands,
  type PaletteCommand,
} from './commandPalette'

const CMDS: PaletteCommand[] = [
  { id: 'dash', title: 'Dashboard', group: 'Overview', href: '/' },
  { id: 'inc', title: 'Incidents', group: 'Operate', href: '/incidents' },
  {
    id: 'audit',
    title: 'Audit Log',
    group: 'Admin',
    keywords: ['history', 'events'],
    href: '/audit',
  },
  { id: 'metrics', title: 'Metrics', group: 'Observe', href: '/metrics' },
]

describe('matchText', () => {
  it('empty query scores 0 (matches everything)', () => {
    expect(matchText('Dashboard', '')).toBe(0)
  })

  it('ranks exact > prefix > substring > subsequence', () => {
    const exact = matchText('metrics', 'metrics')!
    const prefix = matchText('metrics', 'met')!
    const substr = matchText('telemetry', 'lem')! // 'lem' at index 2
    const subseq = matchText('aXbXc', 'abc')! // scattered, not contiguous
    expect(exact).toBeGreaterThan(prefix)
    expect(prefix).toBeGreaterThan(substr)
    expect(substr).toBeGreaterThan(subseq)
  })

  it('is case-insensitive', () => {
    expect(matchText('Incidents', 'INC')).toBe(matchText('incidents', 'inc'))
  })

  it('returns null when not a subsequence (order matters)', () => {
    expect(matchText('Metrics', 'xyz')).toBeNull()
    expect(matchText('abc', 'acb')).toBeNull()
  })

  it('penalizes gaps within a subsequence match', () => {
    const tight = matchText('aXbc', 'abc')! // one gap
    const loose = matchText('aXXbXXc', 'abc')! // more gaps
    expect(tight).toBeGreaterThan(loose)
    expect(tight).toBeLessThan(500) // still below the substring tier
  })
})

describe('scoreCommand', () => {
  it('empty query scores 0', () => {
    expect(scoreCommand(CMDS[0], '')).toBe(0)
  })

  it('a title match outranks a keyword-only match', () => {
    const byTitle = scoreCommand({ id: 't', title: 'Logs', href: '/t' }, 'log')!
    const byKeyword = scoreCommand(
      { id: 'k', title: 'Audit', keywords: ['logs'], href: '/k' },
      'log',
    )!
    expect(byTitle).toBeGreaterThan(byKeyword)
  })

  it('returns null when neither title nor keywords match', () => {
    expect(scoreCommand(CMDS[3], 'zzzz')).toBeNull()
  })
})

describe('rankCommands', () => {
  it('empty query returns all in declared order', () => {
    expect(rankCommands(CMDS, '').map((c) => c.id)).toEqual([
      'dash',
      'inc',
      'audit',
      'metrics',
    ])
  })

  it('returns only matches, best first', () => {
    expect(rankCommands(CMDS, 'inc').map((c) => c.id)).toEqual(['inc'])
  })

  it('finds a command by keyword when the title does not match', () => {
    expect(rankCommands(CMDS, 'history').map((c) => c.id)).toEqual(['audit'])
  })

  it('returns [] when nothing matches', () => {
    expect(rankCommands(CMDS, 'zzzzz')).toEqual([])
  })

  it('is stable for equal scores (declared order wins ties)', () => {
    const items: PaletteCommand[] = [
      { id: 'a', title: 'Alpha', href: '/a' },
      { id: 'b', title: 'Alpine', href: '/b' },
    ]
    expect(rankCommands(items, 'alp').map((c) => c.id)).toEqual(['a', 'b'])
  })
})
