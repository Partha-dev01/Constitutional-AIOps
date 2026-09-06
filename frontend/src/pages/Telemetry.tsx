import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Network,
  RefreshCw,
  Loader2,
  Activity,
  FileText,
  Search,
  Container,
  Database,
  ChevronRight,
} from 'lucide-react'
import api from '../lib/api'
import type { TelemetryLogEntry, TelemetryMetricPoint } from '../lib/api'

/** Human name + icon for a telemetry data source. */
function sourceMeta(source: string): { label: string; Icon: typeof Database } {
  if (source === 'docker') return { label: 'Local Docker socket', Icon: Container }
  if (source === 'loki' || source === 'prometheus') return { label: 'LGTM stack', Icon: Database }
  return { label: 'No source', Icon: Database }
}

/** A small pill naming where the data on a panel came from. */
function SourceBadge({ source }: { source: string }) {
  if (source === 'none') return null
  const { label, Icon } = sourceMeta(source)
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/60 px-2 py-0.5 text-[11px] text-muted-foreground">
      <Icon className="h-3 w-3" />
      {label}
    </span>
  )
}

// ── log line beautifier ──────────────────────────────────────────────────
// Container stdout (esp. Caddy's console format) arrives with ANSI colour codes
// and a trailing JSON object, so a raw dump is a wall of text. Clean it up for
// display only: strip ANSI, and for a structured line show a readable one-line
// summary with the full JSON available on expand.
const ANSI_RE = new RegExp(`${String.fromCharCode(27)}\\[[0-9;]*m`, 'g')
function stripAnsi(input: string): string {
  return input.replace(ANSI_RE, '')
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}
function asString(v: unknown): string {
  return typeof v === 'string' ? v : ''
}

type ParsedLog =
  | { kind: 'structured'; summary: string; detail: string }
  | { kind: 'text'; summary: string }

/** Turn a raw container log line into a readable summary (+ expandable JSON). */
function parseLogMessage(raw: string): ParsedLog {
  const clean = stripAnsi(raw).trim()
  const brace = clean.indexOf('{')
  if (brace !== -1) {
    try {
      const payload: unknown = JSON.parse(clean.slice(brace))
      const detail = JSON.stringify(payload, null, 2)
      // Caddy access log: {"request":{"method","uri","host",...},"status","duration"}
      if (isRecord(payload) && isRecord(payload.request)) {
        const req = payload.request
        const status = typeof payload.status === 'number' ? String(payload.status) : null
        const durMs =
          typeof payload.duration === 'number' ? `${Math.round(payload.duration * 1000)}ms` : null
        const host = asString(req.host)
        const summary = [
          asString(req.method) || '?',
          status,
          asString(req.uri) || null,
          durMs,
          host ? `· ${host}` : null,
        ]
          .filter(Boolean)
          .join(' ')
        return { kind: 'structured', summary, detail }
      }
      // Other structured JSON (e.g. backend structlog): prefer a message field,
      // else the human text before the JSON, else a generic label.
      const field = isRecord(payload)
        ? asString(payload.msg) || asString(payload.message) || asString(payload.event)
        : ''
      const prefix = clean.slice(0, brace).replace(/^\S+\s+[\d:.]+\s*/, '').trim()
      return { kind: 'structured', summary: field || prefix || 'log entry', detail }
    } catch {
      // Not valid JSON after the brace — fall through to cleaned plain text.
    }
  }
  return { kind: 'text', summary: clean }
}

/** One log line's message cell: clean text, or a summary that expands to JSON. */
function LogMessage({ raw }: { raw: string }) {
  const [open, setOpen] = useState(false)
  const parsed = parseLogMessage(raw)
  if (parsed.kind === 'text') {
    return <span className="flex-1 break-all">{parsed.summary}</span>
  }
  return (
    <div className="flex-1 min-w-0">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-1.5 text-left hover:text-foreground"
      >
        <ChevronRight
          className={`h-3 w-3 shrink-0 text-muted-foreground transition-transform ${open ? 'rotate-90' : ''}`}
          aria-hidden="true"
        />
        <span className="truncate">{parsed.summary}</span>
      </button>
      {open && (
        <pre className="mt-2 max-h-72 overflow-auto rounded-md border border-border bg-background/80 p-3 text-xs leading-relaxed text-muted-foreground">
          {parsed.detail}
        </pre>
      )}
    </div>
  )
}

