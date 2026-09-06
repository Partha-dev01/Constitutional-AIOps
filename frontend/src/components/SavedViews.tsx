/**
 * SavedViews (Track 2 QoL) — a small "Views" control that saves the current
 * URL-query filter state under a name and re-applies it on click. Uses a native
 * <details> disclosure (same as ExportMenu) so there is no popover state or
 * click-away handling. Storage is per-browser localStorage via ../lib/savedViews;
 * cross-device sharing is already covered by the deep-link URL.
 */
import { useEffect, useState, type FormEvent, type MouseEvent } from 'react'
import { Bookmark, Trash2, Plus } from 'lucide-react'
import { cn } from '../lib/utils'
import {
  loadViews,
  saveViews,
  addView,
  removeView,
  type SavedView,
} from '../lib/savedViews'

const TRIGGER_CLASS =
  'inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted'

interface SavedViewsProps {
  /** Page namespace for the stored list, e.g. "incidents". */
  scope: string
  /** The current URL query string (without '?') to save when the user asks. */
  currentQuery: string
  /** Apply a saved view's query (typically setSearchParams). */
  onApply: (query: string) => void
  className?: string
}

export function SavedViews({
  scope,
  currentQuery,
  onApply,
  className,
}: SavedViewsProps) {
  const [views, setViews] = useState<SavedView[]>([])
  const [name, setName] = useState('')

  useEffect(() => {
    setViews(loadViews(scope))
  }, [scope])

  function persist(next: SavedView[]) {
    setViews(next)
    saveViews(scope, next)
  }

  function apply(view: SavedView, e: MouseEvent<HTMLButtonElement>) {
    onApply(view.query)
    e.currentTarget.closest('details')?.removeAttribute('open')
  }

  function save(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    persist(addView(views, name, currentQuery))
    setName('')
  }

  return (
    <details className={cn('relative', className)}>
      <summary
        className={cn(
          TRIGGER_CLASS,
          'cursor-pointer list-none [&::-webkit-details-marker]:hidden',
        )}
      >
        <Bookmark className="h-4 w-4" aria-hidden="true" />
        Views
        {views.length > 0 && (
          <span className="rounded-full bg-muted px-1.5 text-xs text-muted-foreground">
            {views.length}
          </span>
        )}
      </summary>
      <div
        role="menu"
        className="absolute right-0 z-20 mt-1 w-64 overflow-hidden rounded-lg border border-border bg-card shadow-lg"
      >
        {views.length === 0 ? (
          <p className="px-3 py-2 text-sm text-muted-foreground">
            No saved views yet.
          </p>
        ) : (
          <ul className="max-h-56 overflow-y-auto py-1">
            {views.map((view) => (
              <li key={view.id} className="flex items-center">
                <button
                  type="button"
                  role="menuitem"
                  onClick={(e) => apply(view, e)}
                  title={view.query || 'All (no filters)'}
                  className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
                >
                  {view.name}
                </button>
                <button
                  type="button"
                  onClick={() => persist(removeView(views, view.id))}
                  aria-label={`Delete view ${view.name}`}
                  className="px-2 py-2 text-muted-foreground transition-colors hover:text-red-500"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>
        )}
        <form
          onSubmit={save}
          className="flex items-center gap-1 border-t border-border p-2"
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Save current as..."
            aria-label="Name for the current view"
            className="min-w-0 flex-1 rounded border border-border bg-transparent px-2 py-1 text-sm outline-none focus:ring-2 focus:ring-primary/40"
          />
          <button
            type="submit"
            disabled={!name.trim()}
            aria-label="Save current view"
            className="rounded border border-border p-1 transition-colors hover:bg-muted disabled:opacity-50"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
          </button>
        </form>
      </div>
    </details>
  )
}

export default SavedViews
