/**
 * Constitutional AIOps — per-user LLM endpoint status (BYOK Phase B).
 *
 * Reports whether the CURRENT user has a usable bring-your-own LLM endpoint so
 * the onboarding gate can route a regular tenant to /setup before they land on a
 * chat that would 400. The admin / self-host (synthetic) user always resolves
 * 'configured': they use the box's global env endpoint, never a per-user one.
 *
 * Also holds the one-shot "the BYOK setup redirect already fired this session"
 * flag, so a tenant who chooses to continue without an endpoint is nudged once,
 * never trapped in a redirect loop.
 */

import { useEffect, useState } from 'react'

import api from './api'
import { useAuthStore } from './auth'

export type EndpointStatus = 'loading' | 'configured' | 'missing'

/** sessionStorage key for the one-shot onboarding-redirect guard. */
const BYOK_SETUP_SEEN_KEY = 'aiops.byok.setup.seen'

/** Record that the BYOK onboarding redirect has fired this browser session. */
export function markByokSetupSeen(): void {
  try {
    window.sessionStorage.setItem(BYOK_SETUP_SEEN_KEY, '1')
  } catch {
    // Storage may be unavailable (private mode); the redirect just fires again.
  }
}

/** Has the BYOK onboarding redirect already fired this session? */
export function byokSetupSeen(): boolean {
  try {
    return window.sessionStorage.getItem(BYOK_SETUP_SEEN_KEY) === '1'
  } catch {
    return false
  }
}

/** True once all four URL+model fields are present (the backend's routing gate). */
function isComplete(c: {
  fastAgentUrl: string
  fastAgentModel: string
  reasoningAgentUrl: string
  reasoningAgentModel: string
}): boolean {
  return Boolean(
    c.fastAgentUrl.trim() &&
      c.fastAgentModel.trim() &&
      c.reasoningAgentUrl.trim() &&
      c.reasoningAgentModel.trim(),
  )
}

/**
 * Endpoint status for the signed-in user. Admin / self-host is always
 * 'configured' (global endpoint). A regular tenant is probed once via
 * GET /settings/models; a load failure fails OPEN ('configured') so a backend
 * hiccup never traps a user in onboarding. Stays 'loading' until auth has
 * bootstrapped, so the caller never decides on a half-known identity.
 */
export function useEndpointStatus(): EndpointStatus {
  const authRequired = useAuthStore((s) => s.authRequired)
  const role = useAuthStore((s) => s.user?.role)
  const authStatus = useAuthStore((s) => s.status)
  const isRegularUser = authRequired && Boolean(role) && role !== 'admin'

  const [status, setStatus] = useState<EndpointStatus>('loading')

  useEffect(() => {
    if (authStatus !== 'ready') {
      setStatus('loading')
      return
    }
    if (!isRegularUser) {
      setStatus('configured')
      return
    }
    let alive = true
    setStatus('loading')
    api.settings
      .getModels()
      .then((c) => {
        if (alive) setStatus(isComplete(c) ? 'configured' : 'missing')
      })
      .catch(() => {
        // Fail OPEN: never trap a user in setup because /settings/models blipped.
        if (alive) setStatus('configured')
      })
    return () => {
      alive = false
    }
  }, [authStatus, isRegularUser])

  return status
}
