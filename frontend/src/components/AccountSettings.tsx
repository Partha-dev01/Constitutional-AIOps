import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  UserCircle2,
  KeyRound,
  ShieldCheck,
  Users,
  Trash2,
  UserPlus,
  Loader2,
  CheckCircle,
  AlertTriangle,
  LogOut,
  Copy,
  Plus,
  Terminal,
} from 'lucide-react'
import api, { AdminUserListItem, AccessTokenSummary } from '../lib/api'
import { useAuthStore } from '../lib/auth'

const MIN_PASSWORD_LEN = 10

function errMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback
}

/**
 * Account tab for the Settings page. Every signed-in user can view their
 * identity and change their own password (verifying the current one).
 * Admins additionally get user management (list / create / reset / delete),
 * backed by the require_admin endpoints under /auth/users.
 */
export function AccountSettings() {
  const user = useAuthStore((s) => s.user)
  const authRequired = useAuthStore((s) => s.authRequired)
  const isAdmin = user?.role === 'admin'

  if (!authRequired || !user) {
    return (
      <div className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
        Account management is available when in-app authentication is enabled.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <ProfileCard username={user.username} role={user.role} />
        <ChangePasswordCard username={user.username} />
      </div>
      <AccessTokensCard />
      {isAdmin && <UserManagementCard currentUsername={user.username} />}
    </div>
  )
}

const EXPIRY_OPTIONS: { label: string; days: number | null }[] = [
  { label: 'No expiry', days: null },
  { label: '30 days', days: 30 },
  { label: '90 days', days: 90 },
  { label: '1 year', days: 365 },
]

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString()
}

/**
 * Personal access tokens: self-service API credentials for the REST API and
 * the SDK. The secret is shown once at creation and only its hash is stored,
 * so a token can be revoked but never re-read.
 */
