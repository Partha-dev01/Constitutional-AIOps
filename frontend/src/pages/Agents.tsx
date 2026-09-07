import { useState, useEffect } from 'react'
import {
  Cpu,
  Zap,
  Brain,
  RefreshCw,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Activity,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import api, { HealthResponse, isComponentHealthy, ModelsConfig } from '../lib/api'
import { JsonView } from '../components/JsonView'
import { Tabs, TabPanel } from '../components/ui/Tabs'

/** Compact host:port (or the raw string) for honest endpoint display. */
function endpointLabel(url?: string): string {
  if (!url) return 'Not configured'
  try {
    const u = new URL(url)
    return u.port ? `${u.hostname}:${u.port}` : u.hostname
  } catch {
    return url
  }
}

// Tab type
type AgentTab = 'fast' | 'reasoning'

// Activity item type for agent activity streams
interface AgentActivity {
  id: string
  timestamp: Date
  type: 'annotation' | 'classification' | 'rca' | 'chat' | 'planning' | 'action'
  input: string
  output: string
  latency_ms: number
  model: string
  status: 'success' | 'error'
}

export function Agents() {
  const [activeTab, setActiveTab] = useState<AgentTab>('fast')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  // Real configured endpoints — no more hardcoded Qwen3/port/context claims.
  const [models, setModels] = useState<ModelsConfig | null>(null)

  // Fast Agent state
  const [fastActivity, setFastActivity] = useState<AgentActivity[]>([])
  const [fastLoading, setFastLoading] = useState(false)

  // Reasoning Agent state
  const [reasoningActivity, setReasoningActivity] = useState<AgentActivity[]>([])
  const [reasoningLoading, setReasoningLoading] = useState(false)

  // Activity row expansion (Fast + Reasoning tabs share this set, keyed by activity.id)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const toggleExpanded = (id: string) => setExpandedIds(prev => {
    const n = new Set(prev)
    if (n.has(id)) n.delete(id)
    else n.add(id)
    return n
  })

  // Derive a one-line collapsed summary from an activity's output, parsing safely.
  // Prefers structured fields when output is valid JSON; otherwise first ~120 chars.
  const outputSummary = (output: string): string => {
    const trimmed = output.trim()
    try {
      const parsed: unknown = JSON.parse(trimmed)
      if (parsed && typeof parsed === 'object') {
        const obj = parsed as Record<string, unknown>
        const pick = (key: string): string | null =>
          typeof obj[key] === 'string' && (obj[key] as string).trim() ? (obj[key] as string).trim() : null
        const summary =
          pick('summary') ??
          pick('root_cause') ??
          pick('plan_name') ??
          pick('reasoning')
        if (summary) return summary
        const severity = pick('severity')
        const category = pick('category')
        if (severity || category) return [severity, category].filter(Boolean).join(' / ')
      }
    } catch {
      // not JSON (truncated/invalid or plain string) — fall through to raw text
    }
    return trimmed.slice(0, 120)
  }

  const tabs = [
    { id: 'fast' as const, label: 'Fast Agent', icon: Zap, description: 'Telemetry annotation' },
    { id: 'reasoning' as const, label: 'Reasoning Agent', icon: Brain, description: 'RCA & Planning' },
  ]

  // Fetch health status
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await api.health.check()
        setHealth(data)
      } catch (err) {
        console.error('Health check failed:', err)
      }
    }
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  // Load the real endpoint config so the status cards show the configured model
  // + endpoint instead of a hardcoded dual-Qwen claim (honest on lite / BYO).
  useEffect(() => {
    let alive = true
    api.settings
      .getModels()
      .then((m) => { if (alive) setModels(m) })
      .catch(() => { /* endpoint config unavailable — cards fall back to labels */ })
    return () => { alive = false }
  }, [])

  // Fetch tab-specific data when tab changes
  useEffect(() => {
    switch (activeTab) {
      case 'fast':
        fetchFastActivity()
        break
      case 'reasoning':
        fetchReasoningActivity()
        break
    }
  }, [activeTab])

  const fetchFastActivity = async () => {
    setFastLoading(true)
    try {
      const response = await fetch('/api/v1/agents/fast/activity')
      if (response.ok) {
        const data = await response.json()
        setFastActivity(data.activities || [])
      } else {
        // No activity yet - show empty state
        setFastActivity([])
      }
    } catch (err) {
      console.error('Failed to fetch fast agent activity:', err)
      setFastActivity([])
    } finally {
      setFastLoading(false)
    }
  }

  const fetchReasoningActivity = async () => {
    setReasoningLoading(true)
    try {
      const response = await fetch('/api/v1/agents/reasoning/activity')
      if (response.ok) {
        const data = await response.json()
        setReasoningActivity(data.activities || [])
      } else {
        setReasoningActivity([])
      }
    } catch (err) {
      console.error('Failed to fetch reasoning agent activity:', err)
      setReasoningActivity([])
    } finally {
      setReasoningLoading(false)
    }
  }

  const fastAgentOnline = isComponentHealthy(health, 'fast_agent')
  const reasoningAgentOnline = isComponentHealthy(health, 'reasoning_agent')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Cpu className="h-6 w-6" />
            Agent Hub
          </h1>
          <p className="text-muted-foreground">
            Monitor and interact with AI agents
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${fastAgentOnline ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>Fast: {fastAgentOnline ? 'Online' : 'Offline'}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${reasoningAgentOnline ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>Reasoning: {reasoningAgentOnline ? 'Online' : 'Offline'}</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation — accessible tablist via shared Tabs primitive */}
      <Tabs
        value={activeTab}
        onChange={(id) => setActiveTab(id as AgentTab)}
        tabs={tabs}
        variant="pill"
      >

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {/* Fast Agent Tab */}
        <TabPanel id="fast" activeTab={activeTab}>
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Zap className="h-5 w-5 text-yellow-500" />
                  Fast Agent Activity
                </h2>
                <p className="text-sm text-muted-foreground">
                  Real-time telemetry annotation and classification
                </p>
              </div>
              <button
                onClick={fetchFastActivity}
                disabled={fastLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
              >
                {fastLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Refresh
              </button>
            </div>

            {/* Agent Status Card */}
            <div className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${fastAgentOnline ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                    <Cpu className={`h-5 w-5 ${fastAgentOnline ? 'text-green-500' : 'text-red-500'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold">{models?.fastAgentModel || 'Fast agent'}</h3>
                    <p className="text-sm text-muted-foreground">{endpointLabel(models?.fastAgentUrl)}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  fastAgentOnline ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                }`}>
                  {fastAgentOnline ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>

            {/* Activity Stream */}
            <div className="bg-card rounded-lg border border-border">
              <div className="p-4 border-b border-border">
                <h3 className="font-semibold">Recent Annotations</h3>
              </div>
              <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
                {fastLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : fastActivity.length > 0 ? (
                  fastActivity.map((activity) => (
                    <button
                      key={activity.id}
                      onClick={() => toggleExpanded(activity.id)}
                      aria-expanded={expandedIds.has(activity.id)}
                      className="w-full p-4 hover:bg-muted/50 text-left"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              activity.type === 'annotation' ? 'bg-blue-500/10 text-blue-500' :
                              activity.type === 'classification' ? 'bg-purple-500/10 text-purple-500' :
                              'bg-gray-500/10 text-gray-500'
                            }`}>
                              {activity.type}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(activity.timestamp).toLocaleTimeString()}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {activity.latency_ms}ms
                            </span>
                            {activity.model && (
                              <span
                                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                                title="Model that produced this"
                              >
                                {activity.model}
                              </span>
                            )}
                          </div>
                          {expandedIds.has(activity.id) ? (
                            <div className="mt-2 space-y-2">
                              <pre className="text-xs font-mono whitespace-pre-wrap break-words bg-muted/50 p-2 rounded">
                                {activity.input.trim()}
                              </pre>
                              <JsonView raw={activity.output} />
                            </div>
                          ) : (
                            <>
                              <p className="text-sm font-mono bg-muted/50 p-2 rounded mt-2 truncate">
                                {activity.input.trim().split('\n')[0].slice(0, 100)}
                              </p>
                              <p className="text-sm text-muted-foreground mt-2 truncate">
                                → {outputSummary(activity.output)}
                              </p>
                            </>
                          )}
                        </div>
                        <div className="flex items-center gap-2 ml-4 shrink-0">
                          <span className={
                            activity.status === 'success' ? 'text-green-500' : 'text-red-500'
                          }>
                            {activity.status === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                          </span>
                          {expandedIds.has(activity.id)
                            ? <ChevronUp className="h-4 w-4 text-muted-foreground" />
                            : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                        </div>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Activity className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No activity yet</p>
                    <p className="text-xs mt-1">Annotations will appear here as telemetry is processed</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </TabPanel>

        {/* Reasoning Agent Tab */}
        <TabPanel id="reasoning" activeTab={activeTab}>
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Brain className="h-5 w-5 text-purple-500" />
                  Reasoning Agent Activity
                </h2>
                <p className="text-sm text-muted-foreground">
                  Root cause analysis, planning, and chat sessions
                </p>
              </div>
              <button
                onClick={fetchReasoningActivity}
                disabled={reasoningLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
              >
                {reasoningLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Refresh
              </button>
            </div>

            {/* Agent Status Card */}
            <div className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${reasoningAgentOnline ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                    <Brain className={`h-5 w-5 ${reasoningAgentOnline ? 'text-green-500' : 'text-red-500'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold">{models?.reasoningAgentModel || 'Reasoning agent'}</h3>
                    <p className="text-sm text-muted-foreground">{endpointLabel(models?.reasoningAgentUrl)}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  reasoningAgentOnline ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                }`}>
                  {reasoningAgentOnline ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>

            {/* Activity Stream */}
            <div className="bg-card rounded-lg border border-border">
              <div className="p-4 border-b border-border">
                <h3 className="font-semibold">Recent RCA & Analysis</h3>
              </div>
              <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
                {reasoningLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : reasoningActivity.length > 0 ? (
                  reasoningActivity.map((activity) => (
                    <button
                      key={activity.id}
                      onClick={() => toggleExpanded(activity.id)}
                      aria-expanded={expandedIds.has(activity.id)}
                      className="w-full p-4 hover:bg-muted/50 text-left"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              activity.type === 'rca' ? 'bg-orange-500/10 text-orange-500' :
                              activity.type === 'chat' ? 'bg-blue-500/10 text-blue-500' :
                              activity.type === 'planning' ? 'bg-green-500/10 text-green-500' :
                              'bg-gray-500/10 text-gray-500'
                            }`}>
                              {activity.type.toUpperCase()}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(activity.timestamp).toLocaleTimeString()}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {activity.latency_ms}ms
                            </span>
                            {activity.model && (
                              <span
                                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                                title="Model that produced this"
                              >
                                {activity.model}
                              </span>
                            )}
                          </div>
                          {expandedIds.has(activity.id) ? (
                            <div className="mt-2 space-y-2">
                              <pre className="text-xs font-mono whitespace-pre-wrap break-words bg-muted/50 p-2 rounded">
                                {activity.input.trim()}
                              </pre>
                              <JsonView raw={activity.output} />
                            </div>
                          ) : (
                            <>
                              <p className="text-sm font-mono bg-muted/50 p-2 rounded mt-2 truncate">
                                {activity.input.trim().split('\n')[0].slice(0, 100)}
                              </p>
                              <p className="text-sm text-muted-foreground mt-2 truncate">
                                → {outputSummary(activity.output)}
                              </p>
                            </>
                          )}
                        </div>
                        <div className="flex items-center gap-2 ml-4 shrink-0">
                          <span className={
                            activity.status === 'success' ? 'text-green-500' : 'text-red-500'
                          }>
                            {activity.status === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                          </span>
                          {expandedIds.has(activity.id)
                            ? <ChevronUp className="h-4 w-4 text-muted-foreground" />
                            : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                        </div>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Brain className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No RCA activity yet</p>
                    <p className="text-xs mt-1">Analysis results will appear here as incidents are processed</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </TabPanel>
      </div>
      </Tabs>
    </div>
  )
}
