import { useState, useCallback } from 'react'
import { Sparkles, Loader2, CheckCircle2, XCircle, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import { JsonView } from '../JsonView'
import type { ToolStep } from '../../hooks/useToolSteps'

interface ToolCallTimelineProps {
  steps: ToolStep[]
  /** Optional text shown verbatim when prefers-reduced-motion (kept simple). */
  reducedMotionFallbackText?: string
}

/**
 * Presentational vertical timeline of derived tool-call steps, shown while a
 * chat request is in flight. Header always renders the literal "Thinking..."
 * label while any step is not yet done (relied on by the live e2e test).
 *
 * Each step has an expandable detail dropdown (button type="button") that
 * shows the service/store/query and — once the response arrives — the
 * concrete result for that step.
 */
export function ToolCallTimeline({ steps, reducedMotionFallbackText }: ToolCallTimelineProps) {
  const anyError = steps.some((s) => s.status === 'error')
  // "Thinking..." should show ONLY while work is genuinely in flight, i.e. some
  // step is still pending/running and nothing has errored. (Relied on by the
  // live e2e test, which expects "Thinking..." while a response loads.)
  const anyRunning =
    !anyError && steps.some((s) => s.status === 'pending' || s.status === 'running')
  // Track which step ids are expanded.
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const toggle = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  return (
    <div className="flex gap-3" aria-live="polite">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary shadow-sm">
        <Sparkles className="h-4 w-4" />
      </div>
      <div
        className={cn(
          'min-w-[220px] max-w-[70%] flex-1 rounded-xl border bg-gradient-to-br from-muted/40 via-muted/20 to-transparent p-3 backdrop-blur-[2px]',
          anyRunning ? 'timeline-active border-primary/30' : 'border-border/50',
        )}
      >
        <div className="flex items-center gap-2 text-sm font-medium">
          {anyError ? (
            <XCircle className="h-4 w-4 text-red-500" />
          ) : (
            <Sparkles className="h-4 w-4 text-primary" />
          )}
          {anyRunning ? (
            <span className="thinking-shimmer">Thinking...</span>
          ) : anyError ? (
            <span className="text-red-600 dark:text-red-400">Request failed</span>
          ) : (
            <span>Done</span>
          )}
        </div>

        {reducedMotionFallbackText && (
          <p className="sr-only">{reducedMotionFallbackText}</p>
        )}

        <ol className="mt-3 space-y-0">
          {steps.map((step, i) => {
            const Icon = step.icon
            const isLast = i === steps.length - 1
            const lineActive = step.status === 'done' || step.status === 'running'
            const isExpanded = expanded.has(step.id)
            const { detail } = step

            return (
              <li key={step.id} className="relative flex gap-3 pb-3 last:pb-0">
                {/* Connector line to the next node. */}
                {!isLast && (
                  <span
                    aria-hidden
                    className={cn(
                      'absolute left-[11px] top-6 bottom-0 w-px',
                      lineActive ? 'bg-primary/40 tool-line' : 'bg-border',
                    )}
                  />
                )}

                {/* Node marker. */}
                <span className="relative z-10 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center">
                  {step.status === 'done' ? (
                    <span className="relative flex h-5 w-5 items-center justify-center">
                      {/* One-shot expanding ring behind the check. */}
                      <span aria-hidden className="check-ripple" />
                      <CheckCircle2 className="h-5 w-5 text-green-500 tool-check" />
                    </span>
                  ) : step.status === 'error' ? (
                    <XCircle className="h-5 w-5 text-red-500" />
                  ) : step.status === 'running' ? (
                    <span className="flex h-5 w-5 items-center justify-center">
                      <span className="absolute h-2.5 w-2.5 rounded-full bg-primary tool-node-running" />
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </span>
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40" />
                  )}
                </span>

                {/* Label row + expand toggle. */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <span
                      className={cn(
                        'flex items-center gap-1.5 text-sm leading-6',
                        step.status === 'done'
                          ? 'text-foreground'
                          : step.status === 'error'
                            ? 'text-red-600 dark:text-red-400 font-medium'
                            : step.status === 'running'
                              ? 'text-foreground font-medium'
                              : 'text-muted-foreground',
                      )}
                    >
                      <Icon className="h-3.5 w-3.5 opacity-70" />
                      {step.label}
                    </span>

                    {/* Expand/collapse toggle — must be type="button" (contract). */}
                    <button
                      type="button"
                      aria-expanded={isExpanded}
                      aria-label={`${isExpanded ? 'Collapse' : 'Expand'} detail for ${step.label}`}
                      onClick={() => toggle(step.id)}
                      className={cn(
                        'ml-1 rounded p-0.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors',
                        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                      )}
                      data-testid={`step-toggle-${step.id}`}
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-3.5 w-3.5" aria-hidden />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5" aria-hidden />
                      )}
                    </button>
                  </div>

                  {/* At-a-glance result summary (visible without expanding). */}
                  {detail.summary && (
                    <p
                      className="text-xs text-muted-foreground/90 leading-5 truncate"
                      data-testid={`step-summary-${step.id}`}
                      title={detail.summary}
                    >
                      {detail.summary}
                    </p>
                  )}

                  {/* Collapsible detail region. */}
                  {isExpanded && (
                    <div
                      className="mt-1.5 rounded-lg border border-border/50 bg-background/60 p-2 text-xs space-y-1.5 backdrop-blur"
                      data-testid={`step-detail-${step.id}`}
                    >
                      {/* Static fields — always available immediately. */}
                      <div className="space-y-0.5">
                        {detail.service && (
                          <p className="text-muted-foreground">
                            <span className="font-medium text-foreground">Service:</span>{' '}
                            {detail.service}
                          </p>
                        )}
                        <p className="text-muted-foreground">
                          <span className="font-medium text-foreground">Store:</span>{' '}
                          {detail.store}
                        </p>
                        <p className="text-muted-foreground">
                          <span className="font-medium text-foreground">Query:</span>{' '}
                          {detail.query}
                        </p>
                      </div>

                      {/* Dynamic result — available after response arrives. */}
                      {detail.result !== null ? (
                        <div>
                          <p className="font-medium text-foreground mb-1">Result:</p>
                          <JsonView raw={detail.result} />
                        </div>
                      ) : step.status === 'error' ? (
                        <p className="text-red-600 dark:text-red-400 italic">
                          This step did not complete — the request failed or timed out.
                        </p>
                      ) : (
                        <p className="text-muted-foreground italic">Waiting for response…</p>
                      )}
                    </div>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      </div>
    </div>
  )
}
