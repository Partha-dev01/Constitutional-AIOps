import type { CSSProperties, ReactNode } from 'react'
import { cn } from '../../lib/utils'

/**
 * The core translucent surface of the marketing redesign. Wraps the `.glass`
 * utility (see styles/landing.css) so every panel across the landing and the
 * content pages reads as one system instead of a stack of flat bordered boxes.
 *
 * Pure presentation, dependency-free, no network. `tone="strong"` is a more
 * present surface for hero panels and figures; `hover` adds the accent lift
 * (killed under reduced motion via the CSS `.glass-hover` rule).
 */

type GlassTag = 'div' | 'li' | 'figure' | 'article' | 'section'

const RADII = {
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl',
  '3xl': 'rounded-3xl',
} as const

interface GlassCardProps {
  children: ReactNode
  tone?: 'default' | 'strong'
  hover?: boolean
  radius?: keyof typeof RADII
  className?: string
  as?: GlassTag
  id?: string
  style?: CSSProperties
}

export function GlassCard({
  children,
  tone = 'default',
  hover = false,
  radius = '2xl',
  className,
  as: Tag = 'div',
  id,
  style,
}: GlassCardProps) {
  return (
    <Tag
      id={id}
      style={style}
      className={cn(
        'glass',
        tone === 'strong' && 'glass-strong',
        hover && 'glass-hover',
        RADII[radius],
        className,
      )}
    >
      {children}
    </Tag>
  )
}

export default GlassCard
