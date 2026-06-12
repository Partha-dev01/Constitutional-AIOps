import { AlertCircle, CheckCircle2, Lock, ShieldAlert, ShieldCheck, XCircle } from 'lucide-react'
import { JsonView } from '../JsonView'
import type { ConstitutionalVerdict, McpToolCallResult } from './types'
import { ACTION_TOOLS, getVerdict } from './types'

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

// query_recent_logs → timestamped log entries table.
function QueryRecentLogsView({ data }: { data: Record<string, unknown> }) {
  const entries = asArray(data.entries)
  const total = typeof data.total_entries === 'number' ? data.total_entries : entries.length
  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">Service: <span className="font-medium">{asString(data.service)}</span></span>
        <span className="px-2 py-0.5 rounded text-xs bg-blue-500/10 text-blue-500">{total} entries</span>
      </div>
      {entries.length === 0 ? (
        <p className="text-xs text-muted-foreground">No log entries found in the time window.</p>
      ) : (
        <div className="rounded-lg border border-border divide-y divide-border max-h-[300px] overflow-y-auto">
          {entries.map((raw, i) => {
            const e = isObject(raw) ? raw : {}
            const level = asString(e.level).toUpperCase()
            return (
              <div key={i} className="flex items-start gap-2 px-3 py-1.5 text-xs font-mono">
                <span className={`shrink-0 px-1 rounded ${
                  level === 'ERROR' || level === 'FATAL' || level === 'CRITICAL' ? 'bg-red-500/10 text-red-500' :
                  level === 'WARN' || level === 'WARNING' ? 'bg-yellow-500/10 text-yellow-500' :
                  'bg-blue-500/10 text-blue-500'
                }`}>{level || 'INFO'}</span>
                <span className="text-muted-foreground shrink-0">{asString(e.timestamp).slice(11, 19)}</span>
                <span className="flex-1 break-all">{asString(e.message)}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// query_metric → metric data points table.
function QueryMetricView({ data }: { data: Record<string, unknown> }) {
  const points = asArray(data.metrics)
  const total = typeof data.total_points === 'number' ? data.total_points : points.length
  // Deduplicate metric names for a summary row
  const names = [...new Set(points.map(p => isObject(p) ? asString(p.name) : '').filter(Boolean))]
  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">Service: <span className="font-medium">{asString(data.service)}</span></span>
        <span className="px-2 py-0.5 rounded text-xs bg-purple-500/10 text-purple-500">{total} data points</span>
      </div>
      {names.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {names.slice(0, 8).map((n, i) => (
            <span key={`${n}-${i}`} className="px-2 py-0.5 rounded bg-muted text-xs font-mono">{n}</span>
          ))}
          {names.length > 8 && <span className="text-xs text-muted-foreground">+{names.length - 8} more</span>}
        </div>
      )}
      {points.length === 0 ? (
        <p className="text-xs text-muted-foreground">No metric data found in the time window.</p>
      ) : (
        <div className="rounded-lg border border-border divide-y divide-border max-h-[240px] overflow-y-auto">
          {points.slice(0, 50).map((raw, i) => {
            const p = isObject(raw) ? raw : {}
            const val = typeof p.value === 'number' ? p.value : parseFloat(asString(p.value))
            return (
              <div key={i} className="flex items-center gap-3 px-3 py-1.5 text-xs font-mono">
                <span className="text-muted-foreground shrink-0">{asString(p.timestamp).slice(11, 19)}</span>
                <span className="flex-1 text-foreground">{asString(p.name)}</span>
                <span className="font-bold shrink-0">{Number.isNaN(val) ? asString(p.value) : val.toFixed(3)}</span>
              </div>
            )
          })}
          {points.length > 50 && (
            <div className="px-3 py-1.5 text-xs text-muted-foreground text-center">
              {points.length - 50} more rows not shown
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// list_containers → container status grid.
function ListContainersView({ data }: { data: Record<string, unknown> }) {
  const containers = asArray(data.containers)
  const total = typeof data.total === 'number' ? data.total : containers.length
  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-3">
        <span className="px-2 py-0.5 rounded text-xs bg-green-500/10 text-green-500">{total} containers</span>
        {data.include_stopped === true && (
          <span className="text-xs text-muted-foreground">including stopped</span>
        )}
      </div>
      {containers.length === 0 ? (
        <p className="text-xs text-muted-foreground">No containers found.</p>
      ) : (
        <div className="rounded-lg border border-border divide-y divide-border">
          {containers.map((raw, i) => {
            const c = isObject(raw) ? raw : {}
            const status = asString(c.status)
            const health = asString(c.health)
            const running = status === 'running'
            return (
              <div key={i} className="flex items-center gap-3 px-3 py-2">
                <span className={`w-2 h-2 rounded-full shrink-0 ${running ? 'bg-green-500' : 'bg-red-400'}`} />
                <span className="flex-1 font-mono text-xs">{asString(c.name)}</span>
                <span className={`px-2 py-0.5 rounded text-xs shrink-0 ${running ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                  {status}
                </span>
                {health && health !== 'null' && (
                  <span className={`px-2 py-0.5 rounded text-xs shrink-0 ${
                    health === 'healthy' ? 'bg-green-500/10 text-green-500' :
                    health === 'unhealthy' ? 'bg-red-500/10 text-red-500' :
                    'bg-yellow-500/10 text-yellow-500'
                  }`}>{health}</span>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// analyze_time_series_anomaly → anomaly count + anomaly rows.
function AnomalyView({ data }: { data: Record<string, unknown> }) {
  const anomalies = asArray(data.anomalies)
  const detected = typeof data.anomalies_detected === 'number' ? data.anomalies_detected : anomalies.length
  const analyzed = typeof data.metrics_analyzed === 'number' ? data.metrics_analyzed : null
  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-3">
        <span className="text-xs text-muted-foreground">Service: <span className="font-medium">{asString(data.service)}</span></span>
        {analyzed !== null && (
          <span className="text-xs text-muted-foreground">{analyzed} metrics analyzed</span>
        )}
        <span className={`px-2 py-0.5 rounded text-xs ${
          detected === 0 ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
        }`}>
          {detected} anomaly{detected !== 1 ? 'ies' : 'y'} detected
        </span>
      </div>
      {anomalies.length > 0 ? (
        <div className="rounded-lg border border-border divide-y divide-border">
          {anomalies.map((raw, i) => {
            const a = isObject(raw) ? raw : {}
            return (
              <div key={i} className="px-3 py-2 text-xs">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="font-mono font-medium">{asString(a.metric)}</span>
                  <span className="text-red-500 font-bold">z={typeof a.z_score === 'number' ? a.z_score.toFixed(2) : asString(a.z_score)}</span>
                </div>
                <div className="flex gap-4 text-muted-foreground">
                  <span>value={typeof a.value === 'number' ? a.value.toFixed(3) : asString(a.value)}</span>
                  <span>mean={typeof a.mean === 'number' ? a.mean.toFixed(3) : asString(a.mean)}</span>
                  <span>std={typeof a.std === 'number' ? a.std.toFixed(3) : asString(a.std)}</span>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground">No statistical anomalies detected (|z| ≤ 2).</p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Constitutional verdict rendering (action tools)
// ---------------------------------------------------------------------------

// Tier pass/fail row inside the verdict block.
function TierRow({ label, passed }: { label: string; passed: boolean | undefined }) {
  const ok = passed === true
  return (
    <div className="flex items-center gap-2 text-xs">
      {ok
        ? <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
        : <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />}
      <span className={ok ? 'text-muted-foreground' : 'text-red-500'}>{label}</span>
    </div>
  )
}

// Prominent constitutional verdict panel — rendered for refusals AND successes.
function VerdictBlock({ verdict }: { verdict: ConstitutionalVerdict }) {
  const violations = verdict.violations ?? []
  const warnings = verdict.warnings ?? []
  return (
    <div className="rounded-lg border border-border p-3 space-y-2.5">
      <div className="flex items-center justify-between">
        <h5 className="text-xs font-semibold flex items-center gap-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-orange-500" />
          Constitutional Verdict
        </h5>
        <div className="flex items-center gap-1.5">
          {verdict.authorization_level && (
            <span className={`px-2 py-0.5 rounded text-xs ${
              verdict.authorization_level === 'automatic' ? 'bg-green-500/10 text-green-500' :
              verdict.authorization_level === 'approval' ? 'bg-amber-500/10 text-amber-500' :
              'bg-red-500/10 text-red-500'
            }`}>
              {verdict.authorization_level}
            </span>
          )}
          {typeof verdict.confidence === 'number' && (
            <span className="px-2 py-0.5 rounded text-xs bg-muted text-muted-foreground">
              conf {(verdict.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5">
        <TierRow label="Tier 1 · Safety" passed={verdict.principles?.tier1_safety_passed} />
        <TierRow label="Tier 2 · Operational" passed={verdict.principles?.tier2_operational_passed} />
        <TierRow label="Tier 3 · Learning" passed={verdict.principles?.tier3_learning_passed} />
      </div>
      {violations.length > 0 && (
        <div className="space-y-1">
          {violations.map((v, i) => (
            <div key={i} className="rounded bg-red-500/5 border border-red-500/15 px-2.5 py-1.5 text-xs">
              <span className="font-mono font-medium text-red-500">
                {v.principle_id ?? 'principle'}
              </span>
              {v.principle_name && <span className="text-red-500"> {v.principle_name}</span>}
              {v.reason && <span className="text-muted-foreground"> — {v.reason}</span>}
            </div>
          ))}
        </div>
      )}
      {warnings.length > 0 && (
        <div className="space-y-1">
          {warnings.map((w, i) => (
            <p key={i} className="text-xs text-yellow-600">{w}</p>
          ))}
        </div>
      )}
      {verdict.explanation && (
        <p className="text-xs text-muted-foreground italic">{verdict.explanation}</p>
      )}
    </div>
  )
}

// restart_service / scale_service success → status summary card.
function ActionResultView({ data }: { data: Record<string, unknown> }) {
  const isScale = asString(data.action).startsWith('scale')
  const clamped = data.clamped === true
  return (
    <div className="rounded-lg border border-border p-3 space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium flex items-center gap-1.5">
          <CheckCircle2 className="h-4 w-4 text-green-500" />
          {isScale ? 'Service scaled' : 'Container restarted'}
        </span>
        <span className="px-2 py-0.5 rounded text-xs bg-green-500/10 text-green-500">
          {asString(data.status) || 'completed'}
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5 text-xs">
        <span className="px-2 py-0.5 rounded bg-muted font-mono">{asString(data.service)}</span>
        {asString(data.container) && asString(data.container) !== asString(data.service) && (
          <span className="px-2 py-0.5 rounded bg-muted font-mono">container: {asString(data.container)}</span>
        )}
        {isScale && typeof data.target_replicas === 'number' && (
          <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-500">
            replicas → {data.target_replicas}
          </span>
        )}
        {clamped && typeof data.requested_replicas === 'number' && (
          <span className="px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-600">
            clamped from {data.requested_replicas}
          </span>
        )}
      </div>
      {asString(data.reason) && (
        <p className="text-xs text-muted-foreground">Reason: {asString(data.reason)}</p>
      )}
    </div>
  )
}

export function McpResultView({ toolName, result }: McpResultViewProps) {
  const verdict = getVerdict(result)

  if (!result.success) {
    // approval_required — distinct amber state: the validator allowed the
    // action only with human approval, so nothing was executed.
    if (result.error_code === 'approval_required') {
      return (
        <div className="space-y-2">
          <div className="p-3 bg-amber-500/10 border border-amber-500/25 rounded-lg">
            <p className="text-sm font-medium text-amber-600 flex items-center gap-1.5">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              Human approval required — not executed
            </p>
            <p className="text-xs text-amber-600/90 mt-1">
              {result.error || 'The constitutional validator requires a human to approve this action.'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              The approval execution workflow is not wired to this panel; review the verdict below.
            </p>
          </div>
          {verdict && <VerdictBlock verdict={verdict} />}
        </div>
      )
    }

    // action_tools_disabled — neutral gated-off state, not an execution error.
    if (result.error_code === 'action_tools_disabled') {
      return (
        <div className="p-3 bg-muted/50 border border-border rounded-lg">
          <p className="text-sm font-medium flex items-center gap-1.5">
            <Lock className="h-4 w-4 text-muted-foreground shrink-0" />
            Action tools disabled
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {result.error || 'Set AIOPS_ENABLE_ACTION_TOOLS=true on the backend to enable.'}
          </p>
        </div>
      )
    }

    // All other failures (validation_blocked, container_not_whitelisted,
    // validator_unavailable, execution_failed, ...) — red, with the verdict
    // attached when validation actually ran.
    return (
      <div className="space-y-2">
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-600 flex items-start gap-1.5">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{result.error || 'Tool execution failed'}</span>
          </p>
          {result.error_code && (
            <p className="text-xs text-red-500/80 font-mono mt-1">{result.error_code}</p>
          )}
        </div>
        {verdict && <VerdictBlock verdict={verdict} />}
      </div>
    )
  }

  const data = result.data

  // Action tools: status card + the verdict that authorized the execution.
  if (ACTION_TOOLS.has(toolName) && isObject(data)) {
    return (
      <div className="space-y-2">
        <ActionResultView data={data} />
        {verdict && <VerdictBlock verdict={verdict} />}
      </div>
    )
  }

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
    // Phase-2 tool shape formatters
    if (toolName === 'query_recent_logs' && 'entries' in data) {
      return <QueryRecentLogsView data={data} />
    }
    if (toolName === 'query_metric' && 'metrics' in data) {
      return <QueryMetricView data={data} />
    }
    if (toolName === 'list_containers' && 'containers' in data) {
      return <ListContainersView data={data} />
    }
    if (toolName === 'analyze_time_series_anomaly' && 'anomalies_detected' in data) {
      return <AnomalyView data={data} />
    }
    // Generic key/value table for other flat objects, raw JSON otherwise.
    const hasNested = Object.values(data).some(v => isObject(v) || Array.isArray(v))
    return hasNested ? <RawJson data={data} /> : <KeyValueTable data={data} />
  }

  // Non-object payloads → raw JSON.
  return <RawJson data={data} />
}
