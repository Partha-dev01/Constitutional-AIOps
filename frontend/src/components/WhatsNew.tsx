/**
 * WhatsNew - a dismissible banner surfacing what changed since the version this
 * browser last saw. Mirrors SetupNudge: soft, never blocks, fails closed (shows
 * nothing) when there is nothing pending. Rendered only in non-demo builds
 * (guarded by the caller). Brand-new browsers see the product tour instead, so
 * this stays empty for them (see lib/tour/whatsNew.pendingWhatsNew).
 */
import { useState } from 'react'
import { Sparkles, X } from 'lucide-react'

import { pendingWhatsNew, markWhatsNewSeen } from '../lib/tour/whatsNew'
import { useProductTour } from '../lib/tour/store'

export function WhatsNew() {
  const [notes, setNotes] = useState(() => pendingWhatsNew())
  if (notes.length === 0) return null

  const latest = notes[0]
  const earlierCount = notes.length - 1

  const dismiss = () => {
    markWhatsNewSeen()
    setNotes([])
  }

  const takeTour = () => {
    useProductTour.getState().start()
  }

  return (
    <div className="mb-4 rounded-xl border border-primary/30 bg-primary/10 p-4">
      <div className="flex items-start gap-3">
        <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">{latest.title}</p>
          <ul className="mt-2 space-y-1">
            {latest.items.map((item) => (
              <li key={item} className="flex gap-2 text-xs text-muted-foreground">
                <span className="mt-0.5 text-primary" aria-hidden="true">
                  &bull;
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
          {earlierCount > 0 && (
            <p className="mt-2 text-xs text-muted-foreground/80">
              and {earlierCount} earlier update{earlierCount > 1 ? 's' : ''}.
            </p>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={takeTour}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-hidden focus:ring-2 focus:ring-primary/40"
            >
              Take the tour
            </button>
            <button
              type="button"
              onClick={dismiss}
              className="rounded-lg px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/40"
            >
              Dismiss
            </button>
          </div>
        </div>
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss what's new"
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/40"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}

export default WhatsNew
