import { useState } from 'react'
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Loader2,
  Ban,
  Sparkles,
} from 'lucide-react'
import api from '../../lib/api'
import type { ProposedAction, ActionDecisionResponse } from '../../lib/api'

interface ProposedActionCardProps {
  action: ProposedAction
}

/** Local UI phase for the "approve" flow. */
type CardPhase = 'idle' | 'deciding' | 'done'

/**
 * Pull a short human-readable reason out of a constitutional verdict object
 * (shape varies by backend), falling back gracefully. Never throws, never
 * renders `[object Object]`.
 */
function verdictReason(verdict: Record<string, unknown> | null | undefined): string | null {
  if (!verdict || typeof verdict !== 'object') return null
  const keys = ['reason', 'explanation', 'message', 'detail', 'summary'] as const
  for (const k of keys) {
    const v = verdict[k]
    if (typeof v === 'string' && v.trim()) return v
  }
  // A list of violations is a common shape — surface the first reason.
  const violations = verdict['violations']
  if (Array.isArray(violations) && violations.length > 0) {
    const first = violations[0]
    if (first && typeof first === 'object') {
      const reason = (first as Record<string, unknown>)['reason']
      if (typeof reason === 'string' && reason.trim()) return reason
    }
  }
  return null
}

/** Pull a short human-readable summary out of an execution result object. */
function resultSummary(result: Record<string, unknown> | null | undefined): string | null {
  if (!result || typeof result !== 'object') return null
  const keys = ['summary', 'output', 'message', 'detail'] as const
  for (const k of keys) {
    const v = result[k]
    if (typeof v === 'string' && v.trim()) return v
  }
  return null
}

/**
 * Approve/Reject card for an AI-proposed remediation, rendered beneath an
 * assistant chat bubble (as a SIBLING of the `.prose` body, never inside it).
 *
 * States:
 *  - status "proposed": title + rationale + verdict preview + Approve/Reject.
 *    Approve → decideAction(id,true) → spinner → success (green) or error (red).
 *    Reject  → decideAction(id,false) → muted "Dismissed".
 *  - status "auto_executed": read-only green "Auto-remediated" badge + result.
 *  - status "blocked": red/amber with the verdict reason (no buttons).
 */
