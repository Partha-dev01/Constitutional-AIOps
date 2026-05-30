import { MessageSquarePlus, Trash2, X, MessagesSquare } from 'lucide-react'
import { cn, formatRelativeTime } from '../../lib/utils'
import type { ConversationSummary } from '../../lib/api'

interface ConversationSidebarProps {
  conversations: ConversationSummary[]
  activeId: string | null
  loading: boolean
  error: boolean
  /** True when the drawer is open below the `lg` breakpoint. */
  mobileOpen: boolean
  onNewConversation: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onCloseMobile: () => void
}

/**
 * Conversation-history sidebar for the Chat page.
 *
 * Layout: permanently docked on `lg+` (a flex column to the left of the
 * thread); a slide-in overlay drawer below `lg`, toggled by the header button
 * in Chat.tsx. Every control is `type="button"` so it never satisfies the
 * live e2e test's `form button[type="submit"]` selector, and nothing here
 * carries the `prose` class (reserved for assistant message bodies).
 */
export function ConversationSidebar({
  conversations,
  activeId,
  loading,
  error,
  mobileOpen,
  onNewConversation,
  onSelect,
  onDelete,
  onCloseMobile,
}: ConversationSidebarProps) {
  const panel = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-2 border-b border-border p-3">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <MessagesSquare className="h-4 w-4 text-primary" />
          Conversations
        </span>
        <button
          type="button"
          onClick={onCloseMobile}
          className="rounded-md p-1 text-muted-foreground hover:bg-muted lg:hidden"
          aria-label="Close conversation history"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="p-3">
        <button
          type="button"
          onClick={onNewConversation}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New chat
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {error && (
          <p className="px-2 py-3 text-xs text-muted-foreground">
            Couldn&apos;t load history. Showing what&apos;s cached.
          </p>
        )}

        {loading && conversations.length === 0 ? (
          <ul className="space-y-1.5 px-1 pt-1" aria-hidden>
            {[0, 1, 2].map((i) => (
              <li key={i} className="h-12 animate-pulse rounded-lg bg-muted/60" />
            ))}
          </ul>
        ) : conversations.length === 0 ? (
          <p className="px-2 py-6 text-center text-xs text-muted-foreground">
            No conversations yet. Start one to see it here.
          </p>
        ) : (
          <ul className="space-y-1">
            {conversations.map((conv) => {
              const isActive = conv.conversation_id === activeId
              const label = conv.preview?.trim() || 'New conversation'
              return (
                <li key={conv.conversation_id} className="group relative">
                  <button
                    type="button"
                    onClick={() => onSelect(conv.conversation_id)}
                    className={cn(
                      'w-full rounded-lg px-3 py-2 pr-9 text-left transition-colors',
                      isActive
                        ? 'bg-muted text-foreground'
                        : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground',
                    )}
                  >
                    <span className="block truncate text-sm">{label}</span>
                    <span className="mt-0.5 block text-xs text-muted-foreground/70">
                      {formatRelativeTime(conv.updated_at)}
                      {conv.message_count > 0 && ` · ${conv.message_count} msgs`}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(conv.conversation_id)}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-muted-foreground/60 opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive focus:opacity-100 group-hover:opacity-100"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )

  return (
    <>
      {/* Docked sidebar (lg and up). */}
      <aside className="hidden w-64 shrink-0 rounded-lg border border-border bg-card lg:block">
        {panel}
      </aside>

      {/* Drawer (below lg). Mounted always so the slide transition can play. */}
      <div
        className={cn(
          'fixed inset-0 z-40 lg:hidden',
          mobileOpen ? 'pointer-events-auto' : 'pointer-events-none',
        )}
        aria-hidden={!mobileOpen}
      >
        <div
          className={cn(
            'absolute inset-0 bg-black/40 transition-opacity duration-200',
            mobileOpen ? 'opacity-100' : 'opacity-0',
          )}
          onClick={onCloseMobile}
        />
        <aside
          className={cn(
            'absolute inset-y-0 left-0 w-72 max-w-[80%] border-r border-border bg-card shadow-xl transition-transform duration-200',
            mobileOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          {panel}
        </aside>
      </div>
    </>
  )
}
