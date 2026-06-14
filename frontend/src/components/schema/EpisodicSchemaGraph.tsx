import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Loader2, Search, Workflow } from 'lucide-react'
import type { EpisodicLink, EpisodicNode } from '../EpisodicGraphExplorer'
import { layoutTopology } from './layout'
import { SchemaCanvas } from './SchemaCanvas'
import { HoverCard } from './HoverCard'
import { DetailDrawer } from './DetailDrawer'
import {
  EpisodicDetail,
  FocusTarget,
  ScrubDerived,
  SelectedItem,
  TopologyEdge,
  TopologyNode,
  edgeKey,
  nodeKey,
} from './types'

// ---------------------------------------------------------------------------
// Episodic ↔ topology adapter.
//
// The Console episodic view reuses the platform SchemaGraph's polished SVG stage
// (SchemaCanvas + DetailDrawer + HoverCard + the layered layout). Those parts
// speak TopologyNode/TopologyEdge, so this component ADAPTS the episodic
// node/link shape into that contract, lays it out TOP-DOWN, and colours nodes /
// edges by episodic semantics — without touching the platform topology path.
//
// Tier flow (top → down): episode (0) → root_cause (1) → action (2) →
// service (3). Entities attach near whatever they relate to (floor tier 2) and
// "resolved" is a STATUS (green), never its own layer.
// ---------------------------------------------------------------------------

const TYPE_TIER: Record<EpisodicNode['type'], number> = {
  episode: 0,
  incident: 0,
  root_cause: 1,
  action: 2,
  entity: 2,
  service: 3,
}

// Bare HSL triplets (consumed as `hsl(${accent})`) mirroring the canonical hex
// palette in EpisodicGraphExplorer's getNodeColor / getLinkColor, so the new
// renderer reads with identical semantics.
const STATUS_HEALTH: Record<string, TopologyNode['health']> = {
  healthy: 'healthy',
  resolved: 'healthy',
  warning: 'warning',
  analyzing: 'warning',
  detected: 'warning',
  remediating: 'unknown',
  critical: 'critical',
}

// Type accents (HSL triplets) — match KIND_ACCENT's episodic entries.
const TYPE_ACCENT: Record<string, string> = {
  episode: '271 91% 65%', // purple  (#a855f7)
  root_cause: '25 95% 53%', // orange (#f97316)
  action: '189 94% 43%', // cyan    (#06b6d4)
  service: '217 91% 60%', // blue    (#3b82f6)
  entity: '330 81% 60%', // pink     (#ec4899)
  incident: '0 84% 60%', // red      (#ef4444)
}

// Status accents that override the type accent (episode lifecycle + service
// health), mirroring getNodeColor's status branches.
const STATUS_ACCENT: Record<string, string> = {
  healthy: '142 71% 45%', // green  (#22c55e)
  resolved: '142 71% 45%', // green (#22c55e)
  warning: '38 92% 50%', // amber   (#f59e0b)
  critical: '0 84% 60%', // red     (#ef4444)
  detected: '38 92% 50%', // amber  (#f59e0b)
  analyzing: '258 90% 66%', // purple (#8b5cf6)
  remediating: '217 91% 60%', // blue (#3b82f6)
}

// Edge accents by relationship (HSL triplets) mirroring getLinkColor.
const RELATION_ACCENT: Record<string, string> = {
  depends_on: '217 91% 60%', // blue   (#3b82f6)
  affects: '0 84% 60%', // red          (#ef4444)
  caused_by: '25 95% 53%', // orange    (#f97316)
  resolved_by: '142 71% 45%', // green  (#22c55e)
  similar_to: '258 90% 66%', // purple  (#8b5cf6)
  experienced: '25 95% 53%', // orange  (#f97316)
  caused: '0 84% 60%', // red           (#ef4444)
  affected: '38 92% 50%', // amber      (#f59e0b)
  triggered: '0 72% 51%', // red        (#dc2626)
  degraded: '38 92% 50%', // amber      (#f59e0b)
  monitors: '217 91% 60%', // blue      (#3b82f6)
  connected_to: '217 91% 60%', // blue  (#3b82f6)
}

const LLM_RELATION_ACCENT = '330 81% 60%' // pink (#ec4899) for unknown LLM edges
const DEFAULT_RELATION_ACCENT = '215 16% 47%' // slate-gray (#64748b)

