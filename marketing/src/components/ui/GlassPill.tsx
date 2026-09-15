import type { ReactNode } from 'react'
import { cn } from '../../lib/utils'

/**
 * A small translucent chip: the hero announcement badge, page eyebrows, and
 * inline tags. Glass surface, rounded-full, quiet text. Presentation only.
 */
export function GlassPill({
  icon,
  children,
  className,
}: {
  icon?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'glass inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-medium text-muted-foreground',
        className,
      )}
    >
      {icon}
      {children}
    </span>
  )
}

export default GlassPill
