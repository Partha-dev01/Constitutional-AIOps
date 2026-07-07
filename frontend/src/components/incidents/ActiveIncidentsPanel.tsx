import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  MessageSquare,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { api } from '../../lib/api'
import type { Incident } from '../../lib/api'

// Statuses that are still "live" and therefore actionable. Typed as plain
// strings because the backend emits more status values than the (stale) TS
// IncidentStatus union; we match on the raw status string instead.
const ACTIVE_STATUSES: string[] = [
  'detecting',
  'analyzing',
  'pending_approval',
  'remediating',
]

const SEV_STYLE: Record<string, string> = {
  critical: 'bg-red-500/15 text-red-400 border-red-500/30',
  high: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  low: 'bg-sky-500/15 text-sky-400 border-sky-500/30',
  info: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
}

const STATUS_LABEL: Record<string, string> = {
  detecting: 'Detecting',
  analyzing: 'Analyzing',
  pending_approval: 'Needs approval',
  remediating: 'Remediating',
  resolved: 'Resolved',
  closed: 'Closed',
}

interface ActionState {
  busy: 'remediate' | 'dismiss' | null
  result?: { ok: boolean; text: string }
}

/**
 * Active-incident strip: lists live incidents and lets the operator act on each
 * one — Approve & Remediate (gated executor / t3 heal), Reject (archive), or
 * Open in Chat (hands the incident to the assistant for deeper investigation).
 * Polls every 12s; resolved/closed incidents drop off on the next poll.
 */
interface ActiveIncidentsPanelProps {
  className?: string
  /**
   * When provided (the Console cockpit), "Open in Chat" hands the prompt to the
   * embedded chat instead of navigating to /chat?ask=. Default = navigate.
   */
  onOpenInChat?: (prompt: string) => void
  /**
   * Notified with the live incident count on every (re)load, so a host layout
   * can collapse/expand the strip (the Console shrinks it when idle).
   */
  onCountChange?: (count: number) => void
}

export function ActiveIncidentsPanel({ className = '', onOpenInChat, onCountChange }: ActiveIncidentsPanelProps) {
  const navigate = useNavigate()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [actions, setActions] = useState<Record<string, ActionState>>({})

  const load = useCallback(async () => {
    try {
      const res = await api.incidents.list({ page_size: 50 })
      // Filter to the active/actionable statuses on the client (the list API
      // status filter expects the narrower TS union).
      const active = (res.items ?? []).filter((i) => ACTIVE_STATUSES.includes(i.status))
      setIncidents(active)
      onCountChange?.(active.length)
    } catch {
      // Transient fetch error — keep the current list rather than blanking it.
    } finally {
      setLoading(false)
    }
  }, [onCountChange])

  useEffect(() => {
    void load()
    const t = setInterval(() => void load(), 12000)
    return () => clearInterval(t)
  }, [load])

  const setAct = (id: string, s: ActionState) =>
    setActions((prev) => ({ ...prev, [id]: s }))

  const handleRemediate = async (inc: Incident) => {
    setAct(inc.id, { busy: 'remediate' })
    try {
      const res = await api.incidents.remediate(inc.id)
      setAct(inc.id, {
        busy: null,
        result: {
          ok: res.success,
          text: res.success
            ? `Remediated — ${res.method === 'demo_heal' ? 'fault healed on host' : 'service restarted via the constitutional gate'}.`
            : `Declined${res.error_code ? ` (${res.error_code})` : ''}. ${res.detail ?? ''}`.trim(),
        },
      })
      void load()
    } catch (e) {
      setAct(inc.id, {
        busy: null,
        result: { ok: false, text: e instanceof Error ? e.message : 'Remediation failed' },
      })
    }
  }

  const handleDismiss = async (inc: Incident) => {
    setAct(inc.id, { busy: 'dismiss' })
    try {
      await api.incidents.dismiss(inc.id)
      void load()
    } catch (e) {
      setAct(inc.id, {
        busy: null,
        result: { ok: false, text: e instanceof Error ? e.message : 'Dismiss failed' },
      })
    }
  }

  const openInChat = (inc: Incident) => {
    const service = inc.affected_services?.[0]?.name ?? 'the affected service'
    const prompt = `Investigate ${inc.id} (${inc.title}). Diagnose the root cause and recommend remediation for ${service}.`
    if (onOpenInChat) onOpenInChat(prompt)
    else navigate(`/chat?ask=${encodeURIComponent(prompt)}`)
  }

  return (
    <div
      className={`bg-card rounded-lg border border-border p-4 ${className}`}
      data-testid="active-incidents-panel"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Active Incidents
          {incidents.length > 0 && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400">
              {incidents.length}
            </span>
          )}
        </h3>
        <button
          onClick={() => void load()}
          className="p-1.5 rounded-md hover:bg-muted text-muted-foreground"
          title="Refresh incidents"
          aria-label="Refresh incidents"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {loading && incidents.length === 0 ? (
        <div className="flex items-center justify-center py-8 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      ) : incidents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center text-sm text-muted-foreground">
          <ShieldCheck className="h-6 w-6 mb-2 text-green-500" />
          No active incidents — all clear.
        </div>
      ) : (
        <ul className="space-y-3">
          {incidents.map((inc) => {
            const st = actions[inc.id]
            const service = inc.affected_services?.[0]?.name
            const rca = inc.rca?.root_cause
            return (
              <li
                key={inc.id}
                data-testid={`active-incident-${inc.id}`}
                className="rounded-xl border border-border bg-background/40 p-4"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded border ${
                      SEV_STYLE[inc.severity] ?? SEV_STYLE.info
                    }`}
                  >
                    {inc.severity}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {STATUS_LABEL[inc.status] ?? inc.status}
                  </span>
                  {service && (
                    <span className="text-xs text-muted-foreground/80">· {service}</span>
                  )}
                  <span className="ml-auto text-xs text-muted-foreground/50">{inc.id}</span>
                </div>
                <p className="mt-1.5 text-sm font-semibold text-foreground break-words">
                  {inc.title}
                </p>
                {rca && (
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground/90 line-clamp-2">
                    {rca}
                  </p>
                )}

                {st?.result && (
                  <div
                    className={`mt-2.5 flex items-start gap-1.5 text-xs ${
                      st.result.ok ? 'text-green-400' : 'text-amber-400'
                    }`}
                  >
                    {st.result.ok ? (
                      <CheckCircle2 className="mt-px h-4 w-4 shrink-0" />
                    ) : (
                      <XCircle className="mt-px h-4 w-4 shrink-0" />
                    )}
                    <span className="break-words">{st.result.text}</span>
                  </div>
                )}

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => void handleRemediate(inc)}
                    disabled={st?.busy != null}
                    data-testid={`incident-remediate-${inc.id}`}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                  >
                    {st?.busy === 'remediate' ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <ShieldCheck className="h-3.5 w-3.5" />
                    )}
                    Approve &amp; Remediate
                  </button>
                  <button
                    onClick={() => void handleDismiss(inc)}
                    disabled={st?.busy != null}
                    data-testid={`incident-dismiss-${inc.id}`}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
                  >
                    {st?.busy === 'dismiss' ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5" />
                    )}
                    Reject
                  </button>
                  <button
                    onClick={() => openInChat(inc)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
                  >
                    <MessageSquare className="h-3.5 w-3.5" />
                    Open in Chat
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
