import { Layers } from 'lucide-react'
import { PageShell, Pill, P, CTARow } from '../components/prose'

/**
 * Standalone "Use cases" page (/usecases.html, a Vite entry). Concrete
 * scenarios, each walked as symptom, what the system sees, proposed fix and how
 * the gate handles it. Fully static and public-safe, no network calls.
 */

const SCENARIOS: {
  tag: string
  title: string
  symptom: string
  sees: string
  fix: string
  gate: string
}[] = [
  {
    tag: 'Saturation',
    title: 'A database connection pool runs dry',
    symptom: 'API latency climbs and a service starts returning 503s under normal traffic.',
    sees: 'Rising error logs correlate with a maxed-out connection pool metric and a slow-query trace, all on the same service.',
    fix: 'Recycle the exhausted pool and flag the slow query for review, rather than restarting the whole service.',
    gate: 'Prefer-minimal-intervention keeps it to the pool. The action is reversible in seconds, so it can run with an audit entry.',
  },
  {
    tag: 'Cascade',
    title: 'A bad deploy ripples across services',
    symptom: 'One service degrades right after a release and two downstream services start timing out.',
    sees: 'The graph links the new incident to a past rollback with the same fingerprint, and traces show the blast radius spreading downstream.',
    fix: 'Roll the single offending service back to the last healthy version and hold the downstream ones steady.',
    gate: 'A change touching several services trips the tier-1 cascade limit, so it is held for a human to approve before anything moves.',
  },
  {
    tag: 'Drift',
    title: 'Configuration drifts after a change',
    symptom: 'A service behaves differently than staging with no code change, and nobody is sure what moved.',
    sees: 'The reasoning agent ties the behaviour change to a config value that no longer matches the expected baseline.',
    fix: 'Propose restoring the drifted setting, with the before-and-after shown in the approval card.',
    gate: 'Evidence-based-decisions means the proposal ships with the diff attached. You approve the exact change, not a black box.',
  },
  {
    tag: 'Triage',
    title: 'On-call at 3am',
    symptom: 'A pager fires and the on-call engineer has to figure out what is actually wrong, quickly.',
    sees: 'Chat summarises the incident, the likely cause, and the two most similar past incidents and how they were resolved.',
    fix: 'Suggest the remediation that worked last time, ready to run or to reject with one tap.',
    gate: 'Nothing acts without sign-off at this hour unless you have opted a specific tool into automatic mode. The trail is complete either way.',
  },
]

export function UseCases() {
  return (
    <PageShell
      maxWidth="5xl"
      pill={<Pill icon={<Layers className="h-3.5 w-3.5" aria-hidden="true" />}>Use cases</Pill>}
      title="What it looks like in practice"
      lead="Four situations an operations team runs into, and how the system reads each one. The pattern is always the same: it explains before it acts, and the gate decides what it is allowed to do on its own."
    >
      <div className="space-y-6">
        {SCENARIOS.map((s, i) => (
          <article key={s.title} className="rounded-xl border border-border bg-card/50 p-6">
            <div className="mb-4 flex flex-wrap items-baseline gap-3">
              <span className="rounded-full border border-border bg-background px-2.5 py-0.5 text-xs font-medium text-primary">
                {String(i + 1).padStart(2, '0')} · {s.tag}
              </span>
              <h2 className="text-xl font-semibold tracking-tight">{s.title}</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Symptom</div>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.symptom}</p>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">What it sees</div>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.sees}</p>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Proposed fix</div>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.fix}</p>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">At the gate</div>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.gate}</p>
              </div>
            </div>
          </article>
        ))}
      </div>

      <P>
        The rules behind the gate column are the{' '}
        <a href="/safety.html" className="font-medium text-primary hover:underline">twelve constitutional principles</a>.
      </P>

      <CTARow />
    </PageShell>
  )
}
