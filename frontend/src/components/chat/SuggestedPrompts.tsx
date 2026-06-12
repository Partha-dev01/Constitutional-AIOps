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
      <div className="float-slow mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 via-primary/10 to-transparent text-primary shadow-[0_8px_30px_-6px_hsl(var(--primary)/0.35)]">
        <Sparkles className="h-7 w-7" />
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
            className="chip-in group flex items-center gap-2 rounded-xl border border-border/60 bg-card/70 p-3 text-left text-sm transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-[0_4px_20px_-4px_hsl(var(--primary)/0.3)]"
          >
            <Sparkles className="h-4 w-4 shrink-0 text-primary/70 transition-colors group-hover:text-primary" />
            <span className="text-foreground">{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
