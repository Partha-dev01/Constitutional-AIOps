/**
 * ServiceActionBar — service-aware quick actions for the Command Center.
 *
 * Reads the live topology (GET /topology/schema) so the actions always match
 * the ACTUAL deployment. Read-only actions (Diagnose / Recent logs /
 * Dependencies / Health) prefill a scoped prompt into the chat composer via
 * `onAction` (never auto-sent). The mutating Restart action also just prefills
 * a request: sending it flows through the normal chat -> constitutional gate ->
 * approve/reject card, so it stays whitelist-gated and never bypasses consent.
 */

import { useEffect, useState } from 'react'
import { Activity, FileText, GitBranch, HeartPulse, RotateCcw, Wrench } from 'lucide-react'
import api from '../../lib/api'
import type { TopologySchemaNode } from '../../lib/api'
import { useContainerStats } from '../../hooks/useContainerStats'

interface ServiceActionBarProps {
  /** Prefill the chat composer with a scoped prompt (never auto-sends). */
  onAction: (prompt: string) => void
}

interface QuickAction {
  key: string
  label: string
  Icon: typeof Activity
  prompt: (svc: string) => string
  mutating?: boolean
}

const READ_ONLY_ACTIONS: QuickAction[] = [
  {
    key: 'diagnose',
    label: 'Diagnose',
    Icon: Activity,
    prompt: (s) => `Diagnose the ${s} service. Summarize its current health, recent errors, and anything unusual.`,
  },
  {
    key: 'logs',
    label: 'Recent logs',
    Icon: FileText,
    prompt: (s) => `Show the recent error logs for ${s}.`,
  },
  {
    key: 'deps',
    label: 'Dependencies',
    Icon: GitBranch,
    prompt: (s) => `What does ${s} depend on, and what depends on it?`,
  },
  {
    key: 'health',
    label: 'Health',
    Icon: HeartPulse,
    prompt: (s) => `Give me a health summary for ${s} right now.`,
  },
]

const RESTART_ACTION: QuickAction = {
  key: 'restart',
  label: 'Restart',
  Icon: RotateCcw,
  prompt: (s) => `Restart the ${s} service.`,
  mutating: true,
}

export function ServiceActionBar({ onAction }: ServiceActionBarProps) {
  const [nodes, setNodes] = useState<TopologySchemaNode[]>([])
  const [selected, setSelected] = useState<string>('')
  // Live CPU for the selected service, so the bar shows real status at a glance.
  const live = useContainerStats({ intervalMs: 5000 })

  useEffect(() => {
    let cancelled = false
    api.topology
      .getSchema()
      .then((schema) => {
        if (cancelled) return
        const ns = Array.isArray(schema.nodes) ? schema.nodes : []
        setNodes(ns)
        if (ns.length > 0) setSelected((cur) => cur || ns[0].label)
      })
      .catch(() => {
        /* No topology configured — the bar simply doesn't render. */
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (nodes.length === 0) return null

  // Match the live series to the selected service by fuzzy name (container names
  // carry an aiops- prefix; topology labels do not).
  const sel = selected.toLowerCase()
  const liveSeries = live.series.find(
    (s) => s.label.toLowerCase() === sel || s.service.toLowerCase().includes(sel),
  )

  const fire = (action: QuickAction) => {
    if (!selected) return
    onAction(action.prompt(selected))
  }

  return (
    <div className="shrink-0 rounded-xl border border-border bg-card/40 p-2.5" data-testid="service-action-bar">
      <div className="mb-2 flex items-center gap-2">
        <Wrench className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-semibold">Service actions</span>
        {liveSeries?.latestCpu != null && (
          <span className="rounded-full border border-border/60 bg-muted/60 px-1.5 py-0.5 text-[10px] text-muted-foreground">
            {liveSeries.latestCpu.toFixed(0)}% CPU
          </span>
        )}
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          aria-label="Select a service"
          data-testid="service-action-select"
          className="ml-auto max-w-[45%] truncate rounded-md border border-border bg-background px-2 py-1 text-xs focus:outline-hidden focus:ring-1 focus:ring-primary"
        >
          {nodes.map((n) => (
            <option key={n.id} value={n.label}>{n.label}</option>
          ))}
        </select>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {READ_ONLY_ACTIONS.map((a) => (
          <button
            key={a.key}
            type="button"
            onClick={() => fire(a)}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground transition-colors hover:border-primary/40 hover:bg-primary/10 hover:text-primary"
          >
            <a.Icon className="h-3 w-3" />
            {a.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => fire(RESTART_ACTION)}
          title="Prefills a restart request — sending it still goes through the constitutional approval card and the container whitelist."
          className="inline-flex items-center gap-1 rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-xs text-amber-600 transition-colors hover:bg-amber-500/20 dark:text-amber-400"
        >
          <RESTART_ACTION.Icon className="h-3 w-3" />
          {RESTART_ACTION.label}
          <span className="ml-0.5 text-[9px] opacity-70">needs approval</span>
        </button>
      </div>
    </div>
  )
}
