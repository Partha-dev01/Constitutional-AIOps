import { ShieldCheck, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { InsightCards } from './InsightCards'
import type { MessageInsights } from './InsightCards'
import { ProposedActionCard } from './ProposedActionCard'
import type { ProposedAction } from '../../lib/api'

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
  /** Optional AI-proposed remediation rendered as a card beneath the bubble. */
  proposedAction?: ProposedAction
}

/**
 * Presentational chat bubble: avatar + markdown body (carrying the `prose`
 * class) + typewriter cursor, with the timestamp on a hover-revealed line
 * below the bubble. Assistant insight cards render beneath the bubble when
 * present and the message is not still typing.
 *
 * The `prose` wrapper here is the ONLY element carrying `prose` for assistant
 * bodies — the live e2e test reads `.prose`.last().innerText().
 */
export function ChatMessage({ message, isTyping, displayedContent, insights, proposedAction }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`group flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {isUser ? (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm">
          <User className="h-4 w-4" />
        </div>
      ) : (
        /* Assistant mark: flat brand-tinted disc — no glowing-orb halo, no toy
           robot. ShieldCheck ties replies to the constitutional/governed system. */
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-primary/25 bg-primary/10 text-primary shadow-sm ring-1 ring-inset ring-white/5">
          <ShieldCheck className="h-[18px] w-[18px]" strokeWidth={2} />
        </div>
      )}
      <div className="max-w-[75%]">
        <div
          className={`rounded-2xl p-3 ${
            isUser
              ? 'rounded-br-md bg-primary text-primary-foreground shadow-sm'
              : 'rounded-tl-md border border-border/60 bg-card shadow-sm'
          }`}
        >
          <div
            className={`text-sm prose prose-sm max-w-none break-words prose-p:leading-relaxed prose-headings:font-semibold prose-code:whitespace-pre-wrap prose-code:break-words prose-code:before:content-none prose-code:after:content-none prose-pre:overflow-x-auto prose-pre:whitespace-pre-wrap prose-pre:border prose-pre:border-border/60 prose-pre:bg-background/80 ${
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
        </div>

        {/* Timestamp lives OUTSIDE the bubble; fades in on group hover. */}
        <p
          className={`mt-1 text-[11px] text-muted-foreground/70 opacity-0 transition-opacity group-hover:opacity-100 ${
            isUser ? 'text-right' : ''
          }`}
        >
          {message.timestamp.toLocaleTimeString()}
        </p>

        {message.role === 'assistant' && !isTyping && insights && (
          <InsightCards insights={insights} />
        )}

        {/* Proposed-action card: a SIBLING of the bubble, OUTSIDE the `.prose`
            wrapper, so the live e2e reading `.prose`.last().innerText() is
            unaffected. Only rendered when this assistant turn carries one. */}
        {message.role === 'assistant' && !isTyping && proposedAction && (
          <ProposedActionCard action={proposedAction} />
        )}
      </div>
    </div>
  )
}
