import { describe, it, expect } from 'vitest'
import { rankRunbook } from './learnedRunbook'

interface Row {
  action_type: string
  target_service?: string
  status: string
}

function row(overrides: Partial<Row> = {}): Row {
  return {
    action_type: 'restart_service',
    target_service: 'nextcloud-db',
    status: 'completed',
    ...overrides,
  }
}

describe('rankRunbook', () => {
  it('ranks by score (successRate * used), highest first', () => {
    // restart_service: 3/3 completed -> rate 1.0, used 3, score 3
    // scale_up: 2/4 completed -> rate 0.5, used 4, score 2
    const entries = rankRunbook([
      row({ action_type: 'restart_service', status: 'completed' }),
      row({ action_type: 'restart_service', status: 'completed' }),
      row({ action_type: 'restart_service', status: 'completed' }),
      row({ action_type: 'scale_up', status: 'completed' }),
      row({ action_type: 'scale_up', status: 'completed' }),
      row({ action_type: 'scale_up', status: 'failed' }),
      row({ action_type: 'scale_up', status: 'failed' }),
    ])
    expect(entries.map((e) => e.key)).toEqual(['restart_service', 'scale_up'])
    expect(entries[0].score).toBe(3)
    expect(entries[1].score).toBe(2)
  })

  it('computes success-rate math from terminal counts', () => {
    const [entry] = rankRunbook([
      row({ action_type: 'rollback', status: 'completed' }),
      row({ action_type: 'rollback', status: 'completed' }),
      row({ action_type: 'rollback', status: 'completed' }),
      row({ action_type: 'rollback', status: 'failed' }),
    ])
    expect(entry.succeeded).toBe(3)
    expect(entry.failed).toBe(1)
    expect(entry.used).toBe(4)
    expect(entry.successRate).toBe(0.75)
    expect(entry.score).toBe(3)
  })

  it('excludes groups with zero terminal outcomes', () => {
    const entries = rankRunbook([
      row({ action_type: 'failover', status: 'pending' }),
      row({ action_type: 'failover', status: 'executing' }),
      row({ action_type: 'restart_service', status: 'completed' }),
    ])
    expect(entries.map((e) => e.key)).toEqual(['restart_service'])
  })

  it('ignores non-terminal statuses within a counted group', () => {
    const [entry] = rankRunbook([
      row({ action_type: 'restart_service', status: 'completed' }),
      row({ action_type: 'restart_service', status: 'failed' }),
      row({ action_type: 'restart_service', status: 'pending' }),
      row({ action_type: 'restart_service', status: 'awaiting_approval' }),
      row({ action_type: 'restart_service', status: 'approved' }),
      row({ action_type: 'restart_service', status: 'executing' }),
      row({ action_type: 'restart_service', status: 'cancelled' }),
      row({ action_type: 'restart_service', status: 'expired' }),
    ])
    // Only the completed + failed pair counts.
    expect(entry.used).toBe(2)
    expect(entry.succeeded).toBe(1)
    expect(entry.failed).toBe(1)
  })

  it('breaks score ties by used desc, then key asc', () => {
    // All three are 100% success (score == used).
    // beta: used 2 -> leads on used. alpha and zeta both used 1 -> key asc.
    const entries = rankRunbook([
      row({ action_type: 'zeta', status: 'completed' }),
      row({ action_type: 'alpha', status: 'completed' }),
      row({ action_type: 'beta', status: 'completed' }),
      row({ action_type: 'beta', status: 'completed' }),
    ])
    expect(entries.map((e) => e.key)).toEqual(['beta', 'alpha', 'zeta'])
  })

  it('groups by target_service when by:"service", skipping rows without one', () => {
    const entries = rankRunbook(
      [
        row({ target_service: 'api', status: 'completed' }),
        row({ target_service: 'api', status: 'completed' }),
        row({ target_service: 'db', status: 'failed' }),
        row({ target_service: undefined, status: 'completed' }),
        row({ target_service: '', status: 'completed' }),
      ],
      { by: 'service' },
    )
    expect(entries.map((e) => e.key)).toEqual(['api', 'db'])
    const api = entries.find((e) => e.key === 'api')
    expect(api?.succeeded).toBe(2)
    expect(api?.used).toBe(2)
    // The undefined and empty-string services were skipped, not grouped.
    expect(entries).toHaveLength(2)
  })

  it('returns an empty list for no history', () => {
    expect(rankRunbook([])).toEqual([])
  })
})
