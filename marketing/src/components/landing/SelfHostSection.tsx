import { Check } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { ShotFrame } from './ShotFrame'
import { GlassCard, Reveal } from '../ui'

interface Step {
  title: string
  body: string
  code: string
}

const STEPS: Step[] = [
  {
    title: 'Clone the repository',
    body: 'One repo, no submodules.',
    code: 'git clone https://github.com/Partha-dev01/Constitutional-AIOps.git\ncd Constitutional-AIOps',
  },
  {
    title: 'Point it at your LLM',
    body: 'Any OpenAI-compatible endpoint: vLLM, Ollama, AWS Bedrock, OpenAI. Both agents may share one URL and model.',
    code: 'cp .env.example .env\n#  FAST_AGENT_URL / REASONING_AGENT_URL\n#  FAST_AGENT_MODEL / REASONING_AGENT_MODEL\n#  LLM_API_KEY   (only if your endpoint needs one)',
  },
  {
    title: 'Start the lite stack',
    body: 'CPU-only, no GPU, no Neo4j required. Self-contained one-liner.',
    code: 'docker compose -f docker/docker-compose.lite.yml up -d',
  },
  {
    title: 'Open the app',
    body: 'The full dashboard, chat, incidents and topology running on your own box.',
    code: '# http://localhost:3000',
  },
]

const HIGHLIGHTS = [
  'No GPU required',
  'Bring your own model endpoint',
  'One command, ~2GB RAM',
  'Change the endpoint live from Settings',
]

/**
 * Self-host walkthrough: numbered steps with copyable commands on one side, a
 * real product screenshot on the other. Mirrors ProofSection styling (glass
 * shot frame, reveal-on-scroll) so it reads as part of the same page.
 */
export function SelfHostSection() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section id="self-host" className="scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto mb-16 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Self-host in minutes
          </h2>
          <p className="mt-4 text-muted-foreground">
            Run the whole platform on your own infrastructure. Bring any
            OpenAI-compatible model endpoint. Nothing is locked to a vendor.
          </p>
        </Reveal>

        <div
          ref={ref}
          className={`reveal${visible ? ' reveal-visible' : ''} flex flex-col items-start gap-10 lg:flex-row lg:gap-14`}
        >
          <ol className="w-full space-y-5 lg:w-7/12">
            {STEPS.map((step, i) => (
              <GlassCard key={step.title} as="li" hover radius="xl" className="p-5">
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
              </GlassCard>
            ))}
          </ol>

          <div className="w-full lg:w-5/12">
            <ShotFrame
              src="/screenshots/selfhost.png"
              alt="The Constitutional AIOps dashboard running on a self-hosted lite deployment"
            />
            <ul className="mt-6 space-y-3">
              {HIGHLIGHTS.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-foreground">
                  <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                    <Check className="h-3.5 w-3.5" aria-hidden="true" />
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
