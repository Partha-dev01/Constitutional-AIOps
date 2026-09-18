/**
 * Constitutional AIOps — first-run onboarding gate (setup-first).
 *
 * Reports whether the CURRENT user should be sent to the guided /setup wizard
 * before landing in the app. Admin / self-host is always 'ok': they configure
 * through Settings, not the first-run wizard, so they never get bounced (this
 * also keeps the box admin and the live post-deploy smoke on the dashboard).
 *
 * A regular tenant is probed once via GET /settings/onboarding. Only an explicit
 * completed=false && skipped=false marks 'needs-setup'; a malformed or catch-all
 * response (missing fields) fails OPEN to 'ok', so a backend blip never traps a
 * user in setup. Pairs with a one-shot session flag so a tenant who leaves the
 * wizard without finishing is never caught in a redirect loop.
 */

import { useEffect, useState } from 'react'

import api from './api'
import { useAuthStore } from './auth'

export type OnboardingGateStatus = 'loading' | 'needs-setup' | 'ok'

/** sessionStorage key for the one-shot setup-redirect guard. */
const ONBOARDING_SETUP_SEEN_KEY = 'aiops.onboarding.setup.seen'

/** Record that the setup redirect has fired this browser session. */
export function markOnboardingSetupSeen(): void {
  try {
    window.sessionStorage.setItem(ONBOARDING_SETUP_SEEN_KEY, '1')
  } catch {
    // Storage may be unavailable (private mode); the redirect just fires again.
  }
}

/** Has the setup redirect already fired this session? */
export function onboardingSetupSeen(): boolean {
  try {
    return window.sessionStorage.getItem(ONBOARDING_SETUP_SEEN_KEY) === '1'
  } catch {
    return false
  }
}

/**
 * Onboarding gate for the signed-in user. Admin / self-host is always 'ok'.
 * Stays 'loading' until auth has bootstrapped so the caller never decides on a
 * half-known identity.
 */
export function useOnboardingStatus(): OnboardingGateStatus {
  const authRequired = useAuthStore((s) => s.authRequired)
  const role = useAuthStore((s) => s.user?.role)
  const authStatus = useAuthStore((s) => s.status)
  const isRegularUser = authRequired && Boolean(role) && role !== 'admin'

  const [status, setStatus] = useState<OnboardingGateStatus>('loading')

  useEffect(() => {
    if (authStatus !== 'ready') {
      setStatus('loading')
      return
    }
    if (!isRegularUser) {
      setStatus('ok')
      return
    }
    let alive = true
    setStatus('loading')
    api.settings
      .getOnboarding()
      .then((ob) => {
        if (!alive) return
        // Strict: only an explicit "not started" state gates. Anything else
        // (completed, skipped, or a malformed response) fails OPEN.
        setStatus(ob.completed === false && ob.skipped === false ? 'needs-setup' : 'ok')
      })
      .catch(() => {
        // Fail OPEN: never trap a user in setup because the probe blipped.
        if (alive) setStatus('ok')
      })
    return () => {
      alive = false
    }
  }, [authStatus, isRegularUser])

  return status
}
