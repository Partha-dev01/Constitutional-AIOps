import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, AlertCircle } from 'lucide-react'
import api, { ChatMessage as ApiChatMessage } from '../lib/api'

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
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message.content,
        timestamp: new Date(response.message.timestamp || Date.now()),
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      setError(err instanceof Error ? err.message : 'Failed to send message')

      // Fallback to mock response if API fails
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateMockResponse(input),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
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
        <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center gap-2 text-yellow-600">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">API unavailable, using mock responses</span>
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
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
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
            <div className="bg-muted rounded-lg p-3">
              <Loader2 className="h-4 w-4 animate-spin" />
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

function generateMockResponse(input: string): string {
  const lowerInput = input.toLowerCase()

  if (lowerInput.includes('incident') || lowerInput.includes('alert')) {
    return `Based on my analysis of the current incidents:

**Active Issues:**
1. High CPU on api-gateway (87% confidence)
   - Root cause: Likely increased traffic from recent deployment
   - Suggested action: Scale horizontally

2. Database connection pool warning (92% confidence)
   - Root cause: Connection leak in user-service v2.3.1
   - Suggested action: Restart affected pods

Would you like me to proceed with any remediation actions?`
  }

  if (lowerInput.includes('status') || lowerInput.includes('health')) {
    return `**System Health Summary:**

✅ Fast Agent (Qwen3-4B): Operational
   - Latency: 42ms avg
   - Requests/min: 847

✅ Reasoning Agent (Qwen3-14B): Operational
   - Latency: 156ms avg
   - Active sessions: 3

✅ Neo4j Memory: Healthy
   - Episodes stored: 1,247
   - Graph nodes: 15,892

⚠️ 3 active incidents requiring attention`
  }

  return `I've analyzed your query. Based on the current system state and telemetry data:

The infrastructure appears to be operating within normal parameters, with a few areas worth monitoring:

1. Memory usage is trending upward on worker nodes
2. Request latency has increased 15% in the last hour
3. No critical security alerts

Would you like me to:
- Perform a deeper analysis on any specific component?
- Generate a remediation plan?
- Show historical trends?`
}
