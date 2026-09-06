import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { Activity, AlertTriangle, CheckCircle, Clock, RefreshCw, Loader2, Wifi, WifiOff, Server, Container, History } from 'lucide-react'
import api, { DashboardStats, HealthResponse, ModelsConfig, isComponentHealthy } from '../lib/api'
import type { Action } from '../lib/api'
import { useWebSocket, EventType } from '../lib/websocket'
import type { WebSocketEvent } from '../lib/websocket'
import { describeEvent, RECENT_ACTIVITY_LIMIT } from '../lib/activity'
import type { ActivityItem } from '../lib/activity'
import { toTickerItems } from '../lib/approvalTicker'
import type { TickerItem } from '../lib/approvalTicker'
import { useContainerStats } from '../hooks/useContainerStats'
import type { ContainerStatsState } from '../hooks/useContainerStats'
import { Sparkline } from '../components/viz/Sparkline'
import { ApprovalTicker } from '../components/ApprovalTicker'

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

/** Host[:port] of a configured endpoint URL, for honest display (never a
 *  hardcoded port — a remote endpoint like Bedrock has no local port). */
function endpointHost(url?: string): string {
  if (!url) return '—'
  try { return new URL(url).host } catch { return url }
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [agentMetrics, setAgentMetrics] = useState<AgentMetricsLite | null>(null)
  const [modelsCfg, setModelsCfg] = useState<ModelsConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [services, setServices] = useState<ServiceStatus[]>([])
  // Live event feed for the Recent Activity widget (Track 2). Bounded, newest
  // first, built only from real WebSocket events — nothing fabricated.
  const [activity, setActivity] = useState<ActivityItem[]>([])
  const [pending, setPending] = useState<TickerItem[]>([])

  // Live per-service CPU%/mem% (Docker-socket source on the lite tier). Polls on
  // its own 5s cadence and accumulates a rolling client-side window.
  const liveStats = useContainerStats({ intervalMs: 5000 })

  // WebSocket connection for real-time updates
  const { isConnected, subscribe } = useWebSocket({
    autoConnect: true,
    reconnect: true,
    onConnect: () => {
      console.log('Dashboard connected to WebSocket')
    },
  })

  // Refresh data AND prepend to the live activity feed on each event.
  const handleEvent = useCallback((event: WebSocketEvent) => {
    const item = describeEvent(event)
    if (item) {
      setActivity((prev) => [item, ...prev].slice(0, RECENT_ACTIVITY_LIMIT))
    }
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
      EventType.ACTION_REJECTED,
      EventType.ACTION_EXECUTED,
      EventType.ACTION_FAILED,
      EventType.RCA_COMPLETED,
      EventType.REMEDIATION_PLANNED,
      EventType.ALERT,
    ]

    eventTypes.forEach((eventType) => {
      unsubscribers.push(subscribe(eventType, handleEvent))
    })

    return () => {
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [subscribe, handleEvent])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [healthData, statsData, containersResponse, metricsResponse, modelsData, pendingActions] = await Promise.all([
        api.health.check(),
        api.dashboard.getStats(),
        fetch('/api/v1/infrastructure/containers').then(r => r.ok ? r.json() : { containers: [] }),
        // Real measured LLM latency/request counts (same source as the Metrics page).
        fetch('/api/v1/metrics').then(r => r.ok ? r.json() : null).catch(() => null),
        // Live endpoint config (same source as Settings -> Models) so the agent
        // cards show the actual model + endpoint, never hardcoded values.
        api.settings.getModels().catch(() => null),
        // Actions awaiting a human decision, for the approval ticker (no-LLM view).
        api.actions.getPending().then((r) => r.actions).catch((): Action[] => []),
      ])
      setHealth(healthData)
      setStats(statsData)
      setAgentMetrics(metricsResponse)
      setModelsCfg(modelsData)
      setPending(toTickerItems(pendingActions))
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
            <Link
              to="/incidents?status=pending"
              className="ml-auto px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm font-medium hover:bg-yellow-600"
            >
              Review Actions
            </Link>
          </div>
        </div>
      )}

      {/* Model Status — model name, endpoint, latency and requests are ALL real
          live values (Settings -> Models config + /api/v1/metrics); nothing here
          is hardcoded. */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ModelCard
          name="Fast Agent"
          model={modelsCfg?.fastAgentModel || '—'}
          endpoint={endpointHost(modelsCfg?.fastAgentUrl)}
          status={isComponentHealthy(health, 'fast_agent') ? 'online' : 'offline'}
          stats={agentMetrics?.fast_agent}
        />
        <ModelCard
          name="Reasoning Agent"
          model={modelsCfg?.reasoningAgentModel || '—'}
          endpoint={endpointHost(modelsCfg?.reasoningAgentUrl)}
          status={isComponentHealthy(health, 'reasoning_agent') ? 'online' : 'offline'}
          stats={agentMetrics?.reasoning_agent}
        />
      </div>

      {/* Two live, no-LLM widgets side by side: the approval ticker surfaces
          actions awaiting a human decision (aging, with confidence band and tier
          checks); Recent Activity is an event-triggered feed of real WebSocket
          events. Both are empty until the system produces one. */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ApprovalTicker items={pending} now={lastRefresh.getTime()} />
        <RecentActivity items={activity} isConnected={isConnected} />
      </div>

      {/* Live System Metrics — real per-service CPU%/mem% sampled from the
          Docker socket (or Prometheus), plotted as they arrive. Replaces the
          old static "Remediation Performance" tiles. Only real sampled points
          are drawn; a first sample shows a single dot, never fabricated history. */}
      <LiveMetricsBand stats={liveStats} successRate={stats?.actions.success_rate ?? null} />

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
                Go to <Link to="/agents" className="text-primary hover:underline">Agent Hub → Infrastructure</Link> to select containers to monitor
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Live per-service resource metrics band. Renders one card per reporting
 * container with a CPU% and a memory% sparkline built from the rolling window.
 * Honest states: a spinner while the first sample lands, a source-aware hint
 * when nothing reports, and only real points on the graphs.
 */
function LiveMetricsBand({
  stats,
  successRate,
}: {
  stats: ContainerStatsState
  successRate: number | null
}) {
  const { series, source, loading, error } = stats
  const hasData = series.length > 0

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <Activity className="h-5 w-5" />
          Live System Metrics
          {source === 'docker' && (
            <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/60 px-2 py-0.5 text-[11px] font-normal text-muted-foreground">
              <Container className="h-3 w-3" />
              Local Docker socket
            </span>
          )}
        </h2>
        <div className="flex items-center gap-3">
          {successRate != null && (
            <span className="rounded-full border border-border/60 bg-muted/50 px-2.5 py-1 text-xs text-muted-foreground">
              Remediation success{' '}
              <span className="font-semibold text-foreground">{(successRate * 100).toFixed(0)}%</span>
            </span>
          )}
          {hasData && (
            <span className="flex items-center gap-1 text-xs text-green-500">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500" />
              Live
            </span>
          )}
        </div>
      </div>

      {hasData ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {series.map((s) => (
            <div key={s.service} className="rounded-lg border border-border/60 bg-muted/30 p-3">
              <div className="mb-1.5 flex items-center justify-between gap-2">
                <span className="truncate text-sm font-medium" title={s.service}>{s.label}</span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {s.latestCpu != null ? `${s.latestCpu.toFixed(1)}% CPU` : '—'}
                </span>
              </div>
              <div className="text-blue-500">
                <Sparkline values={s.cpu} min={0} height={34} ariaLabel={`${s.label} CPU percent trend`} />
              </div>
              <div className="mb-1 mt-2 flex items-center justify-between gap-2">
                <span className="text-xs text-muted-foreground">Memory</span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {s.latestMem != null ? `${s.latestMem.toFixed(1)}%` : '—'}
                  {s.latestMemMb != null ? ` · ${s.latestMemMb.toFixed(0)} MB` : ''}
                </span>
              </div>
              <div className="text-emerald-500">
                <Sparkline values={s.mem} min={0} max={100} height={26} ariaLabel={`${s.label} memory percent trend`} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center text-muted-foreground">
          {loading ? (
            <Loader2 className="mx-auto h-6 w-6 animate-spin opacity-60" aria-label="Collecting metrics" />
          ) : error ? (
            <p className="text-sm">Couldn't load live metrics: {error}</p>
          ) : (
            <>
              <Activity className="mx-auto mb-2 h-8 w-8 opacity-50" />
              <p className="text-sm">No live metrics yet</p>
              <p className="mt-1 text-xs">
                Enable the local Docker socket source in{' '}
                <Link to="/settings" className="text-primary hover:underline">Settings → Telemetry</Link>, or connect Prometheus.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  )
}

/** Relative "3 minutes ago" label, guarding against an unparseable timestamp. */
function relativeTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return formatDistanceToNow(d, { addSuffix: true })
}

/**
 * Event-triggered activity feed. Renders the bounded list the Dashboard builds
 * from live WebSocket events. Purely presentational — an empty feed is the
 * honest state on a quiet system.
 */
function RecentActivity({ items, isConnected }: { items: ActivityItem[]; isConnected: boolean }) {
  const dot: Record<ActivityItem['severity'], string> = {
    info: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  }
  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <History className="h-5 w-5" />
          Recent Activity
        </h2>
        {isConnected && items.length > 0 && (
          <span className="text-xs text-green-500 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Live
          </span>
        )}
      </div>
      {items.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No recent activity</p>
          <p className="text-xs mt-1">
            Events appear here in real time as the system raises incidents, actions, and analyses.
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex items-center gap-3 rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
            >
              <span className={`h-2 w-2 shrink-0 rounded-full ${dot[item.severity]}`} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{item.label}</p>
                {item.detail && (
                  <p className="truncate text-xs text-muted-foreground">{item.detail}</p>
                )}
              </div>
              <time
                className="shrink-0 text-xs text-muted-foreground"
                dateTime={item.at}
                title={new Date(item.at).toLocaleString()}
              >
                {relativeTime(item.at)}
              </time>
            </li>
          ))}
        </ul>
      )}
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
  endpoint,
  status,
  stats,
}: {
  name: string
  model: string
  endpoint: string
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
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground shrink-0">Model</span>
          <span className="truncate text-right" title={model}>{model}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground shrink-0">Endpoint</span>
          <span className="truncate text-right" title={endpoint}>{endpoint}</span>
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
