import {
  Search,
  GitBranch,
  FileText,
  Brain,
  Wrench,
  Boxes,
  Activity,
  RotateCw,
  Scale,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/**
 * Frontend-derived tool-call visualization.
 *
 * While a request is IN FLIGHT the backend hasn't told us anything yet, so this
 * module mirrors the backend's keyword -> tool mapping (see
 * `src/api/routes/chat.py`, `_invoke_mcp_tools_for_query` + `KNOWN_SERVICES`)
 * to derive a plausible, deterministic checklist of steps to animate.
 *
 * Once the response arrives, `enrichToolStepsWithResponse` prefers the REAL
 * list of tools the backend actually executed (`metadata.tool_calls`) and
 * renders those truthfully; it falls back to enriching the derived checklist
 * from `metadata.tools` for older responses that don't carry per-call records.
 */

export type ToolStepStatus = 'pending' | 'running' | 'done' | 'error'

/**
 * Static detail captured at derive-time (known before the response arrives).
 * All fields are strings so they render directly in the dropdown.
 */
export interface ToolStepDetailStatic {
  /** The name of the service being operated on, if any. */
  service: string | null
  /** Human-readable description of the store / data source being hit. */
  store: string
  /** What the step is querying / doing. May be a JSON string (rendered as JSON). */
  query: string
}

/**
 * Dynamic detail filled in by `enrichToolStepWithResponse` once the backend
 * response arrives. `null` means "not yet available".
 */
export interface ToolStepDetailDynamic {
  /** Raw result data — stringified JSON or human-readable text. */
  result: string | null
  /**
   * Concise one-line summary of the result (e.g. "50 logs · 0 errors · 4
   * metrics"), shown inline under the step label so the searched data is
   * visible at a glance without expanding. Filled in by enrichment; absent
   * (undefined) before the response arrives.
   */
  summary?: string | null
  /**
   * The model + token line for the reasoning step, shown as its OWN labelled
   * row in the dropdown (kept SEPARATE from the result, which now carries the
   * relevant reasoning outcome rather than model metadata). Null for tool steps.
   */
  model?: string | null
}

export interface ToolStepDetail extends ToolStepDetailStatic, ToolStepDetailDynamic {}

export interface ToolStep {
  id: string
  label: string
  icon: LucideIcon
  status: ToolStepStatus
  /** Detail payload for the expandable dropdown. Always present post-derive. */
  detail: ToolStepDetail
}

// Mirrors KNOWN_SERVICES in src/api/routes/chat.py (~line 32).
export const KNOWN_SERVICES = [
  'nextcloud',
  'neo4j',
  'loki',
  'prometheus',
  'grafana',
  'tempo',
  'backend',
  'frontend',
  'promtail',
  'otel-collector',
  'mimir',
] as const

// Mirrors the three keyword lists in chat.py (~lines 150-152).
const SIMILAR_KEYWORDS = ['similar', 'past', 'history', 'previous', 'before', 'incident']
const DEPENDENCY_KEYWORDS = [
  'dependency',
  'dependencies',
  'impact',
  'upstream',
  'downstream',
  'affects',
  'affected',
]
const LOG_KEYWORDS = ['log', 'logs', 'error', 'errors', 'analyze', 'pattern', 'debug']

/** Substring service detection, mirroring `_extract_service_from_query`. */
function detectService(messageLower: string): string | null {
  for (const service of KNOWN_SERVICES) {
    if (messageLower.includes(service)) return service
  }
  return null
}

/**
 * Derive the (pending) tool-call checklist for a user message. Pure and
 * deterministic; matches the backend's tool-gating logic exactly. Used only for
 * the IN-FLIGHT animation; the final timeline is rebuilt from the real
 * `metadata.tool_calls` when the response lands.
 */
export function deriveToolSteps(message: string): ToolStep[] {
  const messageLower = message.toLowerCase()
  const service = detectService(messageLower)
  const steps: ToolStep[] = []

  // A detected service triggers a leading telemetry read (the backend builds a
  // telemetry context whenever a service is found in the query).
  if (service) {
    steps.push({
      id: 'telemetry',
      label: `Reading ${service} telemetry`,
      icon: FileText,
      status: 'pending',
      detail: {
        service,
        store: 'Loki (logs) + Prometheus (metrics)',
        query: `Last 15 minutes of logs and metrics for service "${service}"`,
        result: null,
      },
    })
  }

  // find_similar: gated only on keywords (no service required).
  if (SIMILAR_KEYWORDS.some((kw) => messageLower.includes(kw))) {
    steps.push({
      id: 'similar',
      label: 'Searching similar incidents',
      icon: Search,
      status: 'pending',
      detail: {
        service,
        store: 'Neo4j graph memory (find_similar MCP tool)',
        query: `Vector + graph similarity search: "${message.slice(0, 120)}${message.length > 120 ? '…' : ''}"`,
        result: null,
      },
    })
  }

  // get_dependencies: requires BOTH a known service and dependency keywords.
  if (service && DEPENDENCY_KEYWORDS.some((kw) => messageLower.includes(kw))) {
    steps.push({
      id: 'dependencies',
      label: 'Fetching service dependencies',
      icon: GitBranch,
      status: 'pending',
      detail: {
        service,
        store: 'Neo4j graph memory (get_dependencies MCP tool)',
        query: `Upstream + downstream dependency graph for "${service}" (depth 2)`,
        result: null,
      },
    })
  }

  // analyze_logs: requires BOTH a known service and log keywords.
  if (service && LOG_KEYWORDS.some((kw) => messageLower.includes(kw))) {
    steps.push({
      id: 'logs',
      label: 'Analyzing logs',
      icon: FileText,
      status: 'pending',
      detail: {
        service,
        store: 'Loki log store (analyze_logs MCP tool)',
        query: `Error/warn pattern analysis for "${service}" logs`,
        result: null,
      },
    })
  }

  // The reasoning model always runs last.
  steps.push({
    id: 'reasoning',
    label: 'Reasoning with Qwen3-14B',
    icon: Brain,
    status: 'pending',
    detail: {
      service,
      store: 'vLLM (Qwen3-14B-AWQ, constitutional reasoning agent)',
      query: 'Synthesise the request + any tool results into a constitutional analysis',
      result: null,
    },
  })

  return steps
}

/**
 * Per-tool result shapes returned by the backend under
 * `ChatResponse.metadata.tools`. Mirrors the api.ts contract types but is
 * declared locally so this hook has no import dependency on api.ts.
 */
export interface TelemetryToolResult {
  service: string
  log_count: number
  error_count: number
  metrics: { name: string; value: number }[]
  sample_logs: string[]
}

export interface SimilarToolResult {
  count: number
  incidents: { id: string; summary: string; score: number | null }[]
}

export interface DependenciesToolResult {
  upstream: string[]
  downstream: string[]
}

export interface LogsToolResult {
  total_logs: number
  error_count: number
  warning_count: number
  top_errors: { pattern: string; count: number }[]
}

export interface ChatToolResults {
  telemetry?: TelemetryToolResult
  similar?: SimilarToolResult
  dependencies?: DependenciesToolResult
  logs?: LogsToolResult
}

/**
 * A single tool the backend agent actually executed this turn (the truthful,
 * per-call record under `metadata.tool_calls`). Mirrors the api.ts `ChatToolCall`
 * type; declared locally so this hook stays import-free of api.ts.
 */
export interface ToolCallRecord {
  id?: string
  name: string
  arguments?: Record<string, unknown> | null
  status?: 'ok' | 'error' | 'needs_param' | string
  result?: unknown
  error?: string | null
  duration_ms?: number | null
}

/**
 * Subset of ChatResponse fields used for enrichment.
 * Typed locally so this hook has no direct dependency on api.ts.
 */
export interface ToolStepResponseData {
  confidence?: number | null
  related_incidents?: string[] | null
  suggested_actions?: string[] | null
  /** The user's request for this turn (renders in the reasoning step's Query). */
  userMessage?: string | null
  /** Graph/cockpit context attached to the send (renders in the Query JSON). */
  attachedContext?: Record<string, unknown> | null
  metadata?: {
    model_used?: string
    tokens_used?: number | null
    tools?: ChatToolResults
    /** The REAL ordered list of tools the agent executed this turn. */
    tool_calls?: ToolCallRecord[]
    [key: string]: unknown
  } | null
}

// ---------------------------------------------------------------------------
// Rendering REAL executed tool calls (metadata.tool_calls).
// ---------------------------------------------------------------------------

const TOOL_LABELS: Record<string, string> = {
  find_similar: 'Searched similar incidents',
  get_dependencies: 'Fetched service dependencies',
  analyze_logs: 'Analyzed logs',
  query_recent_logs: 'Queried recent logs',
  query_metric: 'Queried metrics',
  list_containers: 'Listed containers',
  analyze_time_series_anomaly: 'Detected metric anomalies',
  restart_service: 'Restarted service',
  scale_service: 'Scaled service',
}

const TOOL_ICONS: Record<string, LucideIcon> = {
  find_similar: Search,
  get_dependencies: GitBranch,
  analyze_logs: FileText,
  query_recent_logs: FileText,
  query_metric: Activity,
  analyze_time_series_anomaly: Activity,
  list_containers: Boxes,
  restart_service: RotateCw,
  scale_service: Scale,
}

const TOOL_STORES: Record<string, string> = {
  find_similar: 'Neo4j graph memory (find_similar)',
  get_dependencies: 'Neo4j graph memory (get_dependencies)',
  analyze_logs: 'Loki log store',
  query_recent_logs: 'Loki log store',
  query_metric: 'Prometheus metrics',
  analyze_time_series_anomaly: 'Prometheus metrics',
  list_containers: 'Docker engine',
  restart_service: 'Docker engine · constitutional gate',
  scale_service: 'Docker engine · constitutional gate',
}

function titleCase(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Pull a service-ish argument out of a tool call for the Service line. */
function serviceFromArguments(args: Record<string, unknown> | null | undefined): string | null {
  if (!args) return null
  if (typeof args.service_name === 'string') return args.service_name
  if (typeof args.service === 'string') return args.service
  return null
}

/** A concise at-a-glance line for an executed tool call. */
function summariseToolCall(call: ToolCallRecord): string | null {
  if (call.status === 'error') return 'Failed'
  if (call.status === 'needs_param') return 'Needs parameters'
  const r = call.result
  if (r && typeof r === 'object') {
    const obj = r as Record<string, unknown>
    // Executors wrap their payload as { success, data }; look inside data too.
    const data =
      obj.data && typeof obj.data === 'object' ? (obj.data as Record<string, unknown>) : obj
    const numericKeys = [
      'total_found',
      'total_entries',
      'total_points',
      'anomalies_detected',
      'total',
      'count',
    ]
    for (const k of numericKeys) {
      if (typeof data[k] === 'number') return `${data[k]} ${k.replace(/_/g, ' ')}`
    }
  }
  return 'OK'
}

/**
 * Build the final reasoning-step detail. The Query is the structured synthesis
 * INPUT as proper JSON (request + attached context + which tools fed the model);
 * the Result is the RELEVANT reasoning OUTCOME (confidence / actions / related),
 * never the model+tokens meta blob; the model+tokens line is returned separately.
 */
function reasoningDetail(
  data: ToolStepResponseData,
  ranToolNames: string[],
): { query: string; result: string; summary: string | null; model: string | null } {
  const model = data.metadata?.model_used ?? null
  const tokens = data.metadata?.tokens_used ?? null
  const modelLine = model ? (tokens != null ? `${model} · ${tokens} tokens` : model) : null

  const queryObj: Record<string, unknown> = {
    request: data.userMessage ?? '(current message)',
  }
  if (data.attachedContext && Object.keys(data.attachedContext).length > 0) {
    queryObj.attached_context = data.attachedContext
  }
  queryObj.synthesised_from =
    ranToolNames.length > 0 ? ranToolNames : ['model knowledge — no tools matched this query']

  const outcome: Record<string, unknown> = { answer: 'Generated the response shown below.' }
  if (typeof data.confidence === 'number' && Number.isFinite(data.confidence)) {
    outcome.confidence = data.confidence
  }
  const acts = data.suggested_actions ?? []
  if (acts.length > 0) outcome.suggested_actions = acts
  const rel = data.related_incidents ?? []
  if (rel.length > 0) outcome.related_incidents = rel

  return {
    query: JSON.stringify(queryObj, null, 2),
    result: JSON.stringify(outcome, null, 2),
    summary: modelLine,
    model: modelLine,
  }
}

function makeReasoningStep(data: ToolStepResponseData, ranToolNames: string[]): ToolStep {
  const rd = reasoningDetail(data, ranToolNames)
  return {
    id: 'reasoning',
    label: 'Reasoning with Qwen3-14B',
    icon: Brain,
    status: 'done',
    detail: {
      service: null,
      store: 'vLLM (Qwen3-14B-AWQ, constitutional reasoning agent)',
      query: rd.query,
      result: rd.result,
      summary: rd.summary,
      model: rd.model,
    },
  }
}

/**
 * Attach concrete backend results to the timeline once the
 * `POST /api/v1/chat/` response arrives. Returns a NEW steps array.
 *
 *  - PREFERRED: when the backend reports `metadata.tool_calls`, the timeline is
 *    REBUILT from the tools that actually ran (truthful name / arguments /
 *    structured result), followed by the reasoning step. This is what makes the
 *    "use the X tool" turns show real JSON instead of bogus narration.
 *  - FALLBACK: older responses with only `metadata.tools` enrich the derived
 *    checklist in place. Either way the reasoning step shows the relevant
 *    outcome (not the model/tokens meta blob), with the model line separate.
 */
export function enrichToolStepsWithResponse(
  steps: ToolStep[],
  data: ToolStepResponseData,
): ToolStep[] {
  const toolCalls = data.metadata?.tool_calls

  if (Array.isArray(toolCalls) && toolCalls.length > 0) {
    const ran = toolCalls.map((c) => c.name)
    const callSteps: ToolStep[] = toolCalls.map((call, i) => {
      const errored = call.status === 'error'
      const result = errored
        ? (call.error ?? 'Tool returned an error.')
        : JSON.stringify(call.result ?? {}, null, 2)
      return {
        id: call.id ?? `tool-${i}-${call.name}`,
        label: TOOL_LABELS[call.name] ?? `Called ${titleCase(call.name)}`,
        icon: TOOL_ICONS[call.name] ?? Wrench,
        status: errored ? 'error' : 'done',
        detail: {
          service: serviceFromArguments(call.arguments),
          store: TOOL_STORES[call.name] ?? 'MCP tool',
          query: JSON.stringify(call.arguments ?? {}, null, 2),
          result,
          summary: summariseToolCall(call),
          model: null,
        },
      }
    })
    callSteps.push(makeReasoningStep(data, ran))
    return callSteps
  }

  // FALLBACK PATH — enrich the derived checklist from metadata.tools.
  const tools = data.metadata?.tools
  const ranLegacy = tools
    ? Object.keys(tools).filter((k) => tools[k as keyof ChatToolResults] != null)
    : []

  return steps.map((step) => {
    let result: string | null = null
    let summary: string | null = null
    let model: string | null = null
    let queryOverride: string | null = null

    switch (step.id) {
      case 'telemetry': {
        const t = tools?.telemetry
        if (t) {
          result = JSON.stringify(t, null, 2)
          summary = `${t.log_count} logs · ${t.error_count} errors · ${t.metrics.length} metrics`
        } else {
          result = 'No telemetry returned.'
        }
        break
      }

      case 'similar': {
        const s = tools?.similar
        if (s) {
          result = JSON.stringify(s, null, 2)
          summary = `${s.count} similar incident${s.count === 1 ? '' : 's'}`
        } else {
          result = 'No similar incidents returned.'
        }
        break
      }

      case 'dependencies': {
        const d = tools?.dependencies
        if (d) {
          result = JSON.stringify(d, null, 2)
          summary = `${d.upstream.length} upstream · ${d.downstream.length} downstream`
        } else {
          result = 'No dependencies returned.'
        }
        break
      }

      case 'logs': {
        const l = tools?.logs
        if (l) {
          result = JSON.stringify(l, null, 2)
          summary = `${l.total_logs} logs · ${l.error_count} errors · ${l.warning_count} warnings`
        } else {
          result = 'No log analysis returned.'
        }
        break
      }

      case 'reasoning': {
        const rd = reasoningDetail(data, ranLegacy)
        queryOverride = rd.query
        result = rd.result
        summary = rd.summary
        model = rd.model
        break
      }
    }

    return {
      ...step,
      detail: {
        ...step.detail,
        ...(queryOverride != null ? { query: queryOverride } : {}),
        result,
        summary,
        model,
      },
    }
  })
}
