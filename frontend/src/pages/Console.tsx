import { lazy, Suspense, useCallback, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Loader2,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  Waypoints,
  X,
} from 'lucide-react'
import { ActiveIncidentsPanel } from '../components/incidents/ActiveIncidentsPanel'
import { ChatPane } from '../components/chat/ChatPane'
import { buildSchemaChatContext } from '../components/schema/types'
import type { SelectedItem } from '../components/schema/types'

// The platform-topology graph is lazy so the Console chunk stays lean; it is
// only fetched when this page mounts (and never when the pane is collapsed off).
const SchemaGraph = lazy(() => import('../components/schema/SchemaGraph'))

// Matches the schema graph's default analysis window so the chat context that
// rides along with a selection describes the same span the graph is showing.
const WINDOW_HOURS = 168

/**
 * Command Center — a single-screen operations cockpit that fuses the three
 * surfaces an operator juggles during an incident:
 *
 *   ┌────────────┬───────────────────────┐
 *   │            │  Active incidents      │
 *   │  Topology  ├───────────────────────┤
 *   │  graph     │  Assistant chat        │
 *   │ (toggle)   │  (tool calls)          │
 *   └────────────┴───────────────────────┘
 *
 * The left graph pane is collapsible to hand its width to the chat. Selecting
 * services on the graph (Ctrl-click) attaches them to the chat as context, and
 * an incident's "Open in Chat" prefills the same composer — so investigation
 * never leaves this screen.
 */
export function Console() {
  const [graphOpen, setGraphOpen] = useState(true)
  const [selection, setSelection] = useState<SelectedItem[]>([])
  // Bumping the key re-prefills the chat composer even with identical text.
  const [injected, setInjected] = useState<{ text: string; key: number }>({ text: '', key: 0 })

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
    <div className="flex flex-col gap-4 xl:h-[calc(100vh-3rem)]">
      {/* Header */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Waypoints className="h-6 w-6 text-primary" />
            Command Center
          </h1>
          <p className="text-sm text-muted-foreground">
            Live topology, active incidents and the assistant — one operations view.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setGraphOpen((v) => !v)}
          className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
          data-testid="console-toggle-graph"
          aria-pressed={graphOpen}
        >
          {graphOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
          {graphOpen ? 'Hide graph' : 'Show graph'}
        </button>
      </div>

      {/* Body: graph (left) + incidents/chat (right). Side-by-side on lg, stacked below. */}
      <div className="flex min-h-0 flex-1 flex-col gap-4 xl:flex-row">
        {/* LEFT — topology graph (collapsible) */}
        {graphOpen ? (
          <section
            className="relative flex h-[340px] min-h-0 flex-col rounded-xl border border-border bg-card p-3 xl:h-auto xl:w-[42%] xl:min-w-[360px] xl:max-w-[680px]"
            data-testid="console-graph-pane"
          >
            <div className="mb-2 flex shrink-0 items-center justify-between">
              <h2 className="flex items-center gap-2 text-sm font-semibold">
                <Waypoints className="h-4 w-4 text-cyan-400" />
                Platform Topology
              </h2>
              <button
                type="button"
                onClick={() => setGraphOpen(false)}
                title="Collapse graph"
                aria-label="Collapse graph"
                className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <PanelLeftClose className="h-4 w-4" />
              </button>
            </div>
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
          </section>
        ) : (
          // Collapsed rail (lg+) — a slim re-open affordance.
          <button
            type="button"
            onClick={() => setGraphOpen(true)}
            className="hidden shrink-0 flex-col items-center gap-2 rounded-xl border border-border bg-card px-2 py-3 text-muted-foreground hover:bg-muted hover:text-foreground xl:flex"
            data-testid="console-graph-rail"
            title="Show graph"
            aria-label="Show graph"
          >
            <PanelLeftOpen className="h-4 w-4" />
            <span className="[writing-mode:vertical-rl] text-xs font-medium">Topology</span>
          </button>
        )}

        {/* RIGHT — incidents (top) + chat (bottom) */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-4">
          {/* TOP — active incidents */}
          <div className="shrink-0 overflow-y-auto xl:max-h-[40%]" data-testid="console-incidents">
            <ActiveIncidentsPanel onOpenInChat={handleOpenInChat} />
          </div>

          {/* BOTTOM — assistant chat with graph-selection context */}
          <div
            className="flex min-h-[460px] min-w-0 flex-1 flex-col rounded-xl border border-border bg-card/40 p-3 xl:min-h-0"
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
              className="flex-1"
            />
          </div>
        </div>
      </div>

      {/* Mobile hint: incidents count never hidden, but the cockpit stacks. */}
      <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground/60 xl:hidden">
        <AlertTriangle className="h-3 w-3" />
        Best viewed on a wider screen — panes stack on narrow viewports.
      </p>
    </div>
  )
}
