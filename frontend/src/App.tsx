import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Landing } from './pages/Landing'
import { Dashboard } from './pages/Dashboard'
import { Agents } from './pages/Agents'
import { Infrastructure } from './pages/Infrastructure'
import { Incidents } from './pages/Incidents'
import { Chat } from './pages/Chat'
import { Metrics } from './pages/Metrics'
import { Benchmark } from './pages/Benchmark'
import { Settings } from './pages/Settings'

function App() {
  return (
    <Routes>
      {/* Public landing page rendered OUTSIDE the sidebar Layout */}
      <Route path="/welcome" element={<Landing />} />
      {/* Everything else lives inside the authed app shell */}
      <Route
        path="*"
        element={
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/infrastructure" element={<Infrastructure />} />
              <Route path="/incidents" element={<Incidents />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/metrics" element={<Metrics />} />
              <Route path="/benchmark" element={<Benchmark />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        }
      />
    </Routes>
  )
}

export default App
