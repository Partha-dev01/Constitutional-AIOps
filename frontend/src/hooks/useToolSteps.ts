import { Search, GitBranch, FileText, Brain } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/**
 * Frontend-derived tool-call visualization.
 *
 * The backend does NOT report which MCP tools it ran for a given chat turn, so
 * this module mirrors the backend's keyword -> tool mapping (see
 * `src/api/routes/chat.py`, `_invoke_mcp_tools_for_query` + `KNOWN_SERVICES`)
 * to derive a plausible, deterministic checklist of steps to animate while a
 * request is in flight. It is purely cosmetic — no network calls.
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
  /** What the step is querying / doing. */
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
 * deterministic; matches the backend's tool-gating logic exactly.
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
      query: 'Synthesise telemetry + tool results → root-cause analysis and response',
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
 * Subset of ChatResponse fields used for enrichment.
 * Typed locally so this hook has no direct dependency on api.ts.
 */
export interface ToolStepResponseData {
  confidence?: number | null
  related_incidents?: string[] | null
  suggested_actions?: string[] | null
  metadata?: {
    model_used?: string
    tokens_used?: number | null
    tools?: ChatToolResults
    [key: string]: unknown
  } | null
}

/**
 * Attach concrete backend results to the relevant derived steps.
 *
 * Called once the `POST /api/v1/chat/` response arrives. Returns a new steps
 * array (immutable update) with `detail.result` filled in from the REAL
 * structured tool data the backend now returns under `metadata.tools`.
 *
 * Mapping (step id → data source):
 *  - "telemetry"    → metadata.tools.telemetry
 *  - "similar"      → metadata.tools.similar
 *  - "dependencies" → metadata.tools.dependencies
 *  - "logs"         → metadata.tools.logs
 *  - "reasoning"    → { model_used, tokens_used, confidence, suggested_actions }
 *
 * When a step has no matching tool data (the backend did not actually run that
 * tool), a truthful short line is shown instead of fabricated prose.
 */
export function enrichToolStepsWithResponse(
  steps: ToolStep[],
  data: ToolStepResponseData,
): ToolStep[] {
  const tools = data.metadata?.tools

  return steps.map((step) => {
    let result: string | null = null
    let summary: string | null = null

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
        const model = data.metadata?.model_used ?? null
        const tokens = data.metadata?.tokens_used ?? null
        result = JSON.stringify(
          {
            model,
            tokens_used: tokens,
            confidence: data.confidence ?? null,
            suggested_actions: data.suggested_actions ?? [],
          },
          null,
          2,
        )
        if (model) {
          summary = tokens != null ? `${model} · ${tokens} tokens` : model
        }
        break
      }
    }

    return { ...step, detail: { ...step.detail, result, summary } }
  })
}
