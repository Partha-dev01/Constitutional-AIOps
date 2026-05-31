import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, AlertCircle, PanelLeftOpen, Plus } from 'lucide-react'
import api from '../lib/api'
import { ChatMessage } from '../components/chat/ChatMessage'
import type { ChatMessageData } from '../components/chat/ChatMessage'
import type { MessageInsights } from '../components/chat/InsightCards'
import { ConversationSidebar } from '../components/chat/ConversationSidebar'
import { SuggestedPrompts } from '../components/chat/SuggestedPrompts'
import { ToolCallTimeline } from '../components/chat/ToolCallTimeline'
import { deriveToolSteps, enrichToolStepsWithResponse } from '../hooks/useToolSteps'
import type { ToolStep } from '../hooks/useToolSteps'
import { useConversationHistory } from '../hooks/useConversationHistory'
import { selectPrompts, pushRecentPrompt, getRecentPrompts } from '../lib/suggestedPrompts'

const PLACEHOLDER = 'Ask about incidents, metrics, or request analysis...'

const WELCOME = "Hello! I'm the Constitutional AIOps assistant. I can help you with infrastructure analysis, incident investigation, and system management. How can I help you today?"

/** How long each derived tool step "runs" before completing (ms). */
const STEP_DURATION_MS = 650

function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

function welcomeMessage(): ChatMessageData {
  return { id: 'welcome', role: 'assistant', content: WELCOME, timestamp: new Date() }
}

export function Chat() {
  const [messages, setMessages] = useState<ChatMessageData[]>([welcomeMessage()])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null)
  const [displayedContent, setDisplayedContent] = useState('')
  const [toolSteps, setToolSteps] = useState<ToolStep[]>([])
  const [insightsById, setInsightsById] = useState<Record<string, MessageInsights>>({})
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [prompts, setPrompts] = useState<string[]>(() => selectPrompts())

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const typingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const stepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  /** Cancellable timer for clearing the enriched step timeline after response. */
  const stepClearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const history = useConversationHistory()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, displayedContent, toolSteps, scrollToBottom])

  // Cleanup timers on unmount.
  useEffect(() => {
    return () => {
      if (typingIntervalRef.current) clearInterval(typingIntervalRef.current)
      if (stepTimerRef.current) clearInterval(stepTimerRef.current)
      if (stepClearTimerRef.current) clearTimeout(stepClearTimerRef.current)
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
   * real response lands (see finishToolSteps). Reduced motion snaps all but
   * the reasoning step to done immediately.
   */
  const startToolSteps = useCallback((message: string) => {
    if (stepTimerRef.current) clearInterval(stepTimerRef.current)
    // Cancel any pending clear-timer from a previous response.
    if (stepClearTimerRef.current) {
      clearTimeout(stepClearTimerRef.current)
      stepClearTimerRef.current = null
    }

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
        // on the reasoning model and is resolved by finishToolSteps().
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
   * Mark every derived step done (response arrived), enrich detail payloads
   * with concrete response data, then clear the timeline shortly after.
   */
  const finishToolSteps = useCallback(
    (responseData?: Parameters<typeof enrichToolStepsWithResponse>[1]) => {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current)
        stepTimerRef.current = null
      }
      setToolSteps((prev) => {
        const done = prev.map((s) => ({ ...s, status: 'done' as const }))
        return responseData ? enrichToolStepsWithResponse(done, responseData) : done
      })
      // Clear the timeline after a short pause so users have time to read
      // the enriched step details before the timeline disappears.
      stepClearTimerRef.current = window.setTimeout(() => {
        stepClearTimerRef.current = null
        setToolSteps([])
      }, 3_000)
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

        finishToolSteps({
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
        finishToolSteps()

        const errorAssistantMessage: ChatMessageData = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `I'm sorry, I couldn't process your request. Error: ${errorMessage}\n\nPlease check that the backend and LLM servers are running.`,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorAssistantMessage])
      } finally {
        setIsLoading(false)
      }
    },
    [conversationId, isLoading, startToolSteps, finishToolSteps, startTypewriter, history],
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
    setToolSteps([])
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

  // Empty-state chips show only on a brand-new, idle conversation.
  const showSuggestions = messages.length <= 1 && !isLoading && !conversationId

  return (
    <div className="flex h-[calc(100vh-3rem)] gap-4">
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

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="mb-4 flex items-center justify-between gap-3">
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
              <p className="text-muted-foreground">
                Interact with the Reasoning Agent (Qwen3-14B)
              </p>
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

        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Error: {error}</span>
          </div>
        )}

        {/* Messages */}
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto rounded-lg border border-border bg-card p-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isTyping={typingMessageId === message.id}
              displayedContent={displayedContent}
              insights={insightsById[message.id]}
            />
          ))}

          {isLoading && toolSteps.length > 0 && (
            <ToolCallTimeline
              steps={toolSteps}
              reducedMotionFallbackText="Thinking... running tools and reasoning."
            />
          )}

          {showSuggestions && (
            <div className="pt-6">
              <SuggestedPrompts prompts={prompts} onPick={handlePickPrompt} />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={PLACEHOLDER}
            className="flex-1 rounded-lg border border-border bg-background px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  )
}
