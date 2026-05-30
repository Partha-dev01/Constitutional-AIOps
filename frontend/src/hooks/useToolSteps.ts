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

export interface ToolStep {
  id: string
  label: string
  icon: LucideIcon
  status: ToolStepStatus
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
    })
  }

  // find_similar: gated only on keywords (no service required).
  if (SIMILAR_KEYWORDS.some((kw) => messageLower.includes(kw))) {
    steps.push({
      id: 'similar',
      label: 'Searching similar incidents',
      icon: Search,
      status: 'pending',
    })
  }

  // get_dependencies: requires BOTH a known service and dependency keywords.
  if (service && DEPENDENCY_KEYWORDS.some((kw) => messageLower.includes(kw))) {
    steps.push({
      id: 'dependencies',
      label: 'Fetching service dependencies',
      icon: GitBranch,
      status: 'pending',
    })
  }

  // analyze_logs: requires BOTH a known service and log keywords.
  if (service && LOG_KEYWORDS.some((kw) => messageLower.includes(kw))) {
    steps.push({
      id: 'logs',
      label: 'Analyzing logs',
      icon: FileText,
      status: 'pending',
    })
  }

  // The reasoning model always runs last.
  steps.push({
    id: 'reasoning',
    label: 'Reasoning with Qwen3-14B',
    icon: Brain,
    status: 'pending',
  })

  return steps
}
