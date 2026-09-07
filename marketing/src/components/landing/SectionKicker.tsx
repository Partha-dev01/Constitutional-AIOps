import type { ReactNode } from 'react'

/**
 * Mono, instrument-style section eyebrow shared across the flagship landing
 * sections (control-room look). Purely presentational; inherits text alignment
 * from its parent (the centered heading blocks center it automatically).
 */
export function SectionKicker({ children }: { children: ReactNode }) {
  return (
    <p className="mb-4 font-mono text-[11px] font-medium uppercase tracking-[0.2em] text-primary/80">
      {children}
    </p>
  )
}

export default SectionKicker
