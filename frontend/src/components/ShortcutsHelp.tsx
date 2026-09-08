/**
 * Keyboard shortcuts help (Track 2 QoL) — a small reference modal listing the
 * app's global shortcuts. Opened by pressing "?" anywhere (except while typing
 * in a field) or via the "Keyboard shortcuts" command in the palette. Only
 * genuinely global shortcuts are listed here so the reference stays accurate.
 */
import { Modal } from './ui/Modal'

interface Shortcut {
  keys: string[]
  description: string
}

function isMac(): boolean {
  return (
    typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.userAgent)
  )
}

function shortcuts(): Shortcut[] {
  const mod = isMac() ? '⌘' : 'Ctrl'
  return [
    { keys: [mod, 'K'], description: 'Open the command palette (jump to any page)' },
    { keys: ['?'], description: 'Show this keyboard shortcuts help' },
    { keys: ['Esc'], description: 'Close a dialog, menu, or the mobile navigation' },
  ]
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex min-w-7 items-center justify-center rounded-sm border border-border bg-muted px-1.5 py-0.5 font-mono text-xs font-medium text-foreground shadow-xs">
      {children}
    </kbd>
  )
}

export function ShortcutsHelp({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Keyboard shortcuts"
      titleId="shortcuts-title"
    >
      <ul className="divide-y divide-border">
        {shortcuts().map((s) => (
          <li
            key={s.description}
            className="flex items-center justify-between gap-4 py-2.5"
          >
            <span className="text-sm text-muted-foreground">{s.description}</span>
            <span className="flex shrink-0 items-center gap-1">
              {s.keys.map((k, i) => (
                <span key={k} className="flex items-center gap-1">
                  {i > 0 && (
                    <span className="text-xs text-muted-foreground" aria-hidden="true">
                      +
                    </span>
                  )}
                  <Kbd>{k}</Kbd>
                </span>
              ))}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-muted-foreground">
        Shortcuts are ignored while you are typing in a text field.
      </p>
    </Modal>
  )
}

export default ShortcutsHelp
