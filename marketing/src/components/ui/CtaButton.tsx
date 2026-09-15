import type { ReactNode } from 'react'
import { ArrowRight } from 'lucide-react'
import { cn } from '../../lib/utils'

/**
 * The one call-to-action button used across the marketing site, so the primary
 * "launch" action and the secondary glass action look identical everywhere.
 *
 * - primary: a blue→indigo gradient with an accent glow (used for the launch /
 *   sign-in CTAs — these carry APP_URL, per the marketing invariant).
 * - secondary: a translucent glass button that lifts toward the accent.
 *
 * A plain <a>, never a <nav>/<button>, keeping the zero-<nav> invariant. The
 * hover motion is CSS-transition based and neutralised under reduced motion.
 */
interface CtaButtonProps {
  href: string
  children: ReactNode
  variant?: 'primary' | 'secondary'
  arrow?: boolean
  className?: string
  testId?: string
}

export function CtaButton({
  href,
  children,
  variant = 'primary',
  arrow = false,
  className,
  testId,
}: CtaButtonProps) {
  const base =
    'group inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background'

  const styles =
    variant === 'primary'
      ? 'bg-gradient-to-br from-primary to-[hsl(258_85%_60%)] text-primary-foreground shadow-[0_10px_30px_-8px_hsl(var(--primary)/0.6)] hover:-translate-y-0.5 hover:shadow-[0_16px_40px_-8px_hsl(var(--primary)/0.7)]'
      : 'glass glass-hover text-foreground hover:text-primary'

  return (
    <a href={href} data-testid={testId} className={cn(base, styles, className)}>
      {children}
      {arrow && (
        <ArrowRight
          className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
          aria-hidden="true"
        />
      )}
    </a>
  )
}

export default CtaButton
