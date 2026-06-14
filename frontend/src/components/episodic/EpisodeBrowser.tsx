import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertTriangle,
  ChevronRight,
  Clock,
  Loader2,
  MessageSquarePlus,
  Search,
  Workflow,
  X,
} from 'lucide-react'
import type { EpisodicLink, EpisodicNode } from '../EpisodicGraphExplorer'
import { layoutTopology } from '../schema/layout'
import { SchemaCanvas } from '../schema/SchemaCanvas'
import { HoverCard } from '../schema/HoverCard'
import { DetailDrawer } from '../schema/DetailDrawer'
import {
  FocusTarget,
  ScrubDerived,
  SelectedItem,
  TopologyEdge,
  TopologyNode,
  edgeKey,
  nodeKey,
} from '../schema/types'
import {
  EpisodeSummary,
  buildFocusGraph,
  buildIndex,
  edgeAccentFor,
  nodeAccentFor,
  titleCase,
} from './episodeGraph'
import { buildEpisodePrompt, edgeDetail, nodeDetail } from './episodeDetail'

// ---------------------------------------------------------------------------
// Severity / status visuals — small, legible chips for the episode list.
// ---------------------------------------------------------------------------
const SEVERITY_CHIP: Record<string, string> = {
  critical: 'border-red-500/40 bg-red-500/10 text-red-300',
  high: 'border-orange-500/40 bg-orange-500/10 text-orange-300',
  medium: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
  low: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
  info: 'border-slate-600/50 bg-slate-700/20 text-slate-300',
}

const STATUS_DOT: Record<string, string> = {
  resolved: 'bg-green-500',
  healthy: 'bg-green-500',
  remediating: 'bg-blue-500',
  analyzing: 'bg-purple-500',
  detected: 'bg-amber-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500',
}

type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low'

const SEVERITY_FILTERS: { key: SeverityFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'critical', label: 'Critical' },
  { key: 'high', label: 'High' },
  { key: 'medium', label: 'Medium' },
  { key: 'low', label: 'Low' },
]

