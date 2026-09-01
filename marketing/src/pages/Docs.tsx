import type { ReactNode } from 'react'
import { ArrowRight, BookOpen, Code2, ExternalLink } from 'lucide-react'
import { LandingHeader } from '../components/landing/LandingHeader'
import { TeamFooter } from '../components/landing/TeamFooter'
import { APP_URL, DEMO_URL, SHOW_SELFHOST, appPath } from '../config'

/**
 * Standalone documentation page (served as /docs.html — a second Vite entry, so
 * it is a real page under the landing, not an in-page section). Reuses the
 * landing header/footer for a consistent shell; the body is markdown-style
 * prose with a sticky table of contents. Fully static and public-safe.
 */

// ── markdown-style prose primitives (no typography plugin in this project) ──
function H2({ id, children }: { id: string; children: ReactNode }) {
  return (
    <h2 id={id} className="scroll-mt-24 mt-14 mb-4 border-b border-border pb-2 text-2xl font-bold tracking-tight">
      {children}
    </h2>
  )
}
function H3({ children }: { children: ReactNode }) {
  return <h3 className="mt-6 mb-2 text-lg font-semibold">{children}</h3>
}
function P({ children }: { children: ReactNode }) {
  return <p className="mb-4 max-w-3xl leading-relaxed text-muted-foreground">{children}</p>
}
function UL({ children }: { children: ReactNode }) {
  return <ul className="mb-4 max-w-3xl list-disc space-y-1.5 pl-6 text-muted-foreground">{children}</ul>
}
function Code({ children }: { children: ReactNode }) {
  return <code className="rounded bg-card px-1.5 py-0.5 font-mono text-[0.85em] text-primary">{children}</code>
}

const TOC: { id: string; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'quick-start', label: 'Quick start' },
  { id: 'configure-model', label: 'Configure your model' },
  { id: 'monitoring', label: 'Connect monitoring' },
  { id: 'interface', label: 'The interface' },
  { id: 'api', label: 'API reference' },
  ...(SHOW_SELFHOST ? [{ id: 'self-host', label: 'Self-host' }] : []),
]

const SCREENS: { name: string; body: string }[] = [
  { name: 'Dashboard', body: 'Live agent status, real service health and open incidents at a glance.' },
  { name: 'Chat', body: 'Ask about an incident; approve or reject the agent’s proposed remediation inline.' },
  { name: 'Agents', body: 'Watch the fast and reasoning agents’ inputs, outputs and the model each one runs on.' },
  { name: 'Graph explorer', body: 'Explore the episodic-memory graph of episodes, services and root causes.' },
  { name: 'Incidents', body: 'Every detected incident with severity, a timeline and suggested actions.' },
  { name: 'Infrastructure', body: 'Real container health, plus the demo and chaos controls when enabled.' },
  { name: 'Metrics & Telemetry', body: 'Prometheus-backed metrics and the logs, metrics and traces flowing in via OpenTelemetry.' },
  { name: 'Topology & Settings', body: 'Set the model endpoint and key, live-test it, and edit or auto-generate the platform topology.' },
  { name: 'Benchmark', body: 'Run the annotation and root-cause benchmarks against your own endpoint.' },
  { name: 'Console & MCP tools', body: 'A live operations console, and the Model Context Protocol tools the agents may call.' },
]

