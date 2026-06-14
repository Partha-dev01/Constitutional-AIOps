import { useEffect, useRef, useState } from 'react'
import { Send, Loader2, Wrench } from 'lucide-react'
import type { FormEvent, RefObject } from 'react'

interface ChatComposerProps {
  input: string
  onChange: (value: string) => void
  onSubmit: (e: FormEvent) => void
  isLoading: boolean
  inputRef: RefObject<HTMLInputElement>
  placeholder: string
}

/** A single MCP tool as returned by GET /api/v1/tools/ (only the bits we use). */
interface McpTool {
  name: string
  description?: string
}

/**
 * Glass composer bar at the bottom of the Chat page. Purely presentational for
 * the input itself — the value, submit handler and loading flag all live in
 * ChatPane and are passed through unchanged.
 *
 * The composer also hosts a small, unobtrusive "Tools" affordance: a popover
 * listing the available MCP tools. Picking one does NOT execute it (the backend
 * auto-runs tools during a chat turn) — it just nudges the model by inserting a
 * natural-language hint into the input via `onChange`.
 *
 * Contract notes: the input keeps the exact placeholder the live e2e test
 * looks up, and the Send button is the ONLY type="submit" button on the page.
 * While a request is in flight the same submit button shows a spinner and is
 * disabled (it never changes type). The Tools button is type="button" so it
 * never satisfies the submit selector.
 */
export function ChatComposer({
  input,
  onChange,
  onSubmit,
  isLoading,
  inputRef,
  placeholder,
}: ChatComposerProps) {
  const [toolsOpen, setToolsOpen] = useState(false)
  const [tools, setTools] = useState<McpTool[]>([])
  const [toolsLoaded, setToolsLoaded] = useState(false)
  const [toolsLoading, setToolsLoading] = useState(false)
  const [toolsError, setToolsError] = useState(false)
  const toolsWrapRef = useRef<HTMLDivElement>(null)

  // Lazily fetch the MCP tool list on first open and cache it for the session.
  useEffect(() => {
    if (!toolsOpen || toolsLoaded || toolsLoading) return
    let cancelled = false
    setToolsLoading(true)
    setToolsError(false)
    fetch('/api/v1/tools/', { credentials: 'same-origin' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data: { tools?: McpTool[] }) => {
        if (cancelled) return
        setTools(Array.isArray(data.tools) ? data.tools : [])
        setToolsLoaded(true)
      })
      .catch(() => {
        if (!cancelled) setToolsError(true)
      })
      .finally(() => {
        if (!cancelled) setToolsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [toolsOpen, toolsLoaded, toolsLoading])

  // Close the popover on outside click or Escape.
  useEffect(() => {
    if (!toolsOpen) return
    const onPointerDown = (event: MouseEvent) => {
      if (!toolsWrapRef.current?.contains(event.target as Node)) setToolsOpen(false)
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setToolsOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [toolsOpen])

  // Insert a graceful natural-language hint so the user can finish the sentence.
  const handlePickTool = (tool: McpTool) => {
    const prefix = input.trim() ? `${input.trim()} ` : ''
    onChange(`${prefix}Use the ${tool.name} tool to `)
    setToolsOpen(false)
    inputRef.current?.focus()
  }

  return (
    <form
      onSubmit={onSubmit}
      className="composer-glow mt-4 flex items-center gap-2 rounded-2xl border border-border/60 bg-card/80 p-2 pl-3 shadow-sm backdrop-blur-sm"
    >
      <div ref={toolsWrapRef} className="relative shrink-0">
        <button
          type="button"
          onClick={() => setToolsOpen((open) => !open)}
          className="flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
          aria-label="Insert an MCP tool hint"
          aria-haspopup="menu"
          aria-expanded={toolsOpen}
          disabled={isLoading}
        >
          <Wrench className="h-5 w-5" />
        </button>

        {toolsOpen && (
          <div
            role="menu"
            aria-label="Available tools"
            className="absolute bottom-full left-0 z-20 mb-2 max-h-72 w-72 overflow-y-auto rounded-xl border border-border/60 bg-card/95 p-1 shadow-lg backdrop-blur-sm"
          >
            <p className="px-2 py-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Available tools
            </p>
            {toolsLoading && (
              <div className="flex items-center gap-2 px-2 py-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading tools…
              </div>
            )}
            {!toolsLoading && toolsError && (
              <p className="px-2 py-2 text-sm text-muted-foreground">
                Couldn’t load tools.
              </p>
            )}
            {!toolsLoading && !toolsError && toolsLoaded && tools.length === 0 && (
              <p className="px-2 py-2 text-sm text-muted-foreground">No tools available.</p>
            )}
            {!toolsLoading &&
              !toolsError &&
              tools.map((tool) => (
                <button
                  key={tool.name}
                  type="button"
                  role="menuitem"
                  onClick={() => handlePickTool(tool)}
                  className="flex w-full flex-col items-start gap-0.5 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-muted"
                >
                  <span className="text-sm font-medium text-foreground">{tool.name}</span>
                  {tool.description && (
                    <span className="line-clamp-2 text-xs text-muted-foreground">
                      {tool.description}
                    </span>
                  )}
                </button>
              ))}
          </div>
        )}
      </div>

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
