/**
 * Schema mode — shared types.
 *
 * The Topology* types mirror the FROZEN payload contract of
 * `GET /api/v1/graph/topology` (see session14-schema-mode plan). The backend
 * lane builds the producer; the canonical sample lives in
 * `frontend/e2e/fixtures/topology.json`. Do not rename fields.
 */

export type SchemaHealth = 'healthy' | 'warning' | 'critical' | 'unknown'

export type SchemaSeverity = 'info' | 'warning' | 'error' | 'critical'

export interface TopologyRecentEpisode {
  id: string
  title: string
  severity: SchemaSeverity
  at: string
}

export interface TopologyNodeMeta {
  port?: number | null
  description?: string | null
  edge_label?: string | null
}

export interface TopologyNode {
  id: string
  label: string
  /** gateway | frontend | backend | datastore | observability | llm | edge */
  kind: string
  tier: number
  health: SchemaHealth
  health_reason?: string | null
  episode_count: number
  incident_count: number
  last_episode_at?: string | null
  /** Per-bucket episode counts, oldest → newest; sum === episode_count. */
  buckets: number[]
  recent_episodes: TopologyRecentEpisode[]
  meta: TopologyNodeMeta
}

export interface TopologyEdge {
  /** "source->target" */
  id: string
  source: string
  target: string
  relationship: 'DEPENDS_ON' | 'SHIPS_TELEMETRY'
  kind: 'static' | 'dynamic'
  co_episode_count: number
  /** Per-bucket co-episode counts, oldest → newest. */
  buckets: number[]
}

export interface TopologyStats {
  nodes: number
  edges: number
  episodes_in_window: number
  source: string
}

export interface TopologyResponse {
  generated_at: string
  window_hours: number
  bucket_minutes: number
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  stats: TopologyStats
}

// ---------------------------------------------------------------------------
// Selection (canvas multi-select → Ask AI chips). Keys are "node:<id>" /
// "edge:<id>" so a node and an edge can never collide in the Map.
// ---------------------------------------------------------------------------

export type SelectedItem =
  | { key: string; type: 'node'; node: TopologyNode }
  | { key: string; type: 'edge'; edge: TopologyEdge }

/** A hovered or drawer-focused canvas element. */
export type FocusTarget =
  | { type: 'node'; node: TopologyNode }
  | { type: 'edge'; edge: TopologyEdge }

/**
 * Scrub-derived display values for one node/edge: cumulative count through
 * the active bucket + the active bucket's own activity. Pure useMemo output —
 * scrubbing never refetches and never recomputes the layout.
 */
export interface ScrubDerived {
  count: number
  activity: number
}

export const nodeKey = (id: string): string => `node:${id}`
export const edgeKey = (id: string): string => `edge:${id}`

/** True for dynamically-discovered edge-host nodes (pinned to the last layer). */
export function isEdgeHostNode(node: Pick<TopologyNode, 'id' | 'kind'>): boolean {
  return node.kind === 'edge' || node.id.startsWith('edge:')
}

// ---------------------------------------------------------------------------
// Chat selection-context payload (FROZEN contract — backend renders it).
// ---------------------------------------------------------------------------

export interface SchemaChatContextNode {
  id: string
  label: string
  kind: string
  health: SchemaHealth
  episode_count: number
  incident_count: number
  recent: { title: string; severity: SchemaSeverity; at: string }[]
}

export interface SchemaChatContextEdge {
  source: string
  target: string
  relationship: string
  co_episode_count: number
}

export interface SchemaChatContext {
  source: 'schema-graph'
  window_hours: number
  selection: {
    nodes: SchemaChatContextNode[]
    edges: SchemaChatContextEdge[]
  }
  /** Index signature so the context can ride ChatRequest.context untouched. */
  [key: string]: unknown
}

/** Build the frozen chat-context payload from the current selection. */
export function buildSchemaChatContext(
  items: SelectedItem[],
  windowHours: number,
): SchemaChatContext {
  const nodes: SchemaChatContextNode[] = []
  const edges: SchemaChatContextEdge[] = []
  for (const item of items) {
    if (item.type === 'node') {
      const n = item.node
      nodes.push({
        id: n.id,
        label: n.label,
        kind: n.kind,
        health: n.health,
        episode_count: n.episode_count,
        incident_count: n.incident_count,
        // Contract: at most 2 recent episodes per node.
        recent: n.recent_episodes.slice(0, 2).map((e) => ({
          title: e.title,
          severity: e.severity,
          at: e.at,
        })),
      })
    } else {
      const e = item.edge
      edges.push({
        source: e.source,
        target: e.target,
        relationship: e.relationship,
        co_episode_count: e.co_episode_count,
      })
    }
  }
  return {
    source: 'schema-graph',
    window_hours: windowHours,
    selection: { nodes, edges },
  }
}
