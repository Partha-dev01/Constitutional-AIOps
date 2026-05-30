import { JsonView } from '../JsonView'
import type { McpToolCallResult } from './types'

interface McpResultViewProps {
  toolName: string
  result: McpToolCallResult
}

// Narrowing helpers (no `any`).
function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}
function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : []
}
function asString(v: unknown): string {
  return typeof v === 'string' ? v : v === undefined || v === null ? '' : String(v)
}

function RawJson({ data }: { data: unknown }) {
  return <JsonView raw={JSON.stringify(data, null, 2)} />
}

// Generic key/value table for a flat-ish object.
function KeyValueTable({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data)
  return (
    <div className="rounded-lg border border-border divide-y divide-border text-sm">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-start gap-3 px-3 py-2">
          <span className="w-40 shrink-0 text-xs text-muted-foreground font-medium">{k}</span>
          <span className="flex-1 break-words">
            {isObject(v) || Array.isArray(v) ? (
              <code className="text-xs font-mono">{JSON.stringify(v)}</code>
            ) : (
              String(v)
            )}
          </span>
        </div>
      ))}
    </div>
  )
}

// find_similar → list of similar incidents with similarity scores.
function FindSimilarView({ data }: { data: Record<string, unknown> }) {
  const incidents = asArray(data.similar_incidents)
  if (incidents.length === 0) {
    return <p className="text-sm text-muted-foreground">No similar incidents found.</p>
  }
  return (
    <div className="space-y-2">
      {incidents.map((raw, i) => {
        const inc = isObject(raw) ? raw : {}
        const score = typeof inc.similarity_score === 'number' ? inc.similarity_score : null
        return (
          <div key={i} className="rounded-lg border border-border p-3">
            <div className="flex items-center justify-between mb-1">
              <h5 className="font-medium text-sm">{asString(inc.title) || asString(inc.incident_id) || `Incident ${i + 1}`}</h5>
              {score !== null && (
                <span className="px-2 py-0.5 rounded text-xs bg-blue-500/10 text-blue-500">
                  {(score * 100).toFixed(0)}% similar
                </span>
              )}
            </div>
            {asString(inc.root_cause) && (
              <p className="text-xs text-muted-foreground">Root cause: {asString(inc.root_cause).replace(/_/g, ' ')}</p>
            )}
            {asString(inc.category) && (
              <p className="text-xs text-muted-foreground">Category: {asString(inc.category)}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}

// get_dependencies → upstream / downstream service lists.
function DependenciesView({ data }: { data: Record<string, unknown> }) {
  const deps = isObject(data.dependencies) ? data.dependencies : {}
  const upstream = asArray(deps.upstream).map(asString)
  const downstream = asArray(deps.downstream).map(asString)
  const Chips = ({ items }: { items: string[] }) =>
    items.length > 0 ? (
      <div className="flex flex-wrap gap-1.5">
        {items.map((s, i) => (
          <span key={`${s}-${i}`} className="px-2 py-0.5 rounded bg-muted text-xs">{s}</span>
        ))}
      </div>
    ) : (
      <span className="text-xs text-muted-foreground">none</span>
    )
  return (
    <div className="space-y-3 text-sm">
      <div>
        <p className="text-xs text-muted-foreground mb-1">Service: <span className="font-medium">{asString(data.service)}</span></p>
      </div>
      <div>
        <p className="text-xs font-medium mb-1">Upstream (depend on this)</p>
        <Chips items={upstream} />
      </div>
      <div>
        <p className="text-xs font-medium mb-1">Downstream (this depends on)</p>
        <Chips items={downstream} />
      </div>
    </div>
  )
}

// analyze_logs → summary counts + top error patterns.
function AnalyzeLogsView({ data }: { data: Record<string, unknown> }) {
  const summary = isObject(data.summary) ? data.summary : {}
  const topErrors = asArray(data.top_errors)
  return (
    <div className="space-y-3 text-sm">
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Total', value: summary.total_logs },
          { label: 'Errors', value: summary.error_count },
          { label: 'Warnings', value: summary.warning_count },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg border border-border p-2 text-center">
            <p className="text-lg font-bold">{typeof value === 'number' ? value : '—'}</p>
            <p className="text-xs text-muted-foreground">{label}</p>
          </div>
        ))}
      </div>
      {topErrors.length > 0 && (
        <div>
          <p className="text-xs font-medium mb-1">Top error patterns</p>
          <div className="rounded-lg border border-border divide-y divide-border">
            {topErrors.map((raw, i) => {
              const e = isObject(raw) ? raw : {}
              return (
                <div key={i} className="flex items-center justify-between gap-3 px-3 py-2">
                  <code className="text-xs font-mono flex-1 break-words">{asString(e.pattern)}</code>
                  <span className="px-2 py-0.5 rounded text-xs bg-red-500/10 text-red-500 shrink-0">
                    {typeof e.count === 'number' ? e.count : ''}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export function McpResultView({ toolName, result }: McpResultViewProps) {
  if (!result.success) {
    return (
      <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-600">
        {result.error || 'Tool execution failed'}
      </div>
    )
  }

  const data = result.data

  // Shape-based formatters for the known read-only tools.
  if (isObject(data)) {
    if (toolName === 'find_similar' && 'similar_incidents' in data) {
      return <FindSimilarView data={data} />
    }
    if (toolName === 'get_dependencies' && 'dependencies' in data) {
      return <DependenciesView data={data} />
    }
    if (toolName === 'analyze_logs' && 'summary' in data) {
      return <AnalyzeLogsView data={data} />
    }
    // Generic key/value table for other flat objects, raw JSON otherwise.
    const hasNested = Object.values(data).some(v => isObject(v) || Array.isArray(v))
    return hasNested ? <RawJson data={data} /> : <KeyValueTable data={data} />
  }

  // Non-object payloads → raw JSON.
  return <RawJson data={data} />
}
