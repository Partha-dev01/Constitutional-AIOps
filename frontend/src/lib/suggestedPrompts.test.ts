import { describe, it, expect } from 'vitest'
import { isSubstantivePrompt, selectPrompts } from './suggestedPrompts'

describe('isSubstantivePrompt', () => {
  it('rejects one-word replies that leak into the recents ring', () => {
    expect(isSubstantivePrompt('yes')).toBe(false)
    expect(isSubstantivePrompt('ok')).toBe(false)
    expect(isSubstantivePrompt('no')).toBe(false)
    expect(isSubstantivePrompt('  yes  ')).toBe(false)
  })

  it('rejects empty and single short words', () => {
    expect(isSubstantivePrompt('')).toBe(false)
    expect(isSubstantivePrompt('help')).toBe(false)
    expect(isSubstantivePrompt('restart')).toBe(false)
  })

  it('accepts real multi-word questions', () => {
    expect(isSubstantivePrompt('Summarize the current health of my system')).toBe(true)
    expect(isSubstantivePrompt('Restart the Caddy service.')).toBe(true)
    expect(isSubstantivePrompt('How is Caddy doing right now?')).toBe(true)
  })
})

describe('selectPrompts', () => {
  it('drops a trivial recent even when passed a raw list', () => {
    const out = selectPrompts(['yes', 'Restart the Caddy service now'], ['Default question here'])
    expect(out).not.toContain('yes')
    expect(out).toContain('Restart the Caddy service now')
  })

  it('keeps recents first, then defaults, de-duped and capped at 6', () => {
    const recent = ['Diagnose the Caddy service now', 'Summarize the current health of my system']
    const defaults = [
      'Summarize the current health of my system', // dupe of a recent, case aside
      'Which services are running right now?',
      'How would you diagnose a spike in errors?',
      'What does the safety gate do before an action?',
      'Show me recent errors across all services',
      'Extra prompt one for the cap',
      'Extra prompt two for the cap',
    ]
    const out = selectPrompts(recent, defaults)
    expect(out[0]).toBe('Diagnose the Caddy service now')
    expect(out.length).toBeLessThanOrEqual(6)
    // de-duped: the shared prompt appears exactly once
    expect(out.filter((p) => p === 'Summarize the current health of my system')).toHaveLength(1)
  })
})
