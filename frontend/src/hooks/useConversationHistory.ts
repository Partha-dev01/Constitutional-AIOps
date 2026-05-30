import { useCallback, useEffect, useState } from 'react'
import api, { ApiError } from '../lib/api'
import type { ConversationSummary } from '../lib/api'

/**
 * Conversation-history state for the Chat sidebar.
 *
 * History is API-first with a localStorage mirror: on mount (and on demand) we
 * fetch the live conversation list from the backend; whatever we get is cached
 * to localStorage so the sidebar still shows *something* immediately on the
 * next visit (and survives a backend hiccup). The in-memory backend store is
 * ephemeral, so the cache is a best-effort convenience, never the source of
 * truth — a successful fetch always replaces it.
 *
 * Everything degrades silently: storage failures (private mode / quota) and
 * fetch failures never throw out of the hook; they just leave the last-known
 * list in place and surface a boolean `error` flag for the UI.
 */

const CACHE_KEY = 'aiops.chat.conversations'

/** Read the cached conversation list. Never throws. */
function readCache(): ConversationSummary[] {
  try {
    const raw = window.localStorage.getItem(CACHE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    // Keep only well-formed summaries (defensive against schema drift).
    return parsed.filter(
      (c): c is ConversationSummary =>
        typeof c === 'object' &&
        c !== null &&
        typeof (c as ConversationSummary).conversation_id === 'string',
    )
  } catch {
    return []
  }
}

/** Persist the conversation list to the mirror. Never throws. */
function writeCache(items: ConversationSummary[]): void {
  try {
    window.localStorage.setItem(CACHE_KEY, JSON.stringify(items))
  } catch {
    // Mirror is best-effort only.
  }
}

export interface UseConversationHistory {
  /** Most-recent-first conversation summaries (API result, mirrored locally). */
  conversations: ConversationSummary[]
  /** True only during the very first load (so the sidebar can show a skeleton). */
  loading: boolean
  /** True when the last refresh failed (cache may still be shown). */
  error: boolean
  /** Re-fetch the list from the backend. */
  refresh: () => Promise<void>
  /** Delete a conversation (backend + mirror), optimistically updating state. */
  remove: (id: string) => Promise<void>
}

export function useConversationHistory(): UseConversationHistory {
  const [conversations, setConversations] = useState<ConversationSummary[]>(() => readCache())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const res = await api.chat.listConversations()
      const items = res.items ?? []
      setConversations(items)
      writeCache(items)
      setError(false)
    } catch (err) {
      // A 404 (no conversations endpoint yet / empty) is not a real error for
      // the UI; treat any failure as "keep the cache, flag softly".
      if (err instanceof ApiError && err.status === 404) {
        setError(false)
      } else {
        setError(true)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const remove = useCallback(async (id: string) => {
    // Optimistic: drop it locally first so the UI feels instant.
    setConversations((prev) => {
      const next = prev.filter((c) => c.conversation_id !== id)
      writeCache(next)
      return next
    })
    try {
      await api.chat.deleteConversation(id)
    } catch {
      // If the delete failed, re-sync from the backend to restore truth.
      void refresh()
    }
  }, [refresh])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return { conversations, loading, error, refresh, remove }
}
