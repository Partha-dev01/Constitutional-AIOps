import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { InsightCards } from './InsightCards'
import type { MessageInsights } from './InsightCards'

export interface ChatMessageData {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatMessageProps {
  message: ChatMessageData
  /** True while this message is being typed out by the typewriter effect. */
  isTyping: boolean
  /** The progressively-revealed content while typing. */
  displayedContent: string
  /** Optional insights rendered beneath an assistant bubble (once not typing). */
  insights?: MessageInsights
}

/**
 * Presentational chat bubble. Markup is the verbatim extraction of the
 * original Chat.tsx bubble: avatar + markdown body (carrying the `prose`
 * class) + timestamp + typewriter cursor. Assistant insight cards render
 * beneath the bubble when present and the message is not still typing.
 *
 * The `prose` wrapper here is the ONLY element carrying `prose` for assistant
 * bodies — the live e2e test reads `.prose`.last().innerText().
 */
export function ChatMessage({ message, isTyping, displayedContent, insights }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className="max-w-[70%]">
        <div
          className={`rounded-lg p-3 ${
            isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
          }`}
        >
          <div
            className={`text-sm prose prose-sm max-w-none ${
              isUser ? 'prose-invert' : 'dark:prose-invert'
            }`}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.role === 'assistant' && isTyping ? displayedContent : message.content}
            </ReactMarkdown>
            {message.role === 'assistant' && isTyping && (
              <span className="inline-block w-2 h-4 bg-current animate-pulse ml-0.5" />
            )}
          </div>
          <p
            className={`text-xs mt-1 ${
              isUser ? 'text-primary-foreground/70' : 'text-muted-foreground'
            }`}
          >
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>

        {message.role === 'assistant' && !isTyping && insights && (
          <InsightCards insights={insights} />
        )}
      </div>
    </div>
  )
}
