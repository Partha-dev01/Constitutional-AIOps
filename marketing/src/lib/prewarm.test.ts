import { describe, it, expect } from 'vitest'
import {
  hasGenuineIntent,
  isLikelyRealBrowser,
  MIN_DWELL_MS,
  CTA_MIN_DWELL_MS,
  type IntentState,
} from './prewarm'

const base: IntentState = {
  visible: true,
  prerendering: false,
  wasDiscarded: false,
  dwellMs: 0,
  pointerMoved: false,
  scrolledPastViewport: false,
  touched: false,
  keyed: false,
  ctaHover: false,
}

function s(partial: Partial<IntentState>): IntentState {
  return { ...base, ...partial }
}

describe('hasGenuineIntent', () => {
  it('does not fire on load (dwell with no interaction)', () => {
    expect(hasGenuineIntent(s({ dwellMs: MIN_DWELL_MS + 500 }))).toBe(false)
  })

  it('does not fire on interaction with too little dwell', () => {
    expect(hasGenuineIntent(s({ dwellMs: 500, pointerMoved: true }))).toBe(false)
  })

  it('fires on dwell + any real interaction', () => {
    const d = MIN_DWELL_MS + 100
    expect(hasGenuineIntent(s({ dwellMs: d, pointerMoved: true }))).toBe(true)
    expect(hasGenuineIntent(s({ dwellMs: d, scrolledPastViewport: true }))).toBe(true)
    expect(hasGenuineIntent(s({ dwellMs: d, touched: true }))).toBe(true)
    expect(hasGenuineIntent(s({ dwellMs: d, keyed: true }))).toBe(true)
  })

  it('fires on a CTA hover after the shorter CTA dwell, without other engagement', () => {
    expect(hasGenuineIntent(s({ dwellMs: CTA_MIN_DWELL_MS, ctaHover: true }))).toBe(true)
  })

  it('does not fire on a CTA hover that happens too early (likely a load-time reflow)', () => {
    expect(hasGenuineIntent(s({ dwellMs: 200, ctaHover: true }))).toBe(false)
  })

  it('never fires in a hidden tab, even when otherwise engaged', () => {
    expect(hasGenuineIntent(s({ visible: false, dwellMs: MIN_DWELL_MS + 100, pointerMoved: true }))).toBe(false)
  })

  it('never fires while prerendering or after a discard', () => {
    const engaged = { dwellMs: MIN_DWELL_MS + 100, pointerMoved: true }
    expect(hasGenuineIntent(s({ ...engaged, prerendering: true }))).toBe(false)
    expect(hasGenuineIntent(s({ ...engaged, wasDiscarded: true }))).toBe(false)
  })
})

describe('isLikelyRealBrowser', () => {
  it('rejects a webdriver-controlled browser', () => {
    expect(isLikelyRealBrowser({ webdriver: true })).toBe(false)
  })

  it('accepts a normal browser', () => {
    expect(isLikelyRealBrowser({ webdriver: false })).toBe(true)
    expect(isLikelyRealBrowser({})).toBe(true)
  })

  it('rejects a missing navigator', () => {
    expect(isLikelyRealBrowser(undefined)).toBe(false)
  })
})
