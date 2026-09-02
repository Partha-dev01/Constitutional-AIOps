import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, BookOpen, Code2, ExternalLink } from 'lucide-react'

/**
 * In-app documentation for signed-in users. Renders inside the app shell
 * (Layout provides the sidebar + main), so this component is just the article
 * body with a sticky table of contents. Content mirrors the public marketing
 * docs but is tailored for someone already inside the app: each interface entry
 * links to its real route, and the interactive API reference points at the
 * backend Swagger console served at /docs (same origin, routed to the backend
 * by the edge). Fully static — no API calls.
 */

// The self-host section is only meaningful on the open-source / self-host build.
const SHOW_SELFHOST = (import.meta.env.VITE_SHOW_SELFHOST as string | undefined) === 'true'

// ── markdown-style prose primitives (no typography plugin in this project) ──
function H2({ id, children }: { id: string; children: ReactNode }) {
  return (
    <h2
      id={id}
      className="scroll-mt-24 mt-12 mb-4 border-b border-border pb-2 text-2xl font-bold tracking-tight"
    >
      {children}
    </h2>
  )
}
function P({ children }: { children: ReactNode }) {
  return <p className="mb-4 max-w-3xl leading-relaxed text-muted-foreground">{children}</p>
}
function UL({ children }: { children: ReactNode }) {
  return (
    <ul className="mb-4 max-w-3xl list-disc space-y-1.5 pl-6 text-muted-foreground">{children}</ul>
  )
}
function Code({ children }: { children: ReactNode }) {
  return (
    <code className="rounded bg-card px-1.5 py-0.5 font-mono text-[0.85em] text-primary">
      {children}
    </code>
  )
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

// Each screen links to its real in-app route so the docs double as navigation.
const SCREENS: { name: string; href: string; body: string }[] = [
  { name: 'Dashboard', href: '/', body: 'Live agent status, real service health and open incidents at a glance, plus a live per-service metrics band.' },
  { name: 'Command Center', href: '/console', body: 'A live operations console with per-service quick actions; read-only actions prefill a scoped question, mutating ones route through the approval card.' },
  { name: 'Chat', href: '/chat', body: 'Ask about an incident; approve or reject the agent’s proposed remediation inline.' },
  { name: 'Incidents', href: '/incidents', body: 'Every detected incident with severity, a timeline and suggested actions.' },
  { name: 'Telemetry', href: '/telemetry', body: 'The logs and metrics flowing in — from your observability stack, or from the local Docker socket on the lite tier.' },
  { name: 'Metrics', href: '/metrics', body: 'Prometheus-backed metric history for the platform.' },
  { name: 'Graph', href: '/graph', body: 'Explore the episodic-memory graph of episodes, services and root causes.' },
  { name: 'Infrastructure', href: '/infrastructure', body: 'Real container health, plus the demo and chaos controls when enabled.' },
  { name: 'Agents', href: '/agents', body: 'Watch the fast and reasoning agents’ inputs, outputs and the model each one runs on.' },
  { name: 'MCP Tools', href: '/mcp', body: 'The Model Context Protocol tools the agents may call.' },
  { name: 'Benchmark', href: '/benchmark', body: 'Run the annotation and root-cause benchmarks against your own endpoint.' },
  { name: 'Settings', href: '/settings', body: 'Set the model endpoint and key, connect monitoring, edit or auto-generate the platform topology, and manage your account.' },
]

export function Docs() {
  return (
    <div className="min-w-0">
      <div className="mb-8 max-w-3xl">
        <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
          <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
          Documentation
        </span>
        <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">
          Everything you can do here
        </h1>
        <p className="mt-3 text-lg text-muted-foreground">
          Point the app at your own model and monitoring, a tour of each screen, and an
          interactive API reference for scripting anything the UI can do.
        </p>
      </div>

      <div className="grid gap-10 lg:grid-cols-[200px_1fr]">
        {/* Sticky table of contents */}
        <nav aria-label="Contents" className="hidden lg:block">
          <div className="sticky top-6">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              On this page
            </p>
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

          <H2 id="quick-start">Quick start</H2>
          <P>You are already signed in. Two steps get you to a fully working instance:</P>
          <ol className="mb-4 max-w-3xl list-decimal space-y-3 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Point it at a model.</span> Set any
              OpenAI-compatible endpoint and API key in{' '}
              <Link to="/settings" className="font-medium text-primary hover:underline">Settings</Link>.
              No GPU is needed for the lite stack.
            </li>
            <li>
              <span className="font-semibold text-foreground">Explore and drive it.</span> Walk
              through each screen below, then use the interactive API reference to script anything
              the UI can do.
            </li>
          </ol>
          <div className="mb-2 mt-6 flex flex-wrap gap-3">
            <Link
              to="/settings"
              className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              Open Settings
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
            </Link>
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
              <span className="font-medium text-foreground">Test connection</span> to verify it live.
            </li>
            <li>
              Minimal setup: point both the fast and reasoning agents at the{' '}
              <span className="font-medium text-foreground">same</span> endpoint and model. No GPU is
              required for the lite stack.
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
            wizard live-tests each one.
          </P>
          <P>
            On the lite tier, which ships without an observability stack, turn on the{' '}
            <span className="font-medium text-foreground">Local Docker socket</span> source in the
            same panel: the app then reads live per-container CPU, memory and logs straight from the
            Docker socket, so the{' '}
            <Link to="/telemetry" className="font-medium text-primary hover:underline">Telemetry</Link>{' '}
            and{' '}
            <Link to="/" className="font-medium text-primary hover:underline">Dashboard</Link>{' '}
            screens show real data with no LGTM stack required. With nothing connected the app still
            runs; it simply shows no live service telemetry.
          </P>

          <H2 id="interface">The interface</H2>
          <P>Every screen, and what it is for — select one to jump straight to it:</P>
          <dl className="mb-4 grid max-w-3xl gap-3 sm:grid-cols-2">
            {SCREENS.map((s) => (
              <Link
                key={s.name}
                to={s.href}
                className="group rounded-lg border border-border bg-card/50 p-4 transition-colors hover:border-primary/50 hover:bg-card"
              >
                <dt className="flex items-center justify-between font-semibold text-foreground">
                  {s.name}
                  <ArrowRight
                    className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                    aria-hidden="true"
                  />
                </dt>
                <dd className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.body}</dd>
              </Link>
            ))}
          </dl>

          <H2 id="api">Interactive API reference</H2>
          <P>
            Every endpoint the UI uses is documented in a live Swagger / OpenAPI console — try
            calls, read the schemas and script your own automation against your instance.
          </P>
          <div className="mb-4 flex flex-col items-start gap-4 rounded-xl border border-border bg-card/60 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                <Code2 className="h-5 w-5" aria-hidden="true" />
              </span>
              <p className="text-sm text-muted-foreground">
                Open the interactive Swagger / OpenAPI reference for this instance.
              </p>
            </div>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
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
        </article>
      </div>
    </div>
  )
}
