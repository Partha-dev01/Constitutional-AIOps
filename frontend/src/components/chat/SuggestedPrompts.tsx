interface SuggestedPromptsProps {
  prompts: string[]
  /** Fills the input with the chosen prompt — does NOT submit. */
  onPick: (prompt: string) => void
  title?: string
  /** Compact single-column layout for the narrow embedded (cockpit) chat pane. */
  dense?: boolean
}

/**
 * Empty-state suggested-prompt chips, styled to match the landing FeatureGrid
 * cards. Picking a chip fills the input (the parent decides what to do); chips
 * are deliberately `type="button"` so they never satisfy the form's submit
 * selector used by the live e2e test.
 */
export function SuggestedPrompts({ prompts, onPick, title, dense = false }: SuggestedPromptsProps) {
  if (prompts.length === 0) return null

  // The embedded cockpit pane is narrow — show fewer chips in a single column
  // so the prompt text never wraps into a cramped 2×N grid.
  const shown = dense ? prompts.slice(0, 3) : prompts

  return (
    <div className={dense ? 'mx-auto w-full max-w-sm text-center' : 'mx-auto max-w-2xl text-center'}>
      <h2 className={dense ? 'text-base font-semibold' : 'text-lg font-semibold'}>
        {title ?? 'Common queries'}
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Pick a prompt to get started, or type your own question below.
      </p>

      <div className={dense ? 'mt-4 grid gap-2' : 'mt-5 grid gap-3 sm:grid-cols-2'}>
        {shown.map((prompt, i) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onPick(prompt)}
            style={{ animationDelay: `${i * 60}ms` }}
            className="chip-in group flex items-center gap-2 rounded-xl border border-border/60 bg-card/70 p-3 text-left text-sm transition-colors hover:border-primary/50"
          >
            <span className="text-foreground">{prompt}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
