/**
 * Constitutional AIOps - Notification inbox (admin only).
 *
 * The in-app alert center: what actually fired, not just which channels
 * Settings configured. Backed by the server-side notification store, which is
 * appended to in-request whenever the system raises an alert (an action
 * awaiting approval, a blocked action, a webhook test). An empty inbox on a
 * fresh instance is the honest, expected result.
 */

import { useCallback, useEffect, useState } from 'react'
import {
  Bell,
  CheckCheck,
  Loader2,
  RefreshCw,
  ShieldAlert,
  Trash2,
} from 'lucide-react'
import { cn } from '../lib/utils'
import api from '../lib/api'
import type { AppNotification } from '../lib/api'
import { useAuthStore } from '../lib/auth'
import { useToast } from '../components/ui/toast'

const SEVERITY_STYLE: Record<string, string> = {
  info: 'bg-muted text-muted-foreground',
  warning: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
  error: 'bg-red-500/15 text-red-600 dark:text-red-400',
  critical: 'bg-red-600/20 text-red-700 dark:text-red-300',
}

const SEVERITY_ACCENT: Record<string, string> = {
  info: 'border-l-muted-foreground/40',
  warning: 'border-l-amber-500',
  error: 'border-l-red-500',
  critical: 'border-l-red-600',
}

function SeverityChip({ severity }: { severity: string }) {
  const s = (severity || 'info').toLowerCase()
  return (
    <span
      className={cn(
        'inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize',
        SEVERITY_STYLE[s] || SEVERITY_STYLE.info,
      )}
    >
      {s}
    </span>
  )
}

function fmtTime(iso: string): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

export function Notifications() {
  const authRequired = useAuthStore((s) => s.authRequired)
  const role = useAuthStore((s) => s.user?.role)
  const isAdmin = !authRequired || role === 'admin'
  const { showConfirm } = useToast()

  const [items, setItems] = useState<AppNotification[]>([])
  const [unread, setUnread] = useState(0)
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchItems = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.notifications.list({ limit: 200, unreadOnly })
      setItems(resp.notifications)
      setUnread(resp.unread)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }, [unreadOnly])

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false)
      return
    }
    void fetchItems()
  }, [isAdmin, fetchItems])

  const markAllRead = async () => {
    if (busy || unread === 0) return
    setBusy(true)
    try {
      await api.notifications.markRead({ all: true })
      await fetchItems()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update notifications')
    } finally {
      setBusy(false)
    }
  }

  const clearAll = async () => {
    if (busy || items.length === 0) return
    const confirmed = await showConfirm(
      'Clear all notifications?',
      'This removes every notification from the inbox. This cannot be undone.',
    )
    if (!confirmed) return
    setBusy(true)
    try {
      await api.notifications.clear()
      await fetchItems()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to clear notifications')
    } finally {
      setBusy(false)
    }
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <ShieldAlert className="mx-auto h-10 w-10 text-muted-foreground" aria-hidden="true" />
        <h1 className="mt-4 text-xl font-semibold">Notifications</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The notification inbox is restricted to administrators. Ask an admin if you need to review
          system alerts.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <Bell className="h-6 w-6 text-primary" aria-hidden="true" />
            Notifications
            {unread > 0 && (
              <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground">
                {unread} unread
              </span>
            )}
          </h1>
          <p className="text-muted-foreground">
            Alerts the system raised: actions awaiting approval, blocked actions, webhook tests.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void fetchItems()}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
          ) : (
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
          )}
          Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(e) => setUnreadOnly(e.target.checked)}
            className="h-4 w-4 rounded-sm border-border"
          />
          <span className="text-muted-foreground">Unread only</span>
        </label>
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={() => void markAllRead()}
            disabled={busy || unread === 0}
            className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted disabled:opacity-50"
          >
            <CheckCheck className="h-4 w-4" aria-hidden="true" />
            Mark all read
          </button>
          <button
            type="button"
            onClick={() => void clearAll()}
            disabled={busy || items.length === 0}
            className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 px-3 py-1.5 text-sm font-medium text-red-600 transition-colors hover:bg-red-500/10 disabled:opacity-50 dark:text-red-400"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Clear
          </button>
        </div>
      </div>

      {error && (
        <div
          className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
        >
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      ) : items.length > 0 ? (
        <ul className="space-y-2">
          {items.map((n) => (
            <li
              key={n.id}
              className={cn(
                'rounded-lg border border-l-4 border-border bg-card p-4',
                SEVERITY_ACCENT[n.severity] || SEVERITY_ACCENT.info,
                !n.read && 'bg-primary/4',
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  {!n.read && (
                    <span
                      className="h-2 w-2 shrink-0 rounded-full bg-primary"
                      aria-label="Unread"
                    />
                  )}
                  <span className="font-medium">{n.title}</span>
                  <SeverityChip severity={n.severity} />
                </div>
                <span className="whitespace-nowrap text-xs text-muted-foreground">
                  {fmtTime(n.timestamp)}
                </span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">{n.message}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                <span className="font-mono">{n.source}</span>
                {n.resource_id ? <span className="font-mono"> · {n.resource_id}</span> : null}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <div className="rounded-lg border border-dashed border-border bg-muted/30 p-10 text-center text-sm text-muted-foreground">
          {unreadOnly
            ? 'No unread notifications.'
            : 'No notifications yet. Alerts appear here as the system raises them.'}
        </div>
      )}
    </div>
  )
}

export default Notifications
