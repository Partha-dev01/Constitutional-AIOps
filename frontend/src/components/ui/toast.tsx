/**
 * Lightweight in-app toast + confirm-dialog system.
 *
 * No new npm deps — hand-rolled with React context.
 *
 * Usage:
 *   // Wrap the app in <ToastProvider>
 *   // In any component:
 *   const { showToast, showConfirm } = useToast()
 *   showToast('Saved!', 'success')
 *   const ok = await showConfirm('Delete this item?', 'This cannot be undone.')
 */
import React, {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from 'react'
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Modal } from './Modal'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

interface ToastItem {
  id: number
  message: string
  variant: ToastVariant
}

interface ConfirmState {
  message: string
  detail?: string
  resolve: (value: boolean) => void
}

interface ToastContextValue {
  /** Show a brief notification that auto-dismisses after ~4 s */
  showToast: (message: string, variant?: ToastVariant) => void
  /** Show a branded confirm dialog; returns true if user clicks Confirm */
  showConfirm: (message: string, detail?: string) => Promise<boolean>
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const ToastContext = createContext<ToastContextValue | null>(null)

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const [confirm, setConfirm] = useState<ConfirmState | null>(null)
  const counterRef = useRef(0)

  const showToast = useCallback(
    (message: string, variant: ToastVariant = 'info') => {
      const id = ++counterRef.current
      setToasts((prev) => [...prev, { id, message, variant }])
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, 4000)
    },
    [],
  )

  const showConfirm = useCallback(
    (message: string, detail?: string): Promise<boolean> =>
      new Promise<boolean>((resolve) => {
        setConfirm({ message, detail, resolve })
      }),
    [],
  )

  const handleConfirmClose = (result: boolean) => {
    confirm?.resolve(result)
    setConfirm(null)
  }

  return (
    <ToastContext.Provider value={{ showToast, showConfirm }}>
      {children}

      {/* Toast stack — bottom-right, announced as status region */}
      <div
        aria-live="polite"
        aria-atomic="false"
        className="fixed bottom-4 right-4 z-[60] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]"
      >
        {toasts.map((toast) => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onDismiss={() =>
              setToasts((prev) => prev.filter((t) => t.id !== toast.id))
            }
          />
        ))}
      </div>

      {/* Confirm dialog */}
      {confirm && (
        <Modal
          open={!!confirm}
          onClose={() => handleConfirmClose(false)}
          title={confirm.message}
          titleId="confirm-dialog-title"
          maxWidth="max-w-md"
        >
          {confirm.detail && (
            <p className="text-sm text-muted-foreground mb-6">{confirm.detail}</p>
          )}
          <div className="flex gap-2 justify-end pt-2">
            <button
              onClick={() => handleConfirmClose(false)}
              className="px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80"
            >
              Cancel
            </button>
            <button
              onClick={() => handleConfirmClose(true)}
              className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg text-sm font-medium hover:bg-destructive/90"
            >
              Confirm
            </button>
          </div>
        </Modal>
      )}
    </ToastContext.Provider>
  )
}

// ---------------------------------------------------------------------------
// Toast item component
// ---------------------------------------------------------------------------

const ICON: Record<ToastVariant, React.ElementType> = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const ICON_CLS: Record<ToastVariant, string> = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-yellow-500',
  info: 'text-blue-400',
}

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: ToastItem
  onDismiss: () => void
}) {
  const Icon = ICON[toast.variant]
  return (
    <div
      role="status"
      className={cn(
        'flex items-start gap-3 rounded-lg border border-border bg-card px-4 py-3 shadow-lg',
        'motion-safe:animate-[fadeInUp_0.2s_ease]',
      )}
    >
      <Icon
        className={cn('h-4 w-4 mt-0.5 shrink-0', ICON_CLS[toast.variant])}
        aria-hidden="true"
      />
      <p className="flex-1 text-sm">{toast.message}</p>
      <button
        onClick={onDismiss}
        className="shrink-0 p-0.5 rounded hover:bg-muted"
        aria-label="Dismiss notification"
      >
        <X className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>')
  return ctx
}
