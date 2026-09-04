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
      </main>

      <TeamFooter />
    </div>
  )
}
