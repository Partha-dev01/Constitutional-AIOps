import { useEffect, useRef } from 'react'
import { prefersReducedMotion } from '../lib/utils'

/**
 * Subtle scroll parallax. Attach the returned ref to an element and it is
 * translated vertically by `scrollY * factor` (e.g. -0.06 drifts it slowly
 * upward as the user scrolls down).
 *
 * - rAF-throttled: at most one transform write per frame, driven by a passive
 *   scroll listener.
 * - Accessibility: bails out entirely (no listener, no transform) when the
 *   user prefers reduced motion.
 */
export function useParallax<T extends HTMLElement = HTMLDivElement>(factor: number) {
  const ref = useRef<T | null>(null)

  useEffect(() => {
    const node = ref.current
    if (!node || prefersReducedMotion()) return

    let frame = 0

    const apply = () => {
      frame = 0
      if (ref.current) {
        ref.current.style.transform = `translate3d(0, ${window.scrollY * factor}px, 0)`
      }
    }

    const onScroll = () => {
      if (frame === 0) {
        frame = window.requestAnimationFrame(apply)
      }
    }

    apply()
    window.addEventListener('scroll', onScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', onScroll)
      if (frame !== 0) window.cancelAnimationFrame(frame)
      node.style.transform = ''
    }
  }, [factor])

  return ref
}
