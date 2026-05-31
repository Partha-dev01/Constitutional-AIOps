import { Lightbulb, History, Gauge } from 'lucide-react'
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
}

/** Confidence-band color: >=0.90 green, 0.70-0.90 yellow, <0.70 red. */
function confidenceTone(confidence: number): { bar: string; text: string; label: string } {
  if (confidence >= 0.9) {
    return { bar: 'bg-green-500', text: 'text-green-600 dark:text-green-400', label: 'High' }
  }
  if (confidence >= 0.7) {
    return { bar: 'bg-yellow-500', text: 'text-yellow-600 dark:text-yellow-400', label: 'Moderate' }
  }
  return { bar: 'bg-red-500', text: 'text-red-600 dark:text-red-400', label: 'Low' }
}

/**
 * Display-only insight cards rendered beneath an assistant message. Each card
 * renders only when its data is present, so off-domain / empty responses
 * produce no output at all. Deliberately does NOT use the `prose` class (that
 * is reserved for assistant message bodies, per the e2e contract).
 */
export function InsightCards({ insights }: InsightCardsProps) {
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
        <div className="rounded-lg border border-border bg-muted/30 p-3">
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
              className={cn('h-full rounded-full transition-all', tone.bar)}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {hasActions && (
        <div className="rounded-lg border border-border bg-muted/30 p-3">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <Lightbulb className="h-3.5 w-3.5" />
            Suggested actions
          </div>
          <ul className="space-y-1">
            {(suggestedActions as string[]).map((action, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="text-primary">•</span>
                <span className="[&_strong]:font-semibold [&_code]:rounded [&_code]:bg-muted [&_code]:px-1">
                  <InlineMarkdown>{action}</InlineMarkdown>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasIncidents && (
        <div className="rounded-lg border border-border bg-muted/30 p-3">
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
