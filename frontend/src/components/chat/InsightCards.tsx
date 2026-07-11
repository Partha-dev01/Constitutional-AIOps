import { Lightbulb, History, Gauge, CornerDownLeft } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useReveal } from '../../hooks/useReveal'
import { cn } from '../../lib/utils'

/**
 * Render a short string as INLINE markdown (bold/italic/code) without block
 * margins, so emphasis renders properly instead of leaking raw `**` markers
 * into the card. Used for suggested actions / related incidents.
 */
function InlineMarkdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <>{children}</>,
        a: ({ children }) => <>{children}</>,
      }}
    >
      {children}
    </ReactMarkdown>
  )
}

export interface MessageInsights {
  confidence?: number | null
  suggestedActions?: string[] | null
  relatedIncidents?: string[] | null
}

interface InsightCardsProps {
  insights: MessageInsights
  /**
   * When provided, suggested-action rows become clickable and hand their text
   * (markdown markers stripped) to the host. The contract mirrors the prompt
   * chips: FILL the composer, never auto-send — the user reviews/edits first,
   * and an actionable send then flows through the normal consent pipeline.
   */
  onUseAction?: (action: string) => void
}

/**
 * Strip the inline markdown markers (`**bold**`, `` `code` ``) the model puts
 * in suggested actions, so the prefilled composer carries clean plain text.
 * Single `*`/`_` are left alone — they appear in identifiers like service_name.
 */
function actionPlainText(action: string): string {
  return action.replace(/\*\*|`/g, '').trim()
}

/** Confidence-band color: >=0.90 green, 0.70-0.90 yellow, <0.70 red. */
function confidenceTone(confidence: number): {
  bar: string
  text: string
  label: string
  accent: string
} {
  if (confidence >= 0.9) {
    return {
      bar: 'bg-gradient-to-r from-green-500 to-emerald-400',
      text: 'text-green-600 dark:text-green-400',
      label: 'High',
      accent: 'border-l-green-500/60 bg-green-500/[0.04]',
    }
  }
  if (confidence >= 0.7) {
    return {
      bar: 'bg-gradient-to-r from-yellow-500 to-amber-400',
      text: 'text-yellow-600 dark:text-yellow-400',
      label: 'Moderate',
      accent: 'border-l-yellow-500/60 bg-yellow-500/[0.04]',
    }
  }
  return {
    bar: 'bg-gradient-to-r from-red-500 to-rose-400',
    text: 'text-red-600 dark:text-red-400',
    label: 'Low',
    accent: 'border-l-red-500/60 bg-red-500/[0.04]',
  }
}

/**
 * Insight cards rendered beneath an assistant message. Each card renders only
 * when its data is present, so off-domain / empty responses produce no output
 * at all. Suggested-action rows are interactive when the host passes
 * `onUseAction` (fill-the-composer; see the prop doc). Deliberately does NOT
 * use the `prose` class (that is reserved for assistant message bodies, per
 * the e2e contract).
 */
export function InsightCards({ insights, onUseAction }: InsightCardsProps) {
  const { ref, visible } = useReveal<HTMLDivElement>()
  const { confidence, suggestedActions, relatedIncidents } = insights

  const hasConfidence = typeof confidence === 'number' && Number.isFinite(confidence)
  const hasActions = Array.isArray(suggestedActions) && suggestedActions.length > 0
  const hasIncidents = Array.isArray(relatedIncidents) && relatedIncidents.length > 0

  if (!hasConfidence && !hasActions && !hasIncidents) return null

  const tone = hasConfidence ? confidenceTone(confidence as number) : null
  const pct = hasConfidence ? Math.round((confidence as number) * 100) : 0

  return (
    <div
      ref={ref}
      className={cn('reveal mt-2 space-y-2', visible && 'reveal-visible')}
    >
      {hasConfidence && tone && (
        <div className={cn('rounded-lg border border-border/60 border-l-2 p-3', tone.accent)}>
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 font-medium text-muted-foreground">
              <Gauge className="h-3.5 w-3.5" />
              Confidence
            </span>
            <span className={cn('font-semibold', tone.text)}>
              {pct}% · {tone.label}
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
            <div
              className={cn('bar-grow h-full rounded-full', tone.bar)}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {hasActions && (
        <div className="rounded-lg border border-border/60 border-l-2 border-l-primary/60 bg-primary/[0.04] p-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Lightbulb className="h-3.5 w-3.5" />
            Suggested actions
          </div>
          <ul className="space-y-1">
            {(suggestedActions as string[]).map((action, i) => (
              <li key={i}>
                {onUseAction ? (
                  <button
                    type="button"
                    data-testid="suggested-action-use"
                    onClick={() => onUseAction(actionPlainText(action))}
                    aria-label={`Use suggested action: ${actionPlainText(action)}`}
                    className="group/action -mx-1.5 flex w-[calc(100%+0.75rem)] items-start gap-2 rounded-md px-1.5 py-1 text-left text-sm text-foreground transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
                  >
                    <span className="text-primary">•</span>
                    <span className="min-w-0 flex-1 [&_strong]:font-semibold [&_code]:rounded [&_code]:bg-muted [&_code]:px-1">
                      <InlineMarkdown>{action}</InlineMarkdown>
                    </span>
                    <span className="flex shrink-0 items-center gap-1 self-center text-[11px] font-medium text-muted-foreground transition-colors group-hover/action:text-primary">
                      <CornerDownLeft className="h-3 w-3" />
                      Use
                    </span>
                  </button>
                ) : (
                  <div className="flex gap-2 text-sm text-foreground">
                    <span className="text-primary">•</span>
                    <span className="[&_strong]:font-semibold [&_code]:rounded [&_code]:bg-muted [&_code]:px-1">
                      <InlineMarkdown>{action}</InlineMarkdown>
                    </span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasIncidents && (
        <div className="rounded-lg border border-border/60 border-l-2 border-l-amber-500/60 bg-amber-500/[0.04] p-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <History className="h-3.5 w-3.5" />
            Related incidents
          </div>
          <ul className="space-y-1">
            {(relatedIncidents as string[]).map((incident, i) => (
              <li key={i} className="text-sm text-muted-foreground">
                {incident}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
