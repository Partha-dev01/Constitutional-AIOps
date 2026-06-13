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
}

/**
 * Schema mode container: fetches `GET /api/v1/graph/topology`, owns the
 * selection map (keyed `node:<id>` / `edge:<id>`), the time-scrub bucket and
 * the detail drawer. All scrub binding is DERIVED (useMemo) — scrubbing never
 * refetches and never recomputes the layered layout.
 */
export default function SchemaGraph({ height = 520 }: SchemaGraphProps) {
  const [data, setData] = useState<TopologyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [selection, setSelection] = useState<Map<string, SelectedItem>>(() => new Map())
  const [activeBucket, setActiveBucket] = useState<number | null>(null)
  const [drawer, setDrawer] = useState<FocusTarget | null>(null)
  const [hover, setHover] = useState<HoverState | null>(null)

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
  const handleNodeClick = useCallback((node: TopologyNode, event: React.MouseEvent) => {
    const item: SelectedItem = { key: nodeKey(node.id), type: 'node', node }
    const additive = event.ctrlKey || event.metaKey
    setSelection((prev) => {
      const next = new Map(prev)
      if (additive) {
        if (next.has(item.key)) next.delete(item.key)
        else next.set(item.key, item)
        return next
      }
      next.clear()
      next.set(item.key, item)
      return next
    })
    if (!additive) setDrawer({ type: 'node', node })
  }, [])

  const handleEdgeClick = useCallback((edge: TopologyEdge, event: React.MouseEvent) => {
    const item: SelectedItem = { key: edgeKey(edge.id), type: 'edge', edge }
    const additive = event.ctrlKey || event.metaKey
    setSelection((prev) => {
      const next = new Map(prev)
      if (additive) {
        if (next.has(item.key)) next.delete(item.key)
        else next.set(item.key, item)
        return next
      }
      next.clear()
      next.set(item.key, item)
      return next
    })
    if (!additive) setDrawer({ type: 'edge', edge })
  }, [])

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

  const handleAddToAskAi = useCallback((target: FocusTarget) => {
    const item: SelectedItem =
      target.type === 'node'
        ? { key: nodeKey(target.node.id), type: 'node', node: target.node }
        : { key: edgeKey(target.edge.id), type: 'edge', edge: target.edge }
    setSelection((prev) => {
      const next = new Map(prev)
      next.set(item.key, item)
      return next
    })
  }, [])

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
        className="flex items-center justify-center rounded-lg bg-gradient-to-br from-slate-900/50 to-slate-800/50"
        style={{ height }}
      >
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !data || !layout || data.nodes.length === 0) {
    // Never blank: explicit fallback with a retry affordance.
    return (
      <div
        className="flex flex-col items-center justify-center rounded-lg border border-slate-800 bg-gradient-to-br from-slate-900/40 to-slate-800/40 text-muted-foreground"
        style={{ height }}
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
            className="relative overflow-hidden rounded-lg border border-slate-800 bg-gradient-to-br from-slate-900/80 to-slate-800/80"
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
                onClose={() => setDrawer(null)}
                onAddToAskAi={handleAddToAskAi}
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
        />
      </div>
    </div>
  )
}
