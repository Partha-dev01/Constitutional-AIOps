import { Cpu, ShieldCheck, Network, Activity, Satellite, UserCheck } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { SectionKicker } from './SectionKicker'
import { GlassCard, Reveal } from '../ui'

interface Feature {
  icon: LucideIcon
  title: string
  copy: string
}

const FEATURES: Feature[] = [
  {
    icon: Cpu,
    title: 'Dual-Agent LLM',
    copy: 'A Qwen3-4B fast annotator and a Qwen3-14B reasoning agent run at the same time on one 24GB GPU, with no hot-swap latency between classification and root-cause analysis.',
  },
  {
    icon: ShieldCheck,
    title: 'Constitutional AI Safety',
    copy: '12 principles across 3 tiers gate every action. Each proposed remediation is validated against the constitution before it goes anywhere near infrastructure.',
  },
  {
    icon: Network,
    title: 'Graph-Episodic Memory',
    copy: 'Neo4j stores semantic triplets of past incidents. Hybrid vector and graph retrieval surfaces relevant precedents, so the agents learn from operational history.',
  },
  {
    icon: Activity,
    title: 'Unified LGTM Observability',
    copy: 'Loki, Grafana, Tempo, and Prometheus are correlated through OpenTelemetry, so logs, metrics, and traces become one operational picture.',
  },
  {
    icon: Satellite,
    title: 'Remote Edge Monitoring',
    copy: 'Grafana Alloy edge agents stream logs and metrics from any Docker host into the platform, so remote fleets get the same autonomous coverage as the core stack.',
  },
  {
    icon: UserCheck,
    title: 'Human-in-the-Loop Authorization',
    copy: 'Graduated trust keeps people in command. Actions above 0.90 confidence run automatically, 0.70 to 0.90 needs human approval, and below 0.70 is alert-only.',
  },
]

export function FeatureGrid() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section id="features" className="scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <SectionKicker>Subsystems</SectionKicker>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Core subsystems
          </h2>
          <p className="mt-4 text-muted-foreground">
            Each subsystem is designed to be inspectable, safe, and grounded in
            real telemetry.
          </p>
        </Reveal>

        {/* Translucent glass cards on the shared system; each lifts toward the
            accent on hover. */}
        <div ref={ref} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, i) => {
            const Icon = feature.icon
            return (
              <GlassCard
                key={feature.title}
                hover
                className={`reveal${visible ? ' reveal-visible' : ''} p-7`}
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-inset ring-primary/20">
                  <Icon className="h-5 w-5" strokeWidth={1.5} aria-hidden="true" />
                </span>
                <h3 className="mt-5 text-base font-semibold tracking-tight">{feature.title}</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-muted-foreground">
                  {feature.copy}
                </p>
              </GlassCard>
            )
          })}
        </div>
      </div>
    </section>
  )
}
