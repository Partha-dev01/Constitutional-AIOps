import { ArrowRight, Check } from 'lucide-react'
import { PageShell, H2, P, Code } from '../components/prose'
import { GlassCard, CtaButton } from '../components/ui'
import { DEMO_URL } from '../config'

/**
 * The GitHub mark, inline.
 *
 * lucide-react dropped every brand icon in v1, so the old `Github` import no
 * longer exists. This is the one brand mark the marketing site uses, and it
 * labels a link that goes to GitHub specifically, so a generic substitute would
 * say less. Inlining it also matches how the rest of this site handles assets:
 * no extra dependency for a single glyph.
 *
 * Sized and coloured by className exactly like a lucide icon, so the call site
 * is unchanged.
 */
function GithubMark({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M12 .5C5.73.5.5 5.73.5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.12 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.41-5.25 5.69.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
    </svg>
  )
}

/**
 * Standalone public "Self-host vs hosted" page (served as /selfhost.html, a Vite
 * entry). Gated at build time: only linked from the header when
 * VITE_SHOW_SELFHOST=true (the public-source flip build). Helps a visitor choose
 * between the hosted demo and running the exact same stack themselves. Fully
 * static and public-safe, no network calls, honest (AGPL FOSS, no paid tier).
 *
 * Uses the shared glass PageShell + prose primitives; keeps a page-specific CTA
 * pair (hosted demo + external source link).
 */

const REPO_URL = 'https://github.com/Partha-dev01/Constitutional-AIOps'

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
    <PageShell
      title="Self-host or use the hosted demo"
      lead="Same software either way. Constitutional AIOps is AGPL open source with no paid tier. Try it instantly on the hosted demo, or run the exact same stack on your own infrastructure. This page helps you pick."
    >
      <article className="min-w-0">
        <H2 id="two-ways">Two ways to run it</H2>
        <P>
          The hosted demo is the fastest way to see the product working. Self-hosting gives you the
          whole system on hardware you control, with your own model endpoint and your data staying
          put. Nothing is held back in the open-source build.
        </P>
        <div className="glass mb-6 overflow-x-auto rounded-xl">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/[0.04] text-muted-foreground">
              <tr>
                <th className="px-4 py-3 font-semibold">Dimension</th>
                <th className="px-4 py-3 font-semibold">Hosted demo</th>
                <th className="px-4 py-3 font-semibold">Self-host</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON.map((row) => (
                <tr key={row.dimension} className="border-t border-white/10 align-top">
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
            <GlassCard key={step.title} as="li" hover radius="xl" className="p-5">
              <div className="flex items-start gap-4">
                <span className="mt-0.5 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary ring-1 ring-inset ring-primary/20">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold">{step.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{step.body}</p>
                  <pre className="mt-3 overflow-x-auto rounded-lg border border-white/10 bg-black/30 p-3 text-xs leading-relaxed text-foreground">
                    <code>{step.code}</code>
                  </pre>
                </div>
              </div>
            </GlassCard>
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
          <CtaButton href={DEMO_URL} arrow>
            Try the hosted demo
          </CtaButton>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="glass glass-hover group inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-foreground transition-all hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <GithubMark className="h-4 w-4" />
            View the source
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
          </a>
        </div>

        <P>
          Want the wider picture? Head back to the{' '}
          <a href="/" className="font-medium text-primary hover:underline">home page</a>, or read the{' '}
          <a href="/opensource.html" className="font-medium text-primary hover:underline">open-source</a>{' '}
          overview.
        </P>
      </article>
    </PageShell>
  )
}
