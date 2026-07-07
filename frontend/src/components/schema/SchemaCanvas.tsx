import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Maximize2, Minus, Plus } from 'lucide-react'
import { NODE_H, NODE_W, SchemaLayout } from './layout'
import { SchemaEdge } from './SchemaEdge'
import { SchemaNode } from './SchemaNode'
import { ScrubDerived, TopologyEdge, TopologyNode } from './types'

const PAD = 48
const MIN_ZOOM = 0.4
const MAX_ZOOM = 2.5

interface ViewBox {
  x: number
  y: number
  w: number
  h: number
}

interface SchemaCanvasProps {
  height: number
  layout: SchemaLayout
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  nodeDerived: Map<string, ScrubDerived>
  edgeDerived: Map<string, ScrubDerived>
  selectedKeys: Set<string>
  onNodeClick: (node: TopologyNode, event: React.MouseEvent) => void
  onEdgeClick: (edge: TopologyEdge, event: React.MouseEvent) => void
  onNodeHover: (node: TopologyNode | null, event?: React.PointerEvent) => void
  onEdgeHover: (edge: TopologyEdge | null, event?: React.PointerEvent) => void
  onBackgroundClick: () => void
  /**
   * Episodic view only: per-node / per-edge accent (bare HSL triplet) and
   * per-node sub-label resolvers, so the episodic renderer can colour by TYPE +
   * STATUS / RELATIONSHIP. All optional — the platform path passes none and
   * renders byte-identically to before.
   */
  nodeAccent?: (node: TopologyNode) => string | undefined
  edgeAccent?: (edge: TopologyEdge) => string | undefined
  nodeSubLabel?: (node: TopologyNode) => string | undefined
  /**
   * Flow direction of the laid-out graph. 'lr' (default) anchors edges on the
   * node's left/right faces (platform). 'td' anchors on top/bottom faces so a
   * top-down episodic layout cascades cleanly. Pan/zoom are unaffected.
   */
  orientation?: 'lr' | 'td'
  /**
   * Show an on-canvas zoom-in / zoom-out / fit control cluster (bottom-left).
   * Opt-in — default off, so existing consumers render byte-identically. The
   * embedded cockpit turns it on to make the (otherwise wheel-only) zoom and a
   * one-click "fit to pane" reset discoverable.
   */
  showControls?: boolean
}

/**
 * The schema SVG stage. Owns viewBox pan/zoom only: wheel zooms toward the
 * cursor (screen → user space via getScreenCTM().inverse(), clamped 0.4×–2.5×),
 * background drag pans, background click clears the selection upstream.
 */
