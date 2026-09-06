/**
 * WhatChangedDiff - a Dashboard widget that captures a baseline of the live
 * incidents + services on mount, then on each Refresh shows what moved since
 * (new / resolved incidents, status changes, added / removed services) and
 * makes the new snapshot the baseline (Track 2 widget). Read-only and no-LLM:
 * a pure client-side diff over data the system already surfaces.
 */

import { useEffect, useRef, useState } from 'react'
import {
  GitCompareArrows,
  RefreshCw,
  History,
  Loader2,
  PlusCircle,
  MinusCircle,
  ArrowRight,
} from 'lucide-react'
import { api } from '../lib/api'
import { diffSnapshots, type Snapshot, type SnapshotDiff } from '../lib/whatChanged'

type Phase = 'loading' | 'baseline' | 'diffed' | 'error'

/** Read the current incidents + services into a snapshot, or null on any error. */
async function captureSnapshot(): Promise<Snapshot | null> {
  try {
    const [list, schema] = await Promise.all([
      api.incidents.list({ page_size: 100 }),
      api.topology.getSchema(),
    ])
    const incidents = (list.items ?? []).map((i) => ({
      id: i.id,
      status: i.status,
      title: i.title,
    }))
    // Services = topology node labels (fall back to id when a node has no label).
    const services = Array.from(
      new Set((schema.nodes ?? []).map((n) => n.label || n.id)),
    )
    return { incidents, services }
  } catch {
    return null
  }
}

function diffCount(d: SnapshotDiff): number {
  return (
    d.addedIncidents.length +
    d.removedIncidents.length +
    d.statusChanges.length +
    d.addedServices.length +
    d.removedServices.length
  )
}

export function WhatChangedDiff() {
  const baseline = useRef<Snapshot | null>(null)
  const [phase, setPhase] = useState<Phase>('loading')
  const [diff, setDiff] = useState<SnapshotDiff | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    void captureSnapshot().then((snap) => {
      if (!alive) return
      if (snap) {
        baseline.current = snap
        setPhase('baseline')
      } else {
        setPhase('error')
      }
    })
    return () => {
      alive = false
    }
  }, [])

  const refresh = async () => {
    setBusy(true)
    const next = await captureSnapshot()
    if (next) {
      const prev = baseline.current ?? next
      setDiff(diffSnapshots(prev, next))
      baseline.current = next
      setPhase('diffed')
    } else if (!baseline.current) {
      // First capture never succeeded — surface the honest error state.
      setPhase('error')
    }
    // A transient refresh error with a baseline in hand keeps the last diff.
    setBusy(false)
  }

  const count = diff ? diffCount(diff) : 0

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <GitCompareArrows className="h-5 w-5" />
          What changed
          {diff && diff.changed && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {count}
            </span>
          )}
        </h2>
        <button
          onClick={() => void refresh()}
          disabled={busy || phase === 'loading'}
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium hover:bg-muted disabled:opacity-50"
          title="Capture a new snapshot and diff it against the baseline"
          aria-label="Refresh"
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCw className="h-3.5 w-3.5" />
          )}
          Refresh
        </button>
      </div>

      {phase === 'loading' && !diff ? (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      ) : phase === 'error' && !diff ? (
        <div className="py-8 text-center text-muted-foreground">
          <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Snapshot unavailable right now.</p>
          <p className="text-xs mt-1">Refresh once the incidents and topology load.</p>
        </div>
      ) : !diff || !diff.changed ? (
        <div className="py-8 text-center text-muted-foreground">
          <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">
            {diff ? 'No changes since the last snapshot.' : 'Baseline captured.'}
          </p>
          <p className="text-xs mt-1">Changes appear after the next refresh.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <DiffGroup
            title="New incidents"
            tone="added"
            items={diff.addedIncidents.map((i) => label(i.id, i.title))}
          />
          <DiffGroup
            title="Cleared incidents"
            tone="removed"
            items={diff.removedIncidents.map((i) => label(i.id, i.title))}
          />
          <DiffGroup
            title="Status changes"
            tone="changed"
            items={diff.statusChanges.map(
              (c) => `${label(c.id, c.title)}: ${c.from} → ${c.to}`,
            )}
          />
          <DiffGroup title="Services added" tone="added" items={diff.addedServices} />
          <DiffGroup title="Services removed" tone="removed" items={diff.removedServices} />
        </div>
      )}
    </div>
  )
}

function label(id: string, title?: string): string {
  return title ? `${id} · ${title}` : id
}

const TONE_ICON = {
  added: PlusCircle,
  removed: MinusCircle,
  changed: ArrowRight,
} as const

const TONE_STYLE: Record<keyof typeof TONE_ICON, string> = {
  added: 'text-green-600 dark:text-green-400',
  removed: 'text-red-600 dark:text-red-400',
  changed: 'text-amber-600 dark:text-amber-400',
}

function DiffGroup({
  title,
  tone,
  items,
}: {
  title: string
  tone: keyof typeof TONE_ICON
  items: string[]
}) {
  if (items.length === 0) return null
  const Icon = TONE_ICON[tone]
  return (
    <div>
      <h3 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <Icon className={`h-3.5 w-3.5 ${TONE_STYLE[tone]}`} aria-hidden="true" />
        {title}
        <span className="font-normal normal-case">({items.length})</span>
      </h3>
      <ul className="space-y-1">
        {items.map((text) => (
          <li
            key={text}
            className="truncate rounded-md border border-border/60 bg-muted/30 px-3 py-1.5 text-sm"
          >
            {text}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default WhatChangedDiff
