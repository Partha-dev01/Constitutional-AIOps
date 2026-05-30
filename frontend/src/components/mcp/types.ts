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
}

// POST /api/v1/tools/call response shape.
export interface McpToolCallResult {
  success: boolean
  data: unknown
  error?: string | null
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

// Read-only tools that are safe to invoke from the UI. The two action tools
// (`restart_service`, `scale_service`) shell out to Docker and stay DISABLED.
export const READ_ONLY_TOOLS: ReadonlySet<string> = new Set([
  'find_similar',
  'get_dependencies',
  'analyze_logs',
  'analyze_time_series_anomaly',
])

export const DISABLED_TOOLS: ReadonlySet<string> = new Set([
  'restart_service',
  'scale_service',
])

export function isToolDisabled(name: string): boolean {
  return DISABLED_TOOLS.has(name)
}
