/**
 * Constitutional AIOps - Audit Log viewer (admin only).
 *
 * A read-only window onto the JSONL audit trail: every constitutional
 * validation, approval, rejection, action and tool call the system records.
 * The trail fills as the system is used, so an empty table on a fresh instance
 * is the honest, expected result rather than an error.
 */

import { useCallback, useEffect, useState } from 'react'
import { Loader2, RefreshCw, ScrollText, ShieldAlert } from 'lucide-react'
import { cn } from '../lib/utils'
import api from '../lib/api'
import type { AuditEvent } from '../lib/api'
import { useAuthStore } from '../lib/auth'

const DAY_OPTIONS = [
  { value: 1, label: 'Last 24 hours' },
  { value: 7, label: 'Last 7 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
]

const SEVERITY_STYLE: Record<string, string> = {
  info: 'bg-muted text-muted-foreground',
  warning: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
  error: 'bg-red-500/15 text-red-600 dark:text-red-400',
  critical: 'bg-red-600/20 text-red-700 dark:text-red-300',
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

export function Audit() {
  const authRequired = useAuthStore((s) => s.authRequired)
  const role = useAuthStore((s) => s.user?.role)
  const isAdmin = !authRequired || role === 'admin'

  const [events, setEvents] = useState<AuditEvent[]>([])
  const [eventTypes, setEventTypes] = useState<string[]>([])
  const [days, setDays] = useState(7)
  const [eventType, setEventType] = useState('')
  const [truncated, setTruncated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.audit.list({ days, limit: 100, eventType: eventType || undefined })
      setEvents(resp.events)
      setTruncated(resp.truncated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load the audit log')
    } finally {
      setLoading(false)
    }
  }, [days, eventType])

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false)
      return
    }
    void fetchEvents()
  }, [isAdmin, fetchEvents])

  // Populate the event-type filter once (best-effort).
  useEffect(() => {
    if (!isAdmin) return
    api.audit
      .eventTypes()
      .then((r) => setEventTypes(r.event_types))
      .catch(() => {
        /* filter dropdown is optional */
      })
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <ShieldAlert className="mx-auto h-10 w-10 text-muted-foreground" aria-hidden="true" />
        <h1 className="mt-4 text-xl font-semibold">Audit log</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The audit log is restricted to administrators. Ask an admin if you need to review the
          action trail.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <ScrollText className="h-6 w-6 text-primary" aria-hidden="true" />
            Audit log
          </h1>
          <p className="text-muted-foreground">
            Every validation, approval and action the system recorded. Read-only.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void fetchEvents()}
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
          <span className="text-muted-foreground">Window</span>
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value, 10))}
            className="rounded border border-border bg-background p-1.5 text-sm text-foreground"
          >
            {DAY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Event</span>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
            className="rounded border border-border bg-background p-1.5 text-sm text-foreground"
          >
            <option value="">All events</option>
            {eventTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive" role="alert">
          {error}
        </div>
      )}

      {truncated && !error && (
        <p className="text-xs text-muted-foreground">
          Showing the 100 most recent events in this window. Narrow the window or filter by event to
          see older entries.
        </p>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
        </div>
      ) : events.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full min-w-[820px] text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Time</th>
                <th className="px-4 py-2 text-left font-medium">Event</th>
                <th className="px-4 py-2 text-left font-medium">Severity</th>
                <th className="px-4 py-2 text-left font-medium">Actor</th>
                <th className="px-4 py-2 text-left font-medium">Resource</th>
                <th className="px-4 py-2 text-left font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.event_id} className="border-t border-border align-top">
                  <td className="whitespace-nowrap px-4 py-2 text-muted-foreground">
                    {fmtTime(ev.timestamp)}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{ev.event_type}</td>
                  <td className="px-4 py-2">
                    <SeverityChip severity={ev.severity} />
                  </td>
                  <td className="px-4 py-2">
                    <span className="font-medium">{ev.actor_id}</span>
                    <span className="block text-xs text-muted-foreground">{ev.actor_type}</span>
                  </td>
                  <td className="px-4 py-2 text-xs">
                    {ev.resource_type ? (
                      <>
                        <span className="text-muted-foreground">{ev.resource_type}</span>
                        {ev.resource_id ? <span className="block font-mono">{ev.resource_id}</span> : null}
                      </>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    {ev.description || '—'}
                    {ev.outcome && ev.outcome !== 'success' && (
                      <span className="ml-2 rounded bg-red-500/15 px-1.5 py-0.5 text-xs text-red-600 dark:text-red-400">
                        {ev.outcome}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border bg-muted/30 p-10 text-center text-sm text-muted-foreground">
          No audited actions in this window yet. The trail fills as validations, approvals and
          actions happen.
        </div>
      )}
    </div>
  )
}

export default Audit
