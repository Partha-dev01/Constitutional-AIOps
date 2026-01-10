import { useEffect, useRef, useState, useCallback } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { Loader2, ZoomIn, ZoomOut, Maximize2, Play, Pause, RotateCcw, Filter } from 'lucide-react'

// Graph node with episodic memory data
interface EpisodicNode extends NodeObject {
  id: string
  label: string
  type: 'service' | 'episode' | 'incident' | 'action' | 'root_cause'
  status?: 'healthy' | 'warning' | 'critical' | 'detected' | 'analyzing' | 'remediating' | 'resolved'
  timestamp?: string
  confidence?: number
  severity?: string
  metadata?: Record<string, unknown>
  // Force graph properties
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number | null
  fy?: number | null
}

interface EpisodicLink extends LinkObject {
  source: string | EpisodicNode
  target: string | EpisodicNode
  label?: string
  type?: 'depends_on' | 'affects' | 'caused_by' | 'resolved_by' | 'similar_to'
  weight?: number
}

interface EpisodicGraphExplorerProps {
  nodes: EpisodicNode[]
  links: EpisodicLink[]
  loading?: boolean
  onNodeClick?: (node: EpisodicNode) => void
  onRefresh?: () => void
  height?: number
  width?: number
}

// Node color mapping by type and status
const getNodeColor = (node: EpisodicNode): string => {
  const colors = {
    service: {
      healthy: '#22c55e',    // green
      warning: '#f59e0b',    // amber
      critical: '#ef4444',   // red
      default: '#3b82f6',    // blue
    },
    episode: {
      detected: '#f59e0b',   // amber
      analyzing: '#8b5cf6',  // purple
      remediating: '#3b82f6', // blue
      resolved: '#22c55e',   // green
      default: '#a855f7',    // purple
    },
    incident: '#ef4444',     // red
    action: '#06b6d4',       // cyan
    root_cause: '#f97316',   // orange
  }

  if (node.type === 'service') {
    return colors.service[node.status as keyof typeof colors.service] || colors.service.default
  }
  if (node.type === 'episode') {
    return colors.episode[node.status as keyof typeof colors.episode] || colors.episode.default
  }
  return colors[node.type] || '#64748b'
}

// Link color by relationship type
const getLinkColor = (link: EpisodicLink): string => {
  const colors = {
    depends_on: '#3b82f6',   // blue
    affects: '#ef4444',      // red
    caused_by: '#f97316',    // orange
    resolved_by: '#22c55e',  // green
    similar_to: '#8b5cf6',   // purple
    default: '#64748b',      // gray
  }
  return colors[link.type || 'default'] || colors.default
}

