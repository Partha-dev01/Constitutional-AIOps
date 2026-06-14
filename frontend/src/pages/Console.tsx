import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, Loader2, Sparkles, Waypoints, X } from 'lucide-react'
import { ActiveIncidentsPanel } from '../components/incidents/ActiveIncidentsPanel'
import { ChatPane } from '../components/chat/ChatPane'
import { EpisodicGraphExplorer } from '../components/EpisodicGraphExplorer'
import type { EpisodicLink, EpisodicNode } from '../components/EpisodicGraphExplorer'
import { buildSchemaChatContext } from '../components/schema/types'
import type { SelectedItem } from '../components/schema/types'

// The platform-topology graph is lazy so the Console chunk stays lean; it is
// only fetched when this page mounts.
const SchemaGraph = lazy(() => import('../components/schema/SchemaGraph'))

// Matches the schema graph's default analysis window so the chat context that
// rides along with a selection describes the same span the graph is showing.
const WINDOW_HOURS = 168

// EpisodicGraphExplorer needs an explicit numeric height; never feed it less
// than this so the canvas stays usable even in a very short pane.
const MIN_EPISODIC_HEIGHT = 280

// Shape of the /api/v1/graph/episodes response we consume. Mirrors the transform
// used by the /graph page (Graph.tsx) so both surfaces render the same memory.
interface EpisodesResponse {
  episodes?: Array<{
    id: string
    title: string
    timestamp?: string
    category?: string
    severity?: string
    status?: string
    root_cause?: string
    confidence?: number
    metadata?: Record<string, unknown>
  }>
  root_causes?: Array<{
    id: string
    name: string
    frequency?: number
    avg_resolution_time_minutes?: number
    success_rate?: number
    metadata?: Record<string, unknown>
  }>
  actions?: Array<{
    id: string
    name: string
    used_count?: number
    success_rate?: number
    avg_execution_time_seconds?: number
    metadata?: Record<string, unknown>
  }>
  services?: Array<{
    name: string
    status?: string
    incident_count?: number
    last_incident?: string
    metadata?: Record<string, unknown>
  }>
  entities?: Array<{
    id: string
    name: string
    relation_count?: number
    metadata?: Record<string, unknown>
  }>
  edges?: Array<{
    source: string
    target: string
    relationship: string
    weight?: number
    metadata?: Record<string, unknown>
  }>
}

// Transform the episodes API payload into the node/link shape the explorer
// expects. Replicates Graph.tsx's transform inline (Graph.tsx is owned by another
// lane and must not be imported/edited here).
function transformEpisodes(data: EpisodesResponse): { nodes: EpisodicNode[]; links: EpisodicLink[] } {
  const nodes: EpisodicNode[] = []
  const links: EpisodicLink[] = []

  for (const episode of data.episodes ?? []) {
    nodes.push({
      id: `episode-${episode.id}`,
      label: episode.title,
      type: 'episode',
      status: episode.status as EpisodicNode['status'],
      timestamp: episode.timestamp,
      confidence: episode.confidence,
      severity: episode.severity,
      category: episode.category,
      rootCause: episode.root_cause,
      metadata: episode.metadata,
    })
  }

  for (const rc of data.root_causes ?? []) {
    nodes.push({
      id: `root_cause-${rc.id}`,
      label: rc.name,
      type: 'root_cause',
      frequency: rc.frequency,
      avgResolutionTime: rc.avg_resolution_time_minutes,
      successRate: rc.success_rate,
      metadata: rc.metadata,
    })
  }

  for (const action of data.actions ?? []) {
    nodes.push({
      id: `action-${action.id}`,
      label: action.name,
      type: 'action',
      usedCount: action.used_count,
      successRate: action.success_rate,
      avgExecutionTime: action.avg_execution_time_seconds,
      metadata: action.metadata,
    })
  }

  for (const service of data.services ?? []) {
    nodes.push({
      id: `service-${service.name}`,
      label: service.name,
      type: 'service',
      status: service.status as EpisodicNode['status'],
      incidentCount: service.incident_count,
      lastIncident: service.last_incident,
      metadata: service.metadata,
    })
  }

  for (const entity of data.entities ?? []) {
    nodes.push({
      id: `entity-${entity.id}`,
      label: entity.name,
      type: 'entity',
      relationCount: entity.relation_count,
      metadata: entity.metadata,
    })
  }

  for (const edge of data.edges ?? []) {
    links.push({
      source: edge.source,
      target: edge.target,
      label: edge.relationship,
      type: edge.relationship,
      weight: edge.weight,
      metadata: edge.metadata,
    })
  }

  return { nodes, links }
}

