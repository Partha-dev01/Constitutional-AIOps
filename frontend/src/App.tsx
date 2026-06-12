import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import { Landing } from './pages/Landing'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Agents } from './pages/Agents'
import { Infrastructure } from './pages/Infrastructure'
import { Incidents } from './pages/Incidents'
import { Chat } from './pages/Chat'
import { Metrics } from './pages/Metrics'
import { Benchmark } from './pages/Benchmark'
import { Settings } from './pages/Settings'
import { useAuthStore } from './lib/auth'

/**
 * Public root gate: logged-out visitors (with enforcement on) see the public
 * Landing page at /; everyone else (signed in, or enforcement off) gets the
 * Dashboard inside the app shell. Renders nothing until the auth store has
 * bootstrapped so the wrong variant never flashes.
 */
function RootGate() {
  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const status = useAuthStore((s) => s.status)

  if (status !== 'ready') return null
  if (authRequired && !user) return <Landing />
  return (
    <Layout>
      <Dashboard />
    </Layout>
  )
}

function App() {
  const bootstrap = useAuthStore((s) => s.bootstrap)

  // Establish auth state once at mount (config + session probe).
  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  return (
    <Routes>
      {/* Public login page rendered OUTSIDE the sidebar Layout */}
      <Route path="/login" element={<Login />} />
      {/* The landing page moved to the public root */}
      <Route path="/welcome" element={<Navigate to="/" replace />} />
      {/* Public root: Landing (logged out, enforcement on) or Dashboard */}
      <Route path="/" element={<RootGate />} />
      {/* Everything else lives inside the authed app shell */}
      <Route
        path="*"
        element={
          <RequireAuth>
            <Layout>
              <Routes>
                <Route path="/agents" element={<Agents />} />
                <Route path="/infrastructure" element={<Infrastructure />} />
                <Route path="/incidents" element={<Incidents />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/metrics" element={<Metrics />} />
                <Route path="/benchmark" element={<Benchmark />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </RequireAuth>
        }
      />
    </Routes>
  )
}

export default App
