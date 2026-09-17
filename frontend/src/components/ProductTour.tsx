/**
 * ProductTour - the first-run guided intro rendered as an accessible modal
 * carousel (reuses the shared ui/Modal: focus trap, Esc, backdrop, scroll lock).
 * State lives in lib/tour/store; content in lib/tour/steps. Closing the modal
 * (any path) records the tour as completed via the store.
 */
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ArrowRight } from 'lucide-react'

import { Modal } from './ui/Modal'
import { TOUR_STEPS } from '../lib/tour/steps'
import { useProductTour } from '../lib/tour/store'

export function ProductTour() {
  const open = useProductTour((s) => s.open)
  const index = useProductTour((s) => s.index)
  const next = useProductTour((s) => s.next)
  const back = useProductTour((s) => s.back)
  const close = useProductTour((s) => s.close)
  const navigate = useNavigate()

  const step = TOUR_STEPS[index]
  if (!open || !step) return null

  const isLast = index === TOUR_STEPS.length - 1
  const Icon = step.icon
  const primaryLabel = isLast ? step.cta ?? 'Done' : 'Next'

  const onPrimary = () => {
    if (isLast && step.to) navigate(step.to)
    next()
  }

  return (
    <Modal
      open={open}
      onClose={close}
      title={step.title}
      titleId="product-tour-title"
      maxWidth="max-w-md"
    >
      <div className="flex items-start gap-4">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary ring-1 ring-inset ring-primary/20"
          aria-hidden="true"
        >
          <Icon className="h-5 w-5" />
        </div>
        <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
      </div>

      {/* Progress dots */}
      <div className="mt-6 flex items-center justify-center gap-1.5" aria-hidden="true">
        {TOUR_STEPS.map((s, i) => (
          <span
            key={s.id}
            className={
              i === index
                ? 'h-1.5 w-5 rounded-full bg-primary transition-all'
                : 'h-1.5 w-1.5 rounded-full bg-muted-foreground/30 transition-all'
            }
          />
        ))}
      </div>

      {/* Footer */}
      <div className="mt-6 flex items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground">
          Step {index + 1} of {TOUR_STEPS.length}
        </span>
        <div className="flex items-center gap-2">
          {!isLast && (
            <button
              type="button"
              onClick={close}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/40"
            >
              Skip
            </button>
          )}
          {index > 0 && (
            <button
              type="button"
              onClick={back}
              className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/40"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Back
            </button>
          )}
          <button
            type="button"
            onClick={onPrimary}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-hidden focus:ring-2 focus:ring-primary/40"
          >
            {primaryLabel}
            {isLast && step.to && <ArrowRight className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default ProductTour