export function EpisodicGraphExplorer({
  nodes,
  links,
  loading = false,
  onNodeClick,
  onRefresh,
  height = 500,
  width = 800,
}: EpisodicGraphExplorerProps) {
  const graphRef = useRef<ForceGraphMethods<EpisodicNode, EpisodicLink>>()
  const containerRef = useRef<HTMLDivElement>(null)

  const [hoveredNode, setHoveredNode] = useState<EpisodicNode | null>(null)
  const [selectedNode, setSelectedNode] = useState<EpisodicNode | null>(null)
  const [isPlaying, setIsPlaying] = useState(true)
  const [filterType, setFilterType] = useState<string>('all')
  const [graphDimensions, setGraphDimensions] = useState({ width, height })

  // Filter nodes based on type
  const filteredNodes = filterType === 'all'
    ? nodes
    : nodes.filter(n => n.type === filterType)

  const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredLinks = links.filter(l => {
    const sourceId = typeof l.source === 'string' ? l.source : l.source?.id
    const targetId = typeof l.target === 'string' ? l.target : l.target?.id
    return filteredNodeIds.has(sourceId || '') && filteredNodeIds.has(targetId || '')
  })

  // Resize observer
  useEffect(() => {
    if (!containerRef.current) return

    const resizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        setGraphDimensions({
          width: entry.contentRect.width || width,
          height: entry.contentRect.height || height,
        })
      }
    })

    resizeObserver.observe(containerRef.current)
    return () => resizeObserver.disconnect()
  }, [width, height])

  // Handle node click
  const handleNodeClick = useCallback((node: EpisodicNode) => {
    setSelectedNode(node)
    onNodeClick?.(node)

    // Center view on clicked node
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 500)
      graphRef.current.zoom(2, 500)
    }
  }, [onNodeClick])

  // Custom node rendering
  const nodeCanvasObject = useCallback((node: EpisodicNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isHovered = hoveredNode?.id === node.id
    const isSelected = selectedNode?.id === node.id
    const size = isSelected ? 12 : isHovered ? 10 : 8
    const fontSize = Math.max(10, 12 / globalScale)

    // Node glow for selected/hovered
    if (isSelected || isHovered) {
      ctx.beginPath()
      ctx.arc(node.x || 0, node.y || 0, size + 4, 0, 2 * Math.PI)
      ctx.fillStyle = `${getNodeColor(node)}40`
      ctx.fill()
    }

    // Main node circle
    ctx.beginPath()
    ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI)
    ctx.fillStyle = getNodeColor(node)
    ctx.fill()

    // Node border
    ctx.strokeStyle = isSelected ? '#fff' : '#00000040'
    ctx.lineWidth = isSelected ? 2 : 1
    ctx.stroke()

    // Node type icon (simplified)
    ctx.fillStyle = '#fff'
    ctx.font = `${size * 0.8}px Arial`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const icon = node.type === 'service' ? 'S' :
                 node.type === 'episode' ? 'E' :
                 node.type === 'incident' ? '!' :
                 node.type === 'action' ? 'A' : 'R'
    ctx.fillText(icon, node.x || 0, node.y || 0)

    // Node label
    if (globalScale > 0.5 || isHovered || isSelected) {
      ctx.font = `${fontSize}px Inter, sans-serif`
      ctx.fillStyle = '#94a3b8'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      const label = node.label.length > 15 ? node.label.slice(0, 12) + '...' : node.label
      ctx.fillText(label, node.x || 0, (node.y || 0) + size + 4)
    }
  }, [hoveredNode, selectedNode])

  // Custom link rendering
  const linkCanvasObject = useCallback((link: EpisodicLink, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const source = link.source as EpisodicNode
    const target = link.target as EpisodicNode

    if (!source.x || !source.y || !target.x || !target.y) return

    // Draw line
    ctx.beginPath()
    ctx.moveTo(source.x, source.y)
    ctx.lineTo(target.x, target.y)
    ctx.strokeStyle = getLinkColor(link)
    ctx.lineWidth = (link.weight || 1) * 1.5
    ctx.globalAlpha = 0.6
    ctx.stroke()
    ctx.globalAlpha = 1

    // Draw arrow
    const angle = Math.atan2(target.y - source.y, target.x - source.x)
    const arrowSize = 6
    const midX = (source.x + target.x) / 2
    const midY = (source.y + target.y) / 2

    ctx.beginPath()
    ctx.moveTo(midX, midY)
    ctx.lineTo(
      midX - arrowSize * Math.cos(angle - Math.PI / 6),
      midY - arrowSize * Math.sin(angle - Math.PI / 6)
    )
    ctx.lineTo(
      midX - arrowSize * Math.cos(angle + Math.PI / 6),
      midY - arrowSize * Math.sin(angle + Math.PI / 6)
    )
    ctx.closePath()
    ctx.fillStyle = getLinkColor(link)
    ctx.fill()

    // Link label
    if (link.label && globalScale > 1) {
      ctx.font = '8px Inter, sans-serif'
      ctx.fillStyle = '#64748b'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(link.label, midX, midY - 8)
    }
  }, [])

  // Zoom controls
  const handleZoomIn = () => graphRef.current?.zoom(graphRef.current.zoom() * 1.5, 300)
  const handleZoomOut = () => graphRef.current?.zoom(graphRef.current.zoom() / 1.5, 300)
  const handleFit = () => graphRef.current?.zoomToFit(400, 50)
  const handleReset = () => {
    graphRef.current?.zoomToFit(400, 50)
    setSelectedNode(null)
    setHoveredNode(null)
  }

  // Toggle physics simulation
  const toggleSimulation = () => {
    if (graphRef.current) {
      if (isPlaying) {
        graphRef.current.pauseAnimation()
      } else {
        graphRef.current.resumeAnimation()
      }
      setIsPlaying(!isPlaying)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[500px] bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-lg">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="relative" ref={containerRef}>
      {/* Graph Container */}
      <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 rounded-lg overflow-hidden">
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes: filteredNodes, links: filteredLinks }}
          width={graphDimensions.width}
          height={graphDimensions.height}
          nodeCanvasObject={nodeCanvasObject}
          linkCanvasObject={linkCanvasObject}
          onNodeClick={handleNodeClick}
          onNodeHover={setHoveredNode}
          nodeId="id"
          linkSource="source"
          linkTarget="target"
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          backgroundColor="transparent"
        />
      </div>

      {/* Control Panel */}
      <div className="absolute top-3 right-3 flex flex-col gap-1.5">
        <button
          onClick={handleZoomIn}
          className="p-1.5 bg-slate-800/90 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4 text-slate-300" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-1.5 bg-slate-800/90 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4 text-slate-300" />
        </button>
        <button
          onClick={handleFit}
          className="p-1.5 bg-slate-800/90 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
          title="Fit to View"
        >
          <Maximize2 className="h-4 w-4 text-slate-300" />
        </button>
        <button
          onClick={toggleSimulation}
          className="p-1.5 bg-slate-800/90 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
          title={isPlaying ? 'Pause Animation' : 'Resume Animation'}
        >
          {isPlaying ? (
            <Pause className="h-4 w-4 text-slate-300" />
          ) : (
            <Play className="h-4 w-4 text-slate-300" />
          )}
        </button>
        <button
          onClick={handleReset}
          className="p-1.5 bg-slate-800/90 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
          title="Reset View"
        >
          <RotateCcw className="h-4 w-4 text-slate-300" />
        </button>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 bg-slate-800/90 hover:bg-slate-700 rounded-md border border-slate-700 transition-colors"
            title="Refresh Data"
          >
            <RotateCcw className="h-4 w-4 text-blue-400" />
          </button>
        )}
      </div>

      {/* Filter Panel */}
      <div className="absolute top-3 left-3 flex items-center gap-2">
        <Filter className="h-4 w-4 text-slate-400" />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="text-xs bg-slate-800/90 text-slate-300 border border-slate-700 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="all">All Types</option>
          <option value="service">Services</option>
          <option value="episode">Episodes</option>
          <option value="incident">Incidents</option>
          <option value="action">Actions</option>
        </select>
      </div>

      {/* Stats Overlay */}
      <div className="absolute bottom-3 right-3 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-md border border-slate-700">
        {filteredNodes.length} nodes | {filteredLinks.length} edges
        {filterType !== 'all' && ` (filtered: ${filterType})`}
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-3 text-xs bg-slate-900/80 px-3 py-2 rounded-md border border-slate-700">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-slate-400">Healthy</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="text-slate-400">Warning</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-slate-400">Critical</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span className="text-slate-400">Episode</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-cyan-500" />
          <span className="text-slate-400">Action</span>
        </div>
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <div className="absolute top-14 left-3 bg-slate-900/95 border border-slate-700 rounded-lg p-3 max-w-xs shadow-lg">
          <div className="flex items-start justify-between mb-2">
            <h4 className="font-medium text-slate-200">{selectedNode.label}</h4>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-500 hover:text-slate-300"
            >
              &times;
            </button>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Type:</span>
              <span className="text-slate-300 capitalize">{selectedNode.type}</span>
            </div>
            {selectedNode.status && (
              <div className="flex justify-between">
                <span className="text-slate-500">Status:</span>
                <span className={`capitalize ${
                  selectedNode.status === 'healthy' || selectedNode.status === 'resolved' ? 'text-green-400' :
                  selectedNode.status === 'warning' || selectedNode.status === 'analyzing' ? 'text-amber-400' :
                  selectedNode.status === 'critical' ? 'text-red-400' : 'text-slate-300'
                }`}>
                  {selectedNode.status}
                </span>
              </div>
            )}
            {selectedNode.confidence !== undefined && (
              <div className="flex justify-between">
                <span className="text-slate-500">Confidence:</span>
                <span className="text-slate-300">{(selectedNode.confidence * 100).toFixed(1)}%</span>
              </div>
            )}
            {selectedNode.severity && (
              <div className="flex justify-between">
                <span className="text-slate-500">Severity:</span>
                <span className={`capitalize ${
                  selectedNode.severity === 'critical' ? 'text-red-400' :
                  selectedNode.severity === 'high' ? 'text-orange-400' :
                  selectedNode.severity === 'medium' ? 'text-amber-400' : 'text-slate-300'
                }`}>
                  {selectedNode.severity}
                </span>
              </div>
            )}
            {selectedNode.timestamp && (
              <div className="flex justify-between">
                <span className="text-slate-500">Time:</span>
                <span className="text-slate-300">
                  {new Date(selectedNode.timestamp).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export type { EpisodicNode, EpisodicLink }
