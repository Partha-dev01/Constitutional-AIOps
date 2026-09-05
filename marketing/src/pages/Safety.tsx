import type { ReactNode } from 'react'
import { ArrowRight, ShieldCheck } from 'lucide-react'
import { LandingHeader } from '../components/landing/LandingHeader'
import { TeamFooter } from '../components/landing/TeamFooter'
import { APP_URL, DEMO_URL } from '../config'

/**
 * Standalone public "Safety" page (served as /safety.html, a Vite entry). The
 * constitutional layer is the product's strongest differentiator, so it gets its
 * own page. Content is the real 12-principle / 3-tier framework and the graduated
 * -trust authorization matrix. Fully static and public-safe, no network calls.
 */

// ── prose primitives (mirrors Docs.tsx; no typography plugin in this project) ──
function H2({ id, children }: { id: string; children: ReactNode }) {
  return (
    <h2 id={id} className="scroll-mt-24 mt-14 mb-4 border-b border-border pb-2 text-2xl font-bold tracking-tight">
      {children}
    </h2>
  )
}
function P({ children }: { children: ReactNode }) {
  return <p className="mb-4 max-w-3xl leading-relaxed text-muted-foreground">{children}</p>
}
function Code({ children }: { children: ReactNode }) {
  return <code className="rounded bg-card px-1.5 py-0.5 font-mono text-[0.85em] text-primary">{children}</code>
}

const TIERS: { tier: string; rule: string; principles: string[] }[] = [
  {
    tier: 'Tier 1 — Safety critical',
    rule: 'Never violated',
    principles: [
      'No data deletion without confirmation',
      'Keep at least two healthy service replicas',
      'No cascade action affecting more than five services',
      'Every action reversible within 60 seconds',
    ],
  },
  {
    tier: 'Tier 2 — Operational',
    rule: 'Require approval',
    principles: [
      'Prefer the minimal intervention',
      'Require evidence-based decisions',
      'Check historical precedent first',
      'Graceful degradation over shutdown',
    ],
  },
  {
    tier: 'Tier 3 — Learning',
    rule: 'Soft guidelines',
    principles: [
      'Attribute outcomes to the actions that caused them',
      'Analyze failures systematically',
      'Reinforce patterns that worked',
      'Keep a diversity of solutions',
    ],
  },
]

const MATRIX: { confidence: string; action: string; review: string }[] = [
  { confidence: 'Above 0.90', action: 'Automatic', review: 'Audit only' },
  { confidence: '0.70 to 0.90', action: 'Approval required', review: 'A human must approve' },
  { confidence: 'Below 0.70', action: 'Alert only', review: 'Notify, do not act' },
]

export function Safety() {
  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-foreground">
      <div className="aurora" aria-hidden="true" />
      <LandingHeader />

      <main className="mx-auto max-w-3xl px-6 pb-16 pt-28 sm:pt-32">
        <div className="mb-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Safety
          </span>
          <h1 className="mt-4 text-4xl font-bold tracking-tight">The constitutional layer</h1>
          <p className="mt-3 text-lg text-muted-foreground">
            An AIOps system that can act on your infrastructure needs a reason to be trusted. Every
            proposed action here passes a fixed set of principles and a graduated-trust gate before
            anything runs, and every decision is recorded.
          </p>
        </div>

        <article className="min-w-0">
          <H2 id="why">Why a constitution</H2>
          <P>
            The reasoning agent proposes remediations. It does not execute them on its own. Instead
            each proposal is checked against twelve principles grouped into three tiers, then routed by
            how confident the system is. High confidence can act and log it, medium confidence waits for
            a human, low confidence only raises an alert. That is the whole idea in one line: the more
            uncertain the system, the more it defers to you.
          </P>

          <H2 id="principles">Twelve principles, three tiers</H2>
          <div className="mb-6 space-y-4">
            {TIERS.map((t) => (
              <div key={t.tier} className="rounded-xl border border-border bg-card/50 p-5">
                <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="text-lg font-semibold">{t.tier}</h3>
                  <span className="rounded-full border border-border px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                    {t.rule}
                  </span>
                </div>
                <ul className="grid gap-2 sm:grid-cols-2">
                  {t.principles.map((p) => (
                    <li key={p} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="mt-1 h-1.5 w-1.5 flex-none rounded-full bg-primary" aria-hidden="true" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <P>
            Tier 1 is absolute. A proposal that would break a Tier 1 principle is refused outright, no
            confidence score can override it. Tier 2 is where human approval lives. Tier 3 shapes how
            the system learns from what happened.
          </P>

          <H2 id="matrix">Graduated trust</H2>
          <P>
            Confidence is a blend of the model's own certainty, how similar past incidents were resolved,
            and the historical success rate of the proposed fix. That single score decides the path:
          </P>
          <div className="mb-6 overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-card/70 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-semibold">Confidence</th>
                  <th className="px-4 py-3 font-semibold">Action</th>
                  <th className="px-4 py-3 font-semibold">Human review</th>
                </tr>
              </thead>
              <tbody>
                {MATRIX.map((row) => (
                  <tr key={row.confidence} className="border-t border-border">
                    <td className="px-4 py-3 font-medium text-foreground">{row.confidence}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.action}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.review}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <H2 id="fail-closed">Fail closed by default</H2>
          <P>
            Action tools that restart or scale services are off unless you turn them on. The master
            switch <Code>AIOPS_ENABLE_ACTION_TOOLS</Code> defaults to false, and only containers on an
            explicit allowlist can ever be touched. A fresh install cannot change your infrastructure by
            accident. You opt in, deliberately, and you choose the mode: diagnose only, approve every
            action, or allow automatic action within the gate.
          </P>

          <H2 id="audit">Approve, reject, and a full audit trail</H2>
          <P>
            When a proposal needs sign-off it appears as an approve-or-reject card in chat, with the
            reasoning and the constitutional verdict attached. Every attempt, approved or blocked, is
            written to an audit log. Nothing acts silently, and nothing is unaccounted for. The same gate
            applies to anything scripted through the API, so automation cannot route around it.
          </P>

          <div className="mb-2 mt-8 flex flex-wrap gap-3">
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

          <P>
            Want the wider picture? Head back to the{' '}
            <a href="/" className="font-medium text-primary hover:underline">home page</a> for the
            feature and architecture overview.
          </P>
        </article>
      </main>

      <TeamFooter />
    </div>
  )
}
