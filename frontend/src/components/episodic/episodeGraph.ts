/**
 * Episode Browser — pure data helpers.
 *
 * The Console's episodic view used to dump every episode, root cause, service,
 * action and entity (plus the dense similar_to web) onto one shared topology
 * canvas at once — an unreadable hairball with truncated labels. The Episode
 * Browser flips that around: it presents episodes as a browsable LIST, and for
 * the ONE episode an operator selects it builds a tiny, legible causal
 * subgraph (episode → root cause → actions → touched services) that renders
 * through the same polished SchemaCanvas.
 *
 * This module owns the data transforms only (no React). It:
 *   1. normalises the raw episodic nodes/links into convenient lookups,
 *   2. repairs the well-known double-prefix endpoint-id mismatch so causal
 *      edges actually resolve,
 *   3. derives, per episode, its root cause / actions / services, and
 *   4. builds the focused TopologyNode/TopologyEdge subgraph the canvas wants.
 *
 * Everything here is framework-free and unit-testable.
 */

import type { EpisodicLink, EpisodicNode } from '../EpisodicGraphExplorer'
import type { TopologyEdge, TopologyNode } from '../schema/types'

// Tier flow (top → down) mirrors the episodic semantics:
// episode/incident (0) → root_cause (1) → action (2) → service (3).
const TYPE_TIER: Record<EpisodicNode['type'], number> = {
  episode: 0,
  incident: 0,
  root_cause: 1,
  action: 2,
  entity: 2,
  service: 3,
}

// Type accents (bare HSL triplets), desaturated from the original neon
// EpisodicGraphExplorer.getNodeColor / schema/types KIND_ACCENT palette so the
// canvas reads as muted category tags rather than a glowing rainbow spread.
// Hues are preserved for identity; saturation/lightness are toned down.
const TYPE_ACCENT: Record<string, string> = {
  episode: '271 35% 58%', // muted purple
  incident: '0 84% 60%', // red       (#ef4444)
  root_cause: '25 45% 52%', // muted orange
  action: '189 30% 45%', // muted cyan
  service: '217 40% 58%', // muted blue
  entity: '330 30% 58%', // muted pink
}

// Status accents override the type accent for the status-driven kinds (episode
// lifecycle + service health), mirroring getNodeColor's status branches.
const STATUS_ACCENT: Record<string, string> = {
  healthy: '142 71% 45%', // green  (#22c55e)
  resolved: '142 71% 45%', // green (#22c55e)
  warning: '38 92% 50%', // amber   (#f59e0b)
  critical: '0 84% 60%', // red     (#ef4444)
  detected: '38 92% 50%', // amber  (#f59e0b)
  analyzing: '258 90% 66%', // purple (#8b5cf6)
  remediating: '217 91% 60%', // blue (#3b82f6)
}

const RELATION_ACCENT: Record<string, string> = {
  depends_on: '217 91% 60%',
  affects: '0 84% 60%',
  caused_by: '25 95% 53%',
  resolved_by: '142 71% 45%',
  similar_to: '258 90% 66%',
  experienced: '25 95% 53%',
  caused: '0 84% 60%',
  affected: '38 92% 50%',
  triggered: '0 72% 51%',
  degraded: '38 92% 50%',
  monitors: '217 91% 60%',
  connected_to: '217 91% 60%',
}

const LLM_RELATION_ACCENT = '330 81% 60%' // pink — unknown LLM edges
const DEFAULT_RELATION_ACCENT = '215 16% 47%' // slate-gray

export const STATUS_HEALTH: Record<string, TopologyNode['health']> = {
  healthy: 'healthy',
  resolved: 'healthy',
  warning: 'warning',
  analyzing: 'warning',
  detected: 'warning',
  remediating: 'unknown',
  critical: 'critical',
}

/** Accent (bare HSL triplet) for an episodic node by TYPE + STATUS. */
export function nodeAccentFor(type: string, status?: string): string {
  if ((type === 'service' || type === 'episode') && status && STATUS_ACCENT[status]) {
    return STATUS_ACCENT[status]
  }
  return TYPE_ACCENT[type] ?? DEFAULT_RELATION_ACCENT
}

/** Accent (bare HSL triplet) for an episodic edge by RELATIONSHIP. */
export function edgeAccentFor(link: Pick<EpisodicLink, 'type' | 'metadata'>): string {
  const relation = (link.type ?? 'default').toLowerCase()
  if (RELATION_ACCENT[relation]) return RELATION_ACCENT[relation]
  if (link.metadata?.extraction_method === 'llm') return LLM_RELATION_ACCENT
  return DEFAULT_RELATION_ACCENT
}

/** Pretty-print a snake_cased relationship / category for display. */
export const titleCase = (text: string): string => text.replace(/_/g, ' ')

