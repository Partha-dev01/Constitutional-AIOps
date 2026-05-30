import { useEffect, useRef, useState } from 'react'

/**
 * Reveal-on-scroll hook. Attach the returned `ref` to an element and read
 * `visible` to toggle a CSS reveal animation class. The element is revealed
 * exactly once (the observer unobserves after the first intersection) so the
 * animation never replays as the user scrolls back and forth.
 *
 * Dependency-free: uses the browser's IntersectionObserver. The animations it
 * gates are disabled under `prefers-reduced-motion` via CSS (see index.css).
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>() {
  const ref = useRef<T | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry && entry.isIntersecting) {
          setVisible(true)
          observer.unobserve(node)
        }
      },
      { threshold: 0.15 },
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return { ref, visible }
}
