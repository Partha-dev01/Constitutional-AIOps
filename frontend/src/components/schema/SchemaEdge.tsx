import React from 'react'
import { TopologyEdge } from './types'

export interface SchemaEdgeProps {
  edge: TopologyEdge
  x1: number
  y1: number
  x2: number
  y2: number
  /** Scrub-derived cumulative co-episode count (stroke width). */
  coCount: number
  /** Scrub-derived current-bucket co-activity (dash speed / opacity). */
  activity: number
  selected: boolean
  onClick: (edge: TopologyEdge, event: React.MouseEvent) => void
  onHover: (edge: TopologyEdge | null, event?: React.PointerEvent) => void
}

/**
 * Cubic-bezier connector with arrowhead, animated dash flow and an invisible
 * 10px hit stroke for hover/click. Dynamic SHIPS_TELEMETRY edges render
 * dashed; width/opacity respond to the scrubbed co-episode activity.
 */
function SchemaEdgeInner({
  edge,
  x1,
  y1,
  x2,
  y2,
  coCount,
  activity,
  selected,
  onClick,
  onHover,
}: SchemaEdgeProps) {
  const dir = Math.sign(x2 - x1) || 1
  const bend = Math.max(40, Math.abs(x2 - x1) * 0.42)
  const d = `M ${x1} ${y1} C ${x1 + dir * bend} ${y1}, ${x2 - dir * bend} ${y2}, ${x2} ${y2}`

  const dynamic = edge.kind === 'dynamic' || edge.relationship === 'SHIPS_TELEMETRY'
  const width = 1.25 + Math.min(2.5, coCount * 0.6) + (selected ? 0.75 : 0)
  const baseOpacity = Math.min(0.95, (dynamic ? 0.55 : 0.45) + activity * 0.2 + (selected ? 0.25 : 0))
  const dashDur = activity > 0 ? Math.max(0.7, 2.4 - activity * 0.6) : dynamic ? 2.8 : 2.4

  const stroke = selected
    ? 'hsl(var(--primary))'
    : dynamic
      ? 'hsl(190 95% 50% / 0.75)'
      : '#5b6b82'
  const marker = dynamic ? 'url(#schemaArrowDynamic)' : selected ? 'url(#schemaArrowActive)' : 'url(#schemaArrow)'

  return (
    <g data-testid={`schema-edge-${edge.id}`}>
      {/* Visible stroke. Dynamic edges are dashed and march on their own. */}
      <path
        d={d}
        fill="none"
        stroke={stroke}
        strokeWidth={width}
        opacity={baseOpacity}
        markerEnd={marker}
        className={dynamic ? 'schema-edge-dynamic' : undefined}
        style={dynamic ? ({ '--schema-dash-dur': `${dashDur}s` } as React.CSSProperties) : undefined}
        pointerEvents="none"
      />
      {/* Animated flow overlay on static edges (primary-tinted dashes). */}
      {!dynamic && (
        <path
          d={d}
          fill="none"
          stroke={selected ? 'hsl(var(--primary))' : 'hsl(var(--primary) / 0.7)'}
          strokeWidth={Math.max(1, width - 0.5)}
          opacity={Math.min(0.9, 0.3 + activity * 0.25 + (selected ? 0.3 : 0))}
          className="schema-edge-flow"
          style={{ '--schema-dash-dur': `${dashDur}s` } as React.CSSProperties}
          pointerEvents="none"
        />
      )}
      {/* Invisible wide hit stroke for hover/click. */}
      <path
        d={d}
        fill="none"
        stroke="transparent"
        strokeWidth={10}
        style={{ cursor: 'pointer' }}
        pointerEvents="stroke"
        onClick={(e) => {
          e.stopPropagation()
          onClick(edge, e)
        }}
        onPointerDown={(e) => e.stopPropagation()}
        onPointerEnter={(e) => onHover(edge, e)}
        onPointerMove={(e) => onHover(edge, e)}
        onPointerLeave={() => onHover(null)}
      />
    </g>
  )
}

export const SchemaEdge = React.memo(SchemaEdgeInner)
