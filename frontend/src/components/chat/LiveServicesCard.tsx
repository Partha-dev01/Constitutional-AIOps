/**
 * LiveServicesCard — an interactive chat artifact for the empty state.
 *
 * Renders the deployment's ACTUAL services (from the topology) as small cards,
 * each with a live CPU sparkline (from the Docker-socket metrics) when data is
 * flowing. Clicking a card prefills a scoped "diagnose" prompt into the composer
 * (never auto-sends), so the chat feels interactive and grounded in real data.
 * Renders nothing when there is no topology, so it is invisible on a bare setup.
 */

import { Boxes } from 'lucide-react'
import type { TopologySchemaNode } from '../../lib/api'
import { useContainerStats } from '../../hooks/useContainerStats'
import { Sparkline } from '../viz/Sparkline'

interface LiveServicesCardProps {
  nodes: TopologySchemaNode[]
  /** Prefill the composer with a scoped prompt (never auto-sends). */
  onPick: (prompt: string) => void
  /** Slimmer padding for the embedded (cockpit) variant. */
  dense?: boolean
}

const MAX_CARDS = 6

export function LiveServicesCard({ nodes, onPick, dense = false }: LiveServicesCardProps) {
  const live = useContainerStats({ intervalMs: 5000 })

  if (!Array.isArray(nodes) || nodes.length === 0) return null

  const seriesFor = (label: string) => {
    const l = label.toLowerCase()
    return live.series.find((s) => s.label.toLowerCase() === l || s.service.toLowerCase().includes(l))
  }

  return (
    <div className={`w-full max-w-2xl rounded-xl border border-border/60 bg-card/60 ${dense ? 'p-2.5' : 'p-3'}`}>
      <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Boxes className="h-3.5 w-3.5" />
        Your services
        {live.source === 'docker' && (
          <span className="flex items-center gap-1 text-[10px] text-green-500">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500" />
            live
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {nodes.slice(0, MAX_CARDS).map((n) => {
          const s = seriesFor(n.label)
          const hasLive = !!(s && s.cpu.length > 0)
          return (
            <button
              key={n.id}
              type="button"
              onClick={() => onPick(`Diagnose the ${n.label} service. Summarize its current health, recent errors, and anything unusual.`)}
              title={`Diagnose ${n.label}`}
              className="group rounded-lg border border-border/60 bg-background/60 p-2 text-left transition-colors hover:border-primary/40 hover:bg-primary/5"
            >
              <div className="flex items-center justify-between gap-1">
                <span className="flex min-w-0 items-center gap-1.5">
                  <span
                    className={`h-1.5 w-1.5 shrink-0 rounded-full ${hasLive ? 'bg-green-500' : 'bg-muted-foreground/40'}`}
                    aria-hidden="true"
                  />
                  <span className="truncate text-xs font-medium" title={n.label}>{n.label}</span>
                </span>
                <span className="shrink-0 rounded bg-muted/60 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-muted-foreground">
                  {n.kind}
                </span>
              </div>
              <div className="mt-1.5 flex h-[20px] items-center text-primary">
                {hasLive ? (
                  <Sparkline values={s!.cpu} min={0} height={20} area={false} ariaLabel={`${n.label} CPU trend`} />
                ) : (
                  <span
                    className="h-px w-full bg-gradient-to-r from-border via-border/60 to-transparent"
                    aria-hidden="true"
                  />
                )}
              </div>
              <div className="mt-1 flex items-center justify-between text-[10px]">
                <span className="text-muted-foreground/70">
                  {hasLive ? `${s!.latestCpu?.toFixed(0) ?? '—'}% CPU` : 'No live metrics'}
                </span>
                <span className="font-medium text-primary/70 opacity-70 transition-opacity group-hover:opacity-100">
                  Diagnose →
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
