import { ReactNode, useState, useEffect, useCallback } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
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
  LogOut,
  Server,
  LayoutPanelLeft,
  UserCircle2,
  Menu,
  PanelLeftClose,
  Wrench,
  Network,
  GitBranch,
} from 'lucide-react'
import { cn } from '../lib/utils'
import api, { HealthResponse, isComponentHealthy } from '../lib/api'
import { useAuthStore } from '../lib/auth'
import { useMediaQuery } from '../hooks/useMediaQuery'

interface LayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Command Center', href: '/console', icon: LayoutPanelLeft },
  { name: 'Agents', href: '/agents', icon: Cpu },
  { name: 'MCP Tools', href: '/mcp', icon: Wrench },
  { name: 'Telemetry', href: '/telemetry', icon: Network },
  { name: 'Graph', href: '/graph', icon: GitBranch },
  { name: 'Infrastructure', href: '/infrastructure', icon: Server },
  { name: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Metrics', href: '/metrics', icon: BarChart3 },
  { name: 'Benchmark', href: '/benchmark', icon: FlaskConical },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const SIDEBAR_COLLAPSED_KEY = 'aiops.sidebar.collapsed'

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const navigate = useNavigate()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const logout = useAuthStore((s) => s.logout)

  // ≥ md (768px) → static column (full or icon-rail). < md → off-canvas drawer.
  const isDesktop = useMediaQuery('(min-width: 768px)')

  // Desktop: full(w-64) ↔ icon-rail(w-16), persisted in localStorage.
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false
    return window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === 'true'
  })

  // Mobile: drawer open/closed.
  const [mobileOpen, setMobileOpen] = useState(false)

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev
      try {
        window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next))
      } catch {
        // Ignore storage failures (private mode / disabled) — state still works.
      }
      return next
    })
  }, [])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  // Auto-close the mobile drawer when we cross up to desktop.
  useEffect(() => {
    if (isDesktop) setMobileOpen(false)
  }, [isDesktop])

  // Esc closes the mobile drawer.
  useEffect(() => {
    if (!mobileOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [mobileOpen])

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

  // Icon-rail (label-less) layout applies only when collapsed on desktop. On
  // mobile the drawer always shows full labels regardless of `collapsed`.
  const isRail = isDesktop && collapsed

  const healthLabel =
    health === null ? 'Checking...' : systemHealthy ? 'System Healthy' : 'System Degraded'

  const sidebar = (
    <nav
      data-testid="app-sidebar"
      className={cn(
        'flex h-full flex-col border-r border-border bg-card',
        isRail ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo + desktop collapse toggle */}
      <div
        className={cn(
          'flex items-center border-b border-border px-3 py-4',
          isRail ? 'justify-center' : 'justify-between gap-2 px-6'
        )}
      >
        {isRail ? (
          /* Rail mode: the Shield itself is the single centered expand control. */
          <button
            type="button"
            data-testid="sidebar-toggle"
            onClick={toggleCollapsed}
            aria-label="Expand sidebar"
            aria-expanded={false}
            title="Expand sidebar"
            className="flex items-center justify-center rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            <Shield className="h-7 w-7 text-primary" aria-hidden="true" />
          </button>
        ) : (
          <>
            <div className="flex min-w-0 items-center gap-2">
              <Shield className="h-8 w-8 shrink-0 text-primary" aria-hidden="true" />
              <div className="min-w-0">
                <h1 className="truncate text-lg font-bold">Constitutional</h1>
                <p className="text-xs text-muted-foreground">AIOps</p>
              </div>
            </div>
            {/* Desktop collapse toggle — hidden on mobile (drawer uses its own). */}
            <button
              type="button"
              data-testid="sidebar-toggle"
              onClick={toggleCollapsed}
              aria-label="Collapse sidebar"
              aria-expanded={true}
              title="Collapse sidebar"
              className="hidden shrink-0 items-center justify-center rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 md:inline-flex"
            >
              <PanelLeftClose className="h-5 w-5" aria-hidden="true" />
            </button>
          </>
        )}
      </div>

      {/* Navigation */}
      <div className="flex-1 space-y-1 overflow-y-auto p-3">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={() => setMobileOpen(false)}
              title={isRail ? item.name : undefined}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isRail && 'justify-center',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
              {!isRail && <span className="truncate">{item.name}</span>}
            </Link>
          )
        })}
      </div>

      {/* System Health Status + identity */}
      <div
        className={cn(
          'space-y-3 border-t border-border p-3',
          isRail && 'flex flex-col items-center space-y-2'
        )}
      >
        {/* Signed-in identity + logout (only meaningful once auth is enforced) */}
        {authRequired && user && (
          isRail ? (
            <button
              type="button"
              onClick={() => { void handleLogout() }}
              title={`Signed in as ${user.username} — log out`}
              aria-label={`Signed in as ${user.username}. Log out`}
              className="flex items-center justify-center rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
            </button>
          ) : (
            <div className="flex items-center justify-between gap-2 text-sm">
              <span
                className="flex min-w-0 items-center gap-2 text-muted-foreground"
                title={`Signed in as ${user.username}`}
              >
                <UserCircle2 className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                <span className="truncate">{user.username}</span>
              </span>
              <button
                type="button"
                onClick={() => { void handleLogout() }}
                className="flex shrink-0 items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                Logout
              </button>
            </div>
          )
        )}

        {isRail ? (
          <span
            title={`${healthLabel} — Fast Agent ${fastAgentOnline ? 'online' : 'offline'}, Reasoning Agent ${reasoningAgentOnline ? 'online' : 'offline'}`}
            aria-label={healthLabel}
          >
            <Activity className={cn('h-5 w-5', systemHealthy ? 'text-green-500' : 'text-red-500')} aria-hidden="true" />
          </span>
        ) : (
          <>
            <div className="flex items-center gap-2 text-sm">
              <Activity className={cn('h-4 w-4', systemHealthy ? 'text-green-500' : 'text-red-500')} aria-hidden="true" />
              <span className="text-muted-foreground">{healthLabel}</span>
            </div>
            <div className="text-xs text-muted-foreground">
              Fast Agent: <span className={fastAgentOnline ? 'text-green-500' : 'text-red-500'}>●</span>
              {fastAgentOnline ? ' Online' : ' Offline'}<br />
              Reasoning Agent: <span className={reasoningAgentOnline ? 'text-green-500' : 'text-red-500'}>●</span>
              {reasoningAgentOnline ? ' Online' : ' Offline'}
            </div>
          </>
        )}
      </div>
    </nav>
  )

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-background">
      {/* Desktop: static column (full or icon-rail). Hidden on mobile. */}
      <div className="hidden shrink-0 md:block">{sidebar}</div>

      {/* Mobile: off-canvas drawer + dim backdrop. */}
      <div className="md:hidden">
        {mobileOpen && (
          <div
            data-testid="sidebar-backdrop"
            onClick={() => setMobileOpen(false)}
            className="fixed inset-0 z-40 bg-black/50"
            aria-hidden="true"
          />
        )}
        <div
          className={cn(
            'fixed inset-y-0 left-0 z-50 motion-safe:transition-transform motion-safe:duration-200 motion-safe:ease-in-out',
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          {sidebar}
        </div>
      </div>

      {/* Content column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile top bar — md:hidden only. */}
        <div className="flex h-12 shrink-0 items-center gap-2 border-b border-border bg-card px-3 md:hidden">
          <button
            type="button"
            data-testid="mobile-nav-toggle"
            onClick={() => setMobileOpen((prev) => !prev)}
            aria-label={mobileOpen ? 'Close navigation' : 'Open navigation'}
            aria-expanded={mobileOpen}
            className="flex items-center justify-center rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <Shield className="h-6 w-6 shrink-0 text-primary" aria-hidden="true" />
          <span className="truncate text-sm font-semibold">Constitutional AIOps</span>
        </div>

        <main className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6 sm:py-6">
          {children}
        </main>
      </div>
    </div>
  )
}
