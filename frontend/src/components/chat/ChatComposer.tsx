import { Send, Loader2 } from 'lucide-react'
import type { FormEvent, RefObject } from 'react'

interface ChatComposerProps {
  input: string
  onChange: (value: string) => void
  onSubmit: (e: FormEvent) => void
  isLoading: boolean
  inputRef: RefObject<HTMLInputElement>
  placeholder: string
}

/**
 * Glass composer bar at the bottom of the Chat page. Purely presentational —
 * the input value, submit handler and loading flag all live in Chat.tsx and
 * are passed through unchanged.
 *
 * Contract notes: the input keeps the exact placeholder the live e2e test
 * looks up, and the Send button is the ONLY type="submit" button on the page.
 * While a request is in flight the same submit button shows a spinner and is
 * disabled (it never changes type).
 */
export function ChatComposer({
  input,
  onChange,
  onSubmit,
  isLoading,
  inputRef,
  placeholder,
}: ChatComposerProps) {
  return (
    <form
      onSubmit={onSubmit}
      className="composer-glow mt-4 flex items-center gap-2 rounded-2xl border border-border/60 bg-card/80 p-2 pl-4 shadow-sm backdrop-blur-sm"
    >
      <input
        ref={inputRef}
        type="text"
        value={input}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-10 min-w-0 flex-1 border-0 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none disabled:opacity-60"
        disabled={isLoading}
      />
      <button
        type="submit"
        disabled={isLoading || !input.trim()}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-md transition-all hover:scale-105 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
        aria-label="Send message"
      >
        {isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <Send className="h-5 w-5" />
        )}
      </button>
    </form>
  )
}
