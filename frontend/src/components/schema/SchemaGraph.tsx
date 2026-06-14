import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Loader2, Network, RefreshCw } from 'lucide-react'
import api from '../../lib/api'
import { layoutTopology } from './layout'
import { SchemaCanvas } from './SchemaCanvas'
import { HoverCard } from './HoverCard'
import { DetailDrawer } from './DetailDrawer'
import { TimeScrubber } from './TimeScrubber'
import { AskAiPanel } from './AskAiPanel'
import {
  FocusTarget,
  ScrubDerived,
  SelectedItem,
  TopologyEdge,
  TopologyNode,
  TopologyResponse,
  edgeKey,
  isEdgeHostNode,
  nodeKey,
} from './types'

const WINDOW_HOURS = 168
const BUCKETS = 28

interface HoverState {
  target: FocusTarget
  x: number
  y: number
}

interface SchemaGraphProps {
  height?: number
  /**
   * Embedded (cockpit) mode: the canvas fills its container height (measured
   * via ResizeObserver), the docked Ask-AI panel and the time scrubber are
   * dropped, and selection changes are surfaced through `onSelectionChange`
   * so a host page (the Console) can feed them to its own chat as context.
   * The default (non-embedded) path is byte-identical to before.
   */
  embedded?: boolean
  /** Embedded mode only: notified whenever the canvas selection set changes. */
  onSelectionChange?: (items: SelectedItem[]) => void
  /**
   * When provided, each "Recent episode" card in the detail drawer becomes a
   * button that hands a ready-made investigation prompt to the host chat (the
   * Console cockpit composer) — "click an episode to ask the LLM about it".
   */
  onAskEpisode?: (prompt: string) => void
}

/**
 * Schema mode container: fetches `GET /api/v1/graph/topology`, owns the
 * selection map (keyed `node:<id>` / `edge:<id>`), the time-scrub bucket and
 * the detail drawer. All scrub binding is DERIVED (useMemo) — scrubbing never
 * refetches and never recomputes the layered layout.
 */