// Human labels + stable display order for the type filter / legend pills.
const TYPE_LABEL: Record<string, string> = {
  episode: 'Episode',
  incident: 'Incident',
  root_cause: 'Root Cause',
  action: 'Action',
  service: 'Service',
  entity: 'Entity',
}
const TYPE_ORDER: EpisodicNode['type'][] = [
  'episode',
  'incident',
  'root_cause',
  'action',
  'service',
  'entity',
]

/** Accent (HSL triplet) for an episodic node by TYPE + STATUS. */
function nodeAccentFor(type: string, status?: string): string {
  // service + episode are status-driven; other types are type-driven.
  if ((type === 'service' || type === 'episode') && status && STATUS_ACCENT[status]) {
    return STATUS_ACCENT[status]
  }
  return TYPE_ACCENT[type] ?? DEFAULT_RELATION_ACCENT
}

/** Accent (HSL triplet) for an episodic edge by RELATIONSHIP. */
function edgeAccentFor(link: EpisodicLink): string {
  const relation = (link.type ?? 'default').toLowerCase()
  if (RELATION_ACCENT[relation]) return RELATION_ACCENT[relation]
  if (link.metadata?.extraction_method === 'llm') return LLM_RELATION_ACCENT
  return DEFAULT_RELATION_ACCENT
}

const titleCase = (text: string): string => text.replace(/_/g, ' ')

const asNumber = (value: unknown): number | undefined =>
  typeof value === 'number' && Number.isFinite(value) ? value : undefined

// Normalise root-cause text so an episode's `rootCause` string can be matched to
// a standalone root_cause node's label even when one is "Connection Timeout" and
// the other "connection_timeout".
const normaliseRc = (text: string): string =>
  text.trim().toLowerCase().replace(/[\s_]+/g, ' ')

// ---------------------------------------------------------------------------
// Adapter output: the topology-shaped nodes/edges the canvas renders, plus
// per-id maps back to the original episodic record so the drawer/hover card can
// show episodic-appropriate detail.
// ---------------------------------------------------------------------------
interface Adapted {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  nodeById: Map<string, EpisodicNode>
  linkById: Map<string, EpisodicLink>
  /** Rendered node count per episodic type (what the canvas actually shows). */
  renderedByType: Map<string, number>
  /** Raw node count per type that did NOT make it onto the canvas (hidden). */
  hiddenByType: Map<string, number>
}

/** Resolve a link endpoint (string id or node ref) to its id string. */
const endpointId = (end: string | EpisodicNode): string =>
  typeof end === 'string' ? end : end.id

// Type-prefixes `transformEpisodes` prepends to a node id. Backend EDGE endpoints
// are emitted from the RAW backend id (e.g. `rootcause-connection_timeout`,
// `action-restart_pod`), but `transformEpisodes` re-prefixes the NODE id with its
// type (`root_cause-…`, `action-…`, `entity-…`) on top of that raw id. The result
// is a node id like `root_cause-rootcause-connection_timeout` that no edge ever
// references — so every caused_by / resolved_by / relates edge is silently dropped
// and root_cause / action / entity nodes render as isolated (then get pruned).
// We can't touch transformEpisodes, so we REPAIR each endpoint here by trying the
// raw id first, then re-adding the type prefix the transform would have added.
const ENDPOINT_PREFIXES = ['root_cause-', 'action-', 'entity-', 'service-', 'episode-', 'incident-']

/**
 * Resolve a backend edge endpoint id to the actual adapted node id, working
 * around the double-prefix id mismatch in transformEpisodes. Returns undefined
 * when no node matches (the edge is then dropped, as before).
 */
function resolveEndpoint(raw: string, nodeIds: ReadonlySet<string>): string | undefined {
  if (nodeIds.has(raw)) return raw
  for (const prefix of ENDPOINT_PREFIXES) {
    const candidate = `${prefix}${raw}`
    if (nodeIds.has(candidate)) return candidate
  }
  return undefined
}

interface FilterState {
  hiddenTypes: ReadonlySet<string>
  showSimilar: boolean
  search: string
}

