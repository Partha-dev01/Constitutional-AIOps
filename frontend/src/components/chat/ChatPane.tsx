import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AlertCircle, PanelLeftOpen, Plus, Sparkles } from 'lucide-react'
import api from '../../lib/api'
import { ChatComposer } from './ChatComposer'
import { ChatMessage } from './ChatMessage'
import type { ChatMessageData } from './ChatMessage'
import type { MessageInsights } from './InsightCards'
import type { ProposedAction } from '../../lib/api'
import { ConversationSidebar } from './ConversationSidebar'
import { SuggestedPrompts } from './SuggestedPrompts'
import { ToolCallTimeline } from './ToolCallTimeline'
import { deriveToolSteps, enrichToolStepsWithResponse } from '../../hooks/useToolSteps'
import type { ToolStep } from '../../hooks/useToolSteps'
import { useConversationHistory } from '../../hooks/useConversationHistory'
import { selectPrompts, pushRecentPrompt, getRecentPrompts } from '../../lib/suggestedPrompts'
import { prefersReducedMotion } from '../../lib/utils'

const PLACEHOLDER = 'Ask about incidents, metrics, or request analysis...'

const WELCOME = "Hello! I'm the Constitutional AIOps assistant. I can help you with infrastructure analysis, incident investigation, and system management. How can I help you today?"

/** How long each derived tool step "runs" before completing (ms). */
const STEP_DURATION_MS = 650

function welcomeMessage(): ChatMessageData {
  return { id: 'welcome', role: 'assistant', content: WELCOME, timestamp: new Date() }
}

export interface ChatPaneProps {
  /**
   * `page` (default) renders the full /chat experience — heading, conversation
   * history sidebar and the ?ask / ?conversation hand-off params — with a DOM
   * the e2e contracts depend on. `embedded` is the slim cockpit variant: no
   * sidebar, a compact header, height-filling, and it attaches a `seedContext`
   * to every send (e.g. the graph selection) for at-a-glance tool context.
   */
  variant?: 'page' | 'embedded'
  /** Embedded only: ride-along context attached to every chat send. */
  seedContext?: Record<string, unknown>
  /** Embedded only: when `key` changes, `text` prefills the composer (never auto-sends). */
  injectedPrompt?: { text: string; key: number }
  /** Embedded only: extra classes on the root (height control). */
  className?: string
}

/**
 * The chat conversation surface, shared by the full /chat page and the Console
 * cockpit. All send / typewriter / tool-step animation state lives here so the
 * two variants never diverge.
 */
