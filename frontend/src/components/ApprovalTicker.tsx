/**
 * ApprovalTicker - a Dashboard widget listing actions awaiting human approval,
 * aging live, each with its constitutional confidence band and tier checks
 * (Track 2 widget). Read-only and no-LLM: purely a view over the pending-actions
 * the system already surfaces. Approve/reject still happens on Incidents/Console.
 */

import { Link } from 'react-router-dom'
import { ShieldCheck, Clock } from 'lucide-react'
import { cn } from '../lib/utils'
import { formatAge, type TickerItem, type ConfidenceBand } from '../lib/approvalTicker'

const BAND_STYLE: Record<ConfidenceBand, string> = {
  high: 'bg-green-500/15 text-green-600 dark:text-green-400',
  medium: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
  low: 'bg-red-500/15 text-red-600 dark:text-red-400',
}
const BAND_LABEL: Record<ConfidenceBand, string> = {
  high: 'High confidence',
  medium: 'Needs approval',
  low: 'Low confidence',
}

function TierBadges({ tiers }: { tiers: TickerItem['tiers'] }) {
  const cells: Array<[string, boolean]> = [
    ['T1', tiers.tier1],
    ['T2', tiers.tier2],
    ['T3', tiers.tier3],
  ]
  return (
    <span className="inline-flex items-center gap-1">
      {cells.map(([label, ok]) => (
        <span
          key={label}
          title={ok ? `${label} passed` : `${label} not passed`}
          className={cn(
            'rounded-sm px-1.5 py-0.5 font-mono text-xs',
            ok
              ? 'bg-muted text-muted-foreground'
              : 'bg-red-500/15 text-red-600 dark:text-red-400',
          )}
        >
          {label}
        </span>
      ))}
    </span>
  )
}

export function ApprovalTicker({
  items,
  now,
  max = 5,
}: {
  items: TickerItem[]
  now: number
  max?: number
}) {
  const shown = items.slice(0, max)
  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <ShieldCheck className="h-5 w-5" />
          Awaiting approval
          {items.length > 0 && (
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              {items.length}
            </span>
          )}
        </h2>
        {items.length > 0 && (
          <Link to="/incidents" className="text-xs text-primary hover:underline">
            View all
          </Link>
        )}
      </div>
      {items.length === 0 ? (
        <div className="py-8 text-center text-muted-foreground">
          <ShieldCheck className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No actions awaiting approval</p>
          <p className="text-xs mt-1">
            Proposed actions that need a human decision appear here with their constitutional
            confidence and tier checks.
          </p>
        </div>
      ) : (
        <ul className="space-y-2">
          {shown.map((item) => (
            <li
              key={item.id}
              className="rounded-lg border border-border/60 bg-muted/30 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="truncate text-sm font-medium">{item.description}</p>
                <span className="shrink-0 inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" aria-hidden="true" />
                  {formatAge(item.createdAt, now)}
                </span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground">{item.target}</span>
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    BAND_STYLE[item.band],
                  )}
                >
                  {BAND_LABEL[item.band]} · {Math.round(item.confidence * 100)}%
                </span>
                <TierBadges tiers={item.tiers} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default ApprovalTicker
