import { describe, it, expect } from 'vitest'
import {
  deriveToolSteps,
  enrichToolStepsWithResponse,
  KNOWN_SERVICES,
} from './useToolSteps'

// ---------------------------------------------------------------------------
// deriveToolSteps
// ---------------------------------------------------------------------------

describe('deriveToolSteps', () => {
  it('always ends with a reasoning step', () => {
    const steps = deriveToolSteps('hello')
    expect(steps[steps.length - 1].id).toBe('reasoning')
  })

  it('adds telemetry step when a known service is mentioned', () => {
    const steps = deriveToolSteps('check nextcloud status')
    const ids = steps.map((s) => s.id)
    expect(ids).toContain('telemetry')
  })

  it('adds similar step when similar keywords are present', () => {
    const steps = deriveToolSteps('show similar incidents')
    const ids = steps.map((s) => s.id)
    expect(ids).toContain('similar')
  })

  it('adds dependencies step only when both service and dependency keyword present', () => {
    // Neither alone is enough.
    expect(deriveToolSteps('nextcloud status').map((s) => s.id)).not.toContain('dependencies')
    expect(deriveToolSteps('show dependencies').map((s) => s.id)).not.toContain('dependencies')
    // Both together triggers it.
    expect(deriveToolSteps('nextcloud dependencies').map((s) => s.id)).toContain('dependencies')
  })

  it('adds logs step only when both service and log keyword present', () => {
    expect(deriveToolSteps('nextcloud').map((s) => s.id)).not.toContain('logs')
    expect(deriveToolSteps('analyze logs').map((s) => s.id)).not.toContain('logs')
    expect(deriveToolSteps('nextcloud error logs').map((s) => s.id)).toContain('logs')
  })

  it('detects every known service', () => {
    for (const svc of KNOWN_SERVICES) {
      const steps = deriveToolSteps(`check ${svc} status`)
      const telemetry = steps.find((s) => s.id === 'telemetry')
      expect(telemetry, `expected telemetry step for service "${svc}"`).toBeDefined()
      expect(telemetry?.detail.service).toBe(svc)
    }
  })

  it('all steps start as pending', () => {
    const steps = deriveToolSteps('show similar nextcloud incidents with errors and dependencies')
    for (const step of steps) {
      expect(step.status).toBe('pending')
    }
  })

  it('all steps have a detail with null result', () => {
    const steps = deriveToolSteps('check nextcloud logs')
    for (const step of steps) {
      expect(step.detail).toBeDefined()
      expect(step.detail.result).toBeNull()
      expect(typeof step.detail.store).toBe('string')
      expect(typeof step.detail.query).toBe('string')
    }
  })
})

// ---------------------------------------------------------------------------
// enrichToolStepsWithResponse
// ---------------------------------------------------------------------------

describe('enrichToolStepsWithResponse', () => {
  const BASE_DATA = {
    confidence: 0.87,
    related_incidents: ['INC-2024-001', 'INC-2024-042'],
    suggested_actions: ['Restart nextcloud', 'Check loki'],
    metadata: { model_used: 'qwen3-14b', tokens_used: 412 },
  }

  function doneSteps(message: string) {
    return deriveToolSteps(message).map((s) => ({ ...s, status: 'done' as const }))
  }

  it('sets result on the similar step from related_incidents', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const similar = enriched.find((s) => s.id === 'similar')
    expect(similar).toBeDefined()
    expect(similar!.detail.result).not.toBeNull()
    const parsed = JSON.parse(similar!.detail.result!)
    expect(parsed.similar_incidents).toEqual(['INC-2024-001', 'INC-2024-042'])
  })

  it('reports "no similar incidents" when related_incidents is empty', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const enriched = enrichToolStepsWithResponse(steps, { ...BASE_DATA, related_incidents: [] })
    const similar = enriched.find((s) => s.id === 'similar')
    expect(similar!.detail.result).toContain('No similar incidents')
  })

  it('reports "no similar incidents" when related_incidents is null', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const enriched = enrichToolStepsWithResponse(steps, { ...BASE_DATA, related_incidents: null })
    const similar = enriched.find((s) => s.id === 'similar')
    expect(similar!.detail.result).toContain('No similar incidents')
  })

  it('sets result on the reasoning step with model and confidence', () => {
    const steps = doneSteps('nextcloud status')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const reasoning = enriched.find((s) => s.id === 'reasoning')
    expect(reasoning!.detail.result).not.toBeNull()
    const parsed = JSON.parse(reasoning!.detail.result!)
    expect(parsed.model).toBe('qwen3-14b')
    expect(parsed.confidence).toBe(0.87)
    expect(parsed.tokens_used).toBe(412)
  })

  it('reasoning result includes suggested_actions', () => {
    const steps = doneSteps('nextcloud status')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const reasoning = enriched.find((s) => s.id === 'reasoning')
    const parsed = JSON.parse(reasoning!.detail.result!)
    expect(parsed.suggested_actions).toEqual(['Restart nextcloud', 'Check loki'])
  })

  it('sets result on the telemetry step', () => {
    const steps = doneSteps('nextcloud cpu high')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const telemetry = enriched.find((s) => s.id === 'telemetry')
    expect(telemetry!.detail.result).not.toBeNull()
    const parsed = JSON.parse(telemetry!.detail.result!)
    expect(parsed.service).toBe('nextcloud')
    expect(parsed.confidence_after_reasoning).toBe(0.87)
  })

  it('sets result on the dependencies step', () => {
    const steps = doneSteps('nextcloud dependencies upstream')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const deps = enriched.find((s) => s.id === 'dependencies')
    expect(deps!.detail.result).not.toBeNull()
    const parsed = JSON.parse(deps!.detail.result!)
    expect(parsed.service_queried).toBe('nextcloud')
  })

  it('sets result on the logs step', () => {
    const steps = doneSteps('nextcloud error logs pattern')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const logs = enriched.find((s) => s.id === 'logs')
    expect(logs!.detail.result).not.toBeNull()
    const parsed = JSON.parse(logs!.detail.result!)
    expect(parsed.service).toBe('nextcloud')
  })

  it('handles missing metadata gracefully', () => {
    const steps = doneSteps('nextcloud status')
    const enriched = enrichToolStepsWithResponse(steps, { ...BASE_DATA, metadata: null })
    const reasoning = enriched.find((s) => s.id === 'reasoning')
    const parsed = JSON.parse(reasoning!.detail.result!)
    expect(parsed.model).toBe('qwen3-14b') // fallback
    expect(parsed.tokens_used).toBeNull()
  })

  it('does not mutate original steps', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const original = JSON.stringify(steps)
    enrichToolStepsWithResponse(steps, BASE_DATA)
    expect(JSON.stringify(steps)).toBe(original)
  })
})