/**
 * Command Center — a single-screen operations cockpit that fuses the three
 * surfaces an operator juggles during an incident:
 *
 *   ┌────────────┬───────────────────────┐
 *   │            │  Active incidents      │
 *   │  Topology  ├───────────────────────┤
 *   │  graph     │  Assistant chat        │
 *   │            │  (tool calls)          │
 *   └────────────┴───────────────────────┘
 *
 * As a cockpit page its root is `h-full min-h-0 flex flex-col` so it EXACTLY
 * fills the shell's bounded `<main>` and scrolls internally — every pane stays
 * reachable on any viewport, nothing clips off-screen. Selecting services on
 * the graph (Ctrl-click) attaches them to the chat as context, and an
 * incident's "Open in Chat" prefills the same composer — so investigation
 * never leaves this screen.
 */
export function Console() {
  const [selection, setSelection] = useState<SelectedItem[]>([])
  // Bumping the key re-prefills the chat composer even with identical text.
  const [injected, setInjected] = useState<{ text: string; key: number }>({ text: '', key: 0 })

  // Which topology the left pane shows. 'platform' is the schema graph (default);
  // 'episodic' is the memory graph rendered top-down via EpisodicGraphExplorer.
  const [graphMode, setGraphMode] = useState<'platform' | 'episodic'>('platform')

  // Episodic graph data — fetched lazily the first time episodic mode is opened.
  const [episodic, setEpisodic] = useState<{ nodes: EpisodicNode[]; links: EpisodicLink[] }>({
    nodes: [],
    links: [],
  })
  const [episodicLoading, setEpisodicLoading] = useState(false)
  // Guards the one-shot fetch so it doesn't re-run on every render.
  const episodicFetchedRef = useRef(false)

  // The explorer needs an explicit numeric height; measure the pane body.
  const episodicBodyRef = useRef<HTMLDivElement>(null)
  const [episodicHeight, setEpisodicHeight] = useState(MIN_EPISODIC_HEIGHT)

  // One-shot fetch of the episodic memory graph when episodic mode is first
  // activated. The ref guard means subsequent mode toggles reuse the data.
  useEffect(() => {
    if (graphMode !== 'episodic' || episodicFetchedRef.current) return
    episodicFetchedRef.current = true

    let cancelled = false
    setEpisodicLoading(true)
    fetch('/api/v1/graph/episodes?limit=50&since_hours=168', { credentials: 'same-origin' })
      .then((res) => {
        if (!res.ok) throw new Error(`Graph fetch failed: ${res.status}`)
        return res.json() as Promise<EpisodesResponse>
      })
      .then((data) => {
        if (!cancelled) setEpisodic(transformEpisodes(data))
      })
      .catch(() => {
        // On failure, allow a later activation to retry by clearing the guard.
        episodicFetchedRef.current = false
      })
      .finally(() => {
        if (!cancelled) setEpisodicLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [graphMode])

  // Track the pane body's height so the (fixed-height) explorer canvas fills it.
  // useLayoutEffect + ResizeObserver keeps it in sync as the pane resizes.
  useLayoutEffect(() => {
    if (graphMode !== 'episodic') return
    const el = episodicBodyRef.current
    if (!el) return

    const measure = () => {
      setEpisodicHeight(Math.max(MIN_EPISODIC_HEIGHT, el.clientHeight))
    }
    measure()

    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [graphMode])

  const handleSelectionChange = useCallback((items: SelectedItem[]) => {
    setSelection(items)
  }, [])

  const handleOpenInChat = useCallback((prompt: string) => {
    setInjected((prev) => ({ text: prompt, key: prev.key + 1 }))
  }, [])

  // The frozen schema-graph chat context, attached to every send while a
  // selection exists. undefined clears it (no empty payload on the wire).
  const seedContext = useMemo(
    () => (selection.length > 0 ? buildSchemaChatContext(selection, WINDOW_HOURS) : undefined),
    [selection],
  )

  const chipLabel = (item: SelectedItem): string =>
    item.type === 'node' ? item.node.label : `${item.edge.source} → ${item.edge.target}`

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      {/* Header — compact so the panes get the vertical room. */}
      <div className="flex shrink-0 flex-wrap items-center gap-2.5">
        <Waypoints className="h-6 w-6 shrink-0 text-primary" />
        <div>
          <h1 className="text-xl font-bold leading-tight">Command Center</h1>
          <p className="text-xs text-muted-foreground">
            Live topology, active incidents and the assistant — one operations view.
          </p>
        </div>
      </div>

      {/* Body: left pane (graph) + right column (incidents over chat). Stacks
          vertically and goes side-by-side at lg (1024) now that the UI is
          80%-scaled. The cockpit fills `<main>` and scrolls INTERNALLY rather
          than growing the page, so nothing is ever cut off. */}
      <div className="flex min-h-0 flex-1 flex-col gap-3 lg:flex-row">
        {/* LEFT PANE — topology graph (always shown) */}
        <section
          className="relative flex h-[46vh] min-h-0 flex-col rounded-xl border border-border bg-card p-3 lg:h-auto lg:w-[58%] lg:min-w-[480px] lg:max-w-none"
          data-testid="console-graph-pane"
        >
          <div className="mb-2 flex shrink-0 items-center justify-between gap-2">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Waypoints className="h-4 w-4 text-cyan-400" />
              {graphMode === 'platform' ? 'Platform Topology' : 'Episodic Topology'}
            </h2>
            {/* Segmented control — switch the pane between the two topologies. */}
            <div className="flex shrink-0 items-center rounded-md bg-muted p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setGraphMode('platform')}
                aria-pressed={graphMode === 'platform'}
                className={`rounded px-2 py-0.5 font-medium transition-colors ${
                  graphMode === 'platform'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Platform
              </button>
              <button
                type="button"
                onClick={() => setGraphMode('episodic')}
                aria-pressed={graphMode === 'episodic'}
                className={`rounded px-2 py-0.5 font-medium transition-colors ${
                  graphMode === 'episodic'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Episodic
              </button>
            </div>
          </div>
          {graphMode === 'platform' ? (
            <>
              <div className="min-h-0 flex-1">
                <Suspense
                  fallback={
                    <div className="flex h-full items-center justify-center rounded-lg bg-gradient-to-br from-slate-900/50 to-slate-800/50">
                      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                  }
                >
                  <SchemaGraph embedded onSelectionChange={handleSelectionChange} />
                </Suspense>
              </div>
              <p className="mt-1.5 shrink-0 text-[11px] leading-snug text-muted-foreground/70">
                Click a service to inspect · Ctrl-click to attach it to the chat as context.
              </p>
            </>
          ) : (
            <>
              {/* Ref'd body whose measured height feeds the explorer; the explorer
                  needs an explicit numeric height (it can't size off flex alone). */}
              <div ref={episodicBodyRef} className="min-h-0 flex-1 overflow-hidden">
                <EpisodicGraphExplorer
                  nodes={episodic.nodes}
                  links={episodic.links}
                  loading={episodicLoading}
                  height={episodicHeight}
                  defaultLayoutMode="dag"
                  dagDirection="td"
                />
              </div>
              <p className="mt-1.5 shrink-0 text-[11px] leading-snug text-muted-foreground/70">
                Episodic memory — incidents, root causes and the services they touched.
              </p>
            </>
          )}
        </section>

        {/* RIGHT COLUMN — incidents (top) + chat (bottom) */}
        <div className="flex min-h-0 min-w-[360px] flex-1 flex-col gap-3">
          {/* TOP — active incidents. Capped to a fraction of the column so it
              never starves the chat; scrolls internally when there are many. */}
          <div className="max-h-[38%] shrink-0 overflow-y-auto" data-testid="console-incidents">
            <ActiveIncidentsPanel onOpenInChat={handleOpenInChat} />
          </div>

          {/* BOTTOM — assistant chat. flex-1 takes the remaining height; the
              ChatPane manages its own internal scroll with the composer pinned. */}
          <div
            className="flex min-h-0 min-w-0 flex-1 flex-col rounded-xl border border-border bg-card/40 p-3"
            data-testid="console-chat"
          >
            {selection.length > 0 && (
              <div className="mb-2 flex shrink-0 flex-wrap items-center gap-1.5 rounded-lg border border-blue-500/30 bg-blue-500/10 px-2.5 py-1.5 text-xs text-blue-200">
                <Sparkles className="h-3.5 w-3.5 shrink-0" />
                <span className="font-medium">
                  {selection.length} attached as context
                </span>
                <span className="flex flex-wrap items-center gap-1">
                  {selection.slice(0, 4).map((item) => (
                    <span
                      key={item.key}
                      className="max-w-[160px] truncate rounded-full border border-blue-500/40 bg-blue-500/10 px-2 py-0.5 text-blue-200"
                    >
                      {chipLabel(item)}
                    </span>
                  ))}
                  {selection.length > 4 && <span className="text-blue-300/80">+{selection.length - 4}</span>}
                </span>
                <span className="ml-auto flex items-center gap-1 text-blue-300/70">
                  <X className="h-3 w-3" />
                  click empty graph space to clear
                </span>
              </div>
            )}
            <ChatPane
              variant="embedded"
              seedContext={seedContext}
              injectedPrompt={injected.key > 0 ? injected : undefined}
              className="min-h-0 flex-1"
            />
          </div>
        </div>
      </div>

      {/* Narrow-viewport hint: the cockpit stacks vertically below lg. */}
      <p className="flex shrink-0 items-center gap-1.5 text-[11px] text-muted-foreground/60 lg:hidden">
        <AlertTriangle className="h-3 w-3" />
        Best viewed on a wider screen — panes stack on narrow viewports.
      </p>
    </div>
  )
}
