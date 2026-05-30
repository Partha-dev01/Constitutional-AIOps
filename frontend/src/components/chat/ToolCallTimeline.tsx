import { Sparkles, Loader2, CheckCircle2 } from 'lucide-react'
import { cn } from '../../lib/utils'
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
 */
export function ToolCallTimeline({ steps, reducedMotionFallbackText }: ToolCallTimelineProps) {
  const anyRunning = steps.some((s) => s.status !== 'done')

  return (
    <div className="flex gap-3" aria-live="polite">
      <div className="w-8 h-8 rounded-full flex items-center justify-center bg-primary/10 text-primary shrink-0">
        <Sparkles className="h-4 w-4" />
      </div>
      <div className="flex-1 rounded-lg border border-border bg-muted/30 p-3 min-w-[220px] max-w-[70%]">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Sparkles className="h-4 w-4 text-primary" />
          {anyRunning ? <span>Thinking...</span> : <span>Done</span>}
        </div>

        {reducedMotionFallbackText && (
          <p className="sr-only">{reducedMotionFallbackText}</p>
        )}

        <ol className="mt-3 space-y-0">
          {steps.map((step, i) => {
            const Icon = step.icon
            const isLast = i === steps.length - 1
            const lineActive = step.status === 'done' || step.status === 'running'
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
                    <CheckCircle2 className="h-5 w-5 text-green-500 tool-check" />
                  ) : step.status === 'running' ? (
                    <span className="flex h-5 w-5 items-center justify-center">
                      <span className="absolute h-2.5 w-2.5 rounded-full bg-primary tool-node-running" />
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </span>
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-muted-foreground/40" />
                  )}
                </span>

                <span
                  className={cn(
                    'flex items-center gap-1.5 text-sm leading-6',
                    step.status === 'done'
                      ? 'text-foreground'
                      : step.status === 'running'
                        ? 'text-foreground font-medium'
                        : 'text-muted-foreground',
                  )}
                >
                  <Icon className="h-3.5 w-3.5 opacity-70" />
                  {step.label}
                </span>
              </li>
            )
          })}
        </ol>
      </div>
    </div>
  )
}
