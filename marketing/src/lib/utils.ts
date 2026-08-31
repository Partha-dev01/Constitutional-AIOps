import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Self-contained copy of the app's class-name + motion helpers. The marketing
// site is an independent project by design, so these tiny helpers are
// duplicated rather than cross-imported from the app.

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** True when the user prefers reduced motion; JS animations must bail out. */
export function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}
