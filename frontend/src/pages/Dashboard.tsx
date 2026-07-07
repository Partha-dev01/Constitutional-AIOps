import { useState, useEffect, useCallback } from 'react'
import { Activity, AlertTriangle, CheckCircle, Clock, RefreshCw, Loader2, Wifi, WifiOff, Server } from 'lucide-react'
import api, { DashboardStats, HealthResponse, isComponentHealthy } from '../lib/api'
import { useWebSocket, EventType } from '../lib/websocket'

interface ServiceStatus {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  monitored: boolean
}

/** Slice of GET /api/v1/metrics we render — REAL measured latency/requests
 *  (the model cards used to show hardcoded placeholder numbers). */
interface AgentLatencyLite {
  count: number
  avg_ms: number
  p95_ms: number
}
interface AgentMetricsLite {
  fast_agent?: AgentLatencyLite
  reasoning_agent?: AgentLatencyLite
}

/** Render a measured latency honestly at any magnitude (ms → s). */
function formatLatency(ms: number): string {
  return ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(1)}s`
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [agentMetrics, setAgentMetrics] = useState<AgentMetricsLite | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [services, setServices] = useState<ServiceStatus[]>([])

  // WebSocket connection for real-time updates
  const { isConnected, subscribe } = useWebSocket({
    autoConnect: true,
    reconnect: true,
    onConnect: () => {
      console.log('Dashboard connected to WebSocket')
    },
  })

  // Refresh data on WebSocket events
  const refreshOnEvent = useCallback(() => {
    fetchData()
  }, [])

  // Subscribe to WebSocket events for real-time updates
  useEffect(() => {
    const unsubscribers: (() => void)[] = []

    // Subscribe to relevant events and refresh on change
    const eventTypes = [
      EventType.INCIDENT_CREATED,
      EventType.INCIDENT_RESOLVED,
      EventType.ACTION_CREATED,
      EventType.ACTION_APPROVED,
      EventType.ACTION_EXECUTED,
      EventType.RCA_COMPLETED,
      EventType.ALERT,
    ]

    eventTypes.forEach((eventType) => {
      unsubscribers.push(subscribe(eventType, refreshOnEvent))
    })

    return () => {
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [subscribe, refreshOnEvent])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [healthData, statsData, containersResponse, metricsResponse] = await Promise.all([
        api.health.check(),
        api.dashboard.getStats(),
        fetch('/api/v1/infrastructure/containers').then(r => r.ok ? r.json() : { containers: [] }),
        // Real measured LLM latency/request counts (same source as the Metrics page).
        fetch('/api/v1/metrics').then(r => r.ok ? r.json() : null).catch(() => null),
      ])
      setHealth(healthData)
      setStats(statsData)
      setAgentMetrics(metricsResponse)
      setLastRefresh(new Date())

      // Update services with container data (current status only — no
      // fabricated history; real uptime series lives in Grafana/Prometheus).
      const containerServices: ServiceStatus[] = (containersResponse.containers || [])
        .filter((c: { monitored?: boolean }) => c.monitored)
        .map((c: { name: string; health: string; monitored: boolean }) => ({
          name: c.name,
          status: (c.health === 'healthy' ? 'healthy' : c.health === 'unhealthy' ? 'unhealthy' : 'unknown') as ServiceStatus['status'],
          monitored: c.monitored,
        }))
      setServices(containerServices)
    } catch (err) {
      console.error('Dashboard fetch error:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch dashboard data'
      setError(errorMessage)
      // Don't use mock data - show actual error state
      setStats(null)
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Constitutional AIOps system overview
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* WebSocket connection status */}
          <div className="flex items-center gap-1.5">
            {isConnected ? (
              <>
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-xs text-green-500">Live</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Offline</span>
              </>
            )}
          </div>
          <span className="text-xs text-muted-foreground">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-muted disabled:opacity-50"
            aria-label="Refresh dashboard"
            title="Refresh"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600 text-sm">
          Error: {error}. Please check that the backend is running.
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Incidents"
          value={stats?.incidents.active?.toString() || '0'}
          icon={AlertTriangle}
          trend={`${stats?.incidents.in_progress || 0} in progress`}
          color="text-yellow-500"
        />
        <StatCard
          title="Resolved"
          value={stats?.incidents.resolved_total?.toString() || '0'}
          icon={CheckCircle}
          trend="Resolved incidents"
          color="text-green-500"
        />
        <StatCard
          title="Avg LLM Latency"
          value={
            agentMetrics?.reasoning_agent && agentMetrics.reasoning_agent.count > 0
              ? formatLatency(agentMetrics.reasoning_agent.avg_ms)
              : 'No data'
          }
          icon={Clock}
          trend="Reasoning agent, measured"
          color="text-blue-500"
        />
        <StatCard
          title="System Health"
          value={`${((stats?.system.health_score || 0) * 100).toFixed(1)}%`}
          icon={Activity}
          trend={`${stats?.system.services_healthy || 0} services healthy`}
          color="text-green-500"
        />
      </div>

      {/* Pending Approvals Alert */}
      {(stats?.actions.pending_approval || 0) > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
          <div className="flex flex-wrap items-center gap-3">
            <Clock className="h-5 w-5 text-yellow-500 shrink-0" />
            <div className="min-w-0">
              <h3 className="font-semibold text-yellow-600">
                {stats?.actions.pending_approval} Actions Awaiting Approval
              </h3>
              <p className="text-sm text-yellow-600/80">
                Review and approve pending remediation actions
              </p>
            </div>
            <a
              href="/incidents?status=pending"
              className="ml-auto px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm font-medium hover:bg-yellow-600"
            >
              Review Actions
            </a>
          </div>
        </div>
      )}

      {/* Model Status — latency/requests are REAL measured values from
          /api/v1/metrics (previously hardcoded placeholder numbers). */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ModelCard
          name="Fast Agent"
          model="Qwen3-4B-AWQ"
          port={8000}
          status={isComponentHealthy(health, 'fast_agent') ? 'online' : 'offline'}
          stats={agentMetrics?.fast_agent}
        />
        <ModelCard
          name="Reasoning Agent"
          model="Qwen3-14B-AWQ"
          port={8001}
          status={isComponentHealthy(health, 'reasoning_agent') ? 'online' : 'offline'}
          stats={agentMetrics?.reasoning_agent}
        />
      </div>

      {/* Action Success Rate */}
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-lg font-semibold mb-4">Remediation Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className={`text-3xl font-bold ${
              (stats?.actions.success_rate ?? 1) >= 0.9
                ? 'text-green-500'
                : (stats?.actions.success_rate ?? 1) >= 0.7
                  ? 'text-yellow-500'
                  : 'text-red-500'
            }`}>
              {`${(((stats?.actions.success_rate ?? 1)) * 100).toFixed(0)}%`}
            </p>
            <p className="text-sm text-muted-foreground">Success Rate</p>
          </div>
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className="text-3xl font-bold">
              {stats?.actions.executed_today === 0
                ? 'None'
                : stats?.actions.executed_today || 0}
            </p>
            <p className="text-sm text-muted-foreground">
              {stats?.actions.executed_today === 0 ? 'No actions today' : 'Actions Today'}
            </p>
          </div>
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className="text-3xl font-bold">
              {stats?.incidents.mttr_minutes != null
                ? `${stats.incidents.mttr_minutes}ms`
                : 'N/A'}
            </p>
            {/* This value is the backend→agent health-probe ping, not LLM
                inference latency — label it honestly. */}
            <p className="text-sm text-muted-foreground">API Health Probe</p>
          </div>
        </div>
      </div>

      {/* Service Availability - Moved to bottom */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Server className="h-5 w-5" />
            Service Availability
          </h2>
          {isConnected && (
            <span className="text-xs text-green-500 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Live monitoring
            </span>
          )}
        </div>
        <div className="space-y-3">
          {services.length > 0 ? (
            services.map((service) => (
              /* Current status only — the old 20-segment bar was fabricated
                 (it just repeated the current status); real uptime history
                 lives in Grafana/Prometheus. */
              <div key={service.name} className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-3 py-2">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    service.status === 'healthy' ? 'bg-green-500' :
                    service.status === 'unhealthy' ? 'bg-red-500' :
                    'bg-yellow-500'
                  }`} />
                  <span className="font-medium text-sm">{service.name}</span>
                  {service.monitored && (
                    <span className="px-1.5 py-0.5 bg-blue-500/10 text-blue-500 rounded text-xs">
                      Monitoring
                    </span>
                  )}
                </div>
                <span className={`text-xs font-medium capitalize ${
                  service.status === 'healthy' ? 'text-green-500' :
                  service.status === 'unhealthy' ? 'text-red-500' :
                  'text-yellow-500'
                }`}>
                  {service.status}
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Server className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No services being monitored</p>
              <p className="text-xs mt-1">
                Go to <a href="/agents" className="text-primary hover:underline">Agent Hub → Infrastructure</a> to select containers to monitor
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  color,
}: {
  title: string
  value: string
  icon: React.ElementType
  trend: string
  color: string
}) {
  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{title}</span>
        <Icon className={`h-5 w-5 ${color}`} />
      </div>
      <div className="mt-2">
        <span className="text-2xl font-bold">{value}</span>
        <p className="text-xs text-muted-foreground mt-1">{trend}</p>
      </div>
    </div>
  )
}

function ModelCard({
  name,
  model,
  port,
  status,
  stats,
}: {
  name: string
  model: string
  port: number
  status: string
  /** Real measured latency/requests from /api/v1/metrics; undefined = no data. */
  stats?: AgentLatencyLite
}) {
  const hasData = stats != null && stats.count > 0
  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">{name}</h3>
        <span
          className={`px-2 py-1 rounded-full text-xs ${
            status === 'online'
              ? 'bg-green-500/10 text-green-500'
              : 'bg-red-500/10 text-red-500'
          }`}
        >
          {status}
        </span>
      </div>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Model</span>
          <span>{model}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Port</span>
          <span>{port}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Avg / P95 Latency</span>
          <span>
            {hasData ? `${formatLatency(stats.avg_ms)} / ${formatLatency(stats.p95_ms)}` : 'No data yet'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Requests (measured)</span>
          <span>{hasData ? stats.count.toLocaleString() : '0'}</span>
        </div>
      </div>
    </div>
  )
}
