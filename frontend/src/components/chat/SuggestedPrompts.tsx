import { Sparkles } from 'lucide-react'

interface SuggestedPromptsProps {
  prompts: string[]
  /** Fills the input with the chosen prompt — does NOT submit. */
  onPick: (prompt: string) => void
  title?: string
}

/**
 * Empty-state suggested-prompt chips, styled to match the landing FeatureGrid
 * cards. Picking a chip fills the input (the parent decides what to do); chips
 * are deliberately `type="button"` so they never satisfy the form's submit
 * selector used by the live e2e test.
 */
export function SuggestedPrompts({ prompts, onPick, title }: SuggestedPromptsProps) {
  if (prompts.length === 0) return null

  return (
    <div className="mx-auto max-w-2xl text-center">
      <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
        <Sparkles className="h-6 w-6" />
      </div>
      <h2 className="text-lg font-semibold">{title ?? 'Try asking about'}</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Pick a prompt to get started, or type your own question below.
      </p>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {prompts.map((prompt, i) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onPick(prompt)}
            style={{ animationDelay: `${i * 60}ms` }}
            className="chip-in group flex items-center gap-2 rounded-lg border border-border bg-card p-3 text-left text-sm transition-all hover:-translate-y-0.5 hover:border-primary/50"
          >
            <Sparkles className="h-4 w-4 shrink-0 text-primary/70 transition-colors group-hover:text-primary" />
            <span className="text-foreground">{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
