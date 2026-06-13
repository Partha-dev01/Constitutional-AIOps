import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
    <svg
      ref={svgRef}
      data-testid="schema-canvas"
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
        {/* Glass-card body: vertical dark gradient. */}
        <linearGradient id="schemaNodeFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1b2540" stopOpacity="0.97" />
          <stop offset="100%" stopColor="#0c1322" stopOpacity="0.97" />
        </linearGradient>
        {/* Gradient hairline stroke, mimicking .glass-card (landing.css). */}
        <linearGradient id="schemaNodeStroke" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" style={{ stopColor: 'hsl(var(--border))' }} />
          <stop offset="45%" style={{ stopColor: 'hsl(var(--primary) / 0.55)' }} />
          <stop offset="100%" style={{ stopColor: 'hsl(var(--border))' }} />
        </linearGradient>
        {/* Inner top highlight. */}
        <linearGradient id="schemaNodeSheen" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.09" />
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
          const forward = tp.x >= sp.x
          const x1 = forward ? sp.x + NODE_W : sp.x
          const x2 = forward ? tp.x : tp.x + NODE_W
          const derived = edgeDerived.get(edge.id)
          return (
            <SchemaEdge
              key={edge.id}
              edge={edge}
              x1={x1}
              y1={sp.y + NODE_H / 2}
              x2={x2}
              y2={tp.y + NODE_H / 2}
              coCount={derived?.count ?? edge.co_episode_count}
              activity={derived?.activity ?? 0}
              selected={selectedKeys.has(`edge:${edge.id}`)}
              onClick={onEdgeClick}
              onHover={onEdgeHover}
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
            />
          )
        })}
      </g>
    </svg>
  )
}
