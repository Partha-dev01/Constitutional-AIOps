import type { ReactNode } from 'react'
import {
  Activity,
  Boxes,
  GitGraph,
  MessageSquare,
  ShieldCheck,
  Gauge,
  Wrench,
  ScanLine,
  LayoutDashboard,
} from 'lucide-react'
import { PageShell, Pill, H2, P, CTARow } from '../components/prose'

/**
 * Standalone "Features" deep-dive (/features.html, a Vite entry). A grid of the
 * real capabilities plus two product screenshots that already ship in
 * public/screenshots. Fully static and public-safe, no network calls.
 */

const FEATURES: { icon: ReactNode; title: string; body: string }[] = [
  {
    icon: <Activity className="h-5 w-5" aria-hidden="true" />,
    title: 'Incident detection and triage',
    body: 'Telemetry is annotated as it arrives and grouped into incidents with a severity, so the signal that matters surfaces without hand-built alert rules for every case.',
  },
  {
    icon: <ScanLine className="h-5 w-5" aria-hidden="true" />,
    title: 'Root-cause analysis',
    body: 'The reasoning agent works from logs, metrics and traces together to name a likely cause and show the evidence behind it, not just a symptom.',
  },
  {
    icon: <GitGraph className="h-5 w-5" aria-hidden="true" />,
    title: 'Graph-episodic memory',
    body: 'Past incidents live in a Neo4j graph. New problems are read against how similar ones actually resolved, and that history feeds the confidence score.',
  },
  {
    icon: <MessageSquare className="h-5 w-5" aria-hidden="true" />,
    title: 'Chat-driven remediation',
    body: 'Ask what is wrong and act on it in the same conversation. Fixes appear as approve-or-reject cards with the reasoning and the safety verdict attached.',
  },
  {
    icon: <ShieldCheck className="h-5 w-5" aria-hidden="true" />,
    title: 'Constitutional safety gate',
    body: 'Twelve principles across three tiers and a graduated-trust matrix decide whether an action runs, waits for a human, or only raises an alert.',
  },
  {
    icon: <Gauge className="h-5 w-5" aria-hidden="true" />,
    title: 'Full observability stack',
    body: 'Loki, Grafana, Tempo and Prometheus ship in the box, fed by an OpenTelemetry collector, so the data the agents reason over is the same data you can inspect.',
  },
  {
    icon: <Wrench className="h-5 w-5" aria-hidden="true" />,
    title: 'Tools over MCP',
    body: 'Remediation actions are exposed as tools, reachable over the Model Context Protocol, and every destructive one is fail-closed until you enable it.',
  },
  {
    icon: <Boxes className="h-5 w-5" aria-hidden="true" />,
    title: 'Benchmark harness',
    body: 'A built-in harness scores a model against a labelled evaluation set, so you can measure any endpoint you point the app at rather than trust a number.',
  },
  {
    icon: <LayoutDashboard className="h-5 w-5" aria-hidden="true" />,
    title: 'Service-aware UI',
    body: 'Dashboard, incidents, graph explorer, infrastructure and telemetry views are wired to the live services, with a no-login demo that runs on fixture data.',
  },
]

const SHOTS: { src: string; caption: string }[] = [
  { src: '/screenshots/incidents.png', caption: 'Incidents, grouped and ranked by severity' },
  { src: '/screenshots/graph-explorer.png', caption: 'The episodic graph of related incidents' },
]

export function Features() {
  return (
    <PageShell
      maxWidth="6xl"
      pill={<Pill icon={<Boxes className="h-3.5 w-3.5" aria-hidden="true" />}>Features</Pill>}
      title="What it does"
      lead="An autonomous operations assistant that watches your telemetry, explains what broke, and proposes a fix you can trust. The capabilities below are the real surface of the product."
    >
      <section>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-border bg-card/50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-primary">
                {f.icon}
              </div>
              <h3 className="mb-1.5 text-base font-semibold">{f.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <H2 id="screens">Seen in the app</H2>
      <P>These are real screens from the product, not mock-ups. The demo runs the same UI on fixture data.</P>
      <div className="grid gap-6 md:grid-cols-2">
        {SHOTS.map((shot) => (
          <figure key={shot.src} className="m-0">
            <div className="shot-frame">
              <img src={shot.src} alt={shot.caption} loading="lazy" className="block w-full" />
            </div>
            <figcaption className="mt-2 text-center text-xs text-muted-foreground">{shot.caption}</figcaption>
          </figure>
        ))}
      </div>

      <P>
        Curious how the pieces fit together? The{' '}
        <a href="/architecture.html" className="font-medium text-primary hover:underline">architecture page</a>{' '}
        walks the full telemetry-to-fix path.
      </P>

      <CTARow />
    </PageShell>
  )
}