const asNumber = (value: unknown): number | undefined =>
  typeof value === 'number' && Number.isFinite(value) ? value : undefined

/** Normalise root-cause text so "Connection Timeout" matches "connection_timeout". */
const normaliseRc = (text: string): string => text.trim().toLowerCase().replace(/[\s_]+/g, ' ')

/** Resolve a link endpoint (string id or node ref) to its id string. */
const endpointId = (end: string | EpisodicNode): string =>
  typeof end === 'string' ? end : end.id

// `transformEpisodes` re-prefixes node ids with their type on top of the raw
// backend id (e.g. `root_cause-rootcause-connection_timeout`), while backend
// EDGE endpoints reference the raw id (`rootcause-connection_timeout`). Repair
// each endpoint by trying the raw id first, then the type-prefixed form.
const ENDPOINT_PREFIXES = ['root_cause-', 'action-', 'entity-', 'service-', 'episode-', 'incident-']

export function resolveEndpoint(raw: string, nodeIds: ReadonlySet<string>): string | undefined {
  if (nodeIds.has(raw)) return raw
  for (const prefix of ENDPOINT_PREFIXES) {
    const candidate = `${prefix}${raw}`
    if (nodeIds.has(candidate)) return candidate
  }
  return undefined
}

// ---------------------------------------------------------------------------
// Indexed view of the raw episodic graph: id→node map + resolved causal edges,
// computed ONCE and reused for every episode focus (cheap re-selection).
// ---------------------------------------------------------------------------

export interface ResolvedEdge {
  source: string
  target: string
  relation: string
  weight: number
  /** Original link (undefined for a synthesized caused_by edge). */
  link?: EpisodicLink
}

export interface EpisodeSummary {
  /** Adapted node id (e.g. `episode-28`). */
  id: string
  node: EpisodicNode
  /** Full, untruncated episode title. */
  title: string
  status?: string
  severity?: string
  category?: string
  /** Root-cause display text (from the episode field or a matched RC node). */
  rootCauseLabel?: string
  /** ms timestamp for sorting (NaN when absent → sorted last). */
  time: number
  /** Service node ids this episode touched. */
  serviceIds: string[]
  /** Action node ids that resolved this episode. */
  actionIds: string[]
  /** Root-cause node id (when a standalone RC node matched). */
  rootCauseId?: string
}

export interface EpisodicIndex {
  /** All adapted nodes by id. */
  nodeById: Map<string, EpisodicNode>
  /** Resolved causal edges (similar_to excluded — see focus builder). */
  edges: ResolvedEdge[]
  /** Per-episode summaries, newest first. */
  episodes: EpisodeSummary[]
  /** Count of every raw node by type (for the KPI strip). */
  countsByType: Map<string, number>
}

/**
 * Build the reusable index from the raw episodic nodes/links. Pure — safe to
 * memoize on (nodes, links) identity.
 */
export function buildIndex(nodes: EpisodicNode[], links: EpisodicLink[]): EpisodicIndex {
  const nodeById = new Map(nodes.map((n) => [n.id, n]))
  const ids = new Set(nodeById.keys())

  // Resolve + repair every real link (drop unresolved / self / similar_to —
  // similar_to is the dense crosser and is never part of a single episode's
  // causal story).
  const edges: ResolvedEdge[] = []
  for (const link of links) {
    const relation = (link.type ?? 'related').toLowerCase()
    if (relation === 'similar_to') continue
    const source = resolveEndpoint(endpointId(link.source), ids)
    const target = resolveEndpoint(endpointId(link.target), ids)
    if (source === undefined || target === undefined || source === target) continue
    edges.push({ source, target, relation, weight: asNumber(link.weight) ?? 0, link })
  }

  // Index a standalone root_cause node id by its normalised label so an
  // episode's free-text `rootCause` can be matched to it.
  const rootCauseByLabel = new Map<string, string>()
  for (const node of nodes) {
    if (node.type === 'root_cause') rootCauseByLabel.set(normaliseRc(node.label), node.id)
  }

  // Outgoing causal edges per source, for per-episode lookups.
  const outgoing = new Map<string, ResolvedEdge[]>()
  for (const e of edges) {
    const list = outgoing.get(e.source)
    if (list) list.push(e)
    else outgoing.set(e.source, [e])
  }

  const episodes: EpisodeSummary[] = []
  for (const node of nodes) {
    if (node.type !== 'episode' && node.type !== 'incident') continue
    const outs = outgoing.get(node.id) ?? []
    const serviceIds: string[] = []
    const actionIds: string[] = []
    let rootCauseId: string | undefined
    for (const e of outs) {
      const target = nodeById.get(e.target)
      if (!target) continue
      if (target.type === 'service' && !serviceIds.includes(e.target)) serviceIds.push(e.target)
      else if (target.type === 'action' && !actionIds.includes(e.target)) actionIds.push(e.target)
      else if (target.type === 'root_cause' && rootCauseId === undefined) rootCauseId = e.target
    }
    // Fall back to a label match when no caused_by edge resolved to an RC node.
    if (rootCauseId === undefined && node.rootCause) {
      const matched = rootCauseByLabel.get(normaliseRc(node.rootCause))
      if (matched && matched !== node.id) rootCauseId = matched
    }
    const rcNode = rootCauseId ? nodeById.get(rootCauseId) : undefined
    const rootCauseLabel = rcNode?.label ?? (node.rootCause ? titleCase(node.rootCause) : undefined)
    const time = node.timestamp ? new Date(node.timestamp).getTime() : Number.NaN

    episodes.push({
      id: node.id,
      node,
      title: node.label,
      status: node.status,
      severity: node.severity,
      category: node.category,
      rootCauseLabel,
      time,
      serviceIds,
      actionIds,
      rootCauseId,
    })
  }

  // Newest first; episodes without a timestamp sink to the bottom but keep a
  // stable relative order.
  episodes.sort((a, b) => {
    const at = Number.isNaN(a.time) ? -Infinity : a.time
    const bt = Number.isNaN(b.time) ? -Infinity : b.time
    return bt - at
  })

  const countsByType = new Map<string, number>()
  for (const n of nodes) countsByType.set(n.type, (countsByType.get(n.type) ?? 0) + 1)

  return { nodeById, edges, episodes, countsByType }
}

