import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Loader2, AlertCircle, ChevronDown } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import api from '../lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hello! I'm the Constitutional AIOps assistant. I can help you with infrastructure analysis, incident investigation, and system management. How can I help you today?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null)
  const [displayedContent, setDisplayedContent] = useState('')
  const [thinkingExpanded, setThinkingExpanded] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const typingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, displayedContent])

  // Cleanup typing interval on unmount
  useEffect(() => {
    return () => {
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current)
      }
    }
  }, [])

  // Typewriter effect function
  const startTypewriter = useCallback((messageId: string, fullContent: string) => {
    setTypingMessageId(messageId)
    setDisplayedContent('')
    let index = 0

    // Clear any existing interval
    if (typingIntervalRef.current) {
      clearInterval(typingIntervalRef.current)
    }

    typingIntervalRef.current = setInterval(() => {
      if (index < fullContent.length) {
        // Type 2-4 characters at a time for faster effect
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
    }, 15) // 15ms per batch for smooth effect
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      // Call the real API
      const response = await api.chat.send({
        message: input,
        conversation_id: conversationId || undefined,
      })

      // Save conversation ID for continuity
      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }

      const messageId = (Date.now() + 1).toString()
      const assistantMessage: Message = {
        id: messageId,
        role: 'assistant',
        content: response.message.content,
        timestamp: new Date(response.message.timestamp || Date.now()),
      }
      setMessages((prev) => [...prev, assistantMessage])
      // Start typewriter effect for the new message
      startTypewriter(messageId, response.message.content)
    } catch (err) {
      console.error('Chat error:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message'
      setError(errorMessage)

      // Show error as assistant message so user knows what happened
      const errorAssistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I'm sorry, I couldn't process your request. Error: ${errorMessage}\n\nPlease check that the backend and LLM servers are running.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorAssistantMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewConversation = () => {
    setConversationId(null)
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: "Hello! I'm the Constitutional AIOps assistant. I can help you with infrastructure analysis, incident investigation, and system management. How can I help you today?",
        timestamp: new Date(),
      },
    ])
    setError(null)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Chat</h1>
          <p className="text-muted-foreground">
            Interact with the Reasoning Agent (Qwen3-14B)
          </p>
        </div>
        <button
          onClick={handleNewConversation}
          className="px-3 py-1.5 text-sm bg-muted text-muted-foreground rounded-lg hover:bg-muted/80"
        >
          New Conversation
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">Error: {error}</span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-card rounded-lg border border-border p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${
              message.role === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              {message.role === 'user' ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </div>
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <div className={`text-sm prose prose-sm max-w-none ${
                message.role === 'user'
                  ? 'prose-invert'
                  : 'dark:prose-invert'
              }`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.role === 'assistant' && typingMessageId === message.id
                    ? displayedContent
                    : message.content}
                </ReactMarkdown>
                {message.role === 'assistant' && typingMessageId === message.id && (
                  <span className="inline-block w-2 h-4 bg-current animate-pulse ml-0.5" />
                )}
              </div>
              <p
                className={`text-xs mt-1 ${
                  message.role === 'user'
                    ? 'text-primary-foreground/70'
                    : 'text-muted-foreground'
                }`}
              >
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-muted">
              <Bot className="h-4 w-4" />
            </div>
            <div className="bg-muted rounded-lg p-3 min-w-[200px]">
              <button
                onClick={() => setThinkingExpanded(!thinkingExpanded)}
                className="flex items-center gap-2 text-sm text-muted-foreground w-full"
              >
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="font-medium">Thinking...</span>
                <ChevronDown
                  className={`h-4 w-4 ml-auto transition-transform ${
                    thinkingExpanded ? 'rotate-180' : ''
                  }`}
                />
              </button>
              {thinkingExpanded && (
                <div className="mt-2 pt-2 border-t border-border/50">
                  <p className="text-xs text-muted-foreground/70 animate-pulse">
                    Analyzing your request with Qwen3-14B reasoning model...
                  </p>
                  <div className="mt-2 flex gap-1">
                    <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about incidents, metrics, or request analysis..."
          className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  )
}

