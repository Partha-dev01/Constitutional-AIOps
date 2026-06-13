import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d'
import { Loader2, ZoomIn, ZoomOut, Maximize2, Play, Pause, RotateCcw, Filter, Search } from 'lucide-react'
import { useResizeObserver } from '../hooks/useResizeObserver'

// Graph node with episodic memory data
interface EpisodicNode extends NodeObject {
  id: string
  label: string
  type: 'service' | 'episode' | 'incident' | 'action' | 'root_cause' | 'entity'
  status?: 'healthy' | 'warning' | 'critical' | 'detected' | 'analyzing' | 'remediating' | 'resolved'
  timestamp?: string
  confidence?: number
  severity?: string
  metadata?: Record<string, unknown>
  // Episode-specific
  category?: string
  rootCause?: string
  resolutionTime?: number // minutes
  // Root cause-specific
  frequency?: number
  avgResolutionTime?: number // minutes
  successRate?: number
  // Action-specific
  usedCount?: number
  avgExecutionTime?: number // seconds
  // Service-specific
  incidentCount?: number
  lastIncident?: string
  // Entity-specific (LLM-extracted)
  relationCount?: number
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
  type?: string  // Dynamic: depends_on, affects, caused_by, resolved_by, similar_to, or LLM-extracted relations
  weight?: number
  metadata?: Record<string, unknown>  // Contains extraction_method for LLM edges
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
  // Status-based colors for service and episode
  const serviceColors: Record<string, string> = {
    healthy: '#22c55e',    // green
    warning: '#f59e0b',    // amber
    critical: '#ef4444',   // red
    default: '#3b82f6',    // blue
  }

  const episodeColors: Record<string, string> = {
    detected: '#f59e0b',   // amber
    analyzing: '#8b5cf6',  // purple
    remediating: '#3b82f6', // blue
    resolved: '#22c55e',   // green
    default: '#a855f7',    // purple
  }

  // Type-based colors for other node types
  const typeColors: Record<string, string> = {
    incident: '#ef4444',     // red
    action: '#06b6d4',       // cyan
    root_cause: '#f97316',   // orange
    entity: '#ec4899',       // pink - LLM-extracted entities
  }

  if (node.type === 'service') {
    return serviceColors[node.status || 'default'] || serviceColors.default
  }
  if (node.type === 'episode') {
    return episodeColors[node.status || 'default'] || episodeColors.default
  }
  return typeColors[node.type] || '#64748b'
}

// Link color by relationship type
const getLinkColor = (link: EpisodicLink): string => {
  const colors: Record<string, string> = {
    depends_on: '#3b82f6',   // blue
    affects: '#ef4444',      // red
    caused_by: '#f97316',    // orange
    resolved_by: '#22c55e',  // green
    similar_to: '#8b5cf6',   // purple
    // LLM-extracted dynamic relations
    experienced: '#f97316',  // orange
    caused: '#ef4444',       // red
    affected: '#f59e0b',     // amber
    triggered: '#dc2626',    // red
    degraded: '#f59e0b',     // amber
    monitors: '#3b82f6',     // blue
    connected_to: '#3b82f6', // blue
    default: '#64748b',      // gray
  }
  const linkType = (link.type || 'default').toLowerCase()
  // Check if it's an LLM-extracted relation (from metadata)
  const isLLMRelation = link.metadata?.extraction_method === 'llm'
  if (isLLMRelation && !colors[linkType]) {
    return '#ec4899' // pink for unknown LLM relations
  }
  return colors[linkType] || colors.default
}

