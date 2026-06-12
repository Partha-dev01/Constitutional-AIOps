// Frontend mirror of the backend MCP tool schema.
//
// The backend (`/api/v1/tools/`) returns each tool's `parameters` as a JSON-Schema
// OBJECT (`{ type: 'object', properties: {...}, required: [...] }`), NOT an array.
// The previous frontend typed it as an array, so the param form never rendered.

export type JsonSchemaType = 'string' | 'integer' | 'number' | 'boolean' | 'array' | 'object'

export interface JsonSchemaProp {
  type?: JsonSchemaType
  description?: string
  enum?: string[]
  default?: unknown
  minimum?: number
  maximum?: number
  items?: JsonSchemaProp
}

export interface ToolParameterSchema {
  type: 'object'
  properties: Record<string, JsonSchemaProp>
  required?: string[]
}

export type ToolRiskLevel = 'low' | 'medium' | 'high'

export interface McpToolInfo {
  name: string
  description: string
  category?: string
  parameters: ToolParameterSchema
  requires_approval?: boolean
  risk_level?: ToolRiskLevel
  // Gating metadata from the backend: action tools report enabled=false (with
  // the controlling env var in gated_by) until AIOPS_ENABLE_ACTION_TOOLS is set.
  enabled?: boolean
  gated_by?: string | null
}

// Serialized constitutional validation verdict, attached by the backend under
// result.metadata.constitutional for action-tool calls (refusals AND successes).
export interface ConstitutionalVerdict {
  can_proceed: boolean
  requires_approval: boolean
  authorization_level?: string | null
  overall_result?: string | null
  confidence?: number | null
  principles?: {
    tier1_safety_passed?: boolean
    tier2_operational_passed?: boolean
    tier3_learning_passed?: boolean
  }
  violations?: {
    principle_id?: string | null
    principle_name?: string | null
    severity?: string | null
    reason?: string | null
  }[]
  warnings?: string[]
  explanation?: string
}

// POST /api/v1/tools/call response shape.
export interface McpToolCallResult {
  success: boolean
  data: unknown
  error?: string | null
  // Machine-readable refusal class: "action_tools_disabled",
  // "approval_required", "validation_blocked", "container_not_whitelisted",
  // "validator_unavailable", "invalid_parameters", "execution_failed", ...
  error_code?: string | null
  execution_time_ms?: number
  metadata?: Record<string, unknown>
}

// One in-session execution history entry (never persisted).
export interface McpExecutionRecord {
  id: string
  toolName: string
  parameters: Record<string, unknown>
  result: McpToolCallResult
  at: Date
}

// Read-only tools that are safe to invoke from the UI without confirmation.
export const READ_ONLY_TOOLS: ReadonlySet<string> = new Set([
  'find_similar',
  'get_dependencies',
  'analyze_logs',
  'analyze_time_series_anomaly',
  // Phase-2 tools
  'query_recent_logs',
  'query_metric',
  'list_containers',
])

// Action-class (mutating) tools: execution shows a confirmation step and the
// backend runs constitutional validation before anything touches Docker.
export const ACTION_TOOLS: ReadonlySet<string> = new Set([
  'restart_service',
  'scale_service',
])

export function isActionTool(tool: McpToolInfo): boolean {
  return tool.category === 'action' || ACTION_TOOLS.has(tool.name)
}

// Data-driven disabled state: trust the backend's `enabled` flag when present;
// fall back to treating action tools as disabled (older backend responses).
export function isToolDisabled(tool: McpToolInfo): boolean {
  if (typeof tool.enabled === 'boolean') return !tool.enabled
  return ACTION_TOOLS.has(tool.name)
}

// Human-readable explanation for a gated-off tool (tooltip / banner copy).
export function disabledReason(tool: McpToolInfo): string {
  const env = tool.gated_by ?? 'AIOPS_ENABLE_ACTION_TOOLS'
  return (
    `This action tool mutates real containers and is disabled by the backend. ` +
    `Set ${env}=true on the backend to allow constitutionally gated execution.`
  )
}

// Extract the constitutional verdict the backend attaches to action-tool
// results (present on refusals and successes whenever validation ran).
export function getVerdict(result: McpToolCallResult): ConstitutionalVerdict | null {
  const raw = result.metadata?.['constitutional']
  if (raw && typeof raw === 'object' && !Array.isArray(raw) && 'can_proceed' in raw) {
    return raw as ConstitutionalVerdict
  }
  return null
}
