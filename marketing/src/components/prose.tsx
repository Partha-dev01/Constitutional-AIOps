import type { ReactNode } from 'react'
import { ArrowRight } from 'lucide-react'
import { LandingHeader } from './landing/LandingHeader'
import { TeamFooter } from './landing/TeamFooter'
import { APP_URL, DEMO_URL } from '../config'

/**
 * Shared building blocks for the standalone content pages (Architecture,
 * Features, Benchmark, Use-cases, FAQ, Open-source). Each page is its own Vite
 * entry and stays fully static. These mirror the prose primitives first written
 * inline in Safety.tsx / Docs.tsx, lifted here so the newer pages do not each
 * redeclare them. No new dependency, same design tokens.
 *
 * PageShell is deliberately a <header>/<main>/<footer> layout with no <nav>, to
 * keep the marketing invariant (zero <nav> elements on any front-door page).
 */

const MAXW = {
  '3xl': 'max-w-3xl',
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  '6xl': 'max-w-6xl',
} as const

export function PageShell({
  maxWidth = '3xl',
  pill,
  title,
  lead,
  children,
}: {
  maxWidth?: keyof typeof MAXW
  pill?: ReactNode
  title: string
  lead: ReactNode
  children: ReactNode
}) {
  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-foreground">
      <div className="aurora" aria-hidden="true" />
      <LandingHeader />

      <main className={`mx-auto ${MAXW[maxWidth]} px-6 pb-16 pt-28 sm:pt-32`}>
        <div className="mb-10">
          {pill}
          <h1 className="mt-4 text-4xl font-bold tracking-tight">{title}</h1>
          <p className="mt-3 max-w-3xl text-lg text-muted-foreground">{lead}</p>
        </div>
        {children}
      </main>

      <TeamFooter />
    </div>
  )
}

export function Pill({ icon, children }: { icon?: ReactNode; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
      {icon}
      {children}
    </span>
  )
}

export function H2({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <h2
      id={id}
      className="scroll-mt-24 mt-14 mb-4 border-b border-border pb-2 text-2xl font-bold tracking-tight"
    >
      {children}
    </h2>
  )
}

export function H3({ children }: { children: ReactNode }) {
  return <h3 className="mt-6 mb-2 text-lg font-semibold">{children}</h3>
}

export function P({ children }: { children: ReactNode }) {
  return <p className="mb-4 max-w-3xl leading-relaxed text-muted-foreground">{children}</p>
}

export function Code({ children }: { children: ReactNode }) {
  return (
    <code className="rounded bg-card px-1.5 py-0.5 font-mono text-[0.85em] text-primary">{children}</code>
  )
}

/** Bordered surface used for feature cards, scenario blocks and the like. */
export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-xl border border-border bg-card/50 p-5 ${className}`}>{children}</div>
}

/** A large number with a small caption, for the benchmark headline figures. */
export function Stat({ value, label }: { value: string; label: ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card/50 p-6">
      <div className="text-4xl font-bold tracking-tight text-foreground">{value}</div>
      <div className="mt-2 text-sm text-muted-foreground">{label}</div>
    </div>
  )
}

/**
 * The standard call-to-action pair used at the foot of every content page:
 * "See it in Demo mode" (the always-on, $0 demo) and "Sign in" (the app).
 */
export function CTARow() {
  return (
    <div className="mb-2 mt-10 flex flex-wrap gap-3">
      <a
        href={DEMO_URL}
        className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
      >
        See it in Demo mode
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
      </a>
      <a
        href={APP_URL}
        className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary"
      >
        Sign in
      </a>
    </div>
  )
}
