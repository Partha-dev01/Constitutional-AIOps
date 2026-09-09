import type { ReactNode } from 'react'
import { ArrowRight, Check, Github, Server } from 'lucide-react'
import { LandingHeader } from '../components/landing/LandingHeader'
import { TeamFooter } from '../components/landing/TeamFooter'
import { DEMO_URL } from '../config'

/**
 * Standalone public "Self-host vs hosted" page (served as /selfhost.html, a Vite
 * entry). Gated at build time: only linked from the header when
 * VITE_SHOW_SELFHOST=true (the public-source flip build). Helps a visitor choose
 * between the hosted demo and running the exact same stack themselves. Fully
 * static and public-safe, no network calls, honest (AGPL FOSS, no paid tier).
 */

const REPO_URL = 'https://github.com/Partha-dev01/Constitutional-AIOps'

// ── prose primitives (mirror Safety.tsx; no typography plugin in this project) ──
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

// Comparison rows. Kept honest: the hosted instance is a shared evaluation demo,
// not a paid, SLA-backed product tier.
const COMPARISON: { dimension: string; hosted: string; selfhost: string }[] = [
  {
    dimension: 'What it is',
    hosted: 'A shared, always-available demo of the live app',
    selfhost: 'The full stack running on your own box',
  },
  {
    dimension: 'Setup',
    hosted: 'Nothing to install, open and go',
    selfhost: 'One docker compose command',
  },
  {
    dimension: 'Cost',
    hosted: 'Free to explore; the shared box sleeps when idle',
    selfhost: 'Your own compute (lite runs on about 2GB RAM, no GPU) plus your model endpoint',
  },
  {
    dimension: 'Your data',
    hosted: 'Lives on the shared demo instance',
    selfhost: 'Never leaves your infrastructure',
  },
  {
    dimension: 'Model endpoint',
    hosted: 'Preconfigured for you',
    selfhost: 'Bring your own OpenAI-compatible endpoint (vLLM, Ollama, Bedrock, OpenAI)',
  },
  {
    dimension: 'Customization',
    hosted: 'Fixed build',
    selfhost: 'Full source, change anything under AGPL-3.0',
  },
  {
    dimension: 'Best for',
    hosted: 'Evaluating, demos, a quick look',
    selfhost: 'Production use, private infrastructure, data control',
  },
]

const STEPS: { title: string; body: string; code: string }[] = [
  {
    title: 'Clone the repository',
    body: 'One repo, no submodules.',
    code: 'git clone https://github.com/Partha-dev01/Constitutional-AIOps.git\ncd Constitutional-AIOps',
  },
  {
    title: 'Point it at your model',
    body: 'Any OpenAI-compatible endpoint. Both agents may share one URL and model.',
    code: 'cp .env.example .env\n#  FAST_AGENT_URL / REASONING_AGENT_URL\n#  FAST_AGENT_MODEL / REASONING_AGENT_MODEL\n#  LLM_API_KEY   (only if your endpoint needs one)',
  },
  {
    title: 'Start the lite stack',
    body: 'CPU only, no GPU, no Neo4j required.',
    code: 'docker compose -f docker/docker-compose.lite.yml up -d',
  },
  {
    title: 'Open the app',
    body: 'The full dashboard, chat, incidents and topology, on your own box.',
    code: '# http://localhost:3000',
  },
]

const NEEDS = [
  'No GPU required',
  'About 2GB RAM for the lite stack',
  'Docker and Docker Compose',
  'Any OpenAI-compatible model endpoint',
]

export function SelfHost() {
  return (
    <div className="relative min-h-screen overflow-x-hidden font-sans text-foreground">
      <div className="aurora" aria-hidden="true" />
      <LandingHeader />

      <main className="mx-auto max-w-3xl px-6 pb-16 pt-28 sm:pt-32">
        <div className="mb-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs font-medium text-muted-foreground">
            <Server className="h-3.5 w-3.5" aria-hidden="true" />
            Deploy
          </span>
          <h1 className="mt-4 text-4xl font-bold tracking-tight">Self-host or use the hosted demo</h1>
          <p className="mt-3 text-lg text-muted-foreground">
            Same software either way. Constitutional AIOps is AGPL open source with no paid tier. Try it
            instantly on the hosted demo, or run the exact same stack on your own infrastructure. This
            page helps you pick.
          </p>
        </div>

        <article className="min-w-0">
          <H2 id="two-ways">Two ways to run it</H2>
          <P>
            The hosted demo is the fastest way to see the product working. Self-hosting gives you the
            whole system on hardware you control, with your own model endpoint and your data staying
            put. Nothing is held back in the open-source build.
          </P>
          <div className="mb-6 overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-card/70 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-semibold">Dimension</th>
                  <th className="px-4 py-3 font-semibold">Hosted demo</th>
                  <th className="px-4 py-3 font-semibold">Self-host</th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON.map((row) => (
                  <tr key={row.dimension} className="border-t border-border align-top">
                    <td className="px-4 py-3 font-medium text-foreground">{row.dimension}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.hosted}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.selfhost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <H2 id="steps">Self-host in four steps</H2>
          <ol className="mb-6 space-y-4">
            {STEPS.map((step, i) => (
              <li key={step.title} className="rounded-xl border border-border bg-card/50 p-5">
                <div className="flex items-start gap-4">
                  <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold">{step.title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{step.body}</p>
                    <pre className="mt-3 overflow-x-auto rounded-lg border border-border/60 bg-background/80 p-3 text-xs leading-relaxed text-foreground">
                      <code>{step.code}</code>
                    </pre>
                  </div>
                </div>
              </li>
            ))}
          </ol>

          <H2 id="requirements">What you need</H2>
          <ul className="mb-6 grid gap-3 sm:grid-cols-2">
            {NEEDS.map((item) => (
              <li key={item} className="flex items-start gap-3 text-sm text-foreground">
                <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                  <Check className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
                {item}
              </li>
            ))}
          </ul>
          <P>
            The lite profile drops the GPU and heavy tracing stack, so a small CPU box is enough. Point
            <Code>FAST_AGENT_URL</Code> and <Code>REASONING_AGENT_URL</Code> at any endpoint you already
            run, and change it live later from Settings.
          </P>

          <H2 id="license">License</H2>
          <P>
            Constitutional AIOps is released under AGPL-3.0. You can run, study, modify and redistribute
            it freely. If you run a modified version as a network service, the AGPL asks you to share
            your changes with its users. There is no separate commercial or enterprise edition.
          </P>

          <div className="mb-2 mt-8 flex flex-wrap gap-3">
            <a
              href={DEMO_URL}
              className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              Try the hosted demo
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
            </a>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary"
            >
              <Github className="h-4 w-4" aria-hidden="true" />
              View the source
            </a>
          </div>

          <P>
            Want the wider picture? Head back to the{' '}
            <a href="/" className="font-medium text-primary hover:underline">home page</a>, or read the{' '}
            <a href="/opensource.html" className="font-medium text-primary hover:underline">open-source</a>{' '}
            overview.
          </P>
        </article>
      </main>

      <TeamFooter />
    </div>
  )
}
