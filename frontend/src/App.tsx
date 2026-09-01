import { lazy, Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import { ErrorBoundary } from './components/ErrorBoundary'
// First-paint-critical pages — kept eager
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { Dashboard } from './pages/Dashboard'
import { useAuthStore } from './lib/auth'
import { DEMO_MODE } from './lib/demo/flag'

// Heavy pages — code-split so they don't bloat the initial bundle
const Console = lazy(() => import('./pages/Console').then((m) => ({ default: m.Console })))
const Agents = lazy(() => import('./pages/Agents').then((m) => ({ default: m.Agents })))
const Mcp = lazy(() => import('./pages/Mcp').then((m) => ({ default: m.Mcp })))
const Telemetry = lazy(() =>
  import('./pages/Telemetry').then((m) => ({ default: m.Telemetry })),
)
const Graph = lazy(() => import('./pages/Graph').then((m) => ({ default: m.Graph })))
const Infrastructure = lazy(() =>
  import('./pages/Infrastructure').then((m) => ({ default: m.Infrastructure })),
)
const Incidents = lazy(() =>
  import('./pages/Incidents').then((m) => ({ default: m.Incidents })),
)
const Chat = lazy(() => import('./pages/Chat').then((m) => ({ default: m.Chat })))
const Metrics = lazy(() => import('./pages/Metrics').then((m) => ({ default: m.Metrics })))
const Benchmark = lazy(() =>
  import('./pages/Benchmark').then((m) => ({ default: m.Benchmark })),
)
const Settings = lazy(() =>
  import('./pages/Settings').then((m) => ({ default: m.Settings })),
)
const Setup = lazy(() => import('./pages/Setup').then((m) => ({ default: m.Setup })))

/** On-theme loading fallback for lazy-loaded route chunks */
function PageFallback() {
  return (
    <div className="flex items-center justify-center h-full min-h-[40dvh]">
      <Loader2 className="h-8 w-8 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
      <span className="sr-only">Loading page…</span>
    </div>
  )
}

/**
 * Public root gate: logged-out visitors (with enforcement on) are sent to the
 * login page; everyone else (signed in, or enforcement off) gets the Dashboard
 * inside the app shell. Renders nothing until the auth store has bootstrapped so
 * the wrong variant never flashes.
 *
 * The branded marketing landing was moved OUT of the app into the standalone
 * front-door `marketing/` site (served serverlessly), so the self-hostable app
 * ships no marketing. Our hosted instance runs this exact same vanilla app.
 */
function RootGate() {
  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const status = useAuthStore((s) => s.status)

  if (status !== 'ready') return null
  if (authRequired && !user) return <Navigate to="/login" replace />
  return (
    <Layout>
      <Dashboard />
    </Layout>
  )
}

/**
 * Persistent "you're in the demo" affordance, rendered only in a DEMO_MODE
 * build. The demo is hosted at <origin>/demo/ alongside the marketing site at
 * <origin>/, so a plain anchor to the landing URL (default: the site root)
 * escapes the /demo/ app entirely — the way out the fixtures cannot provide.
 * Guarded by the compile-time DEMO_MODE constant so it costs the normal build
 * nothing.
 */
function DemoBanner() {
  const landing = (import.meta.env.VITE_LANDING_URL as string | undefined) || '/'
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex justify-center px-4">
      <div className="pointer-events-auto flex items-center gap-3 rounded-full border border-primary/30 bg-card/95 px-4 py-2 text-sm shadow-lg backdrop-blur">
        <span className="inline-flex items-center gap-1.5 font-medium">
          <span className="h-2 w-2 rounded-full bg-primary motion-safe:animate-pulse" aria-hidden="true" />
          Demo mode
        </span>
        <span className="hidden text-muted-foreground sm:inline">Sample data, no login.</span>
        <a
          href={landing}
          className="inline-flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Exit demo
        </a>
      </div>
    </div>
  )
}

function App() {
  const bootstrap = useAuthStore((s) => s.bootstrap)
  const location = useLocation()

  // Establish auth state once at mount (config + session probe).
  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  return (
    // Outer boundary: last-resort net for crashes in the shell itself
    // (Layout, RootGate, login) so the user always gets a recovery card.
    <ErrorBoundary>
      {DEMO_MODE && <DemoBanner />}
      <Routes>
        {/* Public login page rendered OUTSIDE the sidebar Layout */}
        <Route path="/login" element={<Login />} />
        {/* Public self-service signup (hosted demo; redirects away when disabled) */}
        <Route path="/signup" element={<Signup />} />
        {/* Legacy path: redirect to the root (which sends logged-out users to login) */}
        <Route path="/welcome" element={<Navigate to="/" replace />} />
        {/* Public root: Landing (logged out, enforcement on) or Dashboard */}
        <Route path="/" element={<RootGate />} />
        {/* First-run Quick-Setup wizard: full-screen, OUTSIDE the sidebar shell,
            but still auth-gated. A specific path outranks the "*" splat below. */}
        <Route
          path="/setup"
          element={
            <RequireAuth>
              <Suspense fallback={<PageFallback />}>
                <Setup />
              </Suspense>
            </RequireAuth>
          }
        />
        {/* Everything else lives inside the authed app shell */}
        <Route
          path="*"
          element={
            <RequireAuth>
              <Layout>
                {/* Inner boundary keyed by route: a content-page crash shows
                    the fallback in the content area WITHOUT killing the
                    sidebar/shell, and navigating away resets the error. */}
                <ErrorBoundary resetKey={location.pathname}>
                  <Suspense fallback={<PageFallback />}>
                    <Routes>
                      <Route path="/console" element={<Console />} />
                      <Route path="/agents" element={<Agents />} />
                      <Route path="/mcp" element={<Mcp />} />
                      <Route path="/telemetry" element={<Telemetry />} />
                      <Route path="/graph" element={<Graph />} />
                      <Route path="/infrastructure" element={<Infrastructure />} />
                      <Route path="/incidents" element={<Incidents />} />
                      <Route path="/chat" element={<Chat />} />
                      <Route path="/metrics" element={<Metrics />} />
                      <Route path="/benchmark" element={<Benchmark />} />
                      <Route path="/settings" element={<Settings />} />
                    </Routes>
                  </Suspense>
                </ErrorBoundary>
              </Layout>
            </RequireAuth>
          }
        />
      </Routes>
    </ErrorBoundary>
  )
}

export default App
