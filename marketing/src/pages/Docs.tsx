import type { ReactNode } from 'react'
import { ArrowRight, BookOpen } from 'lucide-react'
import { LandingHeader } from '../components/landing/LandingHeader'
import { TeamFooter } from '../components/landing/TeamFooter'
import { APP_URL, DEMO_URL, SHOW_SELFHOST } from '../config'

/**
 * Standalone public documentation page (served as /docs.html — a second Vite
 * entry). Deliberately minimal: it says what the product is and how to get in,
 * then points to the full page-by-page guide and interactive API reference,
 * which both live inside the app behind sign-in. Keeping the public surface
 * small avoids handing the whole manual to scrapers. Fully static and public-safe.
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
function Code({ children }: { children: ReactNode }) {
  return <code className="rounded bg-card px-1.5 py-0.5 font-mono text-[0.85em] text-primary">{children}</code>
}

export function Docs() {
  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-foreground">
      <div className="aurora" aria-hidden="true" />
      <LandingHeader />

      <main className="mx-auto max-w-3xl px-6 pb-16 pt-28 sm:pt-32">
        <div className="mb-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
            Documentation
          </span>
          <h1 className="mt-4 text-4xl font-bold tracking-tight">Get started</h1>
          <p className="mt-3 text-lg text-muted-foreground">
            What Constitutional AIOps is and how to get in. The full page-by-page guide and the
            interactive API reference live inside the app once you sign in.
          </p>
        </div>

        <article className="min-w-0">
          <H2 id="overview">Overview</H2>
          <P>
            Constitutional AIOps is an autonomous infrastructure-operations assistant. A fast agent
            annotates telemetry while a reasoning agent performs root-cause analysis and proposes
            remediation, and every action passes a 12-principle Constitutional AI safety gate before
            anything runs.
          </P>
          <P>
            You can try the whole interface with no login in{' '}
            <a href={DEMO_URL} className="font-medium text-primary hover:underline">Demo mode</a>,
            which runs the real UI on bundled sample data.
          </P>

          <H2 id="quick-start">Quick start</H2>
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
              <span className="font-semibold text-foreground">Drive it.</span> The in-app guide walks
              through every screen, and the interactive API reference lets you script anything the UI
              can do.
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

          <H2 id="interface">Inside the app</H2>
          <P>
            The sidebar groups every screen by what you are doing. Here is the whole interface at a
            glance. The in-app guide covers each screen in depth once you sign in.
          </P>

          <H3>Overview</H3>
          <ul className="mb-4 max-w-3xl list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Dashboard.</span> Live system health,
              open incidents, and recent telemetry in one place, with the agents' status up front.
            </li>
          </ul>

          <H3>Operate</H3>
          <ul className="mb-4 max-w-3xl list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Command Center.</span> The cockpit:
              chat, the service topology, and live metrics side by side on a single pane.
            </li>
            <li>
              <span className="font-semibold text-foreground">Incidents.</span> Triage what is
              firing, read the root-cause analysis, and act on the suggested remediation.
            </li>
            <li>
              <span className="font-semibold text-foreground">Chat.</span> Ask the reasoning agent
              anything. Any action it proposes queues for your approval before it runs.
            </li>
          </ul>

          <H3>Observe</H3>
          <ul className="mb-4 max-w-3xl list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Telemetry.</span> Logs, metrics, and
              traces as they stream in, correlated across the stack.
            </li>
            <li>
              <span className="font-semibold text-foreground">Metrics.</span> Latency, throughput,
              and resource charts for every service.
            </li>
            <li>
              <span className="font-semibold text-foreground">Graph.</span> The episodic-memory graph
              explorer: past incidents and how they relate.
            </li>
            <li>
              <span className="font-semibold text-foreground">Infrastructure.</span> The services,
              hosts, and containers under management.
            </li>
          </ul>

          <H3>AI</H3>
          <ul className="mb-4 max-w-3xl list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Local Model.</span> A private chat that
              runs a model in your browser, with no backend call.
            </li>
            <li>
              <span className="font-semibold text-foreground">Agents.</span> The fast and reasoning
              agents, their models, and whether each is online.
            </li>
            <li>
              <span className="font-semibold text-foreground">MCP Tools.</span> The catalog of tools
              the agents can call, each gated by the constitution.
            </li>
            <li>
              <span className="font-semibold text-foreground">Benchmark.</span> The evaluation
              harness and the accuracy results behind the numbers on the home page.
            </li>
          </ul>

          <H3>Admin</H3>
          <ul className="mb-4 max-w-3xl list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Settings.</span> Point the app at your
              model endpoints, bring your own API keys, and choose how much autonomy remediation gets.
            </li>
            <li>
              <span className="font-semibold text-foreground">Notifications.</span> Wire up alerting
              over Telegram, Matrix, or a webhook, and run ChatOps from your chat app.
            </li>
            <li>
              <span className="font-semibold text-foreground">Audit Log.</span> Every action and
              every gate decision, recorded and searchable.
            </li>
            <li>
              <span className="font-semibold text-foreground">Docs.</span> The full page-by-page guide
              and the interactive API reference, in the app.
            </li>
          </ul>

          <H2 id="hosted-demo">Hosted demo and cold starts</H2>
          <P>
            The public demo runs on a small instance that sleeps when no one is using it, which
            keeps the running cost near zero. Two things follow from that, and both are by design:
          </P>
          <ul className="mb-4 max-w-3xl list-disc space-y-2 pl-6 text-muted-foreground">
            <li>
              <span className="font-semibold text-foreground">Demo mode is instant.</span> It runs
              the real interface on bundled sample data with no backend, so it never waits on
              anything.
            </li>
            <li>
              <span className="font-semibold text-foreground">The full app wakes on your first
              visit.</span> If the box has gone to sleep, opening it starts the instance and shows a
              short holding page while the services come up, usually under a minute. Once it is warm
              everything responds normally until it goes idle again.
            </li>
          </ul>
          <P>
            So a slow first load after a quiet period is the wake-up, not an error. Give the holding
            page a moment to hand off and you are in.
            {SHOW_SELFHOST &&
              ' A self-hosted instance you run yourself stays on, so it has no sleep step and no cold start.'}
          </P>

          {SHOW_SELFHOST && (
            <>
              <H2 id="self-host">Self-host</H2>
              <P>
                Constitutional AIOps is open source. Clone the repository, copy the example
                environment file, point it at your model endpoint and bring the stack up with a
                single <Code>docker compose</Code> command. See the repository README for the full
                walkthrough and the AGPL-3.0 licence.
              </P>
              <P>
                Self-hosting also settles the hosting question: the public demo sleeps to stay
                cheap, but an instance you run is always on, with your own data and your own model
                endpoint and no cold-start wait.
              </P>
            </>
          )}

          <H3>Need the landing page?</H3>
          <P>
            Head back to the <a href="/" className="font-medium text-primary hover:underline">home page</a>{' '}
            for the feature and architecture overview.
          </P>
        </article>
      </main>

      <TeamFooter />
    </div>
  )
}