const relTime = (ms: number): string => {
  if (Number.isNaN(ms)) return 'unknown time'
  const diff = Date.now() - ms
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

interface HoverState {
  target: FocusTarget
  x: number
  y: number
}

interface EpisodeBrowserProps {
  nodes: EpisodicNode[]
  links: EpisodicLink[]
  loading?: boolean
  /** Explicit pane height (the Console measures its pane and feeds this). */
  height?: number
  /** Notified whenever the canvas selection set changes (Console → chat ctx). */
  onSelectionChange?: (items: SelectedItem[]) => void
  /**
   * When provided, the "Ask AI" affordance hands a ready-made investigation
   * prompt to the host chat composer (the Console cockpit). Optional so the
   * browser still works standalone.
   */
  onAskEpisode?: (prompt: string) => void
}

/**
 * Episode Browser — a master/detail replacement for the old episodic hairball.
 *
 * LEFT  a searchable, severity-filterable list of EVERY episode (full titles,
 *       severity + status chips, touched-service count, relative time).
 * RIGHT the SELECTED episode's focused causal subgraph (episode → root cause →
 *       actions → touched services) rendered through the shared SchemaCanvas,
 *       so it keeps the glassy look, hover card, detail drawer, pan/zoom and
 *       Ctrl-click-to-attach-to-chat — but with only a handful of clean nodes.
 *
 * No similarity web, no 94-entity cloud, no truncated titles, no confusing
 * "+N hidden" pills. An operator browses the list and reads one clean story at
 * a time.
 */
export function EpisodeBrowser({
  nodes,
  links,
  loading = false,
  height = 520,
  onSelectionChange,
  onAskEpisode,
}: EpisodeBrowserProps) {
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState<SeverityFilter>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // Canvas-level state (mirrors EpisodicSchemaGraph's contract so the chat
  // hand-off and Ask-AI behaviour are preserved exactly).
  const [selection, setSelection] = useState<Map<string, SelectedItem>>(() => new Map())
  const [drawer, setDrawer] = useState<FocusTarget | null>(null)
  const [hover, setHover] = useState<HoverState | null>(null)
  const hostRef = useRef<HTMLDivElement>(null)

  const index = useMemo(() => buildIndex(nodes, links), [nodes, links])

  // Filtered + sorted episode list (newest first, from buildIndex).
  const visibleEpisodes = useMemo(() => {
    const query = search.trim().toLowerCase()
    return index.episodes.filter((ep) => {
      if (severity !== 'all' && (ep.severity ?? '').toLowerCase() !== severity) return false
      if (query === '') return true
      return (
        ep.title.toLowerCase().includes(query) ||
        (ep.rootCauseLabel ?? '').toLowerCase().includes(query) ||
        (ep.category ?? '').toLowerCase().includes(query)
      )
    })
  }, [index, search, severity])

  // Default the focus to the first (newest / most severe-by-recency) episode,
  // and keep the selection valid as the data/filters change.
  useEffect(() => {
    if (index.episodes.length === 0) {
      setSelectedId(null)
      return
    }
    setSelectedId((prev) => {
      if (prev && index.episodes.some((e) => e.id === prev)) return prev
      return index.episodes[0]?.id ?? null
    })
  }, [index])

  // If the current selection is filtered out, snap to the first visible one so
  // the detail pane is never blank while the list still has rows.
  useEffect(() => {
    if (visibleEpisodes.length === 0) return
    setSelectedId((prev) => {
      if (prev && visibleEpisodes.some((e) => e.id === prev)) return prev
      return visibleEpisodes[0].id
    })
  }, [visibleEpisodes])

  const selectedSummary = useMemo<EpisodeSummary | undefined>(
    () => index.episodes.find((e) => e.id === selectedId),
    [index, selectedId],
  )

  const focus = useMemo(
    () => (selectedId ? buildFocusGraph(index, selectedId) : null),
    [index, selectedId],
  )

  const layout = useMemo(
    () => (focus && focus.nodes.length > 0 ? layoutTopology(focus.nodes, focus.edges, 'td') : null),
    [focus],
  )

  // Episodic nodes carry no time buckets → static derived values.
  const nodeDerived = useMemo(() => {
    const map = new Map<string, ScrubDerived>()
    for (const node of focus?.nodes ?? []) map.set(node.id, { count: 0, activity: 0 })
    return map
  }, [focus])
  const edgeDerived = useMemo(() => {
    const map = new Map<string, ScrubDerived>()
    for (const edge of focus?.edges ?? []) map.set(edge.id, { count: 0, activity: 0 })
    return map
  }, [focus])

  const selectedKeys = useMemo(() => new Set(selection.keys()), [selection])

  // Surface selection changes to the host (Console → chat context).
  useEffect(() => {
    onSelectionChange?.([...selection.values()])
  }, [onSelectionChange, selection])

  // Changing the focused episode clears any in-flight drawer/hover but KEEPS
  // the Ask-AI selection (chips accumulate across episodes, like the platform
  // view), so an operator can attach several episodes' nodes to one question.
  useEffect(() => {
    setDrawer(null)
    setHover(null)
  }, [selectedId])

  // ---- Accent / sub-label resolvers for the canvas -------------------------
  const nodeAccent = useCallback(
    (node: TopologyNode) => nodeAccentFor(node.kind, focus?.nodeById.get(node.id)?.status),
    [focus],
  )
  const edgeAccent = useCallback(
    (edge: TopologyEdge) => {
      const link = focus?.linkById.get(edge.id)
      return link ? edgeAccentFor(link) : undefined
    },
    [focus],
  )
  const nodeSubLabel = useCallback((node: TopologyNode) => titleCase(node.kind), [])

  // ---- Interactions (Ctrl/⌘-click = attach to chat; plain click = inspect) -
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
    (node: TopologyNode | null, event?: React.PointerEvent) => placeHover(node ? { type: 'node', node } : null, event),
    [placeHover],
  )
  const handleEdgeHover = useCallback(
    (edge: TopologyEdge | null, event?: React.PointerEvent) => placeHover(edge ? { type: 'edge', edge } : null, event),
    [placeHover],
  )

  const detailFor = useCallback(
    (target: FocusTarget) => {
      if (target.type === 'node') {
        const original = focus?.nodeById.get(target.node.id)
        return original ? nodeDetail(original) : undefined
      }
      const link = focus?.linkById.get(target.edge.id)
      return link ? edgeDetail(link) : undefined
    },
    [focus],
  )

  // "Ask AI about this episode" → seed the Console composer + attach the node.
  const askAboutEpisode = useCallback(() => {
    if (!selectedSummary || !focus) return
    const services = selectedSummary.serviceIds
      .map((id) => focus.nodeById.get(id)?.label ?? '')
      .filter(Boolean)
    onAskEpisode?.(buildEpisodePrompt(selectedSummary.node, services, selectedSummary.rootCauseLabel))
    const topoNode = focus.nodes.find((n) => n.id === selectedSummary.id)
    if (topoNode) {
      setSelection((prev) => {
        const next = new Map(prev)
        const key = nodeKey(topoNode.id)
        if (!next.has(key)) next.set(key, { key, type: 'node', node: topoNode })
        return next
      })
    }
  }, [selectedSummary, focus, onAskEpisode])

  // ---- KPI strip numbers ---------------------------------------------------
  const totals = useMemo(() => {
    const eps = index.episodes
    const critical = eps.filter((e) => (e.severity ?? '').toLowerCase() === 'critical').length
    const resolved = eps.filter((e) => {
      const s = (e.status ?? '').toLowerCase()
      return s === 'resolved' || s === 'healthy'
    }).length
    return {
      episodes: eps.length,
      critical,
      resolved,
      rootCauses: index.countsByType.get('root_cause') ?? 0,
      services: index.countsByType.get('service') ?? 0,
    }
  }, [index])

  // ---- Render --------------------------------------------------------------
  if (loading) {
    return (
      <div
        className="flex items-center justify-center rounded-lg bg-gradient-to-br from-slate-900/50 to-slate-800/50"
        style={{ height }}
        data-testid="episode-browser-loading"
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (index.episodes.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center rounded-lg border border-slate-700/60 px-4 text-center text-muted-foreground schema-stage"
        style={{ height }}
        data-testid="episode-browser-empty"
      >
        <Workflow className="mb-3 h-12 w-12 opacity-50" />
        <p className="text-base font-medium text-slate-200">No episodes in memory yet</p>
        <p className="mt-1 max-w-md text-sm">
          Episodic memory has no recorded incidents in this window. As the system handles incidents
          they will appear here, newest first.
        </p>
      </div>
    )
  }

  const drawerDetail = drawer ? detailFor(drawer) : undefined
  const hoverDetail = hover ? detailFor(hover.target) : undefined

  return (
    <div
      className="flex h-full min-h-0 flex-col gap-2"
      style={{ height }}
      data-testid="episode-browser"
    >
      {/* KPI strip — one glance at the whole memory. */}
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 text-[11px]">
        <Kpi label="episodes" value={totals.episodes} accent="271 91% 65%" />
        <Kpi label="critical" value={totals.critical} accent="0 84% 60%" />
        <Kpi label="resolved" value={totals.resolved} accent="142 71% 45%" />
        <Kpi label="root causes" value={totals.rootCauses} accent="25 95% 53%" />
        <Kpi label="services" value={totals.services} accent="217 91% 60%" />
      </div>

      {/* Master/detail body. Stacks on very narrow panes; side-by-side otherwise. */}
      <div className="flex min-h-0 flex-1 flex-col gap-2 sm:flex-row">
        {/* LEFT — the episode list (browse every episode). */}
        <div className="flex min-h-0 shrink-0 flex-col gap-2 sm:w-[44%] sm:max-w-[360px]">
          <div className="flex shrink-0 flex-col gap-1.5">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search episodes, root causes…"
                aria-label="Search episodes"
                className="h-8 w-full rounded-md border border-slate-700 bg-slate-800/70 pl-8 pr-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="flex flex-wrap items-center gap-1" role="group" aria-label="Filter by severity">
              {SEVERITY_FILTERS.map((f) => (
                <button
                  key={f.key}
                  type="button"
                  onClick={() => setSeverity(f.key)}
                  aria-pressed={severity === f.key}
                  className={`rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors ${
                    severity === f.key
                      ? 'border-primary/50 bg-primary/15 text-primary-foreground'
                      : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:bg-slate-700/60'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <ul
            className="min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1"
            data-testid="episode-list"
          >
            {visibleEpisodes.length === 0 ? (
              <li className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-center text-xs text-slate-500">
                No episodes match this search/filter.
              </li>
            ) : (
              visibleEpisodes.map((ep) => {
                const isActive = ep.id === selectedId
                const sev = (ep.severity ?? 'info').toLowerCase()
                const status = (ep.status ?? '').toLowerCase()
                return (
                  <li key={ep.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(ep.id)}
                      aria-pressed={isActive}
                      data-testid="episode-list-item"
                      className={`group w-full rounded-lg border p-2.5 text-left transition-colors ${
                        isActive
                          ? 'border-primary/50 bg-primary/[0.08] ring-1 ring-inset ring-primary/30'
                          : 'border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span
                          className={`mt-1 h-2 w-2 shrink-0 rounded-full ${STATUS_DOT[status] ?? 'bg-slate-500'}`}
                          title={status ? titleCase(status) : 'unknown'}
                        />
                        <div className="min-w-0 flex-1">
                          <p className="line-clamp-2 text-xs font-medium leading-snug text-slate-100">
                            {ep.title}
                          </p>
                          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                            <span
                              className={`rounded border px-1.5 py-0.5 text-[10px] font-medium capitalize ${
                                SEVERITY_CHIP[sev] ?? SEVERITY_CHIP.info
                              }`}
                            >
                              {sev}
                            </span>
                            {ep.serviceIds.length > 0 && (
                              <span className="text-[10px] text-slate-500">
                                {ep.serviceIds.length} service{ep.serviceIds.length === 1 ? '' : 's'}
                              </span>
                            )}
                            <span className="ml-auto flex items-center gap-0.5 text-[10px] text-slate-500">
                              <Clock className="h-3 w-3" />
                              {relTime(ep.time)}
                            </span>
                          </div>
                        </div>
                        <ChevronRight
                          className={`mt-0.5 h-4 w-4 shrink-0 transition-colors ${
                            isActive ? 'text-primary' : 'text-slate-600 group-hover:text-slate-400'
                          }`}
                        />
                      </div>
                    </button>
                  </li>
                )
              })
            )}
          </ul>
        </div>

        {/* RIGHT — the focused episode's causal story on the shared canvas. */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2">
          {selectedSummary && (
            <div className="flex shrink-0 items-start justify-between gap-2 rounded-lg border border-slate-800 bg-slate-900/50 p-2.5">
              <div className="min-w-0">
                <p className="truncate text-xs font-semibold text-slate-100" title={selectedSummary.title}>
                  {selectedSummary.title}
                </p>
                <p className="mt-0.5 truncate text-[11px] text-slate-400">
                  {selectedSummary.rootCauseLabel
                    ? `Root cause: ${titleCase(selectedSummary.rootCauseLabel)}`
                    : 'Root cause not recorded'}
                  {' · '}
                  {selectedSummary.serviceIds.length} service
                  {selectedSummary.serviceIds.length === 1 ? '' : 's'} touched
                </p>
              </div>
              {onAskEpisode && (
                <button
                  type="button"
                  onClick={askAboutEpisode}
                  data-testid="episode-ask-ai"
                  className="flex shrink-0 items-center gap-1.5 rounded-md bg-primary px-2.5 py-1.5 text-[11px] font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  <MessageSquarePlus className="h-3.5 w-3.5" />
                  Ask AI
                </button>
              )}
            </div>
          )}

          <div
            ref={hostRef}
            className="schema-stage relative min-h-0 flex-1 overflow-hidden rounded-lg border border-slate-700/60 ring-1 ring-inset ring-white/5"
          >
            {layout && focus && focus.nodes.length > 0 ? (
              <>
                <SchemaCanvas
                  height={Math.max(180, height - 132)}
                  layout={layout}
                  nodes={focus.nodes}
                  edges={focus.edges}
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
                {hover && !drawer && (
                  <HoverCard target={hover.target} x={hover.x} y={hover.y} episodic={hoverDetail} />
                )}
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
                {/* Tiny legend so the colour story reads without a manual. */}
                <div className="pointer-events-none absolute bottom-2 left-2 flex flex-wrap items-center gap-x-2.5 gap-y-1 rounded-md border border-slate-700/60 bg-slate-900/80 px-2 py-1 text-[10px] text-slate-400 backdrop-blur-sm">
                  <LegendDot accent="271 91% 65%" label="Episode" />
                  <LegendDot accent="25 95% 53%" label="Root cause" />
                  <LegendDot accent="189 94% 43%" label="Action" />
                  <LegendDot accent="217 91% 60%" label="Service" />
                </div>
              </>
            ) : (
              <div className="flex h-full flex-col items-center justify-center px-4 text-center text-muted-foreground">
                <AlertTriangle className="mb-2 h-8 w-8 opacity-50" />
                <p className="text-sm font-medium text-slate-200">No causal links recorded</p>
                <p className="mt-1 max-w-xs text-xs">
                  This episode has no linked root cause, action or service in memory yet. Pick another
                  episode from the list.
                </p>
              </div>
            )}
          </div>
          <p className="flex shrink-0 items-center gap-1 text-[10px] leading-snug text-slate-500">
            <X className="h-3 w-3" />
            Click a node to inspect · Ctrl-click to attach it to the chat as context.
          </p>
        </div>
      </div>
    </div>
  )
}

function Kpi({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <span
      className="flex items-center gap-1.5 rounded-md border border-slate-700/70 bg-slate-800/50 px-2 py-1"
      data-testid={`episode-kpi-${label.replace(/\s+/g, '-')}`}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: `hsl(${accent})` }} />
      <span className="font-semibold text-slate-100">{value}</span>
      <span className="text-slate-400">{label}</span>
    </span>
  )
}

function LegendDot({ accent, label }: { accent: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: `hsl(${accent})` }} />
      {label}
    </span>
  )
}

export default EpisodeBrowser