// ---------------------------------------------------------------------------
// Focused subgraph for one episode: the episode + its root cause + actions +
// touched services, as TopologyNode/TopologyEdge for the shared canvas.
// ---------------------------------------------------------------------------

export interface FocusGraph {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  /** Adapted-id → original episodic node (drawer/hover detail). */
  nodeById: Map<string, EpisodicNode>
  /** Topology-edge-id → original/ synthesized link (drawer/hover detail). */
  linkById: Map<string, EpisodicLink>
}

function toTopologyNode(node: EpisodicNode): TopologyNode {
  return {
    id: node.id,
    label: node.label,
    kind: node.type,
    tier: TYPE_TIER[node.type] ?? 2,
    health: (node.status && STATUS_HEALTH[node.status]) ?? 'unknown',
    episode_count: 0,
    incident_count: 0,
    buckets: [],
    recent_episodes: [],
    meta: {},
  }
}

/**
 * Build the focused causal subgraph for a single episode. Only the episode and
 * the nodes one causal hop away (root cause, actions, services) are included,
 * so the canvas renders a clean 3-6 node cascade with no crossing edges.
 */
export function buildFocusGraph(index: EpisodicIndex, episodeId: string): FocusGraph | null {
  const episode = index.nodeById.get(episodeId)
  if (!episode) return null
  const summary = index.episodes.find((e) => e.id === episodeId)
  if (!summary) return null

  const keep = new Set<string>([episodeId])
  if (summary.rootCauseId) keep.add(summary.rootCauseId)
  for (const id of summary.actionIds) keep.add(id)
  for (const id of summary.serviceIds) keep.add(id)

  const nodes: TopologyNode[] = []
  const nodeById = new Map<string, EpisodicNode>()
  for (const id of keep) {
    const n = index.nodeById.get(id)
    if (!n) continue
    nodes.push(toTopologyNode(n))
    nodeById.set(id, n)
  }

  // Causal edges between kept nodes, plus a synthesized episode→root_cause edge
  // when the backend omitted the explicit caused_by link.
  const edges: TopologyEdge[] = []
  const linkById = new Map<string, EpisodicLink>()
  const seen = new Set<string>()
  const pushEdge = (source: string, target: string, relation: string, weight: number, link?: EpisodicLink) => {
    if (!keep.has(source) || !keep.has(target) || source === target) return
    let id = `${source}->${target}:${relation}`
    if (seen.has(id)) id = `${id}#${seen.size}`
    seen.add(id)
    linkById.set(id, link ?? { source, target, type: relation })
    edges.push({
      id,
      source,
      target,
      relationship: 'DEPENDS_ON',
      kind: 'static',
      co_episode_count: weight,
      buckets: [],
    })
  }

  const pairSeen = new Set<string>()
  for (const e of index.edges) {
    if (!keep.has(e.source) || !keep.has(e.target)) continue
    pairSeen.add(`${e.source}->${e.target}`)
    pushEdge(e.source, e.target, e.relation, e.weight, e.link)
  }
  // Synthesized caused_by so the root cause always hangs under the episode.
  if (summary.rootCauseId && !pairSeen.has(`${episodeId}->${summary.rootCauseId}`)) {
    pushEdge(episodeId, summary.rootCauseId, 'caused_by', 0)
  }

  return { nodes, edges, nodeById, linkById }
}
