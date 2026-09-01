import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Loader2, UserPlus } from 'lucide-react'
import { ApiError } from '../lib/api'
import { useAuthStore } from '../lib/auth'
import { CaptchaWidget } from '../components/CaptchaWidget'

/**
 * Public self-service signup for the hosted demo. Only reachable when the
 * backend reports signup_enabled (self-host keeps signup off and admin-managed).
 * On success the backend logs the user straight in, so this navigates to the
 * app exactly like Login. Mirrors Login.tsx's flat, reduced-motion-safe visuals.
 */

function safeNext(raw: string | null): string {
  if (!raw) return '/'
  if (!raw.startsWith('/') || raw.startsWith('//')) return '/'
  return raw
}

export function Signup() {
  const navigate = useNavigate()
  const location = useLocation()
  const next = safeNext(new URLSearchParams(location.search).get('next'))

  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const signupEnabled = useAuthStore((s) => s.signupEnabled)
  const captchaProvider = useAuthStore((s) => s.captchaProvider)
  const captchaSiteKey = useAuthStore((s) => s.captchaSiteKey)
  const status = useAuthStore((s) => s.status)
  const signup = useAuthStore((s) => s.signup)

  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const captchaRequired = Boolean(captchaProvider) && Boolean(captchaSiteKey)
  const onToken = useCallback((token: string | null) => setCaptchaToken(token), [])

  // Already signed in, or auth not enforced at all: go straight to the app.
  useEffect(() => {
    if (status === 'ready' && (!authRequired || user)) {
      navigate(next, { replace: true })
    } else if (status === 'ready' && !signupEnabled) {
      // Signup disabled on this deployment: fall back to the login page.
      navigate('/login', { replace: true })
    }
  }, [status, authRequired, user, signupEnabled, next, navigate])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (submitting) return
    if (captchaRequired && !captchaToken) {
      setError('Please complete the verification challenge.')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      await signup(username.trim(), email.trim(), password, captchaToken ?? undefined)
      navigate(next, { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError('That username or email is already taken.')
      } else if (err instanceof ApiError && err.status === 429) {
        setError('Too many signups from your network. Try again later.')
      } else if (err instanceof ApiError && err.status === 400) {
        setError(err.message || 'Please check your details and try again.')
      } else {
        setError(err instanceof Error ? err.message : 'Signup failed. Please try again.')
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
      className="flex min-h-screen items-center justify-center bg-background px-4 py-8 font-sans text-foreground"
      data-testid="signup-page"
    >
      <div className="w-full max-w-sm rounded-lg border border-border bg-card p-8 shadow-sm">
        <div className="mb-6 flex items-center justify-center gap-2">
          <img src="/logo-mark.png" alt="" aria-hidden="true" className="h-10 w-10 rounded-full" />
          <div>
            <p className="text-lg font-bold leading-tight">Constitutional</p>
            <p className="text-xs text-muted-foreground">AIOps</p>
          </div>
        </div>

        <h1 className="mb-1 text-center text-xl font-semibold" data-testid="signup-heading">
          Create your demo account
        </h1>
        <p className="mb-6 text-center text-sm text-muted-foreground">
          Free access to the live Constitutional AIOps demo
        </p>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="signup-username" className="mb-1 block text-sm font-medium">
              Username
            </label>
            <input
              id="signup-username"
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
            <label htmlFor="signup-email" className="mb-1 block text-sm font-medium">
              Email
            </label>
            <input
              id="signup-email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClasses}
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="signup-password" className="mb-1 block text-sm font-medium">
              Password
            </label>
            <input
              id="signup-password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={10}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClasses}
              placeholder="••••••••••"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              At least 10 characters, and different from your username.
            </p>
          </div>

          {captchaRequired && (
            <CaptchaWidget provider={captchaProvider} siteKey={captchaSiteKey} onToken={onToken} />
          )}

          {error && (
            <p
              className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-400"
              role="alert"
              data-testid="signup-error"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || !username || !email || password.length < 10}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/60 focus:ring-offset-2 focus:ring-offset-card disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                Creating account…
              </>
            ) : (
              <>
                <UserPlus className="h-4 w-4" aria-hidden="true" />
                Create account
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link
            to={`/login${next !== '/' ? `?next=${encodeURIComponent(next)}` : ''}`}
            className="font-medium text-primary hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

export default Signup
