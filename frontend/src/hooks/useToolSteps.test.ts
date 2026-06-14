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
  // Mirrors the real backend ChatResponse.metadata shape: per-tool structured
  // results live under metadata.tools, keyed by step id.
  const TELEMETRY = {
    service: 'nextcloud',
    log_count: 1280,
    error_count: 12,
    metrics: [
      { name: 'cpu_usage', value: 0.74 },
      { name: 'mem_usage', value: 0.61 },
    ],
    sample_logs: ['ERROR db connection refused', 'WARN slow query 1.2s'],
  }
  const SIMILAR = {
    count: 2,
    incidents: [
      { id: 'INC-2024-001', summary: 'nextcloud db outage', score: 0.91 },
      { id: 'INC-2024-042', summary: 'nextcloud disk full', score: null },
    ],
  }
  const DEPENDENCIES = {
    upstream: ['postgres', 'redis'],
    downstream: ['frontend'],
  }
  const LOGS = {
    total_logs: 4000,
    error_count: 12,
    warning_count: 30,
    top_errors: [{ pattern: 'connection refused', count: 9 }],
  }

  const BASE_DATA = {
    confidence: 0.87,
    related_incidents: ['INC-2024-001', 'INC-2024-042'],
    suggested_actions: ['Restart nextcloud', 'Check loki'],
    metadata: {
      model_used: 'qwen3-14b',
      tokens_used: 412,
      tools: {
        telemetry: TELEMETRY,
        similar: SIMILAR,
        dependencies: DEPENDENCIES,
        logs: LOGS,
      },
    },
  }

  function doneSteps(message: string) {
    return deriveToolSteps(message).map((s) => ({ ...s, status: 'done' as const }))
  }

  it('renders REAL telemetry data from metadata.tools.telemetry', () => {
    const steps = doneSteps('nextcloud cpu high')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const telemetry = enriched.find((s) => s.id === 'telemetry')
    expect(telemetry!.detail.result).not.toBeNull()
    const parsed = JSON.parse(telemetry!.detail.result!)
    expect(parsed.service).toBe('nextcloud')
    expect(parsed.log_count).toBe(1280)
    expect(parsed.error_count).toBe(12)
    expect(parsed.metrics).toEqual(TELEMETRY.metrics)
    expect(parsed.sample_logs).toEqual(TELEMETRY.sample_logs)
  })

  it('renders REAL similar-incident data from metadata.tools.similar', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const similar = enriched.find((s) => s.id === 'similar')
    expect(similar).toBeDefined()
    expect(similar!.detail.result).not.toBeNull()
    const parsed = JSON.parse(similar!.detail.result!)
    expect(parsed.count).toBe(2)
    expect(parsed.incidents).toEqual(SIMILAR.incidents)
  })

  it('renders REAL dependency data from metadata.tools.dependencies', () => {
    const steps = doneSteps('nextcloud dependencies upstream')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const deps = enriched.find((s) => s.id === 'dependencies')
    expect(deps!.detail.result).not.toBeNull()
    const parsed = JSON.parse(deps!.detail.result!)
    expect(parsed.upstream).toEqual(['postgres', 'redis'])
    expect(parsed.downstream).toEqual(['frontend'])
  })

  it('renders REAL log analysis from metadata.tools.logs', () => {
    const steps = doneSteps('nextcloud error logs pattern')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const logs = enriched.find((s) => s.id === 'logs')
    expect(logs!.detail.result).not.toBeNull()
    const parsed = JSON.parse(logs!.detail.result!)
    expect(parsed.total_logs).toBe(4000)
    expect(parsed.top_errors).toEqual(LOGS.top_errors)
  })

  it('shows a truthful "No X returned" line when a tool did not run', () => {
    // Steps are derived, but metadata.tools is empty -> no fabricated prose.
    const steps = doneSteps('show similar nextcloud incidents with errors and dependencies')
    const enriched = enrichToolStepsWithResponse(steps, {
      ...BASE_DATA,
      metadata: { model_used: 'qwen3-14b', tokens_used: 0, tools: {} },
    })
    expect(enriched.find((s) => s.id === 'telemetry')!.detail.result).toBe('No telemetry returned.')
    expect(enriched.find((s) => s.id === 'similar')!.detail.result).toBe(
      'No similar incidents returned.',
    )
    expect(enriched.find((s) => s.id === 'dependencies')!.detail.result).toBe(
      'No dependencies returned.',
    )
    expect(enriched.find((s) => s.id === 'logs')!.detail.result).toBe('No log analysis returned.')
  })

  it('never fabricates a "note" string', () => {
    const steps = doneSteps('show similar nextcloud incidents with errors and dependencies')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    for (const step of enriched) {
      // No canned note prose anywhere in the rendered results.
      expect(step.detail.result).not.toContain('injected into the reasoning')
    }
  })

  it('reasoning result carries the relevant outcome (confidence) but NOT model/token meta', () => {
    const steps = doneSteps('nextcloud status')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const reasoning = enriched.find((s) => s.id === 'reasoning')!
    expect(reasoning.detail.result).not.toBeNull()
    const parsed = JSON.parse(reasoning.detail.result!)
    expect(parsed.confidence).toBe(0.87)
    // The model/tokens meta blob is GONE from the result — it lives on its own field.
    expect(parsed.model).toBeUndefined()
    expect(parsed.tokens_used).toBeUndefined()
    expect(reasoning.detail.model).toBe('qwen3-14b · 412 tokens')
  })

  it('reasoning query is proper JSON carrying the request + synthesised inputs', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const enriched = enrichToolStepsWithResponse(steps, {
      ...BASE_DATA,
      userMessage: 'show similar nextcloud incidents',
    })
    const reasoning = enriched.find((s) => s.id === 'reasoning')!
    const q = JSON.parse(reasoning.detail.query) // throws if not valid JSON
    expect(q.request).toBe('show similar nextcloud incidents')
    expect(Array.isArray(q.synthesised_from)).toBe(true)
  })

  it('low-evidence reasoning drops the Result entirely (never a placeholder answer)', () => {
    const steps = doneSteps('hello there')
    const enriched = enrichToolStepsWithResponse(steps, {
      confidence: null,
      suggested_actions: [],
      related_incidents: [],
      userMessage: 'hello there',
      metadata: { model_used: 'qwen3-14b', tokens_used: 23, tools: {} },
    })
    const reasoning = enriched.find((s) => s.id === 'reasoning')!
    // No confidence / actions / incidents -> no Result row at all (null), and
    // never the old hardcoded "Generated the response shown below." placeholder.
    expect(reasoning.detail.result).toBeNull()
    // The model/tokens line still renders on its own row.
    expect(reasoning.detail.model).toBe('qwen3-14b · 23 tokens')
    const q = JSON.parse(reasoning.detail.query)
    expect(q.synthesised_from[0]).toContain('model knowledge')
  })

  it('never emits the hardcoded "Generated the response shown below." placeholder', () => {
    const steps = doneSteps('nextcloud status')
    // Even with a real confidence present, the Result must not fabricate an answer line.
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const reasoning = enriched.find((s) => s.id === 'reasoning')!
    expect(reasoning.detail.result).not.toContain('Generated the response shown below')
    const parsed = JSON.parse(reasoning.detail.result!)
    expect(parsed.answer).toBeUndefined()
    expect(parsed.confidence).toBe(0.87)
  })

  it('attaches a concise at-a-glance summary per enriched step', () => {
    const steps = doneSteps('show similar nextcloud incidents with errors and dependencies')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const summaryOf = (id: string) => enriched.find((s) => s.id === id)!.detail.summary
    expect(summaryOf('telemetry')).toBe('1280 logs · 12 errors · 2 metrics')
    expect(summaryOf('similar')).toBe('2 similar incidents')
    expect(summaryOf('dependencies')).toBe('2 upstream · 1 downstream')
    expect(summaryOf('logs')).toBe('4000 logs · 12 errors · 30 warnings')
    expect(summaryOf('reasoning')).toBe('qwen3-14b · 412 tokens')
  })

  it('leaves summary null when a tool returned no data', () => {
    const steps = doneSteps('check nextcloud logs')
    const enriched = enrichToolStepsWithResponse(steps, {
      ...BASE_DATA,
      metadata: { model_used: 'qwen3-14b', tokens_used: 0, tools: {} },
    })
    expect(enriched.find((s) => s.id === 'telemetry')!.detail.summary).toBeNull()
    expect(enriched.find((s) => s.id === 'logs')!.detail.summary).toBeNull()
  })

  it('reasoning result includes suggested_actions', () => {
    const steps = doneSteps('nextcloud status')
    const enriched = enrichToolStepsWithResponse(steps, BASE_DATA)
    const reasoning = enriched.find((s) => s.id === 'reasoning')
    const parsed = JSON.parse(reasoning!.detail.result!)
    expect(parsed.suggested_actions).toEqual(['Restart nextcloud', 'Check loki'])
  })

  it('reasoning model line is null (not a fake fallback) when metadata is missing', () => {
    const steps = doneSteps('nextcloud status')
    const enriched = enrichToolStepsWithResponse(steps, { ...BASE_DATA, metadata: null })
    const reasoning = enriched.find((s) => s.id === 'reasoning')!
    expect(reasoning.detail.model).toBeNull() // no fabricated 'qwen3-14b'
    const parsed = JSON.parse(reasoning.detail.result!)
    expect(parsed.model).toBeUndefined()
    expect(parsed.tokens_used).toBeUndefined()
  })

  it('shows "No similar incidents returned." when tools.similar is absent', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const enriched = enrichToolStepsWithResponse(steps, { ...BASE_DATA, metadata: null })
    const similar = enriched.find((s) => s.id === 'similar')
    expect(similar!.detail.result).toBe('No similar incidents returned.')
  })

  it('does not mutate original steps', () => {
    const steps = doneSteps('show similar nextcloud incidents')
    const original = JSON.stringify(steps)
    enrichToolStepsWithResponse(steps, BASE_DATA)
    expect(JSON.stringify(steps)).toBe(original)
  })
})