export default function SchemaGraph({ height = 520, embedded = false, onSelectionChange, onAskEpisode }: SchemaGraphProps) {
  const [data, setData] = useState<TopologyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selection, setSelection] = useState<Map<string, SelectedItem>>(() => new Map())
  const [activeBucket, setActiveBucket] = useState<number | null>(null)
  const [drawer, setDrawer] = useState<FocusTarget | null>(null)
  const [hover, setHover] = useState<HoverState | null>(null)
  // Embedded mode: the canvas tracks its flex container's height live.
  const [measuredHeight, setMeasuredHeight] = useState(height)

  const hostRef = useRef<HTMLDivElement>(null)

  const fetchTopology = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.graph.topology({
        window_hours: WINDOW_HOURS,
        buckets: BUCKETS,
      })
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topology')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchTopology()
  }, [fetchTopology])

  // Embedded mode: keep the canvas height pinned to its flex container so the
  // graph fills the cockpit's left pane (and re-fits when that pane resizes,
  // e.g. when the chat/incidents column or the browser window changes size).
  useEffect(() => {
    if (!embedded) return
    const el = hostRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver((entries) => {
      const h = entries[0]?.contentRect.height
      if (h && h > 0) setMeasuredHeight(Math.round(h))
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [embedded])

  // Embedded mode: surface selection changes to the host (Console → chat ctx).
  useEffect(() => {
    if (embedded) onSelectionChange?.([...selection.values()])
  }, [embedded, onSelectionChange, selection])

  // Layered-DAG layout — memoized on topology identity inside layoutTopology,
  // so scrub/hover/selection re-renders reuse the cached result.
  const layout = useMemo(() => {
    if (!data) return null
    return layoutTopology(data.nodes, data.edges)
  }, [data])

  // ---- Scrub-derived display values (pure, zero refetch / zero layout) ----
  const nodeDerived = useMemo(() => {
    const map = new Map<string, ScrubDerived>()
    if (!data) return map
    for (const node of data.nodes) {
      if (activeBucket === null) {
        map.set(node.id, {
          count: node.episode_count,
          activity: node.buckets[node.buckets.length - 1] ?? 0,
        })
      } else {
        let count = 0
        for (let i = 0; i <= activeBucket && i < node.buckets.length; i += 1) {
          count += node.buckets[i]
        }
        map.set(node.id, { count, activity: node.buckets[activeBucket] ?? 0 })
      }
    }
    return map
  }, [data, activeBucket])

  const edgeDerived = useMemo(() => {
    const map = new Map<string, ScrubDerived>()
    if (!data) return map
    for (const edge of data.edges) {
      if (activeBucket === null) {
        map.set(edge.id, {
          count: edge.co_episode_count,
          activity: edge.buckets[edge.buckets.length - 1] ?? 0,
        })
      } else {
        let count = 0
        for (let i = 0; i <= activeBucket && i < edge.buckets.length; i += 1) {
          count += edge.buckets[i]
        }
        map.set(edge.id, { count, activity: edge.buckets[activeBucket] ?? 0 })
      }
    }
    return map
  }, [data, activeBucket])

  // Global per-bucket histogram for the scrubber.
  const globalBuckets = useMemo(() => {
    if (!data) return []
    const length = data.nodes.reduce((m, n) => Math.max(m, n.buckets.length), 0)
    const totals = new Array<number>(length).fill(0)
    for (const node of data.nodes) {
      node.buckets.forEach((value, idx) => {
        totals[idx] += value
      })
    }
    return totals
  }, [data])

  const selectedKeys = useMemo(() => new Set(selection.keys()), [selection])
  const selectionItems = useMemo(() => [...selection.values()], [selection])

  // ---- Interactions --------------------------------------------------------
  // Plain click = INSPECT (open the drawer) without touching the Ask-AI set, so
  // the "Add to Ask AI" button and Ctrl-click are what build context and chips
  // accumulate across services. Ctrl/⌘-click = additive toggle (no drawer).
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

  const handleToggleAskAi = useCallback(
    (target: FocusTarget) => {
      const item: SelectedItem =
        target.type === 'node'
          ? { key: nodeKey(target.node.id), type: 'node', node: target.node }
          : { key: edgeKey(target.edge.id), type: 'edge', edge: target.edge }
      toggleSelection(item)
    },
    [toggleSelection],
  )

  const handleRemoveSelection = useCallback((key: string) => {
    setSelection((prev) => {
      const next = new Map(prev)
      next.delete(key)
      return next
    })
  }, [])

  // ---- Render --------------------------------------------------------------
  if (loading && !data) {
    return (
      <div
        className={`flex items-center justify-center rounded-lg bg-gradient-to-br from-slate-900/50 to-slate-800/50 ${embedded ? 'h-full' : ''}`}
        style={embedded ? undefined : { height }}
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !data || !layout || data.nodes.length === 0) {
    // Never blank: explicit fallback with a retry affordance.
    return (
      <div
        className={`flex flex-col items-center justify-center rounded-lg border border-slate-800 bg-gradient-to-br from-slate-900/40 to-slate-800/40 text-muted-foreground ${embedded ? 'h-full' : ''}`}
        style={embedded ? undefined : { height }}
        data-testid="schema-empty-state"
      >
        <Network className="mb-3 h-12 w-12 opacity-50" />
        <p className="text-lg font-medium">Topology unavailable</p>
        <p className="mt-1 max-w-md text-center text-sm">
          {error
            ? `The topology endpoint could not be reached: ${error}`
            : 'No platform services were returned. The backend falls back to the seeded architecture once it is reachable.'}
        </p>
        <button
          type="button"
          onClick={() => void fetchTopology()}
          className="mt-4 rounded-lg bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    )
  }

  const serviceCount = data.nodes.filter((n) => !isEdgeHostNode(n)).length
  const edgeHostCount = data.nodes.length - serviceCount
  const windowDays = Math.round(data.window_hours / 24)

  // Embedded (cockpit) layout: a compact strip + a height-filling canvas. No
  // docked Ask-AI panel (the Console hosts the chat) and no time scrubber, so
  // the canvas can fill the left pane cleanly. Ctrl-click still multi-selects
  // and the selection is surfaced to the Console via onSelectionChange.
  if (embedded) {
    return (
      <div className="flex h-full flex-col gap-2" data-testid="schema-graph-embedded">
        <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-slate-300">
              {serviceCount} services · {data.edges.length} links
            </span>
            {edgeHostCount > 0 && (
              <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-2 py-0.5 text-cyan-300">
                {edgeHostCount} edge host{edgeHostCount === 1 ? '' : 's'}
              </span>
            )}
            <span className="rounded-full border border-slate-700 bg-slate-800/70 px-2 py-0.5">
              {data.stats.episodes_in_window} episodes · {windowDays}d
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 xl:flex">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-green-500" /> healthy
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-amber-500" /> warning
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-red-500" /> critical
              </span>
            </span>
            <button
              type="button"
              onClick={() => void fetchTopology()}
              disabled={loading}
              aria-label="Refresh topology"
              className="rounded-md border border-slate-700 bg-slate-800/80 p-1.5 text-slate-300 hover:bg-slate-700 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <div
          ref={hostRef}
          className="schema-stage relative min-h-0 flex-1 overflow-hidden rounded-lg border border-slate-700/60 ring-1 ring-inset ring-white/5"
        >
          <SchemaCanvas
            height={measuredHeight}
            layout={layout}
            nodes={data.nodes}
            edges={data.edges}
            nodeDerived={nodeDerived}
            edgeDerived={edgeDerived}
            selectedKeys={selectedKeys}
            onNodeClick={handleNodeClick}
            onEdgeClick={handleEdgeClick}
            onNodeHover={handleNodeHover}
            onEdgeHover={handleEdgeHover}
            onBackgroundClick={handleBackgroundClick}
          />
          {hover && !drawer && <HoverCard target={hover.target} x={hover.x} y={hover.y} />}
          {drawer && (
            <DetailDrawer
              target={drawer}
              inContext={selectedKeys.has(
                drawer.type === 'node' ? nodeKey(drawer.node.id) : edgeKey(drawer.edge.id),
              )}
              onClose={() => setDrawer(null)}
              onToggleAskAi={handleToggleAskAi}
              onAskEpisode={onAskEpisode}
            />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Status strip. Wording rule: "N services · M links" (never nodes|edges). */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-slate-300">
            {serviceCount} services · {data.edges.length} links
          </span>
          {edgeHostCount > 0 && (
            <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-2 py-0.5 text-cyan-300">
              {edgeHostCount} edge host{edgeHostCount === 1 ? '' : 's'}
            </span>
          )}
          <span className="rounded-full border border-slate-700 bg-slate-800/70 px-2 py-0.5">
            {data.stats.episodes_in_window} episodes · last {windowDays}d
          </span>
          <span className="rounded-full border border-slate-700 bg-slate-800/70 px-2 py-0.5">
            source: {data.stats.source}
          </span>
          {data.stats.episodes_in_window === 0 && (
            <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-amber-300">
              No episodes in this window — static architecture view
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Legend. */}
          <span className="hidden items-center gap-2 md:flex">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-green-500" /> healthy
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-amber-500" /> warning
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-red-500" /> critical
            </span>
            <span className="flex items-center gap-1 text-cyan-300">
              <span className="inline-block h-0 w-4 border-t border-dashed border-cyan-400" /> telemetry
            </span>
          </span>
          <button
            type="button"
            onClick={() => void fetchTopology()}
            disabled={loading}
            aria-label="Refresh topology"
            className="rounded-md border border-slate-700 bg-slate-800/80 p-1.5 text-slate-300 hover:bg-slate-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row">
        <div className="min-w-0 flex-1">
          <div
            ref={hostRef}
            className="schema-stage relative overflow-hidden rounded-lg border border-slate-700/60 ring-1 ring-inset ring-white/5"
            style={{ height }}
          >
            <SchemaCanvas
              height={height}
              layout={layout}
              nodes={data.nodes}
              edges={data.edges}
              nodeDerived={nodeDerived}
              edgeDerived={edgeDerived}
              selectedKeys={selectedKeys}
              onNodeClick={handleNodeClick}
              onEdgeClick={handleEdgeClick}
              onNodeHover={handleNodeHover}
              onEdgeHover={handleEdgeHover}
              onBackgroundClick={handleBackgroundClick}
            />
            {hover && !drawer && <HoverCard target={hover.target} x={hover.x} y={hover.y} />}
            {drawer && (
              <DetailDrawer
                target={drawer}
                inContext={selectedKeys.has(
                  drawer.type === 'node' ? nodeKey(drawer.node.id) : edgeKey(drawer.edge.id),
                )}
                onClose={() => setDrawer(null)}
                onToggleAskAi={handleToggleAskAi}
                onAskEpisode={onAskEpisode}
              />
            )}
          </div>

          <TimeScrubber
            buckets={globalBuckets}
            activeBucket={activeBucket}
            onChange={setActiveBucket}
            generatedAt={data.generated_at}
            windowHours={data.window_hours}
            bucketMinutes={data.bucket_minutes}
          />
        </div>

        <AskAiPanel
          selection={selectionItems}
          onRemoveSelection={handleRemoveSelection}
          windowHours={data.window_hours}
          maxHeight={height + 72}
        />
      </div>
    </div>
  )
}
