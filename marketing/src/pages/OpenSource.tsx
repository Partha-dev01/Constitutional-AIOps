import type { ReactNode } from 'react'
import { Scale, Server, KeyRound, HeartHandshake, Lock } from 'lucide-react'
import { PageShell, Pill, H2, P, Code, CTARow } from '../components/prose'
import { SHOW_SELFHOST } from '../config'

/**
 * Standalone "Open source" page (/opensource.html, a Vite entry). States the
 * licence and the no-lock-in philosophy. It is NOT a pricing table. The concrete
 * "get the source" block is gated on SHOW_SELFHOST so nothing links a private
 * repository as public before the release flip. Fully static, no network calls.
 */

const PRINCIPLES: { icon: ReactNode; title: string; body: string }[] = [
  {
    icon: <Scale className="h-5 w-5" aria-hidden="true" />,
    title: 'AGPL-3.0',
    body: 'Copyleft, all the way down. The source is the product, and changes you deploy stay available under the same licence.',
  },
  {
    icon: <Server className="h-5 w-5" aria-hidden="true" />,
    title: 'Self-host first',
    body: 'Designed to run on your own machine with Docker Compose. There is no hosted-only feature held back from the version you run yourself.',
  },
  {
    icon: <KeyRound className="h-5 w-5" aria-hidden="true" />,
    title: 'Bring your own endpoint',
    body: 'Point it at your own models or a provider you trust. No key of ours sits between you and the model, and no usage flows through us.',
  },
  {
    icon: <HeartHandshake className="h-5 w-5" aria-hidden="true" />,
    title: 'No paid tier',
    body: 'There is no upsell and no locked features. This is a research project released as free software, not a funnel.',
  },
]

export function OpenSource() {
  return (
    <PageShell
      maxWidth="4xl"
      pill={<Pill icon={<Scale className="h-3.5 w-3.5" aria-hidden="true" />}>Open source</Pill>}
      title="Free software, no lock-in"
      lead="Constitutional AIOps is released as free software under AGPL-3.0. You run it, you own the deployment, and you decide which model it talks to. This is not a pricing page, because there is nothing to buy."
    >
      <section>
        <div className="grid gap-4 sm:grid-cols-2">
          {PRINCIPLES.map((p) => (
            <div key={p.title} className="rounded-xl border border-border bg-card/50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-primary">
                {p.icon}
              </div>
              <h3 className="mb-1.5 text-base font-semibold">{p.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      <H2 id="data">Your data stays yours</H2>
      <P>
        Because you host the app and choose the model endpoint, there is no middle party. The app talks to
        the endpoint you configure and your own observability stack, and nothing else. There is no
        third-party analytics call baked into the product.
      </P>

      {SHOW_SELFHOST ? (
        <>
          <H2 id="get">Get the source</H2>
          <P>
            Clone the repository, copy the example environment file, and bring it up with one command.
            Point <Code>FAST_AGENT_URL</Code> and <Code>REASONING_AGENT_URL</Code> at your model endpoint
            and you are running.
          </P>
          <div className="mb-6 overflow-x-auto rounded-xl border border-border bg-card/70 p-4 font-mono text-sm text-muted-foreground">
            <div>git clone https://github.com/Partha-dev01/Constitutional-AIOps</div>
            <div>cd Constitutional-AIOps</div>
            <div>cp .env.example .env</div>
            <div>docker compose up -d</div>
          </div>
        </>
      ) : (
        <>
          <H2 id="release">Source release</H2>
          <P>
            The project is finishing its pre-release hardening. The public repository, the self-host
            walkthrough and the client SDKs all open together at the source release. The licence and the
            no-lock-in commitments on this page hold now and will not change at that point.
          </P>
        </>
      )}

      <div className="rounded-xl border border-border bg-card/50 p-5">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
          <Lock className="h-4 w-4 text-primary" aria-hidden="true" />
          Why AGPL and not something more permissive
        </div>
        <p className="text-sm leading-relaxed text-muted-foreground">
          A safety-critical operations tool should stay inspectable. AGPL keeps improvements in the open
          even when the software is offered as a network service, which fits a project whose whole point is
          that you can see exactly how it decides to act.
        </p>
      </div>

      <CTARow />
    </PageShell>
  )
}
