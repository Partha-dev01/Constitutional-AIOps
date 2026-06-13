import { useState, useEffect, lazy, Suspense } from 'react'
import {
  Cpu,
  Zap,
  Brain,
  Network,
  GitBranch,
  Waypoints,
  Wrench,
  RefreshCw,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Activity,
  FileText,
  Search,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import api, { HealthResponse, isComponentHealthy } from '../lib/api'
import { EpisodicGraphExplorer, EpisodicNode, EpisodicLink } from '../components/EpisodicGraphExplorer'
import { JsonView } from '../components/JsonView'
import { McpToolList } from '../components/mcp/McpToolList'
import { McpExecutePanel } from '../components/mcp/McpExecutePanel'
import type { McpToolInfo } from '../components/mcp/types'
import { ActiveIncidentsPanel } from '../components/incidents/ActiveIncidentsPanel'

// The interactive Platform Architecture (schema) graph is lazy-loaded so the
// main bundle chunk doesn't grow; it is only fetched when the Architecture tab
// is opened. The Neo4j episodic Graph Explorer is its own separate tab.
const SchemaGraph = lazy(() => import('../components/schema/SchemaGraph'))

// Tab type
type AgentTab = 'fast' | 'reasoning' | 'telemetry' | 'graph' | 'architecture' | 'tools'

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

// Telemetry data types
interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  service: string
  message: string
}

interface MetricPoint {
  timestamp: string
  value: number
  label: string
}

