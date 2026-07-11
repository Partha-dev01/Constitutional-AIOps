import { FormEvent, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Loader2, LogIn, Shield } from 'lucide-react'
import { ApiError } from '../lib/api'
import { useAuthStore } from '../lib/auth'

/**
 * Full-screen login page, rendered OUTSIDE the sidebar Layout. Submits via
 * the auth store; on success it navigates to the ?next= target (default /).
 * Pre-flip (authRequired === false) or when already signed in it immediately
 * redirects to next, so the page never blocks anyone while enforcement is
 * off. Visuals follow the app brand (Shield + "Constitutional AIOps") on a
 * flat background — no decoration, so it is reduced-motion-safe.
 */

/** Only allow same-app absolute paths as redirect targets (no `//host`). */
function safeNext(raw: string | null): string {
  if (!raw) return '/'
  if (!raw.startsWith('/') || raw.startsWith('//')) return '/'
  return raw
}

export function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const next = safeNext(new URLSearchParams(location.search).get('next'))

  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const status = useAuthStore((s) => s.status)
  const login = useAuthStore((s) => s.login)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Pre-flip or already-signed-in: never block, go straight to the target.
  useEffect(() => {
    if (status === 'ready' && (!authRequired || user)) {
      navigate(next, { replace: true })
    }
  }, [status, authRequired, user, next, navigate])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (submitting) return
    setError('')
    setSubmitting(true)
    try {
      await login(username.trim(), password)
      navigate(next, { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('Invalid username or password.')
      } else if (err instanceof ApiError && err.status === 429) {
        setError('Too many failed attempts. Try again in 15 minutes.')
      } else {
        setError(err instanceof Error ? err.message : 'Login failed. Please try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const inputClasses =
    'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm ' +
    'text-foreground placeholder:text-muted-foreground outline-none transition-colors ' +
    'focus:border-primary focus:ring-2 focus:ring-primary/40'

  return (
    <div
      className="flex min-h-screen items-center justify-center bg-background px-4 font-sans text-foreground"
      data-testid="login-page"
    >
      <div className="w-full max-w-sm rounded-lg border border-border bg-card p-8 shadow-sm">
        {/* Brand wordmark, matching components/Layout.tsx */}
        <div className="mb-6 flex items-center justify-center gap-2">
          <Shield className="h-8 w-8 text-primary" />
          <div>
            <p className="text-lg font-bold leading-tight">Constitutional</p>
            <p className="text-xs text-muted-foreground">AIOps</p>
          </div>
        </div>

        <h1 className="mb-1 text-center text-xl font-semibold" data-testid="login-heading">
          Sign in
        </h1>
        <p className="mb-6 text-center text-sm text-muted-foreground">
          Use your Constitutional AIOps account
        </p>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="login-username" className="mb-1 block text-sm font-medium">
              Username
            </label>
            <input
              id="login-username"
              name="username"
              type="text"
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={inputClasses}
              placeholder="username"
            />
          </div>

          <div>
            <label htmlFor="login-password" className="mb-1 block text-sm font-medium">
              Password
            </label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClasses}
              placeholder="••••••••••"
            />
          </div>

          {error && (
            <p
              className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400"
              role="alert"
              data-testid="login-error"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || !username || !password}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/60 focus:ring-offset-2 focus:ring-offset-card disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                Signing in…
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" aria-hidden="true" />
                Sign in
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