function adapt(nodes: EpisodicNode[], links: EpisodicLink[], filter: FilterState): Adapted {
  const query = filter.search.trim().toLowerCase()

  // Nodes surviving the type + label-search filters.
  const visible = nodes.filter(
    (n) =>
      !filter.hiddenTypes.has(n.type) &&
      (query === '' || n.label.toLowerCase().includes(query)),
  )
  const nodeById = new Map(visible.map((n) => [n.id, n]))
  const visibleIds = new Set(nodeById.keys())

  // ---- Build the causal edge set -----------------------------------------
  // Each entry is a resolved (source,target,relation,weight) tuple + the original
  // link (or undefined for a synthesized edge) for drawer/hover detail.
  interface ResolvedEdge {
    source: string
    target: string
    relation: string
    weight: number
    link?: EpisodicLink
  }
  const resolved: ResolvedEdge[] = []

  // 1. Repair + keep the backend's real edges (affects / caused_by / resolved_by /
  //    relates / similar_to). similar_to is dropped unless toggled on — it's the
  //    densest crosser and reads as a hairball; the causal edges below carry the
  //    tree on their own now that the id mismatch is repaired.
  for (const link of links) {
    const relation = (link.type ?? 'related').toLowerCase()
    if (!filter.showSimilar && relation === 'similar_to') continue
    const source = resolveEndpoint(endpointId(link.source), visibleIds)
    const target = resolveEndpoint(endpointId(link.target), visibleIds)
    if (source === undefined || target === undefined || source === target) continue
    resolved.push({ source, target, relation, weight: asNumber(link.weight) ?? 0, link })
  }

  // 2. Synthesize episode → root_cause edges so root causes appear as a proper
  //    causal layer beneath the episode they explain. Backend caused_by edges are
  //    often absent (or were dropped by the id bug above and re-added in step 1);
  //    where an episode carries a `rootCause` text that matches a standalone
  //    root_cause node's label, link them directly. Skips duplicates already
  //    present from step 1 so we never double-draw a real caused_by edge.
  const rootCauseByLabel = new Map<string, string>() // normalised label → node id
  for (const node of visible) {
    if (node.type === 'root_cause') rootCauseByLabel.set(normaliseRc(node.label), node.id)
  }
  const existingPair = new Set(resolved.map((e) => `${e.source}->${e.target}`))
  for (const node of visible) {
    if (node.type !== 'episode' || !node.rootCause) continue
    const rcId = rootCauseByLabel.get(normaliseRc(node.rootCause))
    if (rcId === undefined || rcId === node.id) continue
    const pair = `${node.id}->${rcId}`
    if (existingPair.has(pair)) continue
    existingPair.add(pair)
    resolved.push({ source: node.id, target: rcId, relation: 'caused_by', weight: 0 })
  }

  // ---- Connectivity prune: hierarchy view shows only connected causal trees --
  // Hide degree-0 nodes so isolated episodes/root-causes/entities don't pile into
  // one flat row (the "string of dots" bug). Entities/actions with no surviving
  // edge simply don't render — and are reported as hidden in the counts.
  const connected = new Set<string>()
  for (const e of resolved) {
    connected.add(e.source)
    connected.add(e.target)
  }

  const topoNodes: TopologyNode[] = []
  const renderedByType = new Map<string, number>()
  for (const node of visible) {
    if (!connected.has(node.id)) continue
    const status = node.status
    topoNodes.push({
      id: node.id,
      label: node.label,
      kind: node.type, // KIND_ACCENT carries the episodic kinds; icon by kind too.
      tier: TYPE_TIER[node.type] ?? 2,
      health: (status && STATUS_HEALTH[status]) ?? 'unknown',
      episode_count: 0,
      incident_count: 0,
      buckets: [],
      recent_episodes: [],
      meta: {},
    })
    renderedByType.set(node.type, (renderedByType.get(node.type) ?? 0) + 1)
  }

  // Hidden-per-type = (every node of that type in the RAW data) − (rendered). This
  // is what makes the pills truthful: a type's pill shows what's on the canvas and
  // flags how many are hidden, instead of the old raw pre-prune counts that summed
  // to far more than the rendered graph.
  const hiddenByType = new Map<string, number>()
  for (const node of nodes) {
    hiddenByType.set(node.type, (hiddenByType.get(node.type) ?? 0) + 1)
  }
  for (const [type, rendered] of renderedByType) {
    hiddenByType.set(type, Math.max(0, (hiddenByType.get(type) ?? 0) - rendered))
  }

  // ---- Topology edges (only between rendered nodes) -----------------------
  // Every episodic edge is a DEPENDS_ON/static edge so the shared layered layout
  // lays them out as a cascade. Direction + accent carry the real relationship.
  const renderedIds = new Set(topoNodes.map((n) => n.id))
  const topoEdges: TopologyEdge[] = []
  const linkById = new Map<string, EpisodicLink>()
  const seen = new Set<string>()
  for (const e of resolved) {
    if (!renderedIds.has(e.source) || !renderedIds.has(e.target)) continue
    // Stable, collision-free id (a node pair can carry several relation types).
    let id = `${e.source}->${e.target}:${e.relation}`
    if (seen.has(id)) id = `${id}#${seen.size}`
    seen.add(id)
    // Synthesized caused_by edges have no original link; fabricate a minimal one
    // so the drawer/hover card still reads "Caused by".
    linkById.set(id, e.link ?? { source: e.source, target: e.target, type: e.relation })
    topoEdges.push({
      id,
      source: e.source,
      target: e.target,
      relationship: 'DEPENDS_ON',
      kind: 'static',
      co_episode_count: e.weight,
      buckets: [],
    })
  }

  return { nodes: topoNodes, edges: topoEdges, nodeById, linkById, renderedByType, hiddenByType }
}

