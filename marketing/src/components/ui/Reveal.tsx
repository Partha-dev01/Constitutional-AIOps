import type { CSSProperties, ReactNode } from 'react'
import { useReveal } from '../../hooks/useReveal'

/**
 * Scroll-reveal wrapper: fades + rises its children in once, when they first
 * enter the viewport. It is the single motion primitive for the landing page,
 * so every block (section headers, the stats band, footer columns) animates in
 * with the same reveal-up language the card grids already use.
 *
 * Pass `delay` (ms) to stagger siblings. Dependency-free (IntersectionObserver
 * via useReveal); the .reveal/.reveal-visible classes are disabled under
 * prefers-reduced-motion in index.css, so this renders fully visible at rest for
 * those users.
 */
export function Reveal({
  children,
  className = '',
  delay,
  id,
}: {
  children: ReactNode
  className?: string
  delay?: number
  id?: string
}) {
  const { ref, visible } = useReveal<HTMLDivElement>()
  const style: CSSProperties | undefined = delay ? { animationDelay: `${delay}ms` } : undefined
  return (
    <div
      ref={ref}
      id={id}
      className={`reveal${visible ? ' reveal-visible' : ''} ${className}`}
      style={style}
    >
      {children}
    </div>
  )
}
