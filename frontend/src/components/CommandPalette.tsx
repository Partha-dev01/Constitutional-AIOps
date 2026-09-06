/**
 * Global command palette (Cmd/Ctrl-K) - a zero-dependency quick-nav over the
 * app's routes. Type to fuzzy-filter, Up/Down to move, Enter to go, Esc to
 * close. Ranking lives in ../lib/commandPalette so this file stays a thin,
 * fast-refresh-clean view. It mirrors the Modal a11y patterns (role="dialog",
 * Esc, backdrop close, focus + scroll-lock management) but is top-aligned and
 * input-first, as command palettes conventionally are.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, CornerDownLeft } from 'lucide-react'
import { cn } from '../lib/utils'
import { rankCommands, type PaletteCommand } from '../lib/commandPalette'

const MAX_RESULTS = 8

export function CommandPalette({
  open,
  onClose,
  commands,
}: {
  open: boolean
  onClose: () => void
  commands: PaletteCommand[]
}) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const results = useMemo(
    () => rankCommands(commands, query).slice(0, MAX_RESULTS),
    [commands, query],
  )

  // Reset query + selection each time the palette opens, and focus the input.
  useEffect(() => {
    if (!open) return
    setQuery('')
    setActive(0)
    const id = requestAnimationFrame(() => inputRef.current?.focus())
    return () => cancelAnimationFrame(id)
  }, [open])

  // Keep the active index in range as the result set changes.
  useEffect(() => {
    setActive((a) => (results.length === 0 ? 0 : Math.min(a, results.length - 1)))
  }, [results.length])

  // Lock body scroll while open (restored on close/unmount).
  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  // Keep the highlighted row visible.
  useEffect(() => {
    const current = results[active]
    if (!current) return
    document
      .getElementById(`cmd-${current.id}`)
      ?.scrollIntoView({ block: 'nearest' })
  }, [active, results])

  if (!open) return null

  const go = (cmd: PaletteCommand | undefined) => {
    if (!cmd) return
    onClose()
    navigate(cmd.href)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((a) => (results.length ? (a + 1) % results.length : 0))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) =>
        results.length ? (a - 1 + results.length) % results.length : 0,
      )
    } else if (e.key === 'Enter') {
      e.preventDefault()
      go(results[active])
    }
  }

  return (
    <div
      className="fixed inset-0 z-[70] flex items-start justify-center bg-black/50 p-4 pt-[12vh]"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        className="w-full max-w-lg overflow-hidden rounded-lg border border-border bg-card shadow-xl"
        onKeyDown={onKeyDown}
      >
        <div className="flex items-center gap-2 border-b border-border px-3">
          <Search
            className="h-4 w-4 shrink-0 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Jump to a page..."
            aria-label="Search pages"
            className="w-full bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
            role="combobox"
            aria-expanded="true"
            aria-controls="command-palette-list"
            aria-activedescendant={
              results[active] ? `cmd-${results[active].id}` : undefined
            }
          />
        </div>
        {results.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-muted-foreground">
            No matching pages
          </div>
        ) : (
          <ul
            id="command-palette-list"
            role="listbox"
            className="max-h-72 overflow-y-auto py-1"
          >
            {results.map((cmd, i) => (
              <li
                key={cmd.id}
                id={`cmd-${cmd.id}`}
                role="option"
                aria-selected={i === active}
                onMouseMove={() => setActive(i)}
                onClick={() => go(cmd)}
                className={cn(
                  'flex cursor-pointer items-center justify-between gap-3 px-3 py-2 text-sm',
                  i === active ? 'bg-muted' : 'hover:bg-muted/50',
                )}
              >
                <span className="truncate">{cmd.title}</span>
                <span className="flex shrink-0 items-center gap-2">
                  {cmd.group && (
                    <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                      {cmd.group}
                    </span>
                  )}
                  {i === active && (
                    <CornerDownLeft
                      className="h-3.5 w-3.5 text-muted-foreground"
                      aria-hidden="true"
                    />
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default CommandPalette
