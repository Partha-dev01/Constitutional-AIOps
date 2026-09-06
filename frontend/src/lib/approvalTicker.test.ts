import { describe, it, expect } from 'vitest'
import { confidenceBand, tierState, formatAge, toTickerItems } from './approvalTicker'
import type { Action } from './api'

function action(overrides: Partial<Action> = {}): Action {
  return {
    id: 'a1',
    action_type: 'restart_service',
    description: 'Restart nextcloud-db',
    target_service: 'nextcloud-db',
    confidence: 0.8,
    status: 'awaiting_approval',
    requires_approval: true,
    created_at: '2026-09-06T10:00:00Z',
    updated_at: '2026-09-06T10:00:00Z',
    ...overrides,
  } as Action
}

describe('confidenceBand', () => {
  it('maps to the constitutional authorization bands', () => {
    expect(confidenceBand(0.95)).toBe('high')
    expect(confidenceBand(0.9)).toBe('high')
    expect(confidenceBand(0.8)).toBe('medium')
    expect(confidenceBand(0.7)).toBe('medium')
    expect(confidenceBand(0.5)).toBe('low')
  })
})

describe('tierState', () => {
  it('reads passed flags from the validation', () => {
    const a = action({
      validation: {
        passed: false,
        authorization_level: 'approval_required',
        confidence: 0.8,
        tier1_passed: true,
        tier2_passed: false,
        tier3_passed: true,
        violations: [],
        warnings: [],
        explanation: '',
      },
    })
    expect(tierState(a)).toEqual({ tier1: true, tier2: false, tier3: true })
  })

  it('defaults to passed when there is no validation yet', () => {
    expect(tierState(action({ validation: undefined }))).toEqual({
      tier1: true,
      tier2: true,
      tier3: true,
    })
  })
})

describe('formatAge', () => {
  const base = new Date('2026-09-06T10:00:00Z').getTime()
  it('formats seconds, minutes, hours and days', () => {
    expect(formatAge('2026-09-06T10:00:00Z', base + 30_000)).toBe('30s')
    expect(formatAge('2026-09-06T10:00:00Z', base + 5 * 60_000)).toBe('5m')
    expect(formatAge('2026-09-06T10:00:00Z', base + 65 * 60_000)).toBe('1h 5m')
    expect(formatAge('2026-09-06T10:00:00Z', base + 2 * 3600_000)).toBe('2h')
    expect(formatAge('2026-09-06T10:00:00Z', base + 2 * 86_400_000)).toBe('2d')
  })

  it('never goes negative and handles a bad date', () => {
    expect(formatAge('2026-09-06T10:00:00Z', base - 5000)).toBe('0s')
    expect(formatAge('not-a-date')).toBe('')
  })
})

describe('toTickerItems', () => {
  it('keeps only pending-approval actions, oldest first, with band and tiers', () => {
    const items = toTickerItems([
      action({ id: 'new', created_at: '2026-09-06T10:05:00Z' }),
      action({ id: 'old', created_at: '2026-09-06T10:00:00Z' }),
      action({ id: 'done', requires_approval: false, status: 'completed' }),
    ])
    expect(items.map((i) => i.id)).toEqual(['old', 'new'])
    expect(items[0].band).toBe('medium')
    expect(items[0].tiers).toEqual({ tier1: true, tier2: true, tier3: true })
  })
})
