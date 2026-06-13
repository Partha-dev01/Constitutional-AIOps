import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ArrowUpRight, Loader2, Send, Sparkles, X } from 'lucide-react'
import api from '../../lib/api'
import { SelectedItem, buildSchemaChatContext } from './types'

interface PanelMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  isError?: boolean
}

const QUICK_QUESTIONS = [
  'Diagnose the selected services',
  'Any incidents in the last 7 days?',
  'How do these services connect?',
]

interface AskAiPanelProps {
  selection: SelectedItem[]
  onRemoveSelection: (key: string) => void
  windowHours: number
  /** Cap so the panel matches the canvas+scrubber and the list scrolls. */
  maxHeight: number
}

/**
 * Docked Ask-AI panel: removable selection chips, canned quick questions, a
 * compact markdown message list and a "Continue in Chat" hand-off once a
 * conversation exists. Sends the frozen schema-graph context payload with
 * every message.
 */
export function AskAiPanel({ selection, onRemoveSelection, windowHours, maxHeight }: AskAiPanelProps) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<PanelMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Keep the compact list pinned to the latest message.
  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, loading])

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || loading) return

      setMessages((prev) => [
        ...prev,
        { id: `u-${Date.now()}`, role: 'user', content: trimmed },
      ])
      setInput('')
      setLoading(true)
      try {
        const context =
          selection.length > 0 ? buildSchemaChatContext(selection, windowHours) : undefined
        const response = await api.chat.send({
          message: trimmed,
          conversation_id: conversationId ?? undefined,
          context,
        })
        if (response.conversation_id) setConversationId(response.conversation_id)
        setMessages((prev) => [
          ...prev,
          { id: `a-${Date.now()}`, role: 'assistant', content: response.message.content },
        ])
      } catch (err) {
        const detail = err instanceof Error ? err.message : 'Request failed'
        setMessages((prev) => [
          ...prev,
          {
            id: `e-${Date.now()}`,
            role: 'assistant',
            content: `Could not reach the assistant: ${detail}`,
            isError: true,
          },
        ])
      } finally {
        setLoading(false)
      }
    },
    [loading, selection, windowHours, conversationId],
  )

  return (
    <div
      className="flex w-full shrink-0 flex-col overflow-hidden rounded-lg border border-slate-700/60 bg-gradient-to-b from-slate-900/85 to-slate-950/70 ring-1 ring-inset ring-white/5 lg:w-80"
      style={{ maxHeight }}
      data-testid="askai-panel"
    >
      <div className="flex items-center justify-between border-b border-slate-800 bg-gradient-to-r from-primary/10 to-transparent px-3 py-2.5">
        <h4 className="flex items-center gap-1.5 text-sm font-semibold text-slate-200">
          <Sparkles className="h-4 w-4 text-blue-400 drop-shadow-[0_0_6px_hsl(var(--primary)/0.7)]" />
          Ask AI
        </h4>
        {conversationId && (
          <button
            type="button"
            data-testid="askai-continue"
            onClick={() => navigate(`/chat?conversation=${conversationId}`)}
            className="flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800/80 px-2 py-1 text-xs text-slate-300 hover:bg-slate-700"
          >
            Continue in Chat
            <ArrowUpRight className="h-3 w-3" />
          </button>
        )}
      </div>

      {/* Selection chips. */}
      <div className="border-b border-slate-800 px-3 py-2">
        {selection.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {selection.map((item) => (
              <span
                key={item.key}
                data-testid={`askai-chip-${item.key}`}
                className="schema-chip inline-flex max-w-full items-center gap-1 rounded-full border border-blue-500/40 bg-blue-500/10 py-0.5 pl-2 pr-1 text-xs text-blue-300"
              >
                <span className="truncate">
                  {item.type === 'node'
                    ? item.node.label
                    : `${item.edge.source} → ${item.edge.target}`}
                </span>
                <button
                  type="button"
                  onClick={() => onRemoveSelection(item.key)}
                  aria-label={`Remove ${item.type === 'node' ? item.node.label : item.edge.id} from selection`}
                  className="rounded-full p-0.5 text-blue-300/80 hover:bg-blue-500/20 hover:text-blue-200"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-[11px] leading-snug text-slate-500">
            Click a service to inspect it, then <span className="text-slate-400">Add to Ask AI</span> —
            or Ctrl-click services and links — to add them here as context for the assistant.
          </p>
        )}
      </div>

      {/* Compact message list. */}
      <div ref={listRef} className="min-h-0 flex-1 space-y-2 overflow-y-auto px-3 py-2">
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center gap-2 px-4 text-center">
            <div className="rounded-full border border-primary/20 bg-primary/10 p-2.5">
              <Sparkles className="h-5 w-5 text-blue-400/80" />
            </div>
            <p className="max-w-[200px] text-xs leading-relaxed text-slate-500">
              Ask about the architecture, health or recent episodes.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`overflow-hidden rounded-2xl px-3 py-2 text-xs leading-relaxed [overflow-wrap:anywhere] ${
              m.role === 'user'
                ? 'ml-6 rounded-br-md bg-gradient-to-br from-primary to-primary/85 text-primary-foreground shadow-sm'
                : m.isError
                  ? 'mr-2 rounded-tl-md border border-red-500/30 bg-red-500/10 text-red-300'
                  : 'mr-2 rounded-tl-md border border-slate-700/60 bg-slate-800/70 text-slate-300'
            }`}
          >
            {m.role === 'assistant' && !m.isError ? (
              <div className="prose prose-invert max-w-none break-words text-xs prose-p:my-1 prose-pre:overflow-x-auto prose-pre:whitespace-pre-wrap prose-li:my-0">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
              </div>
            ) : (
              m.content
            )}
          </div>
        ))}
        {loading && (
          <div className="mr-2 flex items-center gap-2 rounded-2xl rounded-tl-md border border-slate-700/60 bg-slate-800/70 px-3 py-2 text-xs text-slate-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span className="thinking-shimmer">Analyzing selection…</span>
          </div>
        )}
      </div>

      {/* Quick questions. */}
      <div className="flex flex-wrap gap-1.5 px-3 pb-2">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => {
              setInput(q)
              inputRef.current?.focus()
            }}
            className="rounded-full border border-slate-700 bg-slate-800/60 px-2 py-0.5 text-[11px] text-slate-400 hover:border-blue-500/50 hover:text-slate-200"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input row — a /chat-style glass composer. Kept as a div (not a <form>)
          so the schema graph keeps a single <select> and one submit surface. */}
      <div className="composer-glow m-2.5 flex items-center gap-2 rounded-2xl border border-slate-700/60 bg-slate-900/70 p-1.5 pl-3.5 shadow-sm backdrop-blur-sm">
        <input
          ref={inputRef}
          data-testid="askai-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void send(input)
          }}
          placeholder="Ask about your selection..."
          className="h-9 min-w-0 flex-1 border-0 bg-transparent text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none"
        />
        <button
          type="button"
          data-testid="askai-send"
          onClick={() => void send(input)}
          disabled={loading || !input.trim()}
          aria-label="Send to assistant"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80 text-primary-foreground shadow-md transition-all hover:scale-105 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </div>
    </div>
  )
}
