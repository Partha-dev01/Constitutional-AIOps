import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

/**
 * Standalone layout for the public legal pages (Privacy, Terms). Rendered
 * OUTSIDE the authed sidebar shell, so it carries its own header, back link,
 * and cross-links. Theme-aware via the shared token classes. Kept deliberately
 * plain: these are readable documents, not app surfaces.
 */
export function LegalPage({
  title,
  lastUpdated,
  children,
}: {
  title: string
  lastUpdated: string
  children: ReactNode
}) {
  return (
    <div className="min-h-screen bg-background font-sans text-foreground">
      <div className="mx-auto w-full max-w-3xl px-4 py-10">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2">
            <img src="/logo-mark.png" alt="" aria-hidden="true" className="h-8 w-8" />
            <div>
              <p className="text-sm font-bold leading-tight">Constitutional</p>
              <p className="text-xs text-muted-foreground">AIOps</p>
            </div>
          </Link>
          <Link
            to="/signup"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to signup
          </Link>
        </div>

        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">Last updated: {lastUpdated}</p>

        <div className="mt-8 space-y-6">{children}</div>

        <div className="mt-12 border-t border-border pt-6 text-sm text-muted-foreground">
          <Link to="/privacy" className="text-primary hover:underline">
            Privacy Policy
          </Link>
          <span className="px-2" aria-hidden="true">
            ·
          </span>
          <Link to="/terms" className="text-primary hover:underline">
            Terms of Service
          </Link>
        </div>
      </div>
    </div>
  )
}

/** A titled section within a legal document. */
export function LegalSection({
  heading,
  children,
}: {
  heading: string
  children: ReactNode
}) {
  return (
    <section className="space-y-2">
      <h2 className="text-base font-semibold text-foreground">{heading}</h2>
      <div className="space-y-2 text-sm leading-relaxed text-muted-foreground">{children}</div>
    </section>
  )
}

export default LegalPage