// ---------------------------------------------------------------------------
// Detail builders (drawer + hover card). Pull the rich, type-specific fields
// straight off the original episodic record so the panels read like episodic
// memory, not service topology.
// ---------------------------------------------------------------------------
function nodeDetail(node: EpisodicNode): EpisodicDetail {
  const accent = nodeAccentFor(node.type, node.status)
  const rows: EpisodicDetail['rows'] = []

  if (node.status) {
    rows.push({ label: 'Status', value: titleCase(node.status), accent })
  }
  if (node.type === 'episode') {
    if (node.severity) rows.push({ label: 'Severity', value: titleCase(node.severity) })
    if (node.category) rows.push({ label: 'Category', value: titleCase(node.category) })
    if (node.rootCause) rows.push({ label: 'Root cause', value: titleCase(node.rootCause) })
    if (node.confidence !== undefined) {
      rows.push({ label: 'Confidence', value: `${Math.round(node.confidence * 100)}%` })
    }
    if (node.resolutionTime !== undefined) {
      rows.push({ label: 'Resolution', value: `${node.resolutionTime} min` })
    }
    if (node.timestamp) {
      rows.push({ label: 'Detected', value: new Date(node.timestamp).toLocaleString() })
    }
  } else if (node.type === 'root_cause') {
    if (node.frequency !== undefined) rows.push({ label: 'Occurrences', value: String(node.frequency) })
    if (node.avgResolutionTime !== undefined) {
      rows.push({ label: 'Avg resolution', value: `${node.avgResolutionTime} min` })
    }
    if (node.successRate !== undefined) {
      rows.push({ label: 'Success rate', value: `${Math.round(node.successRate * 100)}%` })
    }
  } else if (node.type === 'action') {
    if (node.usedCount !== undefined) rows.push({ label: 'Used', value: `${node.usedCount}×` })
    if (node.successRate !== undefined) {
      rows.push({ label: 'Success rate', value: `${Math.round(node.successRate * 100)}%` })
    }
    if (node.avgExecutionTime !== undefined) {
      rows.push({ label: 'Avg execution', value: `${node.avgExecutionTime}s` })
    }
  } else if (node.type === 'service') {
    if (node.incidentCount !== undefined) {
      rows.push({ label: 'Incidents', value: String(node.incidentCount) })
    }
    if (node.lastIncident) {
      rows.push({ label: 'Last incident', value: new Date(node.lastIncident).toLocaleString() })
    }
  } else if (node.type === 'entity') {
    if (node.relationCount !== undefined) {
      rows.push({ label: 'Relations', value: String(node.relationCount) })
    }
  }

  return {
    title: node.label,
    chip: titleCase(node.type),
    accent,
    rows,
  }
}

function edgeDetail(link: EpisodicLink): EpisodicDetail {
  const accent = edgeAccentFor(link)
  const relation = link.label ?? link.type ?? 'related'
  const rows: EpisodicDetail['rows'] = [
    { label: 'Relationship', value: titleCase(relation), accent },
  ]
  if (link.weight !== undefined) rows.push({ label: 'Weight', value: String(link.weight) })
  const isLlm = link.metadata?.extraction_method === 'llm'
  return {
    title: `${endpointId(link.source)} → ${endpointId(link.target)}`,
    chip: titleCase(relation),
    accent,
    rows,
    note: isLlm
      ? 'LLM-extracted relation from episodic memory.'
      : 'Causal/structural relation from episodic memory.',
  }
}

