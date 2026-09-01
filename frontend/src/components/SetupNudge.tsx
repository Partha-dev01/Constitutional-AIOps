import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Rocket, X } from 'lucide-react'

import api from '../lib/api'

const DISMISS_KEY = 'aiops.setupNudge.dismissed'

function readDismissed(): boolean {
  try {
    return window.sessionStorage.getItem(DISMISS_KEY) === 'true'
  } catch {
    return false
  }
}

/**
 * Soft first-run nudge. When onboarding is neither completed nor skipped, it
 * offers a dismissible banner into the guided /setup wizard — never redirects,
 * never blocks. Rendered only in non-demo builds (guarded by the caller). Fails
 * closed (shows nothing) when the onboarding state cannot be read, and the
 * dismiss is remembered for the browser session.
 */
export function SetupNudge() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    let alive = true
    if (readDismissed()) return
    api.settings
      .getOnboarding()
      .then((ob) => {
        if (alive && !ob.completed && !ob.skipped) setShow(true)
      })
      .catch(() => {
        /* fail closed: no nudge if the state is unreadable */
      })
    return () => {
      alive = false
    }
  }, [])

  if (!show) return null

  const dismiss = () => {
    try {
      window.sessionStorage.setItem(DISMISS_KEY, 'true')
    } catch {
      /* ignore storage failures (private mode / disabled) */
    }
    setShow(false)
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 p-3">
      <Rocket className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">Finish setting up Constitutional AIOps</p>
        <p className="text-xs text-muted-foreground">
          Connect your services, model endpoint and monitoring in a few guided steps.
        </p>
      </div>
      <Link
        to="/setup"
        className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Continue setup
      </Link>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss setup reminder"
        className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  )
}

export default SetupNudge