// ---------------------------------------------------------------------------
// enrichToolStepsWithResponse — REAL executed tool_calls path
// ---------------------------------------------------------------------------

describe('enrichToolStepsWithResponse — real tool_calls path', () => {
  const TOOL_CALLS = [
    {
      id: 'tc-1',
      name: 'get_dependencies',
      arguments: { service_name: 'backend' },
      status: 'ok' as const,
      result: { service: 'backend', dependencies: { upstream: ['neo4j'], downstream: [] }, total: 1 },
      duration_ms: 42,
    },
  ]
  const DATA = {
    confidence: 0.5,
    suggested_actions: [],
    related_incidents: [],
    userMessage: 'Use the get_dependencies tool to find all dependencies',
    metadata: { model_used: 'qwen3-14b', tokens_used: 23, tool_calls: TOOL_CALLS },
  }

  it('rebuilds the timeline from the REAL executed tool calls + a reasoning step', () => {
    const enriched = enrichToolStepsWithResponse(deriveToolSteps('whatever'), DATA)
    const ids = enriched.map((s) => s.id)
    expect(ids).toContain('tc-1')
    expect(ids[ids.length - 1]).toBe('reasoning')
    const dep = enriched.find((s) => s.id === 'tc-1')!
    expect(dep.status).toBe('done')
    expect(dep.detail.service).toBe('backend')
    // Query is the REAL arguments as JSON; Result is the REAL structured output.
    expect(JSON.parse(dep.detail.query).service_name).toBe('backend')
    expect(JSON.parse(dep.detail.result!).total).toBe(1)
  })

  it('renders a needs_param call as a clear skip note, never a raw JSON stub', () => {
    const enriched = enrichToolStepsWithResponse(deriveToolSteps('whatever'), {
      ...DATA,
      metadata: {
        model_used: 'qwen3-14b',
        tokens_used: 5,
        tool_calls: [
          {
            id: 'np1',
            name: 'get_dependencies',
            arguments: {},
            status: 'needs_param' as const,
            result: { status: 'needs_param', missing: ['service_name'] },
            error: 'Missing required parameter(s): service_name',
          },
        ],
      },
    })
    const step = enriched.find((s) => s.id === 'np1')!
    // Not a hard error — it is a clean skip awaiting input.
    expect(step.status).toBe('done')
    expect(step.label).toContain('needs input')
    expect(step.detail.summary).toBe('Needs parameters')
    // Human-readable explanation, NOT the raw {"status":"needs_param",...} blob.
    expect(step.detail.result).toContain('service_name')
    expect(step.detail.result).not.toContain('"status"')
    // A skipped tool did NOT feed the model -> excluded from synthesised_from.
    const reasoning = enriched.find((s) => s.id === 'reasoning')!
    const q = JSON.parse(reasoning.detail.query)
    expect(q.synthesised_from[0]).toContain('model knowledge')
  })

  it('marks an errored tool call as error with its message', () => {
    const enriched = enrichToolStepsWithResponse(deriveToolSteps('x'), {
      ...DATA,
      metadata: {
        model_used: 'qwen3-14b',
        tokens_used: 5,
        tool_calls: [
          { id: 'e1', name: 'query_metric', status: 'error' as const, error: 'Prometheus not available' },
        ],
      },
    })
    const step = enriched.find((s) => s.id === 'e1')!
    expect(step.status).toBe('error')
    expect(step.detail.result).toBe('Prometheus not available')
  })
})
