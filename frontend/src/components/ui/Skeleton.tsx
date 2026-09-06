/**
 * Skeleton - a neutral, content-shaped loading placeholder (Track 2 QoL).
 *
 * Prefer this over a bare spinner for list/table loads: it hints at the shape of
 * what is coming and reduces layout shift. Uses the same muted token as the rest
 * of the UI and only pulses when the viewer has not asked to reduce motion.
 */

import { cn } from '../../lib/utils'

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('motion-safe:animate-pulse rounded bg-muted', className)}
      aria-hidden="true"
    />
  )
}

/** A block of skeleton "cards" for list views (e.g. incidents). */
export function SkeletonCards({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3" role="status" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-4">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-4 w-16" />
          </div>
          <Skeleton className="mt-3 h-3 w-2/3" />
          <Skeleton className="mt-2 h-3 w-1/2" />
        </div>
      ))}
    </div>
  )
}

/** A stack of skeleton bars, e.g. for a table or list loading placeholder. */
export function SkeletonBars({ count = 6, barClassName }: { count?: number; barClassName?: string }) {
  return (
    <div
      className="space-y-2 rounded-lg border border-border bg-card p-4"
      role="status"
      aria-label="Loading"
    >
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className={cn('h-9 w-full', barClassName)} />
      ))}
    </div>
  )
}

export default Skeleton