function AccessTokensCard() {
  const [tokens, setTokens] = useState<AccessTokenSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [expiryIdx, setExpiryIdx] = useState(0)
  const [creating, setCreating] = useState(false)
  const [freshToken, setFreshToken] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.tokens.list()
      setTokens(data.items)
    } catch (err) {
      setError(errMessage(err, 'Could not load access tokens.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    const trimmed = name.trim()
    if (!trimmed) {
      setError('Give the token a name so you can recognise it later.')
      return
    }
    setCreating(true)
    try {
      const created = await api.tokens.create({
        name: trimmed,
        expires_in_days: EXPIRY_OPTIONS[expiryIdx].days,
      })
      setFreshToken(created.token)
      setCopied(false)
      setName('')
      setExpiryIdx(0)
      await load()
    } catch (err) {
      setError(errMessage(err, 'Could not create token.'))
    } finally {
      setCreating(false)
    }
  }

  const onCopy = async () => {
    if (!freshToken) return
    try {
      await navigator.clipboard.writeText(freshToken)
      setCopied(true)
    } catch {
      // Clipboard blocked (insecure context / permissions): leave the value on
      // screen for a manual copy rather than surfacing an error.
    }
  }

  const onRevoke = async (id: string, tokenName: string) => {
    if (!window.confirm(`Revoke token "${tokenName}"? Anything using it stops working.`)) return
    setError(null)
    try {
      await api.tokens.revoke(id)
      await load()
    } catch (err) {
      setError(errMessage(err, 'Could not revoke token.'))
    }
  }

  const field =
    'rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring'

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-1 flex items-center gap-2">
        <Terminal className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Access tokens</h2>
      </div>
      <p className="mb-4 text-sm text-muted-foreground">
        Create a token to call the API or the SDK as yourself. Send it as{' '}
        <code className="rounded bg-muted px-1 py-0.5 text-xs">Authorization: Bearer &lt;token&gt;</code>.
        The secret is shown once.
      </p>

      {error && (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-2.5 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {freshToken && (
        <div className="mb-4 rounded-lg border border-green-500/30 bg-green-500/10 p-3">
          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-green-700">
            <CheckCircle className="h-4 w-4 shrink-0" />
            Copy your token now — it will not be shown again.
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 overflow-x-auto rounded-md border border-border bg-background px-2 py-1.5 text-xs">
              {freshToken}
            </code>
            <button
              type="button"
              onClick={() => void onCopy()}
              className="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium hover:bg-muted"
            >
              {copied ? <CheckCircle className="h-3.5 w-3.5 text-green-600" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button
              type="button"
              onClick={() => setFreshToken(null)}
              className="rounded-md px-2 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              Done
            </button>
          </div>
        </div>
      )}

      <form onSubmit={onCreate} className="mb-6 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[160px]">
          <label className="mb-1 block text-xs font-medium text-muted-foreground" htmlFor="tok-name">
            Token name
          </label>
          <input
            id="tok-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. ci-pipeline"
            maxLength={100}
            className={`${field} w-full`}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground" htmlFor="tok-exp">
            Expires
          </label>
          <select
            id="tok-exp"
            value={expiryIdx}
            onChange={(e) => setExpiryIdx(Number(e.target.value))}
            className={field}
          >
            {EXPIRY_OPTIONS.map((opt, i) => (
              <option key={opt.label} value={i}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          Create token
        </button>
      </form>

      {loading ? (
        <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading tokens…
        </div>
      ) : tokens.length === 0 ? (
        <p className="py-4 text-sm text-muted-foreground">No access tokens yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="pb-2 pr-4 font-medium">Name</th>
                <th className="pb-2 pr-4 font-medium">Token</th>
                <th className="pb-2 pr-4 font-medium">Last used</th>
                <th className="pb-2 pr-4 font-medium">Expires</th>
                <th className="pb-2 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tokens.map((t) => (
                <tr key={t.id} className="border-b border-border/60">
                  <td className="py-2 pr-4 font-medium">{t.name}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-muted-foreground">{t.prefix}…</td>
                  <td className="py-2 pr-4 text-muted-foreground">{fmtDate(t.last_used_at)}</td>
                  <td className="py-2 pr-4 text-muted-foreground">{fmtDate(t.expires_at)}</td>
                  <td className="py-2 text-right">
                    <button
                      type="button"
                      onClick={() => onRevoke(t.id, t.name)}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function ProfileCard({ username, role }: { username: string; role: string }) {
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const [busy, setBusy] = useState<'one' | 'all' | null>(null)

  const doLogout = async (everywhere: boolean) => {
    setBusy(everywhere ? 'all' : 'one')
    try {
      await logout(everywhere)
      navigate('/login')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-4 flex items-center gap-2">
        <UserCircle2 className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Your account</h2>
      </div>
      <dl className="space-y-3 text-sm">
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Username</dt>
          <dd className="font-medium">{username}</dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Role</dt>
          <dd>
            <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium capitalize text-primary">
              {role === 'admin' && <ShieldCheck className="h-3.5 w-3.5" />}
              {role}
            </span>
          </dd>
        </div>
      </dl>

      <div className="mt-6 border-t border-border pt-4">
        <p className="mb-3 text-sm font-medium">Session</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void doLogout(false)}
            disabled={busy !== null}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {busy === 'one' ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogOut className="h-4 w-4" />}
            Log out
          </button>
          <button
            type="button"
            onClick={() => void doLogout(true)}
            disabled={busy !== null}
            className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
          >
            {busy === 'all' ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogOut className="h-4 w-4" />}
            Log out of all devices
          </button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Logging out of all devices ends every active session for this account.
        </p>
      </div>
    </div>
  )
}

function ChangePasswordCard({ username }: { username: string }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validate = (): string | null => {
    if (!current) return 'Enter your current password.'
    if (next.length < MIN_PASSWORD_LEN)
      return `New password must be at least ${MIN_PASSWORD_LEN} characters.`
    if (next === username) return 'New password must be different from your username.'
    if (next === current) return 'New password must be different from the current one.'
    if (next !== confirm) return 'New password and confirmation do not match.'
    return null
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setDone(false)
    const problem = validate()
    if (problem) {
      setError(problem)
      return
    }
    setBusy(true)
    try {
      await api.auth.changePassword(current, next)
      setDone(true)
      setCurrent('')
      setNext('')
      setConfirm('')
    } catch (err) {
      setError(errMessage(err, 'Could not change password.'))
    } finally {
      setBusy(false)
    }
  }

  const field =
    'w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring'

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-4 flex items-center gap-2">
        <KeyRound className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Change password</h2>
      </div>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="pw-current">
            Current password
          </label>
          <input
            id="pw-current"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            className={field}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="pw-new">
            New password
          </label>
          <input
            id="pw-new"
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            className={field}
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium" htmlFor="pw-confirm">
            Confirm new password
          </label>
          <input
            id="pw-confirm"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            className={field}
          />
        </div>
        <p className="text-xs text-muted-foreground">
          At least {MIN_PASSWORD_LEN} characters, and different from your username.
        </p>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-2.5 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {done && (
          <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 p-2.5 text-sm text-green-600">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <span>Password changed.</span>
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
          Update password
        </button>
      </form>
    </div>
  )
}

function UserManagementCard({ currentUsername }: { currentUsername: string }) {
  const [users, setUsers] = useState<AdminUserListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  // Create-user form
  const [newUser, setNewUser] = useState('')
  const [newPass, setNewPass] = useState('')
  const [newRole, setNewRole] = useState<'user' | 'admin'>('user')
  const [creating, setCreating] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.admin.listUsers()
      setUsers(data.items)
    } catch (err) {
      setError(errMessage(err, 'Could not load users.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setNotice(null)
    if (newPass.length < MIN_PASSWORD_LEN) {
      setError(`Password must be at least ${MIN_PASSWORD_LEN} characters.`)
      return
    }
    setCreating(true)
    try {
      await api.admin.createUser({ username: newUser.trim(), password: newPass, role: newRole })
      setNotice(`User "${newUser.trim()}" created.`)
      setNewUser('')
      setNewPass('')
      setNewRole('user')
      await load()
    } catch (err) {
      setError(errMessage(err, 'Could not create user.'))
    } finally {
      setCreating(false)
    }
  }

  const onResetPassword = async (username: string) => {
    const pw = window.prompt(`New password for "${username}" (min ${MIN_PASSWORD_LEN} chars):`)
    if (pw === null) return
    if (pw.length < MIN_PASSWORD_LEN) {
      setError(`Password must be at least ${MIN_PASSWORD_LEN} characters.`)
      return
    }
    setError(null)
    setNotice(null)
    try {
      await api.admin.setPassword(username, pw)
      setNotice(`Password reset for "${username}".`)
    } catch (err) {
      setError(errMessage(err, 'Could not reset password.'))
    }
  }

  const onDelete = async (username: string) => {
    if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) return
    setError(null)
    setNotice(null)
    try {
      await api.admin.deleteUser(username)
      setNotice(`User "${username}" deleted.`)
      await load()
    } catch (err) {
      setError(errMessage(err, 'Could not delete user.'))
    }
  }

  const field =
    'rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring'

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="mb-1 flex items-center gap-2">
        <Users className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Users</h2>
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
          Admin
        </span>
      </div>
      <p className="mb-4 text-sm text-muted-foreground">
        Create accounts, reset passwords, or remove users.
      </p>

      {error && (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-2.5 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {notice && (
        <div className="mb-3 flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 p-2.5 text-sm text-green-600">
          <CheckCircle className="h-4 w-4 shrink-0" />
          <span>{notice}</span>
        </div>
      )}

      {/* Create user */}
      <form onSubmit={onCreate} className="mb-6 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[140px]">
          <label className="mb-1 block text-xs font-medium text-muted-foreground" htmlFor="nu-user">
            Username
          </label>
          <input
            id="nu-user"
            required
            value={newUser}
            onChange={(e) => setNewUser(e.target.value)}
            className={`${field} w-full`}
          />
        </div>
        <div className="flex-1 min-w-[140px]">
          <label className="mb-1 block text-xs font-medium text-muted-foreground" htmlFor="nu-pass">
            Password
          </label>
          <input
            id="nu-pass"
            type="password"
            required
            autoComplete="new-password"
            value={newPass}
            onChange={(e) => setNewPass(e.target.value)}
            className={`${field} w-full`}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground" htmlFor="nu-role">
            Role
          </label>
          <select
            id="nu-role"
            value={newRole}
            onChange={(e) => setNewRole(e.target.value === 'admin' ? 'admin' : 'user')}
            className={field}
          >
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
          Add user
        </button>
      </form>

      {/* User list */}
      {loading ? (
        <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading users…
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-muted-foreground">
                <th className="pb-2 pr-4 font-medium">Username</th>
                <th className="pb-2 pr-4 font-medium">Role</th>
                <th className="pb-2 pr-4 font-medium">Created</th>
                <th className="pb-2 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const self = u.username === currentUsername
                return (
                  <tr key={u.username} className="border-b border-border/60">
                    <td className="py-2 pr-4 font-medium">
                      {u.username}
                      {self && <span className="ml-2 text-xs text-muted-foreground">(you)</span>}
                    </td>
                    <td className="py-2 pr-4 capitalize text-muted-foreground">{u.role}</td>
                    <td className="py-2 pr-4 text-muted-foreground">
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="py-2 text-right">
                      <div className="inline-flex gap-2">
                        <button
                          type="button"
                          onClick={() => onResetPassword(u.username)}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                        >
                          <KeyRound className="h-3.5 w-3.5" />
                          Reset
                        </button>
                        <button
                          type="button"
                          onClick={() => onDelete(u.username)}
                          disabled={self}
                          title={self ? 'You cannot delete your own account' : undefined}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-destructive hover:bg-destructive/10 disabled:opacity-40 disabled:hover:bg-transparent"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
