import React from 'react'
import {
  Activity,
  Box,
  Brain,
  Database,
  Globe,
  Monitor,
  Radio,
  Server,
} from 'lucide-react'
import { NODE_H, NODE_W } from './layout'
import { TopologyNode } from './types'

/** Health-dot palette: green / amber / red / slate. */
const HEALTH_COLOR: Record<string, string> = {
  healthy: '#22c55e',
  warning: '#f59e0b',
  critical: '#ef4444',
  unknown: '#64748b',
}

const KIND_ICON: Record<string, typeof Server> = {
  gateway: Globe,
  frontend: Monitor,
  backend: Server,
  datastore: Database,
  observability: Activity,
  llm: Brain,
  edge: Radio,
}

const truncate = (text: string, max: number): string =>
  text.length > max ? `${text.slice(0, max - 1)}…` : text

export interface SchemaNodeProps {
  node: TopologyNode
  x: number
  y: number
  /** Scrub-derived cumulative episode count (badge). */
  displayCount: number
  /** Scrub-derived current-bucket activity (glow intensity). */
  activity: number
  selected: boolean
  onClick: (node: TopologyNode, event: React.MouseEvent) => void
  onHover: (node: TopologyNode | null, event?: React.PointerEvent) => void
}

/**
 * SVG glass card for one platform service. Pure + memoized: re-renders only
 * when its own scrub-derived numbers or selection state change.
 */
function SchemaNodeInner({
  node,
  x,
  y,
  displayCount,
  activity,
  selected,
  onClick,
  onHover,
}: SchemaNodeProps) {
  const Icon = KIND_ICON[node.kind] ?? Box
  const healthColor = HEALTH_COLOR[node.health] ?? HEALTH_COLOR.unknown
  const glow = Math.min(0.5, activity * 0.22)
  const subLabel = node.meta.port ? `${node.kind} · :${node.meta.port}` : node.kind

  return (
    <g
      className="schema-node"
      transform={`translate(${x}, ${y})`}
      data-testid={`schema-node-${node.id}`}
      onClick={(e) => {
        e.stopPropagation()
        onClick(node, e)
      }}
      onPointerDown={(e) => e.stopPropagation()}
      onPointerEnter={(e) => onHover(node, e)}
      onPointerMove={(e) => onHover(node, e)}
      onPointerLeave={() => onHover(null)}
    >
      {/* Activity glow: brightness driven by the scrubbed current bucket. */}
      {glow > 0 && (
        <rect
          x={-6}
          y={-6}
          width={NODE_W + 12}
          height={NODE_H + 12}
          rx={14}
          fill="hsl(var(--primary))"
          opacity={glow}
          filter="url(#schemaGlow)"
          pointerEvents="none"
        />
      )}

      {/* Selected ring. */}
      {selected && (
        <rect
          x={-4}
          y={-4}
          width={NODE_W + 8}
          height={NODE_H + 8}
          rx={13}
          fill="none"
          stroke="hsl(var(--primary))"
          strokeWidth={1.75}
          opacity={0.95}
          pointerEvents="none"
        />
      )}

      {/* Glass body: gradient fill + gradient hairline stroke (.glass-card). */}
      <rect
        className="schema-node-body"
        width={NODE_W}
        height={NODE_H}
        rx={10}
        fill="url(#schemaNodeFill)"
        stroke="url(#schemaNodeStroke)"
        strokeWidth={1.25}
      />
      {/* Inner top highlight, mimicking .glass-card::before. */}
      <rect
        x={1}
        y={1}
        width={NODE_W - 2}
        height={26}
        rx={9}
        fill="url(#schemaNodeSheen)"
        pointerEvents="none"
      />

      {/* Kind glyph. */}
      <g transform="translate(11, 13)" style={{ color: '#94a3b8' }} pointerEvents="none">
        <Icon width={16} height={16} strokeWidth={1.75} />
      </g>

      {/* Label + sub-label. */}
      <text
        x={36}
        y={24}
        fill="#e2e8f0"
        fontSize={12}
        fontWeight={600}
        pointerEvents="none"
      >
        {truncate(node.label, 15)}
      </text>
      <text x={36} y={40} fill="#7c8aa0" fontSize={9} pointerEvents="none">
        {truncate(subLabel, 22)}
      </text>

      {/* Health dot (bottom-right) + critical pulse ring. */}
      {node.health === 'critical' && (
        <circle
          className="schema-critical-pulse"
          cx={NODE_W - 14}
          cy={NODE_H - 14}
          r={8}
          fill="none"
          stroke={healthColor}
          strokeWidth={1.5}
          pointerEvents="none"
        />
      )}
      <circle
        cx={NODE_W - 14}
        cy={NODE_H - 14}
        r={4}
        fill={healthColor}
        stroke="rgba(2,6,23,0.6)"
        strokeWidth={1}
        pointerEvents="none"
      >
        <title>{`${node.health}${node.health_reason ? `: ${node.health_reason}` : ''}`}</title>
      </circle>

      {/* Episode-count badge (top-right corner, scrub-aware via data-count). */}
      <g
        data-count={displayCount}
        transform={`translate(${NODE_W - 2}, 2)`}
        opacity={displayCount === 0 ? 0.35 : 1}
        pointerEvents="none"
      >
        <rect x={-15} y={-9} width={30} height={18} rx={9} fill="#16213a" stroke="hsl(var(--primary) / 0.55)" strokeWidth={1} />
        <text x={0} y={3.5} textAnchor="middle" fontSize={10} fontWeight={600} fill="#c7d2fe">
          {displayCount}
        </text>
      </g>
    </g>
  )
}

export const SchemaNode = React.memo(SchemaNodeInner)
