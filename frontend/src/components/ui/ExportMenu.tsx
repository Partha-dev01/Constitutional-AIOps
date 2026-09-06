/**
 * ExportMenu - a small "Export" control that downloads the given rows as CSV or
 * JSON (Track 2 QoL). Uses a native <details> disclosure so there is no popover
 * state to manage and no click-away edge cases; it closes itself after a choice.
 * When there is nothing to export it renders a disabled button instead.
 */

import type { MouseEvent } from 'react'
import { Download } from 'lucide-react'
import { cn } from '../../lib/utils'
import { exportRows, type ExportColumn, type ExportFormat } from '../../lib/exportTable'

interface ExportMenuProps<T> {
  rows: readonly T[]
  columns: readonly ExportColumn<T>[]
  /** File name stem; a date and extension are appended (e.g. audit_log_2026-09-06.csv). */
  filenameBase: string
  disabled?: boolean
  className?: string
}

const TRIGGER_CLASS =
  'inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm font-medium transition-colors hover:bg-muted'

export function ExportMenu<T>({
  rows,
  columns,
  filenameBase,
  disabled,
  className,
}: ExportMenuProps<T>) {
  const empty = disabled || rows.length === 0

  if (empty) {
    return (
      <button type="button" disabled className={cn(TRIGGER_CLASS, 'opacity-50', className)}>
        <Download className="h-4 w-4" aria-hidden="true" />
        Export
      </button>
    )
  }

  function choose(format: ExportFormat, e: MouseEvent<HTMLButtonElement>) {
    exportRows(rows, columns, format, filenameBase)
    // Close the native disclosure after the download starts.
    e.currentTarget.closest('details')?.removeAttribute('open')
  }

  return (
    <details className={cn('relative', className)}>
      <summary
        className={cn(
          TRIGGER_CLASS,
          'cursor-pointer list-none [&::-webkit-details-marker]:hidden',
        )}
      >
        <Download className="h-4 w-4" aria-hidden="true" />
        Export
      </summary>
      <div
        role="menu"
        className="absolute right-0 z-20 mt-1 w-32 overflow-hidden rounded-lg border border-border bg-card shadow-lg"
      >
        <button
          type="button"
          role="menuitem"
          onClick={(e) => choose('csv', e)}
          className="block w-full px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
        >
          CSV
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={(e) => choose('json', e)}
          className="block w-full px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
        >
          JSON
        </button>
      </div>
    </details>
  )
}

export default ExportMenu
