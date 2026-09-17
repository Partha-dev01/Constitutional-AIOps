/**
 * Product-tour store (zustand). Holds the modal's open/step state and the
 * navigation actions. Kept tiny and framework-agnostic so the command palette
 * can start it imperatively via `useProductTour.getState().start()` (the
 * supported zustand-v5 out-of-React pattern).
 *
 * Closing the tour (finish, skip, Esc or backdrop) always records it as
 * completed so it never re-auto-opens; an auto-started run also marks the
 * current what's-new as seen, so a first-run user is never double-prompted with
 * the banner right after the tour.
 */
import { create } from 'zustand'

import { TOUR_STEPS } from './steps'
import { APP_VERSION, markTourCompleted, markWhatsNewSeen } from './whatsNew'

interface ProductTourState {
  open: boolean
  index: number
  /** True when this run was auto-started on first visit (vs. user-invoked). */
  autoStarted: boolean
  start: (auto?: boolean) => void
  close: () => void
  next: () => void
  back: () => void
}

export const useProductTour = create<ProductTourState>((set, get) => ({
  open: false,
  index: 0,
  autoStarted: false,

  start: (auto = false) => set({ open: true, index: 0, autoStarted: auto }),

  close: () => {
    markTourCompleted()
    if (get().autoStarted) markWhatsNewSeen(APP_VERSION)
    set({ open: false, autoStarted: false })
  },

  next: () => {
    const { index, close } = get()
    if (index >= TOUR_STEPS.length - 1) {
      close()
    } else {
      set({ index: index + 1 })
    }
  },

  back: () => set((s) => ({ index: Math.max(0, s.index - 1) })),
}))

export default useProductTour
