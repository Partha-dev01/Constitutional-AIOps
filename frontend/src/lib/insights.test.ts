import { describe, it, expect } from 'vitest'
import {
  anomalyExplainPayload,
  blastRadiusExplainPayload,
  incidentNarrativeExplainPayload,
  learnedRunbookExplainPayload,
  graphCopilotExplainPayload,
  reasonLabel,
  type AnomalyItem,
  type GraphCopilotInput,
} from './insights'

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

describe('blastRadiusExplainPayload', () => {
  it('numbers hops from 1 and keeps the total', () => {
    const payload = blastRadiusExplainPayload({
      service: 'api',
      total: 3,
      levels: [['web', 'worker'], ['db']],
    })
    expect(payload.service).toBe('api')
    expect(payload.total).toBe(3)
    expect(payload.hops).toEqual([
      { hop: 1, services: ['web', 'worker'] },
      { hop: 2, services: ['db'] },
    ])
  })

  it('caps each hop and drops emptied hops', () => {
    const wide = Array.from({ length: 20 }, (_, i) => `s${i}`)
    const payload = blastRadiusExplainPayload(
      { service: 'api', total: 20, levels: [wide, []] },
      5,
    )
    expect(payload.hops).toHaveLength(1)
    expect(payload.hops[0].services).toHaveLength(5)
  })

  it('is empty-safe', () => {
    expect(
      blastRadiusExplainPayload({ service: 'api', total: 0, levels: [] }),
    ).toEqual({ service: 'api', total: 0, hops: [] })
  })
})

describe('incidentNarrativeExplainPayload', () => {
  const group = (id: string, stages: string[]) => ({
    incidentId: id,
    stages: stages.map((stage) => ({ stage })),
  })

  it('sends ordered stage keys per incident', () => {
    const payload = incidentNarrativeExplainPayload([
      group('inc-1', ['detected', 'root cause', 'resolved']),
    ])
    expect(payload).toEqual({
      incidents: [{ id: 'inc-1', stages: ['detected', 'root cause', 'resolved'] }],
    })
  })

  it('caps incidents and stages', () => {
    const groups = Array.from({ length: 5 }, (_, i) =>
      group(`inc-${i}`, Array.from({ length: 20 }, (_, j) => `s${j}`)),
    )
    const payload = incidentNarrativeExplainPayload(groups, 2, 3)
    expect(payload.incidents).toHaveLength(2)
    expect(payload.incidents[0].stages).toHaveLength(3)
  })

  it('is empty-safe', () => {
    expect(incidentNarrativeExplainPayload([])).toEqual({ incidents: [] })
  })
})

describe('learnedRunbookExplainPayload', () => {
  const row = (over = {}) => ({
    key: 'restart_service',
    successRate: 0.923,
    succeeded: 12,
    used: 13,
    ...over,
  })

  it('rounds the rate and carries the counts', () => {
    const payload = learnedRunbookExplainPayload([row()])
    expect(payload.runbook[0]).toEqual({
      action: 'restart_service',
      successRate: 0.92,
      succeeded: 12,
      used: 13,
    })
  })

  it('caps to the strongest max rows', () => {
    const rows = Array.from({ length: 10 }, (_, i) => row({ key: `a${i}` }))
    expect(learnedRunbookExplainPayload(rows, 6).runbook).toHaveLength(6)
  })

  it('is empty-safe', () => {
    expect(learnedRunbookExplainPayload([])).toEqual({ runbook: [] })
  })
})

describe('graphCopilotExplainPayload', () => {
  const base = (): GraphCopilotInput => ({
    stats: {
      episodes: 12, rootCauses: 4, actions: 5, services: 6,
      entities: 8, edges: 30, critical: 2, resolved: 9,
    },
    rootCauses: [
      { name: 'oom', frequency: 3, successRate: 0.5 },
      { name: 'disk-full', frequency: 9, successRate: 0.888 },
    ],
    actions: [
      { name: 'restart', usedCount: 2, successRate: 0.75 },
      { name: 'scale-up', usedCount: 8, successRate: 0.9 },
    ],
    services: [
      { name: 'api', incidentCount: 1, status: 'healthy' },
      { name: 'db', incidentCount: 7, status: 'critical' },
    ],
    episodes: [
      { title: 'old', category: 'perf', severity: 'warning', status: 'resolved' },
      { title: 'live', category: 'perf', severity: 'critical', status: 'analyzing' },
    ],
  })

  it('sorts root causes / actions / services by their strength', () => {
    const out = graphCopilotExplainPayload(base())
    expect(out.topRootCauses[0].name).toBe('disk-full') // higher frequency first
    expect(out.topActions[0].action).toBe('scale-up') // higher usedCount first
    expect(out.topServices[0].service).toBe('db') // more incidents first
    expect(out.stats.episodes).toBe(12)
  })

  it('rounds success rates to two places', () => {
    const out = graphCopilotExplainPayload(base())
    expect(out.topRootCauses[0].successRate).toBe(0.89)
  })

  it('orders incidents unresolved-first then by severity', () => {
    const out = graphCopilotExplainPayload(base())
    expect(out.recentIncidents[0].title).toBe('live') // unresolved beats resolved
    expect(out.recentIncidents[0].status).toBe('analyzing')
  })

  it('caps each list', () => {
    const many = base()
    many.rootCauses = Array.from({ length: 10 }, (_, i) => ({ name: `r${i}`, frequency: i, successRate: 0.5 }))
    many.episodes = Array.from({ length: 10 }, (_, i) => ({ title: `e${i}`, category: 'c', severity: 'warning', status: 'resolved' }))
    const out = graphCopilotExplainPayload(many, 6, 5)
    expect(out.topRootCauses).toHaveLength(6)
    expect(out.recentIncidents).toHaveLength(5)
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
