import { PageShell, H2, P, Code, Card, CTARow } from '../components/prose'

/**
 * Standalone public "Safety" page (served as /safety.html, a Vite entry). The
 * constitutional layer is the product's strongest differentiator, so it gets its
 * own page. Content is the real 12-principle / 3-tier framework and the graduated
 * -trust authorization matrix. Fully static and public-safe, no network calls.
 *
 * Uses the shared glass PageShell + prose primitives so it reads as one system
 * with the rest of the marketing site. tests/test_principles_docs.py fails if a
 * principle line here drifts from src/constitutional/principles.py.
 */

const TIERS: { tier: string; rule: string; principles: string[] }[] = [
  {
    tier: 'Tier 1: Safety critical',
    rule: 'Never violated',
    principles: [
      'Never execute actions that could cause data loss or corruption',
      'Never take destructive actions during active incidents without explicit approval',
      'Never exceed resource limits that could cause cascade failures',
      'Never modify security configurations',
    ],
  },
  {
    tier: 'Tier 2: Operational',
    rule: 'Require approval',
    principles: [
      'Prefer the smallest effective action to resolve issues',
      'Require telemetry evidence before taking action',
      'Log all actions for audit and rollback capability',
      'Escalate to humans when confidence is below threshold',
    ],
  },
  {
    tier: 'Tier 3: Learning',
    rule: 'Soft guidelines',
    principles: [
      'Track outcomes of actions for continuous improvement',
      'Learn from human corrections and overrides',
      'Optimize for long-term system health over short-term fixes',
      'Occasionally explore alternative solutions to prevent local optima',
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
    <PageShell
      title="The constitutional layer"
      lead="An AIOps system that can act on your infrastructure needs a reason to be trusted. Every proposed action here passes a fixed set of principles and a graduated-trust gate before anything runs, and every decision is recorded."
    >
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
            <Card key={t.tier}>
              <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-lg font-semibold">{t.tier}</h3>
                <span className="rounded-full bg-white/[0.06] px-2.5 py-0.5 text-xs font-medium text-muted-foreground ring-1 ring-inset ring-white/10">
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
            </Card>
          ))}
        </div>
        <P>
          Tier 1 is absolute and no confidence score can override it. A proposal that would break a
          Tier 1 principle is refused outright. The one way through is written into the second
          principle itself: a destructive action during an active incident waits for an admin to
          approve it. Tier 2 is where the rest of human approval lives. Tier 3 shapes how the system
          learns from what happened.
        </P>

        <H2 id="matrix">Graduated trust</H2>
        <P>
          Confidence is a blend of the model's own certainty, how similar past incidents were resolved,
          and the historical success rate of the proposed fix. That single score decides the path:
        </P>
        <div className="glass mb-6 overflow-x-auto rounded-xl">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/[0.04] text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-semibold">Confidence</th>
                <th className="px-4 py-3 font-semibold">Action</th>
                <th className="px-4 py-3 font-semibold">Human review</th>
              </tr>
            </thead>
            <tbody>
              {MATRIX.map((row) => (
                <tr key={row.confidence} className="border-t border-white/10">
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

        <CTARow />

        <P>
          Want the wider picture? Head back to the{' '}
          <a href="/" className="font-medium text-primary hover:underline">home page</a> for the
          feature and architecture overview.
        </P>
      </article>
    </PageShell>
  )
}
