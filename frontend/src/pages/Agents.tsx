import { useState, useEffect } from 'react'
import {
  Cpu,
  Zap,
  Brain,
  Network,
  GitBranch,
  Wrench,
  RefreshCw,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Activity,
  FileText,
  AlertCircle,
  Search,
  Play,
  Server,
  Box,
  X,
} from 'lucide-react'
import api, { HealthResponse, isComponentHealthy } from '../lib/api'
import { EpisodicGraphExplorer, EpisodicNode, EpisodicLink } from '../components/EpisodicGraphExplorer'

// Tab type
type AgentTab = 'fast' | 'reasoning' | 'telemetry' | 'graph' | 'tools' | 'infrastructure'

// Container info type
interface ContainerInfo {
  name: string
  service: string
  status: string
  health: string | null
  port: string | null
  image: string | null
  description: string | null
  monitored: boolean
}

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

// MCP Tool type
interface MCPTool {
  name: string
  description: string
  parameters: { name: string; type: string; required: boolean; description: string }[]
  risk_level: 'low' | 'medium' | 'high'
}

export function Agents() {
  const [activeTab, setActiveTab] = useState<AgentTab>('fast')
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
  const [tools, setTools] = useState<MCPTool[]>([])
  const [toolsLoading, setToolsLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null)
  const [toolParams, setToolParams] = useState<Record<string, string>>({})
  const [toolExecuting, setToolExecuting] = useState(false)
  const [toolResult, setToolResult] = useState<string | null>(null)

  // Infrastructure state
  const [containers, setContainers] = useState<ContainerInfo[]>([])
  const [containersLoading, setContainersLoading] = useState(false)
  const [infrastructureStats, setInfrastructureStats] = useState<{ total: number; healthy: number; unhealthy: number } | null>(null)
  const [selectedContainers, setSelectedContainers] = useState<Set<string>>(new Set())
  const [monitoringStarting, setMonitoringStarting] = useState(false)

  const tabs = [
    { id: 'fast' as const, label: 'Fast Agent', icon: Zap, description: 'Telemetry annotation' },
    { id: 'reasoning' as const, label: 'Reasoning Agent', icon: Brain, description: 'RCA & Planning' },
    { id: 'telemetry' as const, label: 'Telemetry', icon: Network, description: 'Logs/Metrics/Traces' },
    { id: 'graph' as const, label: 'Graph Explorer', icon: GitBranch, description: 'Neo4j Episodes' },
    { id: 'tools' as const, label: 'MCP Tools', icon: Wrench, description: 'Tool Configuration' },
    { id: 'infrastructure' as const, label: 'Infrastructure', icon: Server, description: 'Docker Containers' },
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
      case 'infrastructure':
        fetchContainers()
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
        // Transform episodes to EpisodicNode/EpisodicLink for force-directed graph
        const nodes: EpisodicNode[] = []
        const links: EpisodicLink[] = []

        if (data.services) {
          data.services.forEach((s: { name: string; status: string; type?: string }) => {
            nodes.push({
              id: `service-${s.name}`,
              label: s.name,
              type: 'service',
              status: (s.status || 'healthy') as 'healthy' | 'warning' | 'critical',
            })
          })
        }

        if (data.episodes) {
          data.episodes.forEach((ep: {
            id: string;
            title: string;
            services: string[];
            timestamp?: string;
            severity?: string;
            confidence?: number;
          }) => {
            nodes.push({
              id: `episode-${ep.id}`,
              label: ep.title,
              type: 'episode',
              status: 'detected',
              timestamp: ep.timestamp,
              severity: ep.severity,
              confidence: ep.confidence,
            })
            // Episode affects services
            ep.services.forEach((svc: string) => {
              links.push({
                source: `episode-${ep.id}`,
                target: `service-${svc}`,
                label: 'affects',
                type: 'affects',
              })
            })
          })
        }

        // Process edges from backend (DEPENDS_ON relationships)
        if (data.edges) {
          data.edges.forEach((edge: { from: string; to: string; label?: string }) => {
            // Avoid duplicates - use source/target for force-graph
            const exists = links.some(l => {
              const src = typeof l.source === 'string' ? l.source : l.source?.id
              const tgt = typeof l.target === 'string' ? l.target : l.target?.id
              return src === edge.from && tgt === edge.to
            })
            if (!exists) {
              links.push({
                source: edge.from,
                target: edge.to,
                label: edge.label || 'depends_on',
                type: (edge.label || 'depends_on') as 'depends_on' | 'affects' | 'caused_by' | 'resolved_by' | 'similar_to',
              })
            }
          })
        }

        setGraphNodes(nodes)
        setGraphEdges(links)
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

  const fetchContainers = async () => {
    setContainersLoading(true)
    try {
      const response = await fetch('/api/v1/infrastructure/containers')
      if (response.ok) {
        const data = await response.json()
        // Sort containers: monitored first, then by name
        const sortedContainers = (data.containers || []).sort((a: ContainerInfo, b: ContainerInfo) => {
          // Monitored containers first
          if (a.monitored && !b.monitored) return -1
          if (!a.monitored && b.monitored) return 1
          // Then sort by name
          return a.name.localeCompare(b.name)
        })
        setContainers(sortedContainers)
        setInfrastructureStats({
          total: data.total || 0,
          healthy: data.healthy || 0,
          unhealthy: data.unhealthy || 0,
        })
      } else {
        setContainers([])
        setInfrastructureStats(null)
      }
    } catch (err) {
      console.error('Failed to fetch containers:', err)
      setContainers([])
      setInfrastructureStats(null)
    } finally {
      setContainersLoading(false)
    }
  }

  const executeTool = async () => {
    if (!selectedTool) return

    setToolExecuting(true)
    setToolResult(null)

    try {
      const response = await fetch('/api/v1/tools/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: selectedTool.name,
          parameters: toolParams,
        }),
      })

      const data = await response.json()
      setToolResult(JSON.stringify(data, null, 2))
    } catch (err) {
      setToolResult(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setToolExecuting(false)
    }
  }

  // Toggle container selection for monitoring
  const toggleContainerSelection = (containerName: string) => {
    setSelectedContainers(prev => {
      const newSet = new Set(prev)
      if (newSet.has(containerName)) {
        newSet.delete(containerName)
      } else {
        newSet.add(containerName)
      }
      return newSet
    })
  }

  // Select all containers
  const selectAllContainers = () => {
    setSelectedContainers(new Set(containers.map(c => c.name)))
  }

  // Deselect all containers
  const deselectAllContainers = () => {
    setSelectedContainers(new Set())
  }

  // Start monitoring selected containers
  const startMonitoring = async () => {
    if (selectedContainers.size === 0) return

    setMonitoringStarting(true)
    try {
      const response = await fetch('/api/v1/infrastructure/monitor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          containers: Array.from(selectedContainers),
        }),
      })

      if (response.ok) {
        // Clear selection and refresh container list to show updated monitoring status
        setSelectedContainers(new Set())
        await fetchContainers()
      } else {
        const data = await response.json()
        alert(`Failed to start monitoring: ${data.message || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Failed to start monitoring:', err)
      alert(`Failed to start monitoring: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setMonitoringStarting(false)
    }
  }

  // Stop monitoring a container
  const stopMonitoring = async (containerName: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent row click
    try {
      const response = await fetch(`/api/v1/infrastructure/containers/${containerName}/monitor`, {
        method: 'DELETE',
      })

      if (response.ok) {
        // Refresh container list to show updated monitoring status
        await fetchContainers()
      } else {
        const data = await response.json()
        alert(`Failed to stop monitoring: ${data.message || 'Unknown error'}`)
      }
    } catch (err) {
      console.error('Failed to stop monitoring:', err)
      alert(`Failed to stop monitoring: ${err instanceof Error ? err.message : 'Unknown error'}`)
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
                    <h3 className="font-semibold">Qwen3-4B Q4_K_M</h3>
                    <p className="text-sm text-muted-foreground">Port 8081 • Context: 8K tokens</p>
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
                    <div key={activity.id} className="p-4 hover:bg-muted/50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
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
                          <p className="text-sm font-mono bg-muted/50 p-2 rounded mt-2">
                            {activity.input.substring(0, 200)}...
                          </p>
                          <p className="text-sm text-muted-foreground mt-2">
                            → {activity.output.substring(0, 100)}...
                          </p>
                        </div>
                        <span className={`ml-4 ${
                          activity.status === 'success' ? 'text-green-500' : 'text-red-500'
                        }`}>
                          {activity.status === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                        </span>
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
                    <h3 className="font-semibold">Qwen3-14B Q4_K_M</h3>
                    <p className="text-sm text-muted-foreground">Port 8082 • Context: 4K tokens</p>
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
                    <div key={activity.id} className="p-4 hover:bg-muted/50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
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
                          <p className="text-sm font-mono bg-muted/50 p-2 rounded mt-2">
                            {activity.input.substring(0, 200)}...
                          </p>
                          <div className="mt-2 p-3 bg-purple-500/5 border border-purple-500/20 rounded">
                            <p className="text-sm">{activity.output}</p>
                          </div>
                        </div>
                        <span className={`ml-4 ${
                          activity.status === 'success' ? 'text-green-500' : 'text-red-500'
                        }`}>
                          {activity.status === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                        </span>
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

            {/* Neo4j Status */}
            <div className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${isComponentHealthy(health, 'neo4j') ? 'bg-green-500/10' : 'bg-yellow-500/10'}`}>
                    <GitBranch className={`h-5 w-5 ${isComponentHealthy(health, 'neo4j') ? 'text-green-500' : 'text-yellow-500'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold">Neo4j Graph Database</h3>
                    <p className="text-sm text-muted-foreground">
                      {isComponentHealthy(health, 'neo4j') ? 'Connected to Neo4j' : 'Using in-memory fallback'}
                    </p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${
                  isComponentHealthy(health, 'neo4j') ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'
                }`}>
                  {isComponentHealthy(health, 'neo4j') ? 'Connected' : 'Fallback Mode'}
                </span>
              </div>
            </div>

            {/* Episodic Graph Explorer - Force-Directed Visualization */}
            <div className="bg-card rounded-lg border border-border p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Episodic Knowledge Graph</h3>
                <button
                  onClick={fetchGraphData}
                  disabled={graphLoading}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 rounded-md transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${graphLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>

              {graphNodes.length > 0 ? (
                <EpisodicGraphExplorer
                  nodes={graphNodes}
                  links={graphEdges}
                  loading={graphLoading}
                  onNodeClick={(node) => setSelectedNode(node)}
                  onRefresh={fetchGraphData}
                  height={500}
                />
              ) : graphLoading ? (
                <div className="flex items-center justify-center h-[500px] bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-lg">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="h-[500px] flex flex-col items-center justify-center text-muted-foreground bg-gradient-to-br from-slate-900/30 to-slate-800/30 rounded-lg">
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
              {/* Available Tools */}
              <div className="bg-card rounded-lg border border-border">
                <div className="p-4 border-b border-border">
                  <h3 className="font-semibold">Available Tools</h3>
                </div>
                <div className="divide-y divide-border max-h-[400px] overflow-y-auto">
                  {toolsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : tools.length > 0 ? (
                    tools.map((tool) => (
                      <div
                        key={tool.name}
                        onClick={() => {
                          setSelectedTool(tool)
                          setToolParams({})
                          setToolResult(null)
                        }}
                        className={`p-4 cursor-pointer hover:bg-muted/50 ${
                          selectedTool?.name === tool.name ? 'bg-muted/50' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-medium">{tool.name}</h4>
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            tool.risk_level === 'low' ? 'bg-green-500/10 text-green-500' :
                            tool.risk_level === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
                            'bg-red-500/10 text-red-500'
                          }`}>
                            {tool.risk_level} risk
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground">{tool.description}</p>
                      </div>
                    ))
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                      <Wrench className="h-8 w-8 mb-2 opacity-50" />
                      <p className="text-sm">No tools available</p>
                      <p className="text-xs mt-1">Configure MCP server in backend</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Tool Execution */}
              <div className="bg-card rounded-lg border border-border">
                <div className="p-4 border-b border-border">
                  <h3 className="font-semibold">
                    {selectedTool ? `Execute: ${selectedTool.name}` : 'Tool Execution'}
                  </h3>
                </div>
                <div className="p-4">
                  {selectedTool ? (
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground">{selectedTool.description}</p>

                      {/* Parameters */}
                      {selectedTool.parameters.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="text-sm font-medium">Parameters</h4>
                          {selectedTool.parameters.map((param) => (
                            <div key={param.name}>
                              <label className="block text-sm mb-1">
                                {param.name}
                                {param.required && <span className="text-red-500 ml-1">*</span>}
                              </label>
                              <input
                                type="text"
                                value={toolParams[param.name] || ''}
                                onChange={(e) => setToolParams({
                                  ...toolParams,
                                  [param.name]: e.target.value,
                                })}
                                placeholder={param.description}
                                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                              />
                              <p className="text-xs text-muted-foreground mt-1">
                                Type: {param.type}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Execute Button */}
                      <button
                        onClick={executeTool}
                        disabled={toolExecuting}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
                      >
                        {toolExecuting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                        Execute Tool
                      </button>

                      {/* Warning for high-risk tools */}
                      {selectedTool.risk_level === 'high' && (
                        <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                          <AlertCircle className="h-4 w-4 text-red-500 mt-0.5" />
                          <p className="text-sm text-red-600">
                            This is a high-risk tool. Execution requires Constitutional AI approval.
                          </p>
                        </div>
                      )}

                      {/* Result */}
                      {toolResult && (
                        <div className="mt-4">
                          <h4 className="text-sm font-medium mb-2">Result</h4>
                          <pre className="p-3 bg-muted/50 rounded-lg text-sm font-mono overflow-x-auto max-h-[200px]">
                            {toolResult}
                          </pre>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                      <Wrench className="h-8 w-8 mb-2 opacity-50" />
                      <p className="text-sm">Select a tool to execute</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Infrastructure Tab */}
        {activeTab === 'infrastructure' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Server className="h-5 w-5 text-green-500" />
                  Infrastructure
                </h2>
                <p className="text-sm text-muted-foreground">
                  Docker containers and services
                </p>
              </div>
              <button
                onClick={fetchContainers}
                disabled={containersLoading}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-muted/80 disabled:opacity-50"
              >
                {containersLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                Refresh
              </button>
            </div>

            {/* Infrastructure Stats */}
            {infrastructureStats && (
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-card rounded-lg border border-border p-4 text-center">
                  <p className="text-3xl font-bold">{infrastructureStats.total}</p>
                  <p className="text-sm text-muted-foreground">Total Containers</p>
                </div>
                <div className="bg-card rounded-lg border border-border p-4 text-center">
                  <p className="text-3xl font-bold text-green-500">{infrastructureStats.healthy}</p>
                  <p className="text-sm text-muted-foreground">Healthy</p>
                </div>
                <div className="bg-card rounded-lg border border-border p-4 text-center">
                  <p className="text-3xl font-bold text-red-500">{infrastructureStats.unhealthy}</p>
                  <p className="text-sm text-muted-foreground">Unhealthy</p>
                </div>
              </div>
            )}

            {/* Container List */}
            <div className="bg-card rounded-lg border border-border">
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Box className="h-4 w-4" />
                    Docker Containers
                    {selectedContainers.size > 0 && (
                      <span className="ml-2 px-2 py-0.5 bg-primary/10 text-primary rounded-full text-xs">
                        {selectedContainers.size} selected
                      </span>
                    )}
                  </h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={selectAllContainers}
                      className="px-2 py-1 text-xs bg-muted rounded hover:bg-muted/80"
                    >
                      Select All
                    </button>
                    <button
                      onClick={deselectAllContainers}
                      className="px-2 py-1 text-xs bg-muted rounded hover:bg-muted/80"
                    >
                      Deselect All
                    </button>
                  </div>
                </div>
              </div>
              <div className="divide-y divide-border">
                {containersLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : containers.length > 0 ? (
                  containers.map((container) => (
                    <div
                      key={container.name}
                      className={`p-4 hover:bg-muted/50 cursor-pointer ${
                        selectedContainers.has(container.name) ? 'bg-primary/5' : ''
                      }`}
                      onClick={() => toggleContainerSelection(container.name)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={selectedContainers.has(container.name)}
                            onChange={() => toggleContainerSelection(container.name)}
                            onClick={(e) => e.stopPropagation()}
                            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                          />
                          <div className={`p-2 rounded-lg ${
                            container.health === 'healthy' ? 'bg-green-500/10' :
                            container.health === 'unhealthy' ? 'bg-red-500/10' :
                            'bg-yellow-500/10'
                          }`}>
                            <Box className={`h-5 w-5 ${
                              container.health === 'healthy' ? 'text-green-500' :
                              container.health === 'unhealthy' ? 'text-red-500' :
                              'text-yellow-500'
                            }`} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold">{container.name}</h4>
                              {container.monitored && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-500/10 text-blue-500 rounded-full text-xs font-medium">
                                  Monitoring
                                  <button
                                    onClick={(e) => stopMonitoring(container.name, e)}
                                    className="ml-1 p-0.5 hover:bg-blue-500/20 rounded"
                                    title="Stop monitoring"
                                  >
                                    <X className="h-3 w-3" />
                                  </button>
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{container.description}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            container.health === 'healthy' ? 'bg-green-500/10 text-green-500' :
                            container.health === 'unhealthy' ? 'bg-red-500/10 text-red-500' :
                            'bg-yellow-500/10 text-yellow-500'
                          }`}>
                            {container.health || 'unknown'}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
                        {container.port && (
                          <span>Port: {container.port}</span>
                        )}
                        {container.image && (
                          <span>Image: {container.image}</span>
                        )}
                        <span>Service: {container.service}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Server className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No containers found</p>
                    <p className="text-xs mt-1">Start the infrastructure to view containers</p>
                  </div>
                )}
              </div>

              {/* Start Monitoring Button */}
              {containers.length > 0 && (
                <div className="p-4 border-t border-border bg-muted/30">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      {selectedContainers.size === 0
                        ? 'Select containers to start monitoring'
                        : `${selectedContainers.size} container(s) selected for monitoring`}
                    </p>
                    <button
                      onClick={startMonitoring}
                      disabled={selectedContainers.size === 0 || monitoringStarting}
                      className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {monitoringStarting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      Start Monitoring
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