interface HoverState {
  target: FocusTarget
  x: number
  y: number
}

interface EpisodicSchemaGraphProps {
  nodes: EpisodicNode[]
  links: EpisodicLink[]
  loading?: boolean
  /** Explicit canvas height (the Console measures its pane and feeds this). */
  height?: number
  /** Notified whenever the canvas selection set changes (Console → chat ctx). */
  onSelectionChange?: (items: SelectedItem[]) => void
}

/**
 * Episodic memory rendered through the platform SchemaGraph stage: the same
 * SVG canvas, pan/zoom, hover card and detail drawer the platform topology
 * uses, but laid out TOP-DOWN and coloured by episodic type/status/relationship.
 * A straight swap-in for the Console's episodic branch.
 */
export function EpisodicSchemaGraph({
  nodes,
  links,
  loading = false,
  height = 520,
  onSelectionChange,
}: EpisodicSchemaGraphProps) {
  const [selection, setSelection] = useState<Map<string, SelectedItem>>(() => new Map())
  const [drawer, setDrawer] = useState<FocusTarget | null>(null)
  const [hover, setHover] = useState<HoverState | null>(null)
  // Filters: hidden node types, whether to show similar_to links, and a label
  // search. similar_to defaults OFF: now that the causal edges (caused_by /
  // resolved_by / affects) connect after the endpoint-id repair in adapt(), the
  // graph is a real tree on its own, and similar_to is the dense crosser that
  // turns it back into a hairball — so it's an opt-in overlay. Entities default
  // hidden too: they only ever link entity↔entity (never into the causal tree),
  // so showing them just inflates the count with a disconnected pink cloud.
  const [hiddenTypes, setHiddenTypes] = useState<ReadonlySet<string>>(() => new Set(['entity']))
  const [showSimilar, setShowSimilar] = useState(false)
  const [search, setSearch] = useState('')
  const hostRef = useRef<HTMLDivElement>(null)

  const adapted = useMemo(
    () => adapt(nodes, links, { hiddenTypes, showSimilar, search }),
    [nodes, links, hiddenTypes, showSimilar, search],
  )

  // Filter/legend pills. A type's pill appears if it exists ANYWHERE in the raw
  // data (so toggling a type off never removes its own pill), but its count is the
  // TRUTHFUL split: `rendered` = nodes actually on the canvas, `hidden` = nodes of
  // that type that did NOT make it (filtered off, or isolated/pruned because their
  // only edges were dropped — e.g. entities, or root_causes with no causal link).
  // This replaces the old raw pre-prune counts whose sum disagreed with both the
  // header total and what was on screen.
  const presentTypes = useMemo(() => {
    const rawCounts = new Map<string, number>()
    for (const n of nodes) rawCounts.set(n.type, (rawCounts.get(n.type) ?? 0) + 1)
    return TYPE_ORDER.filter((t) => rawCounts.has(t)).map((t) => ({
      type: t,
      rendered: adapted.renderedByType.get(t) ?? 0,
      hidden: adapted.hiddenByType.get(t) ?? 0,
    }))
  }, [nodes, adapted])

  const hasSimilar = useMemo(
    () => links.some((l) => (l.type ?? '').toLowerCase() === 'similar_to'),
    [links],
  )

  const toggleType = useCallback((type: string) => {
    setHiddenTypes((prev) => {
      const next = new Set(prev)
      if (next.has(type)) next.delete(type)
      else next.add(type)
      return next
    })
  }, [])

  // Top-down layered layout (platform path stays 'lr'; this passes 'td').
  const layout = useMemo(
    () => (adapted.nodes.length > 0 ? layoutTopology(adapted.nodes, adapted.edges, 'td') : null),
    [adapted],
  )

  // Episodic nodes carry no time buckets, so derived display values are static:
  // count 0 / activity 0. Built once per adapted graph.
  const nodeDerived = useMemo(() => {
    const map = new Map<string, ScrubDerived>()
    for (const node of adapted.nodes) map.set(node.id, { count: 0, activity: 0 })
    return map
  }, [adapted])
  const edgeDerived = useMemo(() => {
    const map = new Map<string, ScrubDerived>()
    for (const edge of adapted.edges) map.set(edge.id, { count: 0, activity: 0 })
    return map
  }, [adapted])

  const selectedKeys = useMemo(() => new Set(selection.keys()), [selection])

  // Surface selection changes to the host (Console → chat context), mirroring
  // SchemaGraph's embedded mode.
  useEffect(() => {
    onSelectionChange?.([...selection.values()])
  }, [onSelectionChange, selection])

  // Reset transient view state when the underlying data changes.
  useEffect(() => {
    setSelection(new Map())
    setDrawer(null)
    setHover(null)
  }, [adapted])

  // ---- Accent / sub-label resolvers for the canvas -------------------------
  const nodeAccent = useCallback(
    (node: TopologyNode) => nodeAccentFor(node.kind, adapted.nodeById.get(node.id)?.status),
    [adapted],
  )
  const edgeAccent = useCallback(
    (edge: TopologyEdge) => {
      const link = adapted.linkById.get(edge.id)
      return link ? edgeAccentFor(link) : undefined
    },
    [adapted],
  )
  const nodeSubLabel = useCallback((node: TopologyNode) => titleCase(node.kind), [])

  // ---- Interactions (Ctrl/⌘-click = multi-select; plain click = inspect) ---
  const toggleSelection = useCallback((item: SelectedItem) => {
    setSelection((prev) => {
      const next = new Map(prev)
      if (next.has(item.key)) next.delete(item.key)
      else next.set(item.key, item)
      return next
    })
  }, [])

  const handleNodeClick = useCallback(
    (node: TopologyNode, event: React.MouseEvent) => {
      if (event.ctrlKey || event.metaKey) {
        toggleSelection({ key: nodeKey(node.id), type: 'node', node })
        return
      }
      setDrawer({ type: 'node', node })
    },
    [toggleSelection],
  )

  const handleEdgeClick = useCallback(
    (edge: TopologyEdge, event: React.MouseEvent) => {
      if (event.ctrlKey || event.metaKey) {
        toggleSelection({ key: edgeKey(edge.id), type: 'edge', edge })
        return
      }
      setDrawer({ type: 'edge', edge })
    },
    [toggleSelection],
  )

  const handleBackgroundClick = useCallback(() => {
    setSelection(new Map())
    setDrawer(null)
  }, [])

  const placeHover = useCallback((target: FocusTarget | null, event?: React.PointerEvent) => {
    if (!target || !event) {
      setHover(null)
      return
    }
    const rect = hostRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = Math.max(0, Math.min(event.clientX - rect.left, rect.width - 264))
    const y = Math.max(0, Math.min(event.clientY - rect.top, rect.height - 130))
    setHover({ target, x, y })
  }, [])

  const handleNodeHover = useCallback(
    (node: TopologyNode | null, event?: React.PointerEvent) => {
      placeHover(node ? { type: 'node', node } : null, event)
    },
    [placeHover],
  )
  const handleEdgeHover = useCallback(
    (edge: TopologyEdge | null, event?: React.PointerEvent) => {
      placeHover(edge ? { type: 'edge', edge } : null, event)
    },
    [placeHover],
  )

  // Episodic detail for the hover card / drawer (built lazily from the target).
  const detailFor = useCallback(
    (target: FocusTarget): EpisodicDetail | undefined => {
      if (target.type === 'node') {
        const original = adapted.nodeById.get(target.node.id)
        return original ? nodeDetail(original) : undefined
      }
      const link = adapted.linkById.get(target.edge.id)
      return link ? edgeDetail(link) : undefined
    },
    [adapted],
  )

  // ---- Render --------------------------------------------------------------
  if (loading) {
    return (
      <div
        className="flex items-center justify-center rounded-lg bg-gradient-to-br from-slate-900/50 to-slate-800/50"
        style={{ height }}
        data-testid="episodic-schema-loading"
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const drawerDetail = drawer ? detailFor(drawer) : undefined
  const hoverDetail = hover ? detailFor(hover.target) : undefined
  const hasGraph = !!layout && adapted.nodes.length > 0

  return (
    <div className="flex h-full flex-col gap-2" data-testid="episodic-schema-graph">
      {/* Filter / legend header: the coloured pills double as the legend AND as
          show/hide toggles per node type; "Similar links" reveals the dense
          episode↔episode web (off by default); search narrows by label. */}
      <div className="flex shrink-0 flex-col gap-1.5">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
          <span className="font-medium text-slate-300">
            {adapted.nodes.length} nodes · {adapted.edges.length} links
          </span>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter nodes…"
              aria-label="Filter episodic nodes by label"
              className="h-7 w-36 rounded-md border border-slate-700 bg-slate-800/70 pl-7 pr-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {presentTypes.map(({ type, rendered, hidden }) => {
            const typeOff = hiddenTypes.has(type)
            // `rendered` = on canvas; `hidden` = of this type but not shown. The
            // pill leads with the rendered count and, when some are not shown,
            // appends a muted "+N hidden" so the numbers never lie about what's
            // on screen.
            return (
              <button
                key={type}
                type="button"
                onClick={() => toggleType(type)}
                aria-pressed={!typeOff}
                title={
                  hidden > 0
                    ? `${rendered} shown · ${hidden} hidden (filtered or not connected to a causal tree)`
                    : `${rendered} shown`
                }
                className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] transition-colors ${
                  typeOff
                    ? 'border-slate-800 bg-slate-900/40 text-slate-500'
                    : 'border-slate-700 bg-slate-800/70 text-slate-200 hover:bg-slate-700/70'
                }`}
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: typeOff ? '#475569' : `hsl(${TYPE_ACCENT[type] ?? DEFAULT_RELATION_ACCENT})` }}
                />
                {TYPE_LABEL[type] ?? type}
                <span className="text-slate-300">{rendered}</span>
                {hidden > 0 && <span className="text-slate-500">+{hidden} hidden</span>}
              </button>
            )
          })}
          {hasSimilar && (
            <button
              type="button"
              onClick={() => setShowSimilar((s) => !s)}
              aria-pressed={showSimilar}
              className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] transition-colors ${
                showSimilar
                  ? 'border-purple-500/50 bg-purple-500/15 text-purple-200'
                  : 'border-slate-800 bg-slate-900/40 text-slate-500 hover:bg-slate-800/60'
              }`}
            >
              <span
                className="inline-block h-0 w-3 border-t border-dashed"
                style={{ borderColor: showSimilar ? 'hsl(258 90% 66%)' : '#475569' }}
              />
              Similar links
            </button>
          )}
        </div>
      </div>

      <div
        ref={hostRef}
        className="schema-stage relative min-h-0 flex-1 overflow-hidden rounded-lg border border-slate-700/60 ring-1 ring-inset ring-white/5"
      >
        {hasGraph ? (
          <>
            <SchemaCanvas
              height={height}
              layout={layout}
              nodes={adapted.nodes}
              edges={adapted.edges}
              nodeDerived={nodeDerived}
              edgeDerived={edgeDerived}
              selectedKeys={selectedKeys}
              onNodeClick={handleNodeClick}
              onEdgeClick={handleEdgeClick}
              onNodeHover={handleNodeHover}
              onEdgeHover={handleEdgeHover}
              onBackgroundClick={handleBackgroundClick}
              nodeAccent={nodeAccent}
              edgeAccent={edgeAccent}
              nodeSubLabel={nodeSubLabel}
              orientation="td"
            />
            {hover && !drawer && <HoverCard target={hover.target} x={hover.x} y={hover.y} episodic={hoverDetail} />}
            {drawer && (
              <DetailDrawer
                target={drawer}
                inContext={selectedKeys.has(
                  drawer.type === 'node' ? nodeKey(drawer.node.id) : edgeKey(drawer.edge.id),
                )}
                onClose={() => setDrawer(null)}
                onToggleAskAi={(target) =>
                  toggleSelection(
                    target.type === 'node'
                      ? { key: nodeKey(target.node.id), type: 'node', node: target.node }
                      : { key: edgeKey(target.edge.id), type: 'edge', edge: target.edge },
                  )
                }
                episodic={drawerDetail}
              />
            )}
          </>
        ) : (
          <div
            className="flex h-full flex-col items-center justify-center px-4 text-center text-muted-foreground"
            data-testid="episodic-schema-empty-state"
          >
            <Workflow className="mb-3 h-12 w-12 opacity-50" />
            <p className="text-base font-medium">
              {nodes.length === 0 ? 'No connected episodes' : 'No nodes match the current filters'}
            </p>
            <p className="mt-1 max-w-md text-sm">
              {nodes.length === 0
                ? 'Episodic memory has no linked incidents, root causes or actions in this window yet.'
                : hasSimilar && !showSimilar
                  ? 'No causal links in this window — enable “Similar links” to show the episode-similarity view, re-enable a type pill, or clear the search.'
                  : 'Re-enable a type pill or clear the search to bring nodes back.'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default EpisodicSchemaGraph