export function Telemetry() {
  const [logs, setLogs] = useState<TelemetryLogEntry[]>([])
  const [metrics, setMetrics] = useState<TelemetryMetricPoint[]>([])
  const [logsSource, setLogsSource] = useState<string>('none')
  const [metricsSource, setMetricsSource] = useState<string>('none')
  const [telemetryLoading, setTelemetryLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')
  // Free-text filter over message + service (the search box used to be dead).
  const [textFilter, setTextFilter] = useState('')

  const fetchTelemetry = async () => {
    setTelemetryLoading(true)
    try {
      const [logsRes, metricsRes] = await Promise.all([
        api.telemetry.logs({ limit: 50 }).catch(() => null),
        api.telemetry.metrics({ range: '1h' }).catch(() => null),
      ])
      if (logsRes) {
        setLogs(logsRes.logs || [])
        setLogsSource(logsRes.source || 'none')
      }
      if (metricsRes) {
        setMetrics(metricsRes.metrics || [])
        setMetricsSource(metricsRes.source || 'none')
      }
    } catch (err) {
      console.error('Failed to fetch telemetry:', err)
      setLogs([])
      setMetrics([])
    } finally {
      setTelemetryLoading(false)
    }
  }

  useEffect(() => {
    fetchTelemetry()
  }, [])

  // Honest, source-aware subtitle: name where the data is actually coming from.
  const anySource = metricsSource !== 'none' ? metricsSource : logsSource
  const subtitle =
    anySource === 'docker'
      ? 'Logs and live metrics read from the local Docker socket'
      : anySource === 'loki' || anySource === 'prometheus'
        ? 'Logs, metrics, and traces from the LGTM stack'
        : 'Connect a monitoring source to see logs and metrics'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Network className="h-6 w-6" />
            Telemetry
          </h1>
          <p className="text-muted-foreground">{subtitle}</p>
        </div>
        <button
          onClick={fetchTelemetry}
          disabled={telemetryLoading}
          className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
        >
          {telemetryLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </button>
      </div>

      {/* Log Level Filter */}
      <div className="flex flex-wrap gap-2">
        {['all', 'ERROR', 'WARN', 'INFO', 'DEBUG'].map((level) => (
          <button
            key={level}
            onClick={() => setLogFilter(level)}
            className={`px-3 py-1 rounded-lg text-sm ${
              logFilter === level
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {level}
          </button>
        ))}
      </div>

      {/* Logs Table */}
      <div className="bg-card rounded-lg border border-border">
        <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-semibold flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Recent Logs
            <SourceBadge source={logsSource} />
          </h3>
          <div className="relative w-full sm:w-auto">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter logs..."
              value={textFilter}
              onChange={(e) => setTextFilter(e.target.value)}
              aria-label="Filter logs by text"
              className="w-full pl-9 pr-3 py-1.5 text-sm rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <div className="divide-y divide-border max-h-[400px] overflow-y-auto font-mono text-sm">
          {telemetryLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : logs.length > 0 ? (
            logs
              .filter((log) => logFilter === 'all' || log.level === logFilter)
              .filter((log) => {
                if (!textFilter.trim()) return true
                const q = textFilter.toLowerCase()
                return (
                  log.message.toLowerCase().includes(q) ||
                  log.service.toLowerCase().includes(q)
                )
              })
              .map((log, i) => (
                <div key={i} className="p-3 hover:bg-muted/50 flex items-start gap-3">
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                    log.level === 'ERROR' ? 'bg-red-500/10 text-red-500' :
                    log.level === 'WARN' ? 'bg-yellow-500/10 text-yellow-500' :
                    log.level === 'INFO' ? 'bg-blue-500/10 text-blue-500' :
                    'bg-gray-500/10 text-gray-500'
                  }`}>
                    {log.level}
                  </span>
                  <span className="text-muted-foreground">[{log.service}]</span>
                  <LogMessage raw={log.message} />
                </div>
              ))
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <FileText className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No logs available</p>
              <p className="text-xs mt-1 text-center px-4">
                Add a Loki endpoint or enable the local Docker socket source in{' '}
                <Link to="/settings" className="text-primary hover:underline">Settings → Telemetry</Link>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Summary */}
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Metrics Summary
          <SourceBadge source={metricsSource} />
        </h3>
        {metrics.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {metrics.slice(0, 8).map((metric, i) => (
              <div key={i} className="p-3 bg-muted/50 rounded-lg text-center">
                <p className="text-2xl font-bold">{metric.value.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">{metric.label}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-muted-foreground">
            <p className="text-sm">No metrics available</p>
            <p className="text-xs mt-1 px-4">
              Add a Prometheus endpoint or enable the local Docker socket source in{' '}
              <Link to="/settings" className="text-primary hover:underline">Settings → Telemetry</Link>
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
