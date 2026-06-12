import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../lib/auth'

/**
 * Route guard: while the auth store is bootstrapping it renders a minimal
 * full-screen spinner (no flash of the wrong page); once ready, anonymous
 * visitors are sent to /login (with the attempted location preserved in
 * ?next=) whenever enforcement is on. With AUTH_REQUIRED off it is a
 * pass-through, so pre-flip behavior is unchanged.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const status = useAuthStore((s) => s.status)
  const location = useLocation()

  if (status !== 'ready') {
    return (
      <div
        className="flex min-h-screen items-center justify-center bg-background"
        role="status"
        aria-label="Loading"
      >
        <div
          className="h-8 w-8 rounded-full border-2 border-border border-t-primary animate-spin motion-reduce:animate-none"
          aria-hidden="true"
        />
      </div>
    )
  }

  if (authRequired && !user) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`)
    return <Navigate to={`/login?next=${next}`} replace />
  }

  return <>{children}</>
}

export default RequireAuth
