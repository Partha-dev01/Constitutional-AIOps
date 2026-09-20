import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest'

import {
  APP_VERSION,
  compareVersions,
  entriesSince,
  parseVersion,
  pendingWhatsNew,
  shouldAutoStartTour,
  tourCompleted,
  markTourCompleted,
  whatsNewLastSeen,
  markWhatsNewSeen,
  type ReleaseNote,
} from './whatsNew'

const note = (version: string): ReleaseNote => ({
  version,
  date: 'x',
  title: `v${version}`,
  items: ['a'],
})

/** In-memory localStorage stand-in (node vitest env has no DOM). */
function makeStorage() {
  const map = new Map<string, string>()
  return {
    getItem: (k: string): string | null => (map.has(k) ? (map.get(k) as string) : null),
    setItem: (k: string, v: string): void => {
      map.set(k, String(v))
    },
    removeItem: (k: string): void => {
      map.delete(k)
    },
    clear: (): void => {
      map.clear()
    },
  }
}

describe('parseVersion', () => {
  it('splits dotted parts to numbers, non-numeric to 0', () => {
    expect(parseVersion('1.2.3')).toEqual([1, 2, 3])
    expect(parseVersion('1.x')).toEqual([1, 0])
  })
})

describe('compareVersions', () => {
  it('orders by numeric parts', () => {
    expect(compareVersions('1.0.0', '1.0.1')).toBe(-1)
    expect(compareVersions('1.2.0', '1.1.9')).toBe(1)
    expect(compareVersions('1.0.0', '1.0.0')).toBe(0)
  })

  it('treats missing trailing parts as zero', () => {
    expect(compareVersions('1.0', '1.0.0')).toBe(0)
    expect(compareVersions('1.1', '1.0.9')).toBe(1)
  })
})

describe('entriesSince', () => {
  // Derived from APP_VERSION rather than pinned to a literal, so a release bump
  // does not have to come back and fix this test. The fixture brackets the
  // current version: one entry above it (must be capped out), the current one
  // (must be returned), and one below the lastSeen floor (must be excluded).
  const nextMajor = `${(parseVersion(APP_VERSION)[0] ?? 0) + 1}.0.0`
  const notes = [note(nextMajor), note(APP_VERSION), note('0.5.0')]

  it('returns only notes strictly newer than lastSeen, capped at APP_VERSION', () => {
    expect(entriesSince('0.9.0', notes).map((n) => n.version)).toEqual([APP_VERSION])
  })

  it('is empty when lastSeen is at or past every capped note', () => {
    expect(entriesSince(APP_VERSION, notes)).toEqual([])
  })
})

describe('storage-gated flags', () => {
  beforeEach(() => {
    vi.stubGlobal('window', { localStorage: makeStorage() })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('auto-starts the tour until completed', () => {
    expect(shouldAutoStartTour()).toBe(true)
    expect(tourCompleted()).toBe(false)
    markTourCompleted()
    expect(tourCompleted()).toBe(true)
    expect(shouldAutoStartTour()).toBe(false)
  })

  it('records and reads the last-seen what’s-new version', () => {
    expect(whatsNewLastSeen()).toBeNull()
    markWhatsNewSeen('0.0.1')
    expect(whatsNewLastSeen()).toBe('0.0.1')
  })

  it('shows nothing to a brand-new browser (no lastSeen recorded)', () => {
    expect(pendingWhatsNew()).toEqual([])
  })

  it('surfaces real notes once a prior version has been seen', () => {
    markWhatsNewSeen('0.0.1')
    const pending = pendingWhatsNew()
    expect(pending.length).toBeGreaterThan(0)
    for (const n of pending) {
      expect(compareVersions(n.version, APP_VERSION)).toBeLessThanOrEqual(0)
    }
  })

  it('shows nothing once the current version has been seen', () => {
    markWhatsNewSeen(APP_VERSION)
    expect(pendingWhatsNew()).toEqual([])
  })
})