export function ChatPane({ variant = 'page', seedContext, injectedPrompt, className = '' }: ChatPaneProps) {
  const embedded = variant === 'embedded'

  const [messages, setMessages] = useState<ChatMessageData[]>([welcomeMessage()])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null)
  const [displayedContent, setDisplayedContent] = useState('')
  const [toolSteps, setToolSteps] = useState<ToolStep[]>([])
  /** Finished, enriched tool timelines kept per assistant message id so the
   *  checkmark steps + searched-data dropdowns PERSIST after the answer (they
   *  no longer vanish when loading ends). */
  const [toolStepsById, setToolStepsById] = useState<Record<string, ToolStep[]>>({})
  const [insightsById, setInsightsById] = useState<Record<string, MessageInsights>>({})
  /** AI-proposed remediation actions keyed by assistant message id, so the
   *  approve-to-run card persists beneath its turn. */
  const [proposedById, setProposedById] = useState<Record<string, ProposedAction>>({})
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [prompts, setPrompts] = useState<string[]>(() => selectPrompts())

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const typingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const stepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  /** Mirror of the live `toolSteps` so the async send handler can read the
   *  latest step states (e.g. which had completed) when committing on finish
   *  or failure, without adding them to its dependency array. */
  const liveStepsRef = useRef<ToolStep[]>([])
  /** Latest seedContext for the async send handler (avoids stale closure). */
  const seedContextRef = useRef<Record<string, unknown> | undefined>(seedContext)
  useEffect(() => {
    seedContextRef.current = seedContext
  }, [seedContext])

  const history = useConversationHistory()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: prefersReducedMotion() ? 'auto' : 'smooth',
    })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, displayedContent, toolSteps, scrollToBottom])

  // Keep the live-steps ref in sync with state for the async send handler.
  useEffect(() => {
    liveStepsRef.current = toolSteps
  }, [toolSteps])

  // Cleanup timers on unmount.
  useEffect(() => {
    return () => {
      if (typingIntervalRef.current) clearInterval(typingIntervalRef.current)
      if (stepTimerRef.current) clearInterval(stepTimerRef.current)
    }
  }, [])

  // Typewriter effect for a freshly-arrived assistant message.
  const startTypewriter = useCallback((messageId: string, fullContent: string) => {
    if (typingIntervalRef.current) clearInterval(typingIntervalRef.current)

    // Under reduced motion, render the full answer immediately.
    if (prefersReducedMotion()) {
      setTypingMessageId(null)
      setDisplayedContent('')
      return
    }

    setTypingMessageId(messageId)
    setDisplayedContent('')
    let index = 0

    typingIntervalRef.current = setInterval(() => {
      if (index < fullContent.length) {
        const charsToAdd = Math.min(3, fullContent.length - index)
        setDisplayedContent(fullContent.slice(0, index + charsToAdd))
        index += charsToAdd
      } else {
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current)
          typingIntervalRef.current = null
        }
        setTypingMessageId(null)
      }
    }, 15)
  }, [])

  /**
   * Animate the derived tool-call checklist: each non-final step runs then
   * completes on a timer; the final "Reasoning" step stays running until the
   * real response lands (see commitToolSteps). Reduced motion snaps all but
   * the reasoning step to done immediately.
   */
  const startToolSteps = useCallback((message: string) => {
    if (stepTimerRef.current) clearInterval(stepTimerRef.current)

    const derived = deriveToolSteps(message)
    const lastIndex = derived.length - 1

    if (prefersReducedMotion()) {
      setToolSteps(
        derived.map((s, i) => ({ ...s, status: i === lastIndex ? 'running' : 'done' })),
      )
      return
    }

    // First step starts running immediately; the rest stay pending.
    setToolSteps(derived.map((s, i) => ({ ...s, status: i === 0 ? 'running' : 'pending' })))

    let running = 0
    stepTimerRef.current = setInterval(() => {
      setToolSteps((prev) => {
        if (prev.length === 0) return prev
        // Don't auto-advance past the last step — it represents the live wait
        // on the reasoning model and is resolved by commitToolSteps().
        if (running >= lastIndex) {
          if (stepTimerRef.current) {
            clearInterval(stepTimerRef.current)
            stepTimerRef.current = null
          }
          return prev
        }
        const next = prev.map((s, i) => {
          if (i === running) return { ...s, status: 'done' as const }
          if (i === running + 1) return { ...s, status: 'running' as const }
          return s
        })
        running += 1
        return next
      })
    }, STEP_DURATION_MS)
  }, [])

  /**
   * The response (or failure) for `messageId` has arrived. Stop the live
   * animation and PERSIST the finished timeline against that assistant message
   * so its checkmark steps + searched-data dropdowns stay visible in the
   * conversation (they used to vanish the instant loading ended / after 3s).
   *
   * On success: every step is marked done and enriched with the real data.
   * On failure: steps that hadn't completed are marked errored (never falsely
   * green), so the user can see WHERE it failed.
   */
  const commitToolSteps = useCallback(
    (
      messageId: string,
      outcome: 'done' | 'error',
      responseData?: Parameters<typeof enrichToolStepsWithResponse>[1],
    ) => {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current)
        stepTimerRef.current = null
      }
      const live = liveStepsRef.current
      let finished: ToolStep[]
      if (outcome === 'done') {
        const done = live.map((s) => ({ ...s, status: 'done' as const }))
        finished = responseData ? enrichToolStepsWithResponse(done, responseData) : done
      } else {
        finished = live.map((s) =>
          s.status === 'done' ? s : { ...s, status: 'error' as const },
        )
      }
      if (finished.length > 0) {
        setToolStepsById((prev) => ({ ...prev, [messageId]: finished }))
      }
      // Retire the live (ephemeral) timeline; the persisted one takes over.
      setToolSteps([])
    },
    [],
  )

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isLoading) return

      const userMessage: ChatMessageData = {
        id: Date.now().toString(),
        role: 'user',
        content: trimmed,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, userMessage])
      setInput('')
      setIsLoading(true)
      setError(null)
      startToolSteps(trimmed)

      // Persist to the recent-prompt ring (best-effort) and refresh chips.
      pushRecentPrompt(trimmed)
      setPrompts(selectPrompts(getRecentPrompts()))

      try {
        const response = await api.chat.send({
          message: trimmed,
          conversation_id: conversationId || undefined,
          context: seedContextRef.current,
        })

        if (response.conversation_id) {
          setConversationId(response.conversation_id)
        }

        const messageId = (Date.now() + 1).toString()
        const assistantMessage: ChatMessageData = {
          id: messageId,
          role: 'assistant',
          content: response.message.content,
          timestamp: new Date(response.message.timestamp || Date.now()),
        }

        setInsightsById((prev) => ({
          ...prev,
          [messageId]: {
            confidence: response.confidence,
            suggestedActions: response.suggested_actions,
            relatedIncidents: response.related_incidents,
          },
        }))

        // Stash any AI-proposed remediation against this assistant turn so the
        // approve-to-run card renders (and persists) beneath the reply.
        if (response.proposed_action) {
          const proposed = response.proposed_action
          setProposedById((prev) => ({ ...prev, [messageId]: proposed }))
        }

        commitToolSteps(messageId, 'done', {
          confidence: response.confidence,
          related_incidents: response.related_incidents,
          suggested_actions: response.suggested_actions,
          metadata: response.metadata,
        })
        setMessages((prev) => [...prev, assistantMessage])
        startTypewriter(messageId, response.message.content)

        // Reflect the new/updated conversation in the sidebar.
        void history.refresh()
      } catch (err) {
        console.error('Chat error:', err)
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
        setError(errorMessage)

        const errorMessageId = (Date.now() + 1).toString()
        commitToolSteps(errorMessageId, 'error')

        const errorAssistantMessage: ChatMessageData = {
          id: errorMessageId,
          role: 'assistant',
          content: `I'm sorry, I couldn't process your request. Error: ${errorMessage}\n\nPlease check that the backend and LLM servers are running.`,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorAssistantMessage])
      } finally {
        setIsLoading(false)
      }
    },
    [
      conversationId,
      isLoading,
      startToolSteps,
      commitToolSteps,
      startTypewriter,
      history,
    ],
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    void sendMessage(input)
  }

  // Suggested-prompt chips FILL the input (never auto-submit), then focus it.
  const handlePickPrompt = useCallback((prompt: string) => {
    setInput(prompt)
    inputRef.current?.focus()
  }, [])

  const handleNewConversation = useCallback(() => {
    setConversationId(null)
    setMessages([welcomeMessage()])
    setInsightsById({})
    setProposedById({})
    setToolSteps([])
    setToolStepsById({})
    setError(null)
    setSidebarOpen(false)
    setPrompts(selectPrompts(getRecentPrompts()))
  }, [])

  const handleSelectConversation = useCallback(
    async (id: string) => {
      setSidebarOpen(false)
      if (id === conversationId) return
      setError(null)
      setToolSteps([])
      setToolStepsById({})
      try {
        const conv = await api.chat.getConversation(id)
        const loaded: ChatMessageData[] = conv.messages
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .map((m, i) => ({
            id: `${id}-${i}`,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
          }))
        setConversationId(id)
        setInsightsById({})
        setProposedById({})
        setMessages(loaded.length > 0 ? loaded : [welcomeMessage()])
      } catch (err) {
        console.error('Failed to load conversation:', err)
        setError(err instanceof Error ? err.message : 'Failed to load conversation')
      }
    },
    [conversationId],
  )

  const handleDeleteConversation = useCallback(
    (id: string) => {
      void history.remove(id)
      if (id === conversationId) handleNewConversation()
    },
    [history, conversationId, handleNewConversation],
  )

  // Hand-off entry point (e.g. schema-graph "Continue in Chat"): when the page
  // mounts with ?conversation=<id>, load that conversation through the normal
  // selection path, then strip the param so reload/back stays clean. The ref
  // guard makes this strictly mount-once without trimming the dependency list.
  // Page variant only — the embedded cockpit never hijacks the URL.
  const [searchParams, setSearchParams] = useSearchParams()
  const handledConversationParamRef = useRef(false)
  useEffect(() => {
    if (embedded) return
    if (handledConversationParamRef.current) return
    handledConversationParamRef.current = true
    const requested = searchParams.get('conversation')
    if (!requested) return
    const next = new URLSearchParams(searchParams)
    next.delete('conversation')
    setSearchParams(next, { replace: true })
    if (requested !== conversationId) void handleSelectConversation(requested)
  }, [embedded, searchParams, setSearchParams, conversationId, handleSelectConversation])

  // Hand-off entry point: ?ask=<prompt> prefills the composer (e.g. an incident's
  // "Open in Chat") so the operator can review and send. Prefill only — never
  // auto-sends — so the empty-state / loading contract is unaffected.
  const handledAskParamRef = useRef(false)
  useEffect(() => {
    if (embedded) return
    if (handledAskParamRef.current) return
    handledAskParamRef.current = true
    const ask = searchParams.get('ask')
    if (!ask) return
    const next = new URLSearchParams(searchParams)
    next.delete('ask')
    setSearchParams(next, { replace: true })
    setInput(ask)
  }, [embedded, searchParams, setSearchParams])

  // Embedded hand-off: a host (the Console) injects a prompt to prefill the
  // composer. Keyed by `key` so re-injecting the same text refires.
  const injectedKey = injectedPrompt?.key
  useEffect(() => {
    if (!embedded || !injectedPrompt?.text) return
    setInput(injectedPrompt.text)
    inputRef.current?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [embedded, injectedKey])

  // Empty-state chips show only on a brand-new, idle conversation.
  const showSuggestions = messages.length <= 1 && !isLoading && !conversationId

  // The scrolling conversation surface + composer — identical across variants.
  const conversation = (
    <>
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">Error: {error}</span>
        </div>
      )}

      {/* Messages. The outer wrapper paints the gradient backdrop + a subtle
          inset top glow hairline; the inner div stays the ONE scrollable
          element that auto-scroll (messagesEndRef) depends on. */}
      <div className="relative min-h-0 flex-1 overflow-hidden rounded-xl border border-border/60 bg-gradient-to-b from-card to-card/70 shadow-sm before:pointer-events-none before:absolute before:inset-x-6 before:top-0 before:z-10 before:h-px before:bg-gradient-to-r before:from-transparent before:via-primary/40 before:to-transparent">
        <div className="flex h-full flex-col space-y-4 overflow-y-auto p-4">
          {messages.map((message) => (
            <div key={message.id} className="msg-in space-y-4">
              {/* Persisted tool-call timeline for this answer: the checkmark
                  steps + searched-data dropdowns stay visible above the reply. */}
              {message.role === 'assistant' && toolStepsById[message.id]?.length > 0 && (
                <ToolCallTimeline steps={toolStepsById[message.id]} />
              )}
              <ChatMessage
                message={message}
                isTyping={typingMessageId === message.id}
                displayedContent={displayedContent}
                insights={insightsById[message.id]}
                proposedAction={proposedById[message.id]}
              />
            </div>
          ))}

          {/* Live animated timeline while a request is in flight. On completion
              (success or failure) it is retired and re-rendered, persisted,
              above its assistant message (see toolStepsById). */}
          {toolSteps.length > 0 && isLoading && (
            <ToolCallTimeline
              steps={toolSteps}
              reducedMotionFallbackText="Thinking... running tools and reasoning."
            />
          )}

          {showSuggestions && (
            <div className="flex flex-1 items-center justify-center">
              <SuggestedPrompts prompts={prompts} onPick={handlePickPrompt} />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatComposer
        input={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        inputRef={inputRef}
        placeholder={PLACEHOLDER}
      />
    </>
  )

  // ---- Embedded (cockpit) variant: slim header, no sidebar, fills its cell.
  if (embedded) {
    return (
      <div className={`flex h-full min-h-0 flex-col ${className}`} data-testid="chat-pane-embedded">
        <div className="mb-2 flex shrink-0 items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-400 drop-shadow-[0_0_6px_hsl(var(--primary)/0.7)]" />
            <span className="text-sm font-semibold">Assistant</span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-card/60 px-2 py-0.5 text-[11px] text-muted-foreground">
              <span className="relative flex h-1.5 w-1.5" aria-hidden>
                <span className="absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75 motion-safe:animate-ping" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-green-500" />
              </span>
              Qwen3-14B
            </span>
          </div>
          <button
            type="button"
            onClick={handleNewConversation}
            className="flex items-center gap-1.5 rounded-lg bg-muted px-2.5 py-1 text-xs text-muted-foreground hover:bg-muted/80"
          >
            <Plus className="h-3.5 w-3.5" />
            New
          </button>
        </div>
        {conversation}
      </div>
    )
  }

  // ---- Page variant: the full /chat experience (DOM the e2e contracts read).
  // Root fills the shell's bounded <main> (h-full min-h-0) so the messages area
  // scrolls internally with the composer pinned — no page-level cutoff.
  return (
    <div className="flex h-full min-h-0 gap-4">
      <ConversationSidebar
        conversations={history.conversations}
        activeId={conversationId}
        loading={history.loading}
        error={history.error}
        mobileOpen={sidebarOpen}
        onNewConversation={handleNewConversation}
        onSelect={handleSelectConversation}
        onDelete={handleDeleteConversation}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="mb-4 flex shrink-0 items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-muted lg:hidden"
              aria-label="Open conversation history"
            >
              <PanelLeftOpen className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold">Chat</h1>
              {/* Status pill — deliberately a SIBLING of the h1, never inside
                  it, so the heading's accessible name stays exactly "Chat". */}
              <span className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-border/60 bg-card/60 px-2.5 py-0.5 text-xs text-muted-foreground shadow-sm">
                <span className="relative flex h-1.5 w-1.5" aria-hidden>
                  <span className="absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75 motion-safe:animate-ping" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-green-500" />
                </span>
                Qwen3-14B · Reasoning Agent
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleNewConversation}
            className="flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-sm text-muted-foreground hover:bg-muted/80"
          >
            <Plus className="h-4 w-4" />
            New
          </button>
        </div>

        {conversation}
      </div>
    </div>
  )
}
