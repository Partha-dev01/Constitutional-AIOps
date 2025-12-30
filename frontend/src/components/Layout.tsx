import { ReactNode, useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  AlertTriangle,
  MessageSquare,
  Settings,
  Activity,
  Shield,
  Cpu,
  Play,
  RotateCcw,
  Loader2,
  BarChart3
} from 'lucide-react'
import { cn } from '../lib/utils'
import api, { HealthResponse, isComponentHealthy } from '../lib/api'

interface LayoutProps {
  children: ReactNode
}

interface DemoStatus {
  active: boolean
  started_at: string | null
  anomalies_triggered: number
  container_name: string
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Agents', href: '/agents', icon: Cpu },
  { name: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [demoStatus, setDemoStatus] = useState<DemoStatus | null>(null)
  const [demoLoading, setDemoLoading] = useState(false)

  // Fetch health status periodically
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await api.health.check()
        setHealth(data)
      } catch (err) {
        console.error('Health check failed:', err)
        setHealth(null)
      }
    }
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000) // Every 30 seconds
    return () => clearInterval(interval)
  }, [])

  // Fetch demo status periodically
  useEffect(() => {
    const fetchDemoStatus = async () => {
      try {
        const response = await fetch('/api/v1/demo/status')
        if (response.ok) {
          const data = await response.json()
          setDemoStatus(data)
        }
      } catch (err) {
        console.error('Demo status check failed:', err)
      }
    }
    fetchDemoStatus()
    const interval = setInterval(fetchDemoStatus, 10000) // Every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const fastAgentOnline = isComponentHealthy(health, 'fast_agent')
  const reasoningAgentOnline = isComponentHealthy(health, 'reasoning_agent')
  const systemHealthy = fastAgentOnline && reasoningAgentOnline

  const handleStartDemo = async () => {
    setDemoLoading(true)
    try {
      const response = await fetch('/api/v1/demo/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.ok) {
        const data = await response.json()
        console.log('Demo started:', data)
        // Refresh demo status
        const statusResponse = await fetch('/api/v1/demo/status')
        if (statusResponse.ok) {
          setDemoStatus(await statusResponse.json())
        }
      } else {
        const error = await response.json()
        alert(`Failed to start demo: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Failed to start demo:', err)
      alert('Failed to start demo. Check console for details.')
    } finally {
      setDemoLoading(false)
    }
  }

  const handleResetDemo = async () => {
    setDemoLoading(true)
    try {
      const response = await fetch('/api/v1/demo/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (response.ok) {
        const data = await response.json()
        console.log('Demo reset:', data)
        // Refresh demo status
        const statusResponse = await fetch('/api/v1/demo/status')
        if (statusResponse.ok) {
          setDemoStatus(await statusResponse.json())
        }
      } else {
        const error = await response.json()
        alert(`Failed to reset demo: ${error.detail || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Failed to reset demo:', err)
      alert('Failed to reset demo. Check console for details.')
    } finally {
      setDemoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border">
        {/* Logo */}
        <div className="flex items-center gap-2 px-6 py-4 border-b border-border">
          <Shield className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-lg font-bold">Constitutional</h1>
            <p className="text-xs text-muted-foreground">AIOps</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Demo Mode + Status */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border space-y-3">
          {/* Demo Mode Controls */}
          <div className="p-2 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium">Demo Mode</span>
              {demoStatus?.active && (
                <span className="text-xs text-orange-500 animate-pulse">Active</span>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleStartDemo}
                disabled={demoLoading || demoStatus?.active}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded',
                  'bg-green-600 text-white hover:bg-green-700',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {demoLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
                Start
              </button>
              <button
                onClick={handleResetDemo}
                disabled={demoLoading}
                className={cn(
                  'flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded',
                  'bg-orange-600 text-white hover:bg-orange-700',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {demoLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RotateCcw className="h-3 w-3" />
                )}
                Reset
              </button>
            </div>
            {demoStatus?.active && demoStatus.anomalies_triggered > 0 && (
              <div className="mt-2 text-xs text-muted-foreground">
                {demoStatus.anomalies_triggered} anomalies triggered
              </div>
            )}
          </div>

          {/* System Health Status */}
          <div className="flex items-center gap-2 text-sm">
            <Activity className={cn('h-4 w-4', systemHealthy ? 'text-green-500' : 'text-red-500')} />
            <span className="text-muted-foreground">
              {health === null ? 'Checking...' : systemHealthy ? 'System Healthy' : 'System Degraded'}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            Fast Agent: <span className={fastAgentOnline ? 'text-green-500' : 'text-red-500'}>●</span>
            {fastAgentOnline ? ' Online' : ' Offline'}<br />
            Reasoning Agent: <span className={reasoningAgentOnline ? 'text-green-500' : 'text-red-500'}>●</span>
            {reasoningAgentOnline ? ' Online' : ' Offline'}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
