import type { ReactNode } from 'react'
import { HelpCircle, ChevronDown } from 'lucide-react'
import { PageShell, Pill, CTARow } from '../components/prose'

/**
 * Standalone "FAQ" page (/faq.html, a Vite entry). Native <details> accordions,
 * no JavaScript needed. Includes the cold-start explainer for the demo box.
 * Fully static and public-safe, no network calls.
 */

const QA: { q: string; a: ReactNode }[] = [
  {
    q: 'Is it safe to let it act on my infrastructure?',
    a: (
      <>
        That is the whole design. Action tools are off by default, only containers you allowlist can be
        touched, and every proposal clears a twelve-principle safety gate. High-confidence, low-risk
        actions can run and log themselves, anything uncertain waits for you, and tier-1 rules like keeping
        healthy replicas can never be overridden.
      </>
    ),
  },
  {
    q: 'What models does it use, and do I need a GPU?',
    a: (
      <>
        It runs two agents, a fast one and a reasoning one, against any OpenAI-compatible endpoint. You
        bring your own: your hosted models, a local runtime, or a managed provider. The project does not
        need to run its own GPU, and you can point both agents at a single model for a minimal setup.
      </>
    ),
  },
  {
    q: 'Why did the live demo take a moment to load?',
    a: (
      <>
        The hosted demo box sleeps when nobody is using it, which keeps running costs near zero. The first
        visit after it has been idle wakes it, so it can take a short moment to come up before the app
        appears. Later visits are instant while it stays warm. The no-login demo itself runs on fixture
        data and never needs the box at all.
      </>
    ),
  },
  {
    q: 'Is my data sent anywhere?',
    a: (
      <>
        The app talks only to the model endpoint you configure and your own observability stack. There is
        no third-party analytics or telemetry call baked into the product. Where your prompts and data go
        is decided by which endpoint you point it at.
      </>
    ),
  },
  {
    q: 'How accurate is it?',
    a: (
      <>
        On the project's evaluation corpus it reaches 82.4% overall accuracy, and its root-cause analysis
        runs about 10.8 points ahead of a strong open baseline on the same cases. The benchmark harness
        ships in the app, so you can score any endpoint yourself rather than take the figure on faith. The{' '}
        <a href="/benchmark.html" className="font-medium text-primary hover:underline">benchmark page</a>{' '}
        has the detail.
      </>
    ),
  },
  {
    q: 'What is the constitution, exactly?',
    a: (
      <>
        Twelve principles grouped into three tiers, plus a confidence score that routes each proposed
        action to automatic, human-approval, or alert-only. It is the mechanism that lets an autonomous
        system be trusted with real infrastructure. The{' '}
        <a href="/safety.html" className="font-medium text-primary hover:underline">safety page</a> walks
        all of it.
      </>
    ),
  },
  {
    q: 'Can I self-host it?',
    a: (
      <>
        Yes. It is built to be self-hosted with Docker Compose and a bring-your-own model endpoint, under
        an AGPL-3.0 licence. The full self-host walkthrough opens with the public source release. See the{' '}
        <a href="/opensource.html" className="font-medium text-primary hover:underline">open-source page</a>{' '}
        for how that works.
      </>
    ),
  },
]

export function Faq() {
  return (
    <PageShell
      maxWidth="3xl"
      pill={<Pill icon={<HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />}>FAQ</Pill>}
      title="Questions, answered"
      lead="The things people ask first. If safety is your main concern, start with the first answer, then read the safety page in full."
    >
      <div className="divide-y divide-border overflow-hidden rounded-xl border border-border">
        {QA.map((item) => (
          <details key={item.q} className="group bg-card/40 open:bg-card/60">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 text-base font-semibold marker:content-none">
              {item.q}
              <ChevronDown
                className="h-4 w-4 flex-none text-muted-foreground transition-transform group-open:rotate-180"
                aria-hidden="true"
              />
            </summary>
            <div className="px-5 pb-5 text-sm leading-relaxed text-muted-foreground">{item.a}</div>
          </details>
        ))}
      </div>

      <CTARow />
    </PageShell>
  )
}