export function ProposedActionCard({ action }: ProposedActionCardProps) {
  const [phase, setPhase] = useState<CardPhase>('idle')
  const [decision, setDecision] = useState<ActionDecisionResponse | null>(null)
  const [rejected, setRejected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const verdictText = verdictReason(action.verdict)

  const decide = async (approved: boolean) => {
    setPhase('deciding')
    setError(null)
    try {
      const res = await api.chat.decideAction(action.id, approved)
      setDecision(res)
      setRejected(!approved)
      setPhase('done')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Decision failed')
      setPhase('idle')
    }
  }

  // ── Auto-executed (read-only, green) ──────────────────────────────────────
  if (action.status === 'auto_executed') {
    const summary = resultSummary(action.execution_result) ?? verdictReason(action.verdict)
    return (
      <div
        data-testid="proposed-action-card"
        data-status="auto_executed"
        className="mt-2 rounded-xl border border-green-500/30 bg-green-500/10 p-3 text-sm"
      >
        <div className="flex items-center gap-2 font-medium text-green-600">
          <Sparkles className="h-4 w-4 shrink-0" />
          Auto-remediated
        </div>
        <p className="mt-1 font-medium">{action.title}</p>
        {summary && <p className="mt-1 text-xs text-muted-foreground">{summary}</p>}
      </div>
    )
  }

  // ── Blocked (no buttons, amber/red) ───────────────────────────────────────
  if (action.status === 'blocked') {
    return (
      <div
        data-testid="proposed-action-card"
        data-status="blocked"
        className="mt-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm"
      >
        <div className="flex items-center gap-2 font-medium text-red-600">
          <Ban className="h-4 w-4 shrink-0" />
          Blocked by constitution
        </div>
        <p className="mt-1 font-medium">{action.title}</p>
        <p className="mt-1 text-xs text-red-600/90">
          {verdictText ?? 'This action was blocked by a safety check.'}
        </p>
      </div>
    )
  }

  // ── Persisted decision outcomes (reloaded conversations, read-only) ───────
  // The backend writes the human decision back onto the stored turn so a
  // reloaded chat shows what happened instead of a stale interactive card.
  if (action.status === 'executed') {
    const summary = resultSummary(action.execution_result) ?? verdictReason(action.verdict)
    return (
      <div
        data-testid="proposed-action-card"
        data-status="executed"
        className="mt-2 rounded-xl border border-green-500/30 bg-green-500/10 p-3 text-sm"
      >
        <div className="flex items-center gap-2 font-medium text-green-600">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Executed
        </div>
        <p className="mt-1 font-medium">{action.title}</p>
        {summary && <p className="mt-1 text-xs text-muted-foreground">{summary}</p>}
      </div>
    )
  }
  if (action.status === 'rejected') {
    return (
      <div
        data-testid="proposed-action-card"
        data-status="dismissed"
        className="mt-2 rounded-xl border border-border/60 bg-muted/40 p-3 text-sm text-muted-foreground"
      >
        <div className="flex items-center gap-2 font-medium">
          <XCircle className="h-4 w-4 shrink-0" />
          Dismissed
        </div>
        <p className="mt-1">{action.title}</p>
      </div>
    )
  }
  if (action.status === 'refused') {
    return (
      <div
        data-testid="proposed-action-card"
        data-status="error"
        className="mt-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm"
      >
        <div className="flex items-center gap-2 font-medium text-red-600">
          <XCircle className="h-4 w-4 shrink-0" />
          Refused
        </div>
        <p className="mt-1 font-medium">{action.title}</p>
        <p className="mt-1 text-xs text-red-600/90">
          {verdictText ?? 'The constitutional gate declined this action when it was approved.'}
        </p>
      </div>
    )
  }

  // ── Proposed (interactive) ────────────────────────────────────────────────
  // Decided outcome takes over the card once a decision returns.
  if (phase === 'done' && decision) {
    // "Dismissed" is reserved for a deliberate human reject (or a backend
    // `rejected` with no error). A `refused` carrying an error_code is a
    // constitutional refusal and must surface as the red error card below.
    const userDismissed =
      (rejected || decision.status === 'rejected') && decision.error_code === null
    if (userDismissed) {
      return (
        <div
          data-testid="proposed-action-card"
          data-status="dismissed"
          className="mt-2 rounded-xl border border-border/60 bg-muted/40 p-3 text-sm text-muted-foreground"
        >
          <div className="flex items-center gap-2 font-medium">
            <XCircle className="h-4 w-4 shrink-0" />
            Dismissed
          </div>
          <p className="mt-1">{action.title}</p>
        </div>
      )
    }
    // Executed: success → green, error_code set → red.
    const failed = !decision.success || decision.error_code !== null
    if (failed) {
      const reason = verdictReason(decision.verdict) ?? resultSummary(decision.result)
      return (
        <div
          data-testid="proposed-action-card"
          data-status="error"
          className="mt-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm"
        >
          <div className="flex items-center gap-2 font-medium text-red-600">
            <XCircle className="h-4 w-4 shrink-0" />
            Failed
            {decision.error_code && (
              <code className="rounded bg-red-500/15 px-1.5 py-0.5 text-xs">
                {decision.error_code}
              </code>
            )}
          </div>
          <p className="mt-1 font-medium">{action.title}</p>
          {reason && <p className="mt-1 text-xs text-red-600/90">{reason}</p>}
        </div>
      )
    }
    const summary = resultSummary(decision.result) ?? verdictReason(decision.verdict)
    return (
      <div
        data-testid="proposed-action-card"
        data-status="executed"
        className="mt-2 rounded-xl border border-green-500/30 bg-green-500/10 p-3 text-sm"
      >
        <div className="flex items-center gap-2 font-medium text-green-600">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          Executed
        </div>
        <p className="mt-1 font-medium">{action.title}</p>
        {summary && <p className="mt-1 text-xs text-muted-foreground">{summary}</p>}
      </div>
    )
  }

  const deciding = phase === 'deciding'

  return (
    <div
      data-testid="proposed-action-card"
      data-status="proposed"
      className="mt-2 rounded-xl border border-primary/30 bg-primary/5 p-3 text-sm shadow-sm"
    >
      <div className="flex items-center gap-2 font-medium text-primary">
        <ShieldCheck className="h-4 w-4 shrink-0" />
        Proposed remediation
        <span className="ml-auto rounded-full border border-border/60 bg-card/60 px-2 py-0.5 text-[11px] font-normal text-muted-foreground">
          {action.target}
        </span>
      </div>

      <p className="mt-2 font-semibold">{action.title}</p>
      <p className="mt-1 text-muted-foreground">{action.rationale}</p>

      <div className="mt-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{action.tool_name}</span>
        {' · '}
        {action.parameters.service_name}
        {action.parameters.target_replicas !== undefined &&
          ` · ${action.parameters.target_replicas} replica${action.parameters.target_replicas === 1 ? '' : 's'}`}
      </div>

      {verdictText && (
        <p className="mt-2 rounded-lg bg-muted/50 px-2.5 py-1.5 text-xs text-muted-foreground">
          {verdictText}
        </p>
      )}

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

      <div className="mt-3 flex items-center gap-2">
        <button
          type="button"
          data-testid="proposed-action-approve"
          onClick={() => void decide(true)}
          disabled={deciding}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {deciding ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
          Approve
        </button>
        <button
          type="button"
          data-testid="proposed-action-reject"
          onClick={() => void decide(false)}
          disabled={deciding}
          className="flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted/80 disabled:opacity-50"
        >
          <XCircle className="h-4 w-4" />
          Reject
        </button>
      </div>
    </div>
  )
}
