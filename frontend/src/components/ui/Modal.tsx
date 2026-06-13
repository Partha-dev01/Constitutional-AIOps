/**
 * Accessible Modal primitive — WAI-ARIA dialog pattern.
 *
 * - role="dialog" + aria-modal="true" + aria-labelledby
 * - Focus moves into the dialog on open (first focusable element)
 * - Tab is trapped inside the dialog while open
 * - Esc closes the dialog
 * - Backdrop click closes the dialog
 * - Focus returns to the opener element on close
 * - Body scroll is locked while open
 *
 * Usage:
 *   <Modal open={open} onClose={onClose} title="Review Action" titleId="approve-title">
 *     <p>Content here</p>
 *   </Modal>
 */
import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { cn } from '../../lib/utils'

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

interface ModalProps {
  open: boolean
  onClose: () => void
  /** Human-readable title rendered in an <h2> and linked via aria-labelledby */
  title: string
  /** Optional: id to use for the heading; defaults to "modal-title" */
  titleId?: string
  children: React.ReactNode
  /** Max-width Tailwind class, e.g. "max-w-lg" (default) or "max-w-2xl" */
  maxWidth?: string
  /** Extra classes on the inner dialog panel */
  className?: string
}

export function Modal({
  open,
  onClose,
  title,
  titleId = 'modal-title',
  children,
  maxWidth = 'max-w-lg',
  className,
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  // Store the element that was focused before the dialog opened
  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement
      // Move focus into the dialog after the DOM updates
      requestAnimationFrame(() => {
        const dialog = dialogRef.current
        if (!dialog) return
        const first = dialog.querySelector<HTMLElement>(FOCUSABLE)
        if (first) first.focus()
        else dialog.focus()
      })
      // Lock body scroll
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
      // Restore focus to the opener
      previousFocusRef.current?.focus()
    }

    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  // Esc handler
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  if (!open) return null

  // Focus trap on Tab / Shift+Tab
  const handleTabTrap = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'Tab') return
    const dialog = dialogRef.current
    if (!dialog) return
    const focusable = Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE))
    if (focusable.length === 0) return

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault()
        last.focus()
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
  }

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      aria-hidden="false"
    >
      {/* Dialog panel */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={handleTabTrap}
        className={cn(
          'bg-card rounded-lg border border-border p-6 w-full mx-4 max-h-[90dvh] overflow-y-auto',
          'focus:outline-none',
          maxWidth,
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 id={titleId} className="text-xl font-bold">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-lg"
            aria-label="Close dialog"
            title="Close"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {children}
      </div>
    </div>
  )
}