export function Docs() {
  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-foreground">
      <div className="aurora" aria-hidden="true" />
      <LandingHeader />

      <main className="mx-auto max-w-6xl px-6 pb-16 pt-28 sm:pt-32">
        <div className="mb-10 max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
            Documentation
          </span>
          <h1 className="mt-4 text-4xl font-bold tracking-tight">Get started, then use every function</h1>
          <p className="mt-3 text-lg text-muted-foreground">
            Three steps to a running instance, how to point it at your own model and monitoring,
            a tour of each screen, and an interactive API reference.
          </p>
        </div>

        <div className="grid gap-10 lg:grid-cols-[210px_1fr]">
          {/* Sticky table of contents */}
          <nav aria-label="Contents" className="hidden lg:block">
            <div className="sticky top-24">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">On this page</p>
              <ul className="space-y-2 border-l border-border">
                {TOC.map((t) => (
                  <li key={t.id}>
                    <a
                      href={`#${t.id}`}
                      className="-ml-px block border-l border-transparent pl-4 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
                    >
                      {t.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </nav>

          {/* Content */}
          <article className="min-w-0">
            <H2 id="overview">Overview</H2>
            <P>
              Constitutional AIOps is an autonomous infrastructure-operations assistant. A fast
              agent annotates telemetry while a reasoning agent performs root-cause analysis and
              proposes remediation, and every action passes a 12-principle Constitutional AI safety
              gate before anything runs. Incidents, root causes and services are correlated in a
              Neo4j graph-episodic memory.
            </P>
            <P>
              You can try the whole interface with no login in{' '}
              <a href={DEMO_URL} className="font-medium text-primary hover:underline">Demo mode</a>,
              which runs the real UI on bundled sample data.
            </P>

            <H2 id="quick-start">Quick start</H2>
            <P>Three steps take you from nothing to a running instance:</P>
            <ol className="mb-4 max-w-3xl list-decimal space-y-3 pl-6 text-muted-foreground">
              <li>
                <span className="font-semibold text-foreground">Get in.</span> Sign in to your
                instance, or open Demo mode to explore the real UI on sample data with no login.
              </li>
              <li>
                <span className="font-semibold text-foreground">Point it at a model.</span> Set any
                OpenAI-compatible endpoint and API key in Settings. No GPU is needed for the lite
                stack.
              </li>
              <li>
                <span className="font-semibold text-foreground">Explore and drive it.</span> Walk
                through each screen below, then use the interactive API reference to script anything
                the UI can do.
              </li>
            </ol>
            <div className="mb-2 mt-6 flex flex-wrap gap-3">
              <a
                href={APP_URL}
                className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Sign in
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </a>
              <a
                href={DEMO_URL}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary"
              >
                Open Demo mode
              </a>
            </div>

            <H2 id="configure-model">Configure your model</H2>
            <P>
              Constitutional AIOps is bring-your-own-endpoint. It talks to any OpenAI-compatible
              chat-completions API, so you can point it at a hosted provider or a local server.
            </P>
            <UL>
              <li>
                Open <Code>Settings → Models</Code> and set the endpoint URL, model name and API key
                for the reasoning agent (and the fast agent, if separate). Use{' '}
                <span className="font-medium text-foreground">Test connection</span> to verify it
                live.
              </li>
              <li>
                Minimal setup: point both the fast and reasoning agents at the{' '}
                <span className="font-medium text-foreground">same</span> endpoint and model. No GPU
                is required for the lite stack.
              </li>
              <li>
                The same key powers the AI features, including{' '}
                <Code>Settings → Topology Schema → Generate topology with AI</Code>, which asks your
                reasoning model to draft a platform topology.
              </li>
            </UL>

            <H2 id="monitoring">Connect monitoring</H2>
            <P>
              Under <Code>Settings → Telemetry</Code> you can connect your observability sources —
              Loki for logs, Prometheus for metrics and Tempo for traces — by URL, and the setup
              wizard live-tests each one. With nothing connected the app still runs; it simply shows
              no live service telemetry (the lite tier ships without an observability stack).
            </P>

            <H2 id="interface">The interface</H2>
            <P>Every screen, and what it is for:</P>
            <dl className="mb-4 max-w-3xl space-y-3">
              {SCREENS.map((s) => (
                <div key={s.name} className="rounded-lg border border-border bg-card/50 p-4">
                  <dt className="font-semibold">{s.name}</dt>
                  <dd className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.body}</dd>
                </div>
              ))}
            </dl>

            <H2 id="api">Interactive API reference</H2>
            <P>
              Every endpoint the UI uses is documented in a live Swagger / OpenAPI console — try
              calls, read the schemas and script your own automation. It runs on your instance, so
              opening it wakes the app first if it is asleep.
            </P>
            <div className="mb-4 flex flex-col items-start gap-4 rounded-xl border border-border bg-card/60 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                  <Code2 className="h-5 w-5" aria-hidden="true" />
                </span>
                <p className="text-sm text-muted-foreground">
                  Open the interactive Swagger / OpenAPI reference for your instance.
                </p>
              </div>
              <a
                href={appPath('/docs')}
                className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
              >
                Open the API reference
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
              </a>
            </div>

            {SHOW_SELFHOST && (
              <>
                <H2 id="self-host">Self-host</H2>
                <P>
                  Constitutional AIOps is open source. Clone the repository, copy the example
                  environment file, point it at your model endpoint and bring the stack up with a
                  single <Code>docker compose</Code> command. See the repository README for the full
                  walkthrough and the AGPL-3.0 licence.
                </P>
              </>
            )}

            <H3>Need the landing page?</H3>
            <P>
              Head back to the <a href="/" className="font-medium text-primary hover:underline">home page</a>{' '}
              for the feature and architecture overview.
            </P>
          </article>
        </div>
      </main>

      <TeamFooter />
    </div>
  )
}
