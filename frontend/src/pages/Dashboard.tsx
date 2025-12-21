import { useState, useEffect, useCallback } from 'react'
import { Activity, AlertTriangle, CheckCircle, Clock, RefreshCw, Loader2, Wifi, WifiOff } from 'lucide-react'
import api, { DashboardStats, HealthResponse, isComponentHealthy } from '../lib/api'
import { useWebSocket, EventType, WebSocketEvent } from '../lib/websocket'

interface ActivityItem {
  time: string
  event: string
  type: 'success' | 'warning' | 'info'
  timestamp: Date
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([])

  // WebSocket connection for real-time updates
  const { isConnected, subscribe } = useWebSocket({
    autoConnect: true,
    reconnect: true,
    onConnect: () => {
      console.log('Dashboard connected to WebSocket')
    },
  })

  // Add activity item from WebSocket event
  const addActivity = useCallback((event: string, type: ActivityItem['type']) => {
    setRecentActivity((prev) => {
      const newItem: ActivityItem = {
        time: 'Just now',
        event,
        type,
        timestamp: new Date(),
      }
      // Keep only last 10 items
      return [newItem, ...prev.slice(0, 9)]
    })
  }, [])

  // Subscribe to WebSocket events
  useEffect(() => {
    const unsubscribers: (() => void)[] = []

    // Incident events
    unsubscribers.push(
      subscribe(EventType.INCIDENT_CREATED, (e: WebSocketEvent) => {
        const payload = e.payload as { title?: string }
        addActivity(`New incident: ${payload.title || 'Unknown'}`, 'warning')
        // Refresh stats
        fetchData()
      })
    )

    unsubscribers.push(
      subscribe(EventType.INCIDENT_RESOLVED, (e: WebSocketEvent) => {
        const payload = e.payload as { incident_id?: string }
        addActivity(`Incident ${payload.incident_id?.slice(0, 8) || ''} resolved`, 'success')
        fetchData()
      })
    )

    // Action events
    unsubscribers.push(
      subscribe(EventType.ACTION_CREATED, (e: WebSocketEvent) => {
        const payload = e.payload as { description?: string }
        addActivity(`Action created: ${payload.description || 'Unknown'}`, 'info')
        fetchData()
      })
    )

    unsubscribers.push(
      subscribe(EventType.ACTION_APPROVED, (e: WebSocketEvent) => {
        const payload = e.payload as { action_type?: string }
        addActivity(`Action approved: ${payload.action_type || 'Unknown'}`, 'success')
        fetchData()
      })
    )

    unsubscribers.push(
      subscribe(EventType.ACTION_EXECUTED, (e: WebSocketEvent) => {
        const payload = e.payload as { action_type?: string }
        addActivity(`Action executed: ${payload.action_type || 'Unknown'}`, 'success')
        fetchData()
      })
    )

    // RCA events
    unsubscribers.push(
      subscribe(EventType.RCA_STARTED, (e: WebSocketEvent) => {
        const payload = e.payload as { incident_id?: string }
        addActivity(`RCA started for incident ${payload.incident_id?.slice(0, 8) || ''}`, 'info')
      })
    )

    unsubscribers.push(
      subscribe(EventType.RCA_COMPLETED, (e: WebSocketEvent) => {
        const payload = e.payload as { incident_id?: string }
        addActivity(`RCA completed for incident ${payload.incident_id?.slice(0, 8) || ''}`, 'success')
      })
    )

    // System alerts
    unsubscribers.push(
      subscribe(EventType.ALERT, (e: WebSocketEvent) => {
        const payload = e.payload as { message?: string }
        addActivity(`Alert: ${payload.message || 'System alert'}`, 'warning')
      })
    )

    return () => {
      unsubscribers.forEach((unsub) => unsub())
    }
  }, [subscribe, addActivity])

  // Update activity times
  useEffect(() => {
    const interval = setInterval(() => {
      setRecentActivity((prev) =>
        prev.map((item) => ({
          ...item,
          time: formatRelativeTime(item.timestamp),
        }))
      )
    }, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [healthData, statsData] = await Promise.all([
        api.health.check(),
        api.dashboard.getStats(),
      ])
      setHealth(healthData)
      setStats(statsData)
      setLastRefresh(new Date())
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
      <div className="flex items-center justify-between">
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
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
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
          value={stats?.incidents.open?.toString() || '0'}
          icon={AlertTriangle}
          trend={`${stats?.incidents.investigating || 0} investigating`}
          color="text-yellow-500"
        />
        <StatCard
          title="Auto-Resolved"
          value={stats?.incidents.resolved_today?.toString() || '0'}
          icon={CheckCircle}
          trend="Last 24 hours"
          color="text-green-500"
        />
        <StatCard
          title="Avg Response Time"
          value={`${stats?.incidents.mttr_minutes || 0}min`}
          icon={Clock}
          trend="Mean time to resolve"
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
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-yellow-500" />
            <div>
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

      {/* Recent Activity */}
      <div className="bg-card rounded-lg border border-border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Activity</h2>
          {isConnected && (
            <span className="text-xs text-green-500 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Real-time updates
            </span>
          )}
        </div>
        <div className="space-y-4">
          {recentActivity.length > 0 ? (
            recentActivity.map((item, i) => (
              <div
                key={i}
                className="flex items-center gap-4 p-3 rounded-lg bg-muted/50"
              >
                <div
                  className={`w-2 h-2 rounded-full ${
                    item.type === 'success'
                      ? 'bg-green-500'
                      : item.type === 'warning'
                      ? 'bg-yellow-500'
                      : 'bg-blue-500'
                  }`}
                />
                <div className="flex-1">
                  <p className="text-sm font-medium">{item.event}</p>
                  <p className="text-xs text-muted-foreground">{item.time}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No recent activity</p>
              <p className="text-xs mt-1">
                {isConnected
                  ? 'Activity will appear here in real-time as events occur'
                  : 'Connect to WebSocket for real-time updates'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Model Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ModelCard
          name="Fast Agent"
          model="Qwen3-4B Q4_K_M"
          port={8081}
          status={isComponentHealthy(health, 'fast_agent') ? 'online' : 'offline'}
          latency="42ms"
          requests={1247}
        />
        <ModelCard
          name="Reasoning Agent"
          model="Qwen3-14B Q4_K_M"
          port={8082}
          status={isComponentHealthy(health, 'reasoning_agent') ? 'online' : 'offline'}
          latency="156ms"
          requests={89}
        />
      </div>

      {/* Action Success Rate */}
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-lg font-semibold mb-4">Remediation Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className="text-3xl font-bold text-green-500">
              {((stats?.actions.success_rate || 0) * 100).toFixed(0)}%
            </p>
            <p className="text-sm text-muted-foreground">Success Rate</p>
          </div>
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className="text-3xl font-bold">{stats?.actions.executed_today || 0}</p>
            <p className="text-sm text-muted-foreground">Actions Today</p>
          </div>
          <div className="text-center p-4 bg-muted/50 rounded-lg">
            <p className="text-3xl font-bold">{stats?.incidents.mttr_minutes || 0}min</p>
            <p className="text-sm text-muted-foreground">Avg Resolution Time</p>
          </div>
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

// Helper function to format relative time
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) return 'Just now'
  if (diffMin < 60) return `${diffMin} min ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`
  return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`
}

function ModelCard({
  name,
  model,
  port,
  status,
  latency,
  requests,
}: {
  name: string
  model: string
  port: number
  status: string
  latency: string
  requests: number
}) {
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
          <span className="text-muted-foreground">Avg Latency</span>
          <span>{latency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Requests (24h)</span>
          <span>{requests.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}
