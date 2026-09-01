import { useState } from 'react'
import { BookOpen, ChevronDown, Code2, ExternalLink } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { ShotFrame } from './ShotFrame'
import { APP_URL, DEMO_URL, DOCS_URL } from '../../config'

interface Step {
  n: number
  title: string
  body: string
}

const STEPS: Step[] = [
  {
    n: 1,
    title: 'Get in',
    body: 'Sign in to your instance, or open Demo mode to explore the real UI on sample data with no login.',
  },
  {
    n: 2,
    title: 'Point it at a model',
    body: 'Self-hosting? Set any OpenAI-compatible endpoint and key in Settings. No GPU needed for the lite stack.',
  },
  {
    n: 3,
    title: 'Explore and drive it',
    body: 'Walk through each function below, then use the interactive API reference to script anything the UI does.',
  },
]

interface Fn {
  key: string
  title: string
  shot: string
  how: string
}

/**
 * Each function paired with a real product screenshot. Screenshots live in
 * marketing/public/screenshots. If one is ever missing the frame simply shows
 * empty rather than breaking the page.
 */
const FUNCTIONS: Fn[] = [
  { key: 'dashboard', title: 'Dashboard', shot: '/screenshots/dashboard.png', how: 'Live agent status, real service health and open incidents at a glance.' },
  { key: 'chat', title: 'Chat', shot: '/screenshots/chat.png', how: 'Ask about an incident; approve or reject the agent’s proposed remediation inline.' },
  { key: 'agents', title: 'Agents', shot: '/screenshots/agent-hub.png', how: 'Watch the fast and reasoning agents’ inputs, outputs and configured models.' },
  { key: 'graph', title: 'Graph explorer', shot: '/screenshots/graph-explorer.png', how: 'Explore the episodic-memory graph of episodes, services and root causes.' },
  { key: 'incidents', title: 'Incidents', shot: '/screenshots/incidents.png', how: 'Every detected incident with severity, a timeline and suggested actions.' },
  { key: 'infrastructure', title: 'Infrastructure', shot: '/screenshots/infrastructure.png', how: 'Real container health, plus the demo and chaos controls when enabled.' },
  { key: 'metrics', title: 'Metrics', shot: '/screenshots/metrics.png', how: 'Prometheus-backed metrics alongside the app’s own latency and token stats.' },
  { key: 'telemetry', title: 'Telemetry', shot: '/screenshots/telemetry.png', how: 'Logs, metrics and traces flowing in through OpenTelemetry.' },
  { key: 'settings', title: 'Topology and settings', shot: '/screenshots/settings.png', how: 'Configure the model endpoint, or edit and live-sync the platform topology.' },
  { key: 'benchmark', title: 'Benchmark', shot: '/screenshots/benchmark.png', how: 'Run the annotation and root-cause benchmarks against your own endpoint.' },
  { key: 'console', title: 'Console', shot: '/screenshots/console.png', how: 'A live operations console over the running stack.' },
  { key: 'mcp', title: 'MCP tools', shot: '/screenshots/mcp.png', how: 'The Model Context Protocol tools the agents are allowed to call.' },
]

/**
 * In-page documentation: a short get-started, a per-function walkthrough where
 * each function reveals its own screenshot on click (kept collapsed so the page
 * stays light), and a link to the interactive Swagger / OpenAPI reference. Fully
 * self-contained and public-safe (no repository or external docs-site link).
 */
export function DocsSection() {
  const { ref, visible } = useReveal<HTMLDivElement>()
  const [open, setOpen] = useState<string>(FUNCTIONS[0].key)

  return (
    <section id="docs" className="border-b border-border py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
            Docs
          </span>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
            Get started, then use every function
          </h2>
          <p className="mt-4 text-muted-foreground">
            Three steps to a running instance, a guided tour of each screen, and an
            interactive API reference for everything the UI can do.
          </p>
        </div>

        {/* Get started */}
        <div className="mb-14 grid gap-4 sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.n} className="rounded-xl border border-border bg-card/60 p-5">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary">
                {step.n}
              </span>
              <h3 className="mt-3 font-semibold">{step.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{step.body}</p>
            </div>
          ))}
        </div>
        <div className="mb-16 flex flex-wrap justify-center gap-3">
          <a
            href={APP_URL}
            className="inline-flex items-center justify-center rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Sign in
          </a>
          <a
            href={DEMO_URL}
            className="inline-flex items-center justify-center rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary"
          >
            Open Demo mode
          </a>
        </div>

        {/* Per-function walkthrough: click a function to reveal its screenshot */}
        <div
          ref={ref}
          className={`reveal${visible ? ' reveal-visible' : ''} grid gap-8 lg:grid-cols-5`}
        >
          <ul className="lg:col-span-2 space-y-1.5">
            {FUNCTIONS.map((fn) => {
              const isOpen = open === fn.key
              return (
                <li key={fn.key}>
                  <button
                    type="button"
                    onClick={() => setOpen(fn.key)}
                    aria-expanded={isOpen}
                    className={`flex w-full items-center justify-between gap-3 rounded-lg border px-4 py-3 text-left text-sm transition-colors ${
                      isOpen
                        ? 'border-primary/50 bg-primary/10 text-foreground'
                        : 'border-border bg-card/60 text-muted-foreground hover:border-primary/40 hover:text-foreground'
                    }`}
                  >
                    <span className="min-w-0">
                      <span className="block font-semibold">{fn.title}</span>
                      {isOpen && <span className="mt-1 block text-xs text-muted-foreground">{fn.how}</span>}
                    </span>
                    <ChevronDown
                      className={`h-4 w-4 shrink-0 transition-transform ${isOpen ? 'rotate-180 text-primary' : ''}`}
                      aria-hidden="true"
                    />
                  </button>
                </li>
              )
            })}
          </ul>

          <div className="lg:col-span-3">
            {FUNCTIONS.filter((fn) => fn.key === open).map((fn) => (
              <figure key={fn.key}>
                <ShotFrame src={fn.shot} alt={`Constitutional AIOps ${fn.title} screen`} />
                <figcaption className="mt-3 text-center text-sm text-muted-foreground">
                  {fn.title} — {fn.how}
                </figcaption>
              </figure>
            ))}
          </div>
        </div>

        {/* Interactive API reference (Swagger / OpenAPI) */}
        <div className="mt-16 flex flex-col items-start gap-4 rounded-xl border border-border bg-card/60 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
              <Code2 className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h3 className="font-semibold">Interactive API reference</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Every endpoint the UI uses, in a live Swagger / OpenAPI console. Try
                calls, read schemas, script your own automation.
              </p>
            </div>
          </div>
          <a
            href={DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Open the API reference
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  )
}