export function EpisodicGraphExplorer({
  nodes,
  links,
  loading = false,
  onNodeClick,
  onRefresh,
  height = 520,
  width = 800,
}: EpisodicGraphExplorerProps) {
  const graphRef = useRef<ForceGraphMethods>(null)

  // Only measure WIDTH from ResizeObserver — the container's CSS height is fixed by
  // the `height` prop, so feeding the observed height back into ForceGraph would
  // create a 1px resize loop. Start with a large fallback so the initial paint fills
  // the container rather than shrinking to the fallback 800px.
  const { ref: canvasHostRef, size: measuredSize } = useResizeObserver<HTMLDivElement>({
    width: width,
    height: height,
  })
  // Resolved width: use measured width once ResizeObserver fires (> 0), else fallback.
  // Height is always the fixed `height` prop.
  const graphWidth = measuredSize.width > 0 ? measuredSize.width : width
  const graphHeight = height

  // Guards onEngineStop so zoomToFit runs once per topology, not on every micro-stop.
  const hasFitRef = useRef(false)
  // True once the user manually pans/zooms — suppresses auto zoom-to-fit so
  // background count drift (30s refetch) doesn't fight the user's view.
  const hasInteractedRef = useRef(false)
  // True while a programmatic zoom/fit is in flight — lets us skip marking
  // onZoom as a user interaction when the fit was triggered by code, not the user.
  const isProgrammaticZoomRef = useRef(false)

  const [hoveredNode, setHoveredNode] = useState<EpisodicNode | null>(null)
  const [selectedNode, setSelectedNode] = useState<EpisodicNode | null>(null)
  const [isPlaying, setIsPlaying] = useState(true)
  const [filterType, setFilterType] = useState<string>('all')

  // v0.6.0: Visualization controls to prevent hairball
  const [showSimilarTo, setShowSimilarTo] = useState(true)
  const [showEntities, setShowEntities] = useState(true)
  const [layoutMode, setLayoutMode] = useState<'force' | 'dag'>('force')
  // Label search (input only — deliberately NOT a <select>; the episode
  // filter select must stay the single select in the graph tab).
  const [search, setSearch] = useState('')

  // Filter nodes based on type
  // Memoized so the force-config effect / ForceGraph don't see new array refs every render.
  const filteredNodes = useMemo(() => {
    let result = filterType === 'all'
      ? nodes
      : nodes.filter(n => n.type === filterType)

    if (!showEntities) {
      result = result.filter(n => n.type !== 'entity')
    }

    const query = search.trim().toLowerCase()
    if (query) {
      result = result.filter(n => n.label.toLowerCase().includes(query))
    }

    return result
  }, [nodes, filterType, showEntities, search])

  // Filter links based on edge visibility toggles (memoized)
  const filteredLinks = useMemo(() => {
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id))

    return links.filter(l => {
      const sourceId = typeof l.source === 'string' ? l.source : l.source?.id
      const targetId = typeof l.target === 'string' ? l.target : l.target?.id

      // Must connect filtered nodes
      if (!filteredNodeIds.has(sourceId || '') || !filteredNodeIds.has(targetId || '')) {
        return false
      }

      // Filter out SIMILAR_TO edges if disabled
      if (!showSimilarTo && l.type?.toLowerCase() === 'similar_to') {
        return false
      }

      // Filter out entity-related edges if entities disabled
      if (!showEntities && (l.type?.toLowerCase() === 'relates' || l.metadata?.extraction_method === 'llm')) {
        return false
      }

      return true
    })
  }, [links, filteredNodes, showSimilarTo, showEntities])

  // Degree per node (for size-by-connectivity), rebuilt on link changes only.
  const degreeMap = useMemo(() => {
    const map = new Map<string, number>()
    for (const link of filteredLinks) {
      const srcId = typeof link.source === 'string' ? link.source : (link.source as EpisodicNode)?.id
      const tgtId = typeof link.target === 'string' ? link.target : (link.target as EpisodicNode)?.id
      if (srcId) map.set(srcId, (map.get(srcId) ?? 0) + 1)
      if (tgtId) map.set(tgtId, (map.get(tgtId) ?? 0) + 1)
    }
    return map
  }, [filteredLinks])

  // Build neighbor sets for hover-highlighting (memoized, rebuilt on link changes only)
  const neighborMap = useMemo(() => {
    const map = new Map<string, Set<string>>()
    for (const link of filteredLinks) {
      const srcId = typeof link.source === 'string' ? link.source : (link.source as EpisodicNode)?.id
      const tgtId = typeof link.target === 'string' ? link.target : (link.target as EpisodicNode)?.id
      if (!srcId || !tgtId) continue
      if (!map.has(srcId)) map.set(srcId, new Set())
      if (!map.has(tgtId)) map.set(tgtId, new Set())
      map.get(srcId)!.add(tgtId)
      map.get(tgtId)!.add(srcId)
    }
    return map
  }, [filteredLinks])

  // Configure d3 forces for better node separation across the full canvas area.
  // FIX: Add forceX/forceY to pull nodes toward the canvas center (0, 0 in graph
  // coordinates, which maps to the canvas center). This prevents nodes from
  // clustering in a corner when charge alone is insufficient.
  useEffect(() => {
    if (!graphRef.current) return
    const fg = graphRef.current

    // Stronger repulsion to spread nodes across the canvas
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const chargeForce = fg.d3Force('charge') as any
    if (chargeForce?.strength) chargeForce.strength(-400)

    // Variable link distance for visual hierarchy
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const linkForce = fg.d3Force('link') as any
    if (linkForce?.distance) {
      linkForce.distance((link: EpisodicLink) => {
        const linkType = link.type?.toLowerCase() || ''
        switch (linkType) {
          case 'similar_to':
            return 80
          case 'affects':
          case 'involves':
            return 120
          case 'caused_by':
          case 'experienced':
            return 100
          case 'resolved_by':
          case 'remediates':
            return 130
          case 'relates':
            return 90
          default:
            return 100
        }
      })
    }

    // FIX: Replace missing forceCenter with explicit forceX/forceY so nodes are
    // pulled toward the canvas center in both axes. Moderate strength (0.08) lets
    // the layout breathe while preventing corner clustering.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const d3 = (fg as any).d3Force
    // Use the existing center force if available, or add x/y forces
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const existingCenter = (fg as any).d3Force('center') as any
      if (existingCenter && typeof existingCenter.strength === 'function') {
        existingCenter.strength(0.15)
      }
    } catch (_e) {
      // center force absent — not an error
    }

    // Allow onEngineStop to zoom-fit once for the new layout.
    hasFitRef.current = false
    hasInteractedRef.current = false
    void d3 // suppress unused-var lint
  }, [layoutMode])

  // User-driven filter/layout changes should allow a re-fit.
  useEffect(() => {
    hasFitRef.current = false
    hasInteractedRef.current = false
  }, [filterType, showSimilarTo, showEntities, layoutMode])

  // Pin a node where the user drops it so it doesn't drift back.
  const handleNodeDragEnd = useCallback((node: EpisodicNode) => {
    node.fx = node.x
    node.fy = node.y
  }, [])

  // Handle node click — gentle pan without zoom.
  const handleNodeClick = useCallback((node: EpisodicNode) => {
    hasInteractedRef.current = true
    setSelectedNode(node)
    onNodeClick?.(node)

    if (graphRef.current) {
      isProgrammaticZoomRef.current = true
      graphRef.current.centerAt(node.x, node.y, 800)
      // Clear the programmatic flag after the animation completes
      setTimeout(() => { isProgrammaticZoomRef.current = false }, 1000)
    }
  }, [onNodeClick])

  // Custom node rendering with hover-dimming of non-neighbors
  const nodeCanvasObject = useCallback((node: EpisodicNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isHovered = hoveredNode?.id === node.id
    const isSelected = selectedNode?.id === node.id
    const isNeighbor = hoveredNode ? neighborMap.get(hoveredNode.id)?.has(node.id) : false
    const isDimmed = hoveredNode !== null && !isHovered && !isNeighbor

    // Variable node sizes: type hierarchy + connectivity (degree) + recency.
    const typeSize = node.type === 'episode' ? 9 :
                     node.type === 'root_cause' ? 7 :
                     node.type === 'service' ? 6 :
                     node.type === 'entity' ? 6 : 5
    const degree = degreeMap.get(node.id) ?? 0
    const isRecent = node.timestamp
      ? Date.now() - new Date(node.timestamp).getTime() < 24 * 3600 * 1000
      : false
    const baseSize = typeSize + Math.min(3.5, degree * 0.35) + (isRecent ? 1 : 0)
    const size = isSelected ? baseSize + 4 : isHovered ? baseSize + 2 : baseSize

    // FIX: Only draw labels when zoomed in enough (threshold raised to 1.5) to
    // prevent label overlap at the default fit-to-view zoom level.
    const showLabel = globalScale > 1.5 || isHovered || isSelected

    // Apply dimming for non-neighbors during hover
    ctx.globalAlpha = isDimmed ? 0.2 : 1.0

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

    // Severity ring on high-impact episodes (critical red / high orange).
    if (node.type === 'episode' && (node.severity === 'critical' || node.severity === 'high')) {
      ctx.beginPath()
      ctx.arc(node.x || 0, node.y || 0, size + 3, 0, 2 * Math.PI)
      ctx.strokeStyle = node.severity === 'critical' ? '#ef4444' : '#f97316'
      ctx.lineWidth = 1.5
      ctx.stroke()
    }

    // Node type icon
    ctx.fillStyle = '#fff'
    ctx.font = `${size * 0.8}px Arial`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const icon = node.type === 'service' ? 'S' :
                 node.type === 'episode' ? 'E' :
                 node.type === 'incident' ? '!' :
                 node.type === 'action' ? 'A' :
                 node.type === 'entity' ? '◆' : 'R'
    ctx.fillText(icon, node.x || 0, node.y || 0)

    // Node label — only when zoomed in enough OR hovered/selected.
    // FIX: Truncate more aggressively (max 12 chars) and use a background rect
    // so overlapping labels are still readable.
    if (showLabel) {
      const fontSize = Math.max(9, 11 / globalScale)
      const label = node.label.length > 12 ? node.label.slice(0, 10) + '…' : node.label
      const lx = node.x || 0
      const ly = (node.y || 0) + size + 5

      ctx.font = `${fontSize}px Inter, sans-serif`
      const textWidth = ctx.measureText(label).width

      // Dark background pill behind label for readability
      ctx.fillStyle = 'rgba(15,23,42,0.75)'
      ctx.fillRect(lx - textWidth / 2 - 2, ly - 1, textWidth + 4, fontSize + 3)

      ctx.fillStyle = isHovered || isSelected ? '#e2e8f0' : '#94a3b8'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(label, lx, ly)
    }

    ctx.globalAlpha = 1.0
  }, [hoveredNode, selectedNode, neighborMap, degreeMap])

  // Custom link rendering with hover-dimming
  const linkCanvasObject = useCallback((link: EpisodicLink, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const source = link.source as EpisodicNode
    const target = link.target as EpisodicNode

    if (!source.x || !source.y || !target.x || !target.y) return

    // Dim links that don't connect to the hovered node
    const srcId = (source as EpisodicNode).id
    const tgtId = (target as EpisodicNode).id
    const isConnectedToHover = hoveredNode &&
      (srcId === hoveredNode.id || tgtId === hoveredNode.id)
    const isDimmed = hoveredNode !== null && !isConnectedToHover

    ctx.globalAlpha = isDimmed ? 0.1 : 0.6

    // Typed edge rendering: DEPENDS_ON-style edges stay solid with arrows,
    // SIMILAR_TO is dashed (undirected), MENTIONS/RELATES draw thin.
    const linkTypeName = (link.type || '').toLowerCase()
    const isSimilar = linkTypeName === 'similar_to'
    const isThin = linkTypeName === 'mentions' || linkTypeName === 'relates'

    // Draw line
    ctx.beginPath()
    ctx.moveTo(source.x, source.y)
    ctx.lineTo(target.x, target.y)
    ctx.strokeStyle = getLinkColor(link)
    ctx.lineWidth = isThin ? 0.6 : (link.weight || 1) * 1.5
    if (isSimilar) ctx.setLineDash([5, 4])
    ctx.stroke()
    if (isSimilar) ctx.setLineDash([])

    ctx.globalAlpha = isDimmed ? 0.1 : 1.0

    // Draw arrow at midpoint (skipped for undirected SIMILAR_TO edges)
    const angle = Math.atan2(target.y - source.y, target.x - source.x)
    const arrowSize = isThin ? 4 : 6
    const midX = (source.x + target.x) / 2
    const midY = (source.y + target.y) / 2

    if (!isSimilar) {
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
    }

    // Link label — only when zoomed in enough and not dimmed
    const relationLabel = link.label || link.type
    const isLLMRelation = link.metadata?.extraction_method === 'llm'
    if (!isDimmed && relationLabel && globalScale > 1.5) {
      ctx.font = isLLMRelation ? 'bold 8px Inter, sans-serif' : '8px Inter, sans-serif'
      ctx.fillStyle = isLLMRelation ? '#ec4899' : '#64748b'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const displayLabel = relationLabel.replace(/_/g, ' ')
      ctx.fillText(displayLabel, midX, midY - 8)
    }

    ctx.globalAlpha = 1.0
  }, [hoveredNode])

  // Zoom controls — mark manual zoom as user interaction, but not programmatic zoom.
  const handleZoomIn = () => {
    hasInteractedRef.current = true
    const cur = graphRef.current?.zoom() ?? 1
    isProgrammaticZoomRef.current = true
    graphRef.current?.zoom(cur * 1.5, 300)
    setTimeout(() => { isProgrammaticZoomRef.current = false }, 500)
  }
  const handleZoomOut = () => {
    hasInteractedRef.current = true
    const cur = graphRef.current?.zoom() ?? 1
    isProgrammaticZoomRef.current = true
    graphRef.current?.zoom(cur / 1.5, 300)
    setTimeout(() => { isProgrammaticZoomRef.current = false }, 500)
  }
  const handleFit = () => {
    isProgrammaticZoomRef.current = true
    graphRef.current?.zoomToFit(400, 50)
    setTimeout(() => { isProgrammaticZoomRef.current = false }, 600)
  }
  const handleReset = () => {
    // Unpin dragged nodes and clear the interaction lock so the view re-fits.
    filteredNodes.forEach(n => { n.fx = null; n.fy = null })
    hasInteractedRef.current = false
    hasFitRef.current = false
    setSelectedNode(null)
    setHoveredNode(null)
    isProgrammaticZoomRef.current = true
    graphRef.current?.zoomToFit(400, 50)
    setTimeout(() => { isProgrammaticZoomRef.current = false }, 600)
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
      <div className="flex items-center justify-center bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-lg" style={{ height }}>
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Graph Container — this div is measured by ResizeObserver for width only.
          Height is pinned by the `height` prop via inline style. The `w-full` class
          lets it fill its parent's flex/grid cell; overflow-hidden clips the canvas. */}
      <div
        ref={canvasHostRef}
        className="w-full bg-gradient-to-br from-slate-900/80 to-slate-800/80 rounded-lg overflow-hidden"
        style={{ height: graphHeight }}
      >
        <ForceGraph2D
          ref={graphRef}
          graphData={{ nodes: filteredNodes as NodeObject[], links: filteredLinks as LinkObject[] }}
          // FIX: Pass resolved width/height directly. Height = fixed prop (no
          // ResizeObserver feed-back loop). Width = observed width once measured.
          width={graphWidth}
          height={graphHeight}
          nodeCanvasObject={(node, ctx, globalScale) => nodeCanvasObject(node as EpisodicNode, ctx, globalScale)}
          linkCanvasObject={(link, ctx, globalScale) => linkCanvasObject(link as EpisodicLink, ctx, globalScale)}
          onNodeClick={(node) => handleNodeClick(node as EpisodicNode)}
          onNodeHover={(node) => setHoveredNode(node as EpisodicNode | null)}
          onNodeDragEnd={(node) => handleNodeDragEnd(node as EpisodicNode)}
          // FIX: Only mark user-initiated pan/zoom as an interaction. Programmatic
          // zoom (zoomToFit, centerAt) fires onZoom too — suppress those via the ref.
          onZoom={() => {
            if (!isProgrammaticZoomRef.current) {
              hasInteractedRef.current = true
            }
          }}
          nodeId="id"
          linkSource="source"
          linkTarget="target"
          // FIX: Increased warmup + cooldown so the layout fully settles before
          // zoomToFit runs. More ticks = cleaner initial spread.
          warmupTicks={150}
          cooldownTicks={200}
          d3AlphaDecay={0.028}
          d3VelocityDecay={0.4}
          d3AlphaMin={0.005}
          // Node size hint for force-graph internal collision
          nodeRelSize={8}
          // Auto-fit ONCE per topology when the sim stops, unless the user has
          // already interacted with the view (so 30s refetch can't hijack the pan).
          onEngineStop={() => {
            if (!hasFitRef.current && !hasInteractedRef.current) {
              hasFitRef.current = true
              isProgrammaticZoomRef.current = true
              graphRef.current?.zoomToFit(400, 60)
              setTimeout(() => { isProgrammaticZoomRef.current = false }, 600)
            }
          }}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          backgroundColor="transparent"
          minZoom={0.1}
          maxZoom={10}
          dagMode={layoutMode === 'dag' ? 'lr' : null}
          dagLevelDistance={100}
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
      <div className="absolute top-3 left-3 flex flex-col gap-2">
        {/* Node Type Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-xs bg-slate-800/90 text-slate-300 border border-slate-700 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="episode">Episodes</option>
            <option value="root_cause">Root Causes</option>
            <option value="action">Actions</option>
            <option value="service">Services</option>
            <option value="entity">Entities (LLM)</option>
          </select>
        </div>

        {/* Label search — an <input>, deliberately NOT a <select>, so the
            graph touch-sim contract (single episode-type <select>) holds. */}
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search nodes…"
            aria-label="Search nodes by label"
            className="text-xs bg-slate-800/90 text-slate-300 border border-slate-700 rounded-md px-2 py-1 w-40 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder:text-slate-500"
          />
        </div>

        {/* Edge Visibility Toggles */}
        <div className="flex items-center gap-3 text-xs bg-slate-800/90 text-slate-300 border border-slate-700 rounded-md px-2 py-1.5">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={showSimilarTo}
              onChange={(e) => setShowSimilarTo(e.target.checked)}
              className="w-3 h-3 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
            />
            <span>Similar To</span>
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={showEntities}
              onChange={(e) => setShowEntities(e.target.checked)}
              className="w-3 h-3 rounded border-slate-600 bg-slate-700 text-pink-500 focus:ring-pink-500 focus:ring-offset-0"
            />
            <span>Entities</span>
          </label>
        </div>

        {/* Layout Mode Toggle */}
        <div className="flex items-center gap-1 text-xs">
          <button
            onClick={() => setLayoutMode('force')}
            className={`px-2 py-1 rounded-l-md border transition-colors ${
              layoutMode === 'force'
                ? 'bg-blue-600 text-white border-blue-500'
                : 'bg-slate-800/90 text-slate-400 border-slate-700 hover:bg-slate-700'
            }`}
          >
            Force
          </button>
          <button
            onClick={() => setLayoutMode('dag')}
            className={`px-2 py-1 rounded-r-md border-t border-r border-b transition-colors ${
              layoutMode === 'dag'
                ? 'bg-blue-600 text-white border-blue-500'
                : 'bg-slate-800/90 text-slate-400 border-slate-700 hover:bg-slate-700'
            }`}
          >
            Hierarchy
          </button>
        </div>
      </div>

      {/* Stats Overlay */}
      <div className="absolute bottom-3 right-3 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-md border border-slate-700">
        {filteredNodes.length} nodes | {filteredLinks.length} edges
        {filterType !== 'all' && ` (filtered: ${filterType})`}
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex flex-wrap gap-2.5 text-xs bg-slate-900/80 px-3 py-2 rounded-md border border-slate-700">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span className="text-slate-400">Episode</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-orange-500" />
          <span className="text-slate-400">Root Cause</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-cyan-500" />
          <span className="text-slate-400">Action</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-slate-400">Service</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-pink-500" />
          <span className="text-slate-400">Entity (LLM)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-slate-400">Resolved</span>
        </div>
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <div className="absolute top-14 left-3 bg-slate-900/95 border border-slate-700 rounded-lg p-3 max-w-sm shadow-lg">
          <div className="flex items-start justify-between mb-2">
            <div>
              <h4 className="font-medium text-slate-200">{selectedNode.label}</h4>
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                selectedNode.type === 'episode' ? 'bg-purple-500/20 text-purple-400' :
                selectedNode.type === 'root_cause' ? 'bg-orange-500/20 text-orange-400' :
                selectedNode.type === 'action' ? 'bg-cyan-500/20 text-cyan-400' :
                selectedNode.type === 'service' ? 'bg-blue-500/20 text-blue-400' :
                selectedNode.type === 'entity' ? 'bg-pink-500/20 text-pink-400' :
                'bg-slate-500/20 text-slate-400'
              }`}>
                {selectedNode.type.replace('_', ' ')}
              </span>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-500 hover:text-slate-300 ml-2"
            >
              &times;
            </button>
          </div>
          <div className="space-y-1.5 text-xs">
            {/* Common fields */}
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

            {/* Episode-specific fields */}
            {selectedNode.type === 'episode' && (
              <>
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
                {selectedNode.category && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Category:</span>
                    <span className="text-slate-300 capitalize">{selectedNode.category}</span>
                  </div>
                )}
                {selectedNode.rootCause && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Root Cause:</span>
                    <span className="text-orange-400">{selectedNode.rootCause.replace(/_/g, ' ')}</span>
                  </div>
                )}
                {selectedNode.confidence !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Confidence:</span>
                    <span className="text-slate-300">{(selectedNode.confidence * 100).toFixed(0)}%</span>
                  </div>
                )}
                {selectedNode.resolutionTime !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Resolution:</span>
                    <span className="text-green-400">{selectedNode.resolutionTime} min</span>
                  </div>
                )}
                {selectedNode.timestamp && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Detected:</span>
                    <span className="text-slate-300">
                      {new Date(selectedNode.timestamp).toLocaleString()}
                    </span>
                  </div>
                )}
              </>
            )}

            {/* Root Cause-specific fields */}
            {selectedNode.type === 'root_cause' && (
              <>
                {selectedNode.frequency !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Occurrences:</span>
                    <span className="text-slate-300">{selectedNode.frequency}</span>
                  </div>
                )}
                {selectedNode.avgResolutionTime !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Resolution:</span>
                    <span className="text-slate-300">{selectedNode.avgResolutionTime} min</span>
                  </div>
                )}
                {selectedNode.successRate !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Success Rate:</span>
                    <span className={selectedNode.successRate >= 0.9 ? 'text-green-400' : 'text-amber-400'}>
                      {(selectedNode.successRate * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </>
            )}

            {/* Action-specific fields */}
            {selectedNode.type === 'action' && (
              <>
                {selectedNode.usedCount !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Times Used:</span>
                    <span className="text-slate-300">{selectedNode.usedCount}</span>
                  </div>
                )}
                {selectedNode.successRate !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Success Rate:</span>
                    <span className={selectedNode.successRate >= 0.9 ? 'text-green-400' : 'text-amber-400'}>
                      {(selectedNode.successRate * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
                {selectedNode.avgExecutionTime !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Execution:</span>
                    <span className="text-slate-300">{selectedNode.avgExecutionTime}s</span>
                  </div>
                )}
              </>
            )}

            {/* Service-specific fields */}
            {selectedNode.type === 'service' && (
              <>
                {selectedNode.incidentCount !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Incidents:</span>
                    <span className={selectedNode.incidentCount > 1 ? 'text-amber-400' : 'text-slate-300'}>
                      {selectedNode.incidentCount}
                    </span>
                  </div>
                )}
                {selectedNode.lastIncident && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Last Incident:</span>
                    <span className="text-slate-300">
                      {new Date(selectedNode.lastIncident).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </>
            )}

            {/* Entity-specific fields (LLM-extracted) */}
            {selectedNode.type === 'entity' && (
              <>
                {selectedNode.relationCount !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Relations:</span>
                    <span className="text-pink-400">{selectedNode.relationCount}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-500">Source:</span>
                  <span className="text-pink-400">LLM Extracted</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export type { EpisodicNode, EpisodicLink }
