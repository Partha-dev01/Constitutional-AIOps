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

export type ToolStepStatus = 'pending' | 'running' | 'done'

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
 * Subset of ChatResponse fields used for enrichment.
 * Typed locally so this hook has no direct dependency on api.ts.
 */
export interface ToolStepResponseData {
  confidence?: number | null
  related_incidents?: string[] | null
  suggested_actions?: string[] | null
  metadata?: {
    model_used?: string
    tokens_used?: number
    [key: string]: unknown
  } | null
}

/**
 * Attach concrete backend results to the relevant derived steps.
 *
 * Called once the `POST /api/v1/chat/` response arrives. Returns a new steps
 * array (immutable update) with `detail.result` filled in for each step whose
 * data is available in the response.
 *
 * Mapping:
 *  - "similar"      → related_incidents list
 *  - "dependencies" → service name (no dedicated output field; note it ran)
 *  - "telemetry"    → confidence + model from metadata
 *  - "logs"         → confidence + metadata
 *  - "reasoning"    → model_used, tokens_used, confidence, suggested_actions
 */
export function enrichToolStepsWithResponse(
  steps: ToolStep[],
  data: ToolStepResponseData,
): ToolStep[] {
  return steps.map((step) => {
    let result: string | null = null

    switch (step.id) {
      case 'similar': {
        const incidents = data.related_incidents
        if (incidents && incidents.length > 0) {
          result = JSON.stringify({ similar_incidents: incidents }, null, 2)
        } else {
          result = 'No similar incidents found in Neo4j graph memory.'
        }
        break
      }

      case 'dependencies': {
        // The dependency data is fed into the LLM context string, not returned
        // as a structured field. Surface what we do know: the service queried.
        result = JSON.stringify(
          {
            note: 'Dependency graph was fetched and injected into the reasoning context.',
            service_queried: step.detail.service,
            store: 'Neo4j get_dependencies (depth 2)',
          },
          null,
          2,
        )
        break
      }

      case 'telemetry': {
        result = JSON.stringify(
          {
            note: 'Telemetry context was built from Loki + Prometheus and injected into the reasoning prompt.',
            service: step.detail.service,
            confidence_after_reasoning: data.confidence ?? null,
            model: data.metadata?.model_used ?? 'qwen3-14b',
          },
          null,
          2,
        )
        break
      }

      case 'logs': {
        result = JSON.stringify(
          {
            note: 'Log analysis was performed and included in the reasoning context.',
            service: step.detail.service,
            confidence_after_reasoning: data.confidence ?? null,
          },
          null,
          2,
        )
        break
      }

      case 'reasoning': {
        result = JSON.stringify(
          {
            model: data.metadata?.model_used ?? 'qwen3-14b',
            tokens_used: data.metadata?.tokens_used ?? null,
            confidence: data.confidence ?? null,
            suggested_actions: data.suggested_actions ?? [],
          },
          null,
          2,
        )
        break
      }
    }

    return { ...step, detail: { ...step.detail, result } }
  })
}