export function SchemaCanvas({
  height,
  layout,
  nodes,
  edges,
  nodeDerived,
  edgeDerived,
  selectedKeys,
  onNodeClick,
  onEdgeClick,
  onNodeHover,
  onEdgeHover,
  onBackgroundClick,
  nodeAccent,
  edgeAccent,
  nodeSubLabel,
  orientation = 'lr',
  showControls = false,
}: SchemaCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  const baseViewBox = useMemo<ViewBox>(
    () => ({
      x: -PAD,
      y: -PAD,
      w: Math.max(1, layout.width + PAD * 2),
      h: Math.max(1, layout.height + PAD * 2),
    }),
    [layout],
  )

  const [viewBox, setViewBox] = useState<ViewBox>(baseViewBox)
  const viewBoxRef = useRef(viewBox)
  viewBoxRef.current = viewBox

  // New topology → re-fit the stage.
  useEffect(() => {
    setViewBox(baseViewBox)
  }, [baseViewBox])

  // Wheel zoom must preventDefault (page scroll), so attach non-passively.
  useEffect(() => {
    const svg = svgRef.current
    if (!svg) return
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const ctm = svg.getScreenCTM()
      if (!ctm) return
      const cursor = new DOMPoint(e.clientX, e.clientY).matrixTransform(ctm.inverse())
      const vb = viewBoxRef.current
      const factor = e.deltaY < 0 ? 1 / 1.15 : 1.15
      // zoom = baseW / vb.w; clamp the resulting zoom to [0.4, 2.5].
      const minW = baseViewBox.w / MAX_ZOOM
      const maxW = baseViewBox.w / MIN_ZOOM
      const newW = Math.min(maxW, Math.max(minW, vb.w * factor))
      if (newW === vb.w) return
      const k = newW / vb.w
      setViewBox({
        x: cursor.x - (cursor.x - vb.x) * k,
        y: cursor.y - (cursor.y - vb.y) * k,
        w: newW,
        h: vb.h * k,
      })
    }
    svg.addEventListener('wheel', onWheel, { passive: false })
    return () => svg.removeEventListener('wheel', onWheel)
  }, [baseViewBox])

  // Button-driven zoom about the viewport centre (mirrors the wheel clamp), and
  // a one-click "fit" that snaps back to the whole-graph viewBox.
  const zoomAtCentre = useCallback(
    (factor: number) => {
      const minW = baseViewBox.w / MAX_ZOOM
      const maxW = baseViewBox.w / MIN_ZOOM
      setViewBox((vb) => {
        const newW = Math.min(maxW, Math.max(minW, vb.w * factor))
        if (newW === vb.w) return vb
        const k = newW / vb.w
        const newH = vb.h * k
        return {
          x: vb.x + vb.w / 2 - newW / 2,
          y: vb.y + vb.h / 2 - newH / 2,
          w: newW,
          h: newH,
        }
      })
    },
    [baseViewBox],
  )
  const fitView = useCallback(() => setViewBox(baseViewBox), [baseViewBox])

  // Background drag = pan; background click (no movement) = clear selection.
  const panRef = useRef<{
    pointerId: number
    startClientX: number
    startClientY: number
    startViewBox: ViewBox
    inverse: DOMMatrix
    moved: boolean
  } | null>(null)

  const handlePointerDown = useCallback((e: React.PointerEvent<SVGSVGElement>) => {
    // Nodes and edges stop pointerdown propagation, so reaching here means
    // the press started on the background.
    const svg = svgRef.current
    const ctm = svg?.getScreenCTM()
    if (!svg || !ctm) return
    panRef.current = {
      pointerId: e.pointerId,
      startClientX: e.clientX,
      startClientY: e.clientY,
      startViewBox: viewBoxRef.current,
      inverse: ctm.inverse(),
      moved: false,
    }
    svg.setPointerCapture(e.pointerId)
  }, [])

  const handlePointerMove = useCallback((e: React.PointerEvent<SVGSVGElement>) => {
    const pan = panRef.current
    if (!pan || pan.pointerId !== e.pointerId) return
    const dxPx = e.clientX - pan.startClientX
    const dyPx = e.clientY - pan.startClientY
    if (!pan.moved && Math.hypot(dxPx, dyPx) < 4) return
    pan.moved = true
    const p0 = new DOMPoint(pan.startClientX, pan.startClientY).matrixTransform(pan.inverse)
    const p1 = new DOMPoint(e.clientX, e.clientY).matrixTransform(pan.inverse)
    setViewBox({
      x: pan.startViewBox.x - (p1.x - p0.x),
      y: pan.startViewBox.y - (p1.y - p0.y),
      w: pan.startViewBox.w,
      h: pan.startViewBox.h,
    })
  }, [])

  const handlePointerUp = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      const pan = panRef.current
      if (!pan || pan.pointerId !== e.pointerId) return
      const wasClick = !pan.moved
      panRef.current = null
      if (wasClick) onBackgroundClick()
    },
    [onBackgroundClick],
  )

  return (
    <>
    <svg
      ref={svgRef}
      data-testid="schema-canvas"
      role="application"
      aria-label="Service topology diagram — use Tab to move between nodes, Enter or Space to select"
      className="block h-full w-full touch-none select-none"
      style={{ height }}
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
      preserveAspectRatio="xMidYMid meet"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <defs>
        {/* Flat card body — solid slate, no dramatic glass gradient. */}
        <linearGradient id="schemaNodeFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#141c2c" />
          <stop offset="100%" stopColor="#111825" />
        </linearGradient>
        {/* Crisp flat hairline stroke (no primary-accent glow gradient). */}
        <linearGradient id="schemaNodeStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#2b3850" />
          <stop offset="100%" stopColor="#2b3850" />
        </linearGradient>
        {/* Very subtle inner top highlight. */}
        <linearGradient id="schemaNodeSheen" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.04" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
        {/* Soft glow used by activity halos. */}
        <filter id="schemaGlow" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="9" />
        </filter>
        {/* Arrowheads. */}
        <marker
          id="schemaArrow"
          viewBox="0 0 10 10"
          refX="8.5"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 9 5 L 0 9 z" fill="hsl(217 24% 56%)" />
        </marker>
        <marker
          id="schemaArrowActive"
          viewBox="0 0 10 10"
          refX="8.5"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 9 5 L 0 9 z" style={{ fill: 'hsl(var(--primary))' }} />
        </marker>
        <marker
          id="schemaArrowDynamic"
          viewBox="0 0 10 10"
          refX="8.5"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 9 5 L 0 9 z" fill="hsl(190 95% 50% / 0.85)" />
        </marker>
      </defs>

      {/* Edges under nodes. */}
      <g>
        {edges.map((edge) => {
          const sp = layout.positions.get(edge.source)
          const tp = layout.positions.get(edge.target)
          if (!sp || !tp) return null
          const derived = edgeDerived.get(edge.id)
          // Anchor on left/right faces for 'lr', top/bottom faces for 'td', so
          // the bezier always leaves and enters the node cleanly.
          let x1: number
          let y1: number
          let x2: number
          let y2: number
          if (orientation === 'td') {
            const downward = tp.y >= sp.y
            x1 = sp.x + NODE_W / 2
            y1 = downward ? sp.y + NODE_H : sp.y
            x2 = tp.x + NODE_W / 2
            y2 = downward ? tp.y : tp.y + NODE_H
          } else {
            const forward = tp.x >= sp.x
            x1 = forward ? sp.x + NODE_W : sp.x
            y1 = sp.y + NODE_H / 2
            x2 = forward ? tp.x : tp.x + NODE_W
            y2 = tp.y + NODE_H / 2
          }
          return (
            <SchemaEdge
              key={edge.id}
              edge={edge}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              coCount={derived?.count ?? edge.co_episode_count}
              activity={derived?.activity ?? 0}
              selected={selectedKeys.has(`edge:${edge.id}`)}
              onClick={onEdgeClick}
              onHover={onEdgeHover}
              accent={edgeAccent?.(edge)}
              orientation={orientation}
            />
          )
        })}
      </g>

      {/* Nodes. */}
      <g>
        {nodes.map((node) => {
          const pos = layout.positions.get(node.id)
          if (!pos) return null
          const derived = nodeDerived.get(node.id)
          return (
            <SchemaNode
              key={node.id}
              node={node}
              x={pos.x}
              y={pos.y}
              displayCount={derived?.count ?? node.episode_count}
              activity={derived?.activity ?? 0}
              selected={selectedKeys.has(`node:${node.id}`)}
              onClick={onNodeClick}
              onHover={onNodeHover}
              accent={nodeAccent?.(node)}
              subLabel={nodeSubLabel?.(node)}
            />
          )
        })}
      </g>
    </svg>
      {showControls && (
        <div className="absolute bottom-3 left-3 z-20 flex flex-col gap-1" data-testid="schema-zoom-controls">
          <button
            type="button"
            aria-label="Zoom in"
            title="Zoom in"
            onClick={() => zoomAtCentre(0.8)}
            className="rounded-md border border-slate-700 bg-slate-900/80 p-1.5 text-slate-300 backdrop-blur transition-colors hover:bg-slate-800 hover:text-white"
          >
            <Plus className="h-4 w-4" />
          </button>
          <button
            type="button"
            aria-label="Zoom out"
            title="Zoom out"
            onClick={() => zoomAtCentre(1.25)}
            className="rounded-md border border-slate-700 bg-slate-900/80 p-1.5 text-slate-300 backdrop-blur transition-colors hover:bg-slate-800 hover:text-white"
          >
            <Minus className="h-4 w-4" />
          </button>
          <button
            type="button"
            aria-label="Fit graph to view"
            title="Fit to view"
            onClick={fitView}
            className="rounded-md border border-slate-700 bg-slate-900/80 p-1.5 text-slate-300 backdrop-blur transition-colors hover:bg-slate-800 hover:text-white"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      )}
    </>
  )
}
