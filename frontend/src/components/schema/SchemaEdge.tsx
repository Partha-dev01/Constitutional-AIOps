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
  /**
   * Episodic view only: a bare HSL accent triplet that colours the connector by
   * the episodic RELATIONSHIP (caused_by, resolved_by, …). Omitted on the
   * platform path → the static/dynamic colour logic below is used unchanged.
   * Selection always wins (primary-blue), in both views.
   */
  accent?: string
  /**
   * Connector flow: 'lr' (default, platform) curves horizontally; 'td' curves
   * vertically so a top-down episodic stack reads as a clean cascade.
   */
  orientation?: 'lr' | 'td'
}

/**
 * Cubic-bezier connector with arrowhead and an invisible 10px hit stroke for
 * hover/click. Dynamic SHIPS_TELEMETRY edges render as a static dashed line;
 * width/opacity respond to the scrubbed co-episode activity.
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
  accent,
  orientation = 'lr',
}: SchemaEdgeProps) {
  // 'lr' curves with horizontal tangents (platform). 'td' curves with vertical
  // tangents so a top-down stack cascades cleanly from node bottom to node top.
  const d =
    orientation === 'td'
      ? (() => {
          const dir = Math.sign(y2 - y1) || 1
          const bend = Math.max(40, Math.abs(y2 - y1) * 0.42)
          return `M ${x1} ${y1} C ${x1} ${y1 + dir * bend}, ${x2} ${y2 - dir * bend}, ${x2} ${y2}`
        })()
      : (() => {
          const dir = Math.sign(x2 - x1) || 1
          const bend = Math.max(40, Math.abs(x2 - x1) * 0.42)
          return `M ${x1} ${y1} C ${x1 + dir * bend} ${y1}, ${x2 - dir * bend} ${y2}, ${x2} ${y2}`
        })()

  const dynamic = edge.kind === 'dynamic' || edge.relationship === 'SHIPS_TELEMETRY'
  const width = 1.25 + Math.min(2.5, coCount * 0.6) + (selected ? 0.75 : 0)
  const baseOpacity = Math.min(0.95, (dynamic ? 0.6 : 0.52) + activity * 0.2 + (selected ? 0.25 : 0))
  // Episodic relationship edges are kept deliberately faint so a dense memory
  // graph reads as a soft web rather than an opaque hairball (selection pops).
  const effectiveOpacity = accent && !selected ? baseOpacity * 0.55 : baseOpacity

  // Episodic accent (when supplied) colours the unselected connector by
  // relationship; selection still wins so the primary-blue selected state reads
  // the same in both views. Platform path: accent is undefined → unchanged.
  const stroke = selected
    ? 'hsl(var(--primary))'
    : accent
      ? `hsl(${accent})`
      : dynamic
        ? 'hsl(190 95% 50% / 0.8)'
        : 'hsl(217 24% 56%)'
  const marker = dynamic ? 'url(#schemaArrowDynamic)' : selected ? 'url(#schemaArrowActive)' : 'url(#schemaArrow)'

  return (
    <g data-testid={`schema-edge-${edge.id}`}>
      {/* Visible stroke. Dynamic (telemetry) edges render as a static dashed
          line — no marching-ants animation. */}
      <path
        d={d}
        fill="none"
        stroke={stroke}
        strokeWidth={width}
        strokeDasharray={dynamic ? '5 6' : undefined}
        opacity={effectiveOpacity}
        markerEnd={marker}
        pointerEvents="none"
      />
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
