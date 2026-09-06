import { describe, it, expect } from 'vitest'
import { anomalyExplainPayload, reasonLabel, type AnomalyItem } from './insights'

const item = (over: Partial<AnomalyItem> = {}): AnomalyItem => ({
  series: 'api · cpu',
  value: 91.5,
  z: 3.14159,
  direction: 'high',
  ...over,
})

describe('anomalyExplainPayload', () => {
  it('reports the full count but caps the top list', () => {
    const items = Array.from({ length: 12 }, (_, i) => item({ series: `s${i}` }))
    const payload = anomalyExplainPayload(items, 5)
    expect(payload.count).toBe(12)
    expect(payload.top).toHaveLength(5)
    expect(payload.top[0].series).toBe('s0')
  })

  it('rounds z to two places and keeps direction', () => {
    const payload = anomalyExplainPayload([item({ z: 3.14159, direction: 'low' })])
    expect(payload.top[0].z).toBe(3.14)
    expect(payload.top[0].direction).toBe('low')
  })

  it('is empty-safe', () => {
    expect(anomalyExplainPayload([])).toEqual({ count: 0, top: [] })
  })

  it('a non-positive max yields no top items but keeps the count', () => {
    const payload = anomalyExplainPayload([item(), item()], 0)
    expect(payload.count).toBe(2)
    expect(payload.top).toHaveLength(0)
  })
})

describe('reasonLabel', () => {
  it('maps each known reason to actionable text', () => {
    expect(reasonLabel('ai_widgets_disabled')).toMatch(/Settings/i)
    expect(reasonLabel('budget_reached')).toMatch(/budget/i)
    expect(reasonLabel('no_endpoint')).toMatch(/endpoint/i)
    expect(reasonLabel('empty')).toMatch(/again/i)
    expect(reasonLabel('error')).toMatch(/reach/i)
  })

  it('falls back for unknown / null reasons', () => {
    expect(reasonLabel(null)).toMatch(/unavailable/i)
    expect(reasonLabel('something-new')).toMatch(/unavailable/i)
  })
})
