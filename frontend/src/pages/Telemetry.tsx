import { useState, useEffect } from 'react'
import {
  Network,
  RefreshCw,
  Loader2,
  Activity,
  FileText,
  Search,
} from 'lucide-react'

// Telemetry data types
interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  service: string
  message: string
}

interface MetricPoint {
  timestamp: string
  value: number
  label: string
}

export function Telemetry() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [metrics, setMetrics] = useState<MetricPoint[]>([])
  const [telemetryLoading, setTelemetryLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')

  const fetchTelemetry = async () => {
    setTelemetryLoading(true)
    try {
      const [logsRes, metricsRes] = await Promise.all([
        fetch('/api/v1/telemetry/logs?limit=50'),
        fetch('/api/v1/telemetry/metrics?range=1h'),
      ])
      if (logsRes.ok) {
        const data = await logsRes.json()
        setLogs(data.logs || [])
      }
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data.metrics || [])
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Network className="h-6 w-6" />
            Telemetry
          </h1>
          <p className="text-muted-foreground">
            Logs, metrics, and traces from the LGTM stack
          </p>
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
          </h3>
          <div className="relative w-full sm:w-auto">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Filter logs..."
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
                  <span className="flex-1">{log.message}</span>
                </div>
              ))
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <FileText className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No logs available</p>
              <p className="text-xs mt-1">Configure Loki endpoint in Settings</p>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Summary */}
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Metrics Summary
        </h3>
        {metrics.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {metrics.slice(0, 4).map((metric, i) => (
              <div key={i} className="p-3 bg-muted/50 rounded-lg text-center">
                <p className="text-2xl font-bold">{metric.value.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">{metric.label}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-muted-foreground">
            <p className="text-sm">No metrics available</p>
            <p className="text-xs mt-1">Configure Prometheus endpoint in Settings</p>
          </div>
        )}
      </div>
    </div>
  )
}
