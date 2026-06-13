import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { EpisodicGraphExplorer } from '../components/EpisodicGraphExplorer'
import { Loader2, RefreshCw } from 'lucide-react'

/**
 * Graph Page - Episodic Knowledge Graph Visualization
 *
 * Displays the episodic memory graph with:
 * - Episodes (incidents)
 * - Root causes
 * - Actions
 * - Services
 * - Entities (LLM-extracted)
 *
 * v0.6.0: Includes edge filtering controls, DAG mode, and optimized physics
 */

interface GraphNode {
  id: string
  label: string
  type: 'service' | 'episode' | 'incident' | 'action' | 'root_cause' | 'entity'
  status?: 'healthy' | 'warning' | 'critical' | 'detected' | 'analyzing' | 'remediating' | 'resolved'
  timestamp?: string
  confidence?: number
  severity?: string
  metadata?: Record<string, unknown>
  category?: string
  rootCause?: string
  resolutionTime?: number
  frequency?: number
  avgResolutionTime?: number
  successRate?: number
  usedCount?: number
  avgExecutionTime?: number
  incidentCount?: number
  lastIncident?: string
  relationCount?: number
  [key: string]: unknown  // Index signature for compatibility
}

interface GraphLink {
  source: string
  target: string
  label?: string
  type?: string
  weight?: number
  metadata?: Record<string, unknown>
  [key: string]: unknown  // Index signature for compatibility
}

interface GraphData {
  episodes: Array<{
    id: string
    title: string
    type: string
    timestamp: string
    category: string
    severity: string
    status: string
    root_cause?: string
    confidence: number
    services: string[]
    successful_actions: string[]
    metadata: Record<string, unknown>
  }>
  root_causes: Array<{
    id: string
    name: string
    type: string
    frequency: number
    avg_resolution_time_minutes: number
    success_rate: number
    metadata: Record<string, unknown>
  }>
  actions: Array<{
    id: string
    name: string
    type: string
    used_count: number
    success_rate: number
    avg_execution_time_seconds: number
    metadata: Record<string, unknown>
  }>
  services: Array<{
    name: string
    type: string
    status: string
    incident_count: number
    last_incident?: string
    metadata: Record<string, unknown>
  }>
  entities: Array<{
    id: string
    name: string
    type: string
    relation_count: number
    metadata: Record<string, unknown>
  }>
  edges: Array<{
    source: string
    target: string
    relationship: string
    weight?: number
    metadata?: Record<string, unknown>
  }>
  stats: {
    total_episodes: number
    total_root_causes: number
    total_actions: number
    total_services: number
    total_entities: number
    total_edges: number
    critical_episodes: number
    resolved_episodes: number
    dynamic_edges: number
  }
}

// Transform API response to graph format
function transformGraphData(data: GraphData): { nodes: GraphNode[]; links: GraphLink[] } {
  const nodes: GraphNode[] = []
  const links: GraphLink[] = []

  // Add episode nodes
  for (const episode of data.episodes ?? []) {
    nodes.push({
      id: `episode-${episode.id}`,
      label: episode.title,
      type: 'episode',
      status: episode.status as GraphNode['status'],
      timestamp: episode.timestamp,
      confidence: episode.confidence,
      severity: episode.severity,
      category: episode.category,
      rootCause: episode.root_cause,
      metadata: episode.metadata,
    })
  }

  // Add root cause nodes
  for (const rc of data.root_causes ?? []) {
    nodes.push({
      id: `root_cause-${rc.id}`,
      label: rc.name,
      type: 'root_cause',
      frequency: rc.frequency,
      avgResolutionTime: rc.avg_resolution_time_minutes,
      successRate: rc.success_rate,
      metadata: rc.metadata,
    })
  }

  // Add action nodes
  for (const action of data.actions ?? []) {
    nodes.push({
      id: `action-${action.id}`,
      label: action.name,
      type: 'action',
      usedCount: action.used_count,
      successRate: action.success_rate,
      avgExecutionTime: action.avg_execution_time_seconds,
      metadata: action.metadata,
    })
  }

  // Add service nodes
  for (const service of data.services ?? []) {
    nodes.push({
      id: `service-${service.name}`,
      label: service.name,
      type: 'service',
      status: service.status as GraphNode['status'],
      incidentCount: service.incident_count,
      lastIncident: service.last_incident,
      metadata: service.metadata,
    })
  }

  // Add entity nodes
  for (const entity of data.entities ?? []) {
    nodes.push({
      id: `entity-${entity.id}`,
      label: entity.name,
      type: 'entity',
      relationCount: entity.relation_count,
      metadata: entity.metadata,
    })
  }

  // Add edges
  for (const edge of data.edges ?? []) {
    links.push({
      source: edge.source,
      target: edge.target,
      label: edge.relationship,
      type: edge.relationship,
      weight: edge.weight,
      metadata: edge.metadata,
    })
  }

  return { nodes, links }
}

export function Graph() {
  const [refreshKey, setRefreshKey] = useState(0)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['episodic-graph', refreshKey],
    queryFn: async () => {
      const response = await axios.get<GraphData>('/api/v1/graph/episodes', {
        params: {
          limit: 50,
          since_hours: 168, // 7 days
        },
      })
      return response.data
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  })

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1)
    refetch()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-slate-400">Loading graph...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-400">
        <p>Error loading graph data</p>
        <button
          onClick={handleRefresh}
          className="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-md flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    )
  }

  const graphData = data ? transformGraphData(data) : { nodes: [], links: [] }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div>
          <h1 className="text-xl font-semibold text-slate-200">Episodic Knowledge Graph</h1>
          <p className="text-sm text-slate-400">
            {data?.stats?.total_episodes || 0} episodes, {data?.stats?.total_edges || 0} edges
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-md flex items-center gap-2 text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
      <div className="flex-1 relative">
        <EpisodicGraphExplorer
          nodes={graphData.nodes}
          links={graphData.links}
          loading={isLoading}
          onRefresh={handleRefresh}
        />
      </div>
    </div>
  )
}