export function Agents() {
  const [activeTab, setActiveTab] = useState<AgentTab>('architecture')
  const [health, setHealth] = useState<HealthResponse | null>(null)

  // Fast Agent state
  const [fastActivity, setFastActivity] = useState<AgentActivity[]>([])
  const [fastLoading, setFastLoading] = useState(false)

  // Reasoning Agent state
  const [reasoningActivity, setReasoningActivity] = useState<AgentActivity[]>([])
  const [reasoningLoading, setReasoningLoading] = useState(false)

  // Telemetry state
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [metrics, setMetrics] = useState<MetricPoint[]>([])
  const [telemetryLoading, setTelemetryLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')

  // Graph state - using EpisodicNode/EpisodicLink for force-directed graph
  const [graphNodes, setGraphNodes] = useState<EpisodicNode[]>([])
  const [graphEdges, setGraphEdges] = useState<EpisodicLink[]>([])
  const [graphLoading, setGraphLoading] = useState(false)
  // Note: selectedNode is tracked internally by EpisodicGraphExplorer component
  const [_selectedNode, setSelectedNode] = useState<EpisodicNode | null>(null)

  // MCP Tools state
  const [tools, setTools] = useState<McpToolInfo[]>([])
  const [toolsLoading, setToolsLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState<McpToolInfo | null>(null)

  // Activity row expansion (Fast + Reasoning tabs share this set, keyed by activity.id)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const toggleExpanded = (id: string) => setExpandedIds(prev => {
    const n = new Set(prev)
    n.has(id) ? n.delete(id) : n.add(id)
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
    { id: 'architecture' as const, label: 'Architecture', icon: Waypoints, description: 'Live platform topology' },
    { id: 'tools' as const, label: 'MCP Tools', icon: Wrench, description: 'Tool Configuration' },
    { id: 'fast' as const, label: 'Fast Agent', icon: Zap, description: 'Telemetry annotation' },
    { id: 'reasoning' as const, label: 'Reasoning Agent', icon: Brain, description: 'RCA & Planning' },
    { id: 'telemetry' as const, label: 'Telemetry', icon: Network, description: 'Logs/Metrics/Traces' },
    { id: 'graph' as const, label: 'Graph Explorer', icon: GitBranch, description: 'Neo4j Episodes' },
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

  // Fetch tab-specific data when tab changes
  useEffect(() => {
    switch (activeTab) {
      case 'fast':
        fetchFastActivity()
        break
      case 'reasoning':
        fetchReasoningActivity()
        break
      case 'telemetry':
        fetchTelemetry()
        break
      case 'graph':
        fetchGraphData()
        break
      case 'tools':
        fetchTools()
        break
    }
  }, [activeTab])

  // Auto-refresh the Neo4j episodic graph every 30s while its tab is active
  // (matches Fast Agent interval). The Architecture tab owns its own fetching.
  useEffect(() => {
    if (activeTab !== 'graph') return
    const interval = setInterval(() => {
      fetchGraphData()
    }, 30000) // 30 seconds - matches background processor interval
    return () => clearInterval(interval)
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

  const fetchTelemetry = async () => {
    setTelemetryLoading(true)
    try {
      const [logsRes, metricsRes] = await Promise.all([
        fetch('/api/v1/telemetry/logs?limit=50'),
        fetch('/api/v1/telemetry/metrics?range=1h'),
      ])
      if (logsRes.ok) {
        const data = await logsRes.json()
        setLogs(data.logs || [])
      }
      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data.metrics || [])
      }
    } catch (err) {
      console.error('Failed to fetch telemetry:', err)
      setLogs([])
      setMetrics([])
    } finally {
      setTelemetryLoading(false)
    }
  }

  const fetchGraphData = async () => {
    setGraphLoading(true)
    try {
      const response = await fetch('/api/v1/graph/episodes?limit=50')
      if (response.ok) {
        const data = await response.json()
        // Transform new EpisodicGraphData format to EpisodicNode/EpisodicLink for force-directed graph
        const nodes: EpisodicNode[] = []
        const links: EpisodicLink[] = []

        // Process Episodes - main nodes showing incidents
        if (data.episodes) {
          data.episodes.forEach((ep: {
            id: string;
            title: string;
            type?: string;
            timestamp?: string;
            category?: string;
            severity?: string;
            status?: string;
            root_cause?: string;
            confidence?: number;
            resolution_time_minutes?: number;
            services?: string[];
            successful_actions?: string[];
          }) => {
            nodes.push({
              id: `episode-${ep.id}`,
              label: ep.title,
              type: 'episode',
              status: ep.status === 'resolved' ? 'resolved' :
                     ep.severity === 'critical' ? 'critical' :
                     ep.severity === 'high' ? 'warning' : 'detected',
              timestamp: ep.timestamp,
              severity: ep.severity,
              confidence: ep.confidence,
              category: ep.category,
              rootCause: ep.root_cause,
              resolutionTime: ep.resolution_time_minutes,
            })
          })
        }

        // Process Root Causes - semantic abstractions of failure patterns
        if (data.root_causes) {
          data.root_causes.forEach((rc: {
            id: string;
            name: string;
            type?: string;
            frequency?: number;
            avg_resolution_time_minutes?: number;
            success_rate?: number;
          }) => {
            nodes.push({
              id: rc.id,
              label: rc.name.replace(/_/g, ' '),
              type: 'root_cause',
              status: rc.success_rate && rc.success_rate >= 0.9 ? 'healthy' :
                     rc.success_rate && rc.success_rate >= 0.7 ? 'warning' : 'critical',
              frequency: rc.frequency,
              avgResolutionTime: rc.avg_resolution_time_minutes,
              successRate: rc.success_rate,
            })
          })
        }

        // Process Actions - remediation patterns
        if (data.actions) {
          data.actions.forEach((action: {
            id: string;
            name: string;
            type?: string;
            used_count?: number;
            success_rate?: number;
            avg_execution_time_seconds?: number;
          }) => {
            nodes.push({
              id: action.id,
              label: action.name,
              type: 'action',
              status: action.success_rate && action.success_rate >= 0.9 ? 'healthy' :
                     action.success_rate && action.success_rate >= 0.7 ? 'warning' : 'critical',
              usedCount: action.used_count,
              successRate: action.success_rate,
              avgExecutionTime: action.avg_execution_time_seconds,
            })
          })
        }

        // Process Services - only those affected by episodes
        if (data.services) {
          data.services.forEach((s: {
            name: string;
            type?: string;
            status?: string;
            incident_count?: number;
            last_incident?: string;
          }) => {
            nodes.push({
              id: `service-${s.name}`,
              label: s.name,
              type: 'service',
              status: (s.status || 'healthy') as 'healthy' | 'warning' | 'critical',
              incidentCount: s.incident_count,
              lastIncident: s.last_incident,
            })
          })
        }

        // Process Edges - relationships between nodes
        if (data.edges) {
          data.edges.forEach((edge: {
            source: string;
            target: string;
            relationship: string;
            weight?: number;
            metadata?: Record<string, unknown>;
          }) => {
            // Map relationship to edge type
            const edgeType = edge.relationship as 'depends_on' | 'affects' | 'caused_by' | 'resolved_by' | 'similar_to'

            links.push({
              source: edge.source,
              target: edge.target,
              label: edge.relationship.replace(/_/g, ' '),
              type: edgeType,
              weight: edge.weight,
            })
          })
        }

        // Merge by id to preserve node identity (and d3-assigned x/y/vx/vy)
        // across refetch, so the force simulation does not reheat from random.
        setGraphNodes(prev => {
          const byId = new Map(prev.map(n => [n.id, n]))
          return nodes.map(n => {
            const old = byId.get(n.id)
            return old ? Object.assign(old, n) : n
          })
        })

        // Reuse the previous edge array reference when the edge key-set is
        // unchanged, so EpisodicGraphExplorer's memoized links stay stable.
        setGraphEdges(prev => {
          const keyOf = (l: EpisodicLink) =>
            `${typeof l.source === 'string' ? l.source : (l.source as { id: string }).id}|${typeof l.target === 'string' ? l.target : (l.target as { id: string }).id}|${l.type}`
          const prevKeys = new Set(prev.map(keyOf))
          const nextKeys = new Set(links.map(keyOf))
          const same = prevKeys.size === nextKeys.size && [...nextKeys].every(k => prevKeys.has(k))
          return same ? prev : links
        })

        // Log stats for debugging
        if (data.stats) {
          console.log('Episodic Graph Stats:', data.stats)
        }
      } else {
        setGraphNodes([])
        setGraphEdges([])
      }
    } catch (err) {
      console.error('Failed to fetch graph data:', err)
      setGraphNodes([])
      setGraphEdges([])
    } finally {
      setGraphLoading(false)
    }
  }

  const fetchTools = async () => {
    setToolsLoading(true)
    try {
      const response = await fetch('/api/v1/tools/')
      if (response.ok) {
        const data = await response.json()
        setTools(data.tools || [])
      } else {
        setTools([])
      }
    } catch (err) {
      console.error('Failed to fetch tools:', err)
      setTools([])
    } finally {
      setToolsLoading(false)
    }
  }

  const fastAgentOnline = isComponentHealthy(health, 'fast_agent')
  const reasoningAgentOnline = isComponentHealthy(health, 'reasoning_agent')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
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

      {/* Tab Navigation */}
      <div className="flex gap-1 p-1 bg-muted rounded-lg overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {/* Fast Agent Tab */}
        {activeTab === 'fast' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
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
                    <h3 className="font-semibold">Qwen3-4B-AWQ</h3>
                    <p className="text-sm text-muted-foreground">Port 8000 • Context: 4K tokens</p>
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
                    <div
                      key={activity.id}
                      onClick={() => toggleExpanded(activity.id)}
                      className="p-4 hover:bg-muted/50 cursor-pointer"
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
                    </div>
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
        )}

        {/* Reasoning Agent Tab */}
        {activeTab === 'reasoning' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
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
                    <h3 className="font-semibold">Qwen3-14B-AWQ</h3>
                    <p className="text-sm text-muted-foreground">Port 8001 • Context: 8K tokens</p>
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
                    <div
                      key={activity.id}
                      onClick={() => toggleExpanded(activity.id)}
                      className="p-4 hover:bg-muted/50 cursor-pointer"
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
                    </div>
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
        )}

        {/* Telemetry Tab */}
        {activeTab === 'telemetry' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Network className="h-5 w-5 text-blue-500" />
                  Telemetry Viewer
                </h2>
                <p className="text-sm text-muted-foreground">
                  Logs, metrics, and traces from LGTM stack
                </p>
              </div>
              <button
                onClick={fetchTelemetry}
                disabled={telemetryLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
              >
                {telemetryLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Refresh
              </button>
            </div>

            {/* Log Level Filter */}
            <div className="flex gap-2">
              {['all', 'ERROR', 'WARN', 'INFO', 'DEBUG'].map((level) => (
                <button
                  key={level}
                  onClick={() => setLogFilter(level)}
                  className={`px-3 py-1 rounded-lg text-sm ${
                    logFilter === level
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>

            {/* Logs Table */}
            <div className="bg-card rounded-lg border border-border">
              <div className="p-4 border-b border-border flex items-center justify-between">
                <h3 className="font-semibold flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Recent Logs
                </h3>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Filter logs..."
                    className="pl-9 pr-3 py-1.5 text-sm rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
              <div className="divide-y divide-border max-h-[400px] overflow-y-auto font-mono text-sm">
                {telemetryLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : logs.length > 0 ? (
                  logs
                    .filter((log) => logFilter === 'all' || log.level === logFilter)
                    .map((log, i) => (
                      <div key={i} className="p-3 hover:bg-muted/50 flex items-start gap-3">
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                          log.level === 'ERROR' ? 'bg-red-500/10 text-red-500' :
                          log.level === 'WARN' ? 'bg-yellow-500/10 text-yellow-500' :
                          log.level === 'INFO' ? 'bg-blue-500/10 text-blue-500' :
                          'bg-gray-500/10 text-gray-500'
                        }`}>
                          {log.level}
                        </span>
                        <span className="text-muted-foreground">[{log.service}]</span>
                        <span className="flex-1">{log.message}</span>
                      </div>
                    ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <FileText className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No logs available</p>
                    <p className="text-xs mt-1">Configure Loki endpoint in Settings</p>
                  </div>
                )}
              </div>
            </div>

            {/* Metrics Summary */}
            <div className="bg-card rounded-lg border border-border p-4">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Metrics Summary
              </h3>
              {metrics.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {metrics.slice(0, 4).map((metric, i) => (
                    <div key={i} className="p-3 bg-muted/50 rounded-lg text-center">
                      <p className="text-2xl font-bold">{metric.value.toFixed(1)}</p>
                      <p className="text-xs text-muted-foreground">{metric.label}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <p className="text-sm">No metrics available</p>
                  <p className="text-xs mt-1">Configure Prometheus endpoint in Settings</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Graph Explorer Tab */}
        {activeTab === 'graph' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <GitBranch className="h-5 w-5 text-cyan-500" />
                  Graph Explorer
                </h2>
                <p className="text-sm text-muted-foreground">
                  Neo4j episodic memory and service dependencies
                </p>
              </div>
              <button
                onClick={fetchGraphData}
                disabled={graphLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
              >
                {graphLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Refresh
              </button>
            </div>

            {/* Episodic Knowledge Graph (Neo4j). The interactive Platform
                Architecture graph lives in its own Architecture tab. */}
            <div className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Episodic Knowledge Graph</h3>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${isComponentHealthy(health, 'neo4j') ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'}`}
                  title={isComponentHealthy(health, 'neo4j') ? 'Connected to Neo4j' : 'Using in-memory fallback'}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${isComponentHealthy(health, 'neo4j') ? 'bg-green-500' : 'bg-yellow-500'}`} />
                  Neo4j • {isComponentHealthy(health, 'neo4j') ? 'Connected' : 'Fallback'}
                </span>
              </div>

              {graphNodes.length > 0 ? (
                <EpisodicGraphExplorer
                  nodes={graphNodes}
                  links={graphEdges}
                  loading={graphLoading}
                  onNodeClick={(node) => setSelectedNode(node)}
                  onRefresh={fetchGraphData}
                  height={520}
                />
              ) : graphLoading ? (
                <div className="flex items-center justify-center h-[520px] bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-lg">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="h-[520px] flex flex-col items-center justify-center text-muted-foreground bg-gradient-to-br from-slate-900/30 to-slate-800/30 rounded-lg">
                  <GitBranch className="h-12 w-12 mb-3 opacity-50" />
                  <p className="text-lg font-medium">No Graph Data Available</p>
                  <p className="text-sm mt-1 max-w-md text-center">
                    Start monitoring containers to build the episodic knowledge graph.
                    The graph will show service dependencies and incident relationships.
                  </p>
                  <button
                    onClick={fetchGraphData}
                    className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                  >
                    Load Graph Data
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Architecture Tab — interactive platform topology (schema graph) */}
        {activeTab === 'architecture' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Waypoints className="h-5 w-5 text-cyan-500" />
                  Architecture
                </h2>
                <p className="text-sm text-muted-foreground">
                  Live platform topology, health and episode evolution
                </p>
              </div>
            </div>

            {/* Active incidents — deal with them right here: approve & remediate
                (gated executor / t3 heal), reject, or open in chat. */}
            <ActiveIncidentsPanel />

            <div className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Platform Architecture</h3>
              </div>
              <Suspense
                fallback={
                  <div className="flex items-center justify-center h-[460px] bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-lg">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                }
              >
                <SchemaGraph height={460} />
              </Suspense>
            </div>
          </div>
        )}

        {/* MCP Tools Tab */}
        {activeTab === 'tools' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Wrench className="h-5 w-5 text-orange-500" />
                  MCP Tools
                </h2>
                <p className="text-sm text-muted-foreground">
                  Configure and execute infrastructure tools
                </p>
              </div>
              <button
                onClick={fetchTools}
                disabled={toolsLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
              >
                {toolsLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Refresh
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <McpToolList
                tools={tools}
                loading={toolsLoading}
                selectedTool={selectedTool}
                onSelect={setSelectedTool}
              />
              <McpExecutePanel tool={selectedTool} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
