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
  BarChart3,
  FlaskConical,
  Server
} from 'lucide-react'
import { cn } from '../lib/utils'
import api, { HealthResponse, isComponentHealthy } from '../lib/api'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Agents', href: '/agents', icon: Cpu },
  { name: 'Infrastructure', href: '/infrastructure', icon: Server },
  { name: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  { name: 'Benchmark', href: '/benchmark', icon: FlaskConical },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [health, setHealth] = useState<HealthResponse | null>(null)

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

  const fastAgentOnline = isComponentHealthy(health, 'fast_agent')
  const reasoningAgentOnline = isComponentHealthy(health, 'reasoning_agent')
  const systemHealthy = fastAgentOnline && reasoningAgentOnline

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

        {/* System Health Status */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border space-y-3">
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
