import { Cpu, ShieldCheck, Network, Activity, Satellite, UserCheck } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { SectionKicker } from './SectionKicker'

interface Feature {
  icon: LucideIcon
  title: string
  copy: string
}

const FEATURES: Feature[] = [
  {
    icon: Cpu,
    title: 'Dual-Agent LLM',
    copy: 'A Qwen3-4B fast annotator and a Qwen3-14B reasoning agent run simultaneously on a single 24GB GPU — zero hot-swap latency between classification and root-cause analysis.',
  },
  {
    icon: ShieldCheck,
    title: 'Constitutional AI Safety',
    copy: '12 principles across 3 tiers gate every action. Each proposed remediation is validated against the constitution before it is allowed anywhere near infrastructure.',
  },
  {
    icon: Network,
    title: 'Graph-Episodic Memory',
    copy: 'Neo4j stores semantic triplets of past incidents. Hybrid vector + graph retrieval surfaces relevant precedents so the agents learn from operational history.',
  },
  {
    icon: Activity,
    title: 'Unified LGTM Observability',
    copy: 'Loki, Grafana, Tempo, and Prometheus are correlated through OpenTelemetry — logs, metrics, and traces stitched into a single operational picture.',
  },
  {
    icon: Satellite,
    title: 'Remote Edge Monitoring',
    copy: 'Grafana Alloy edge agents stream logs and metrics from any Docker host into the platform, so remote fleets get the same autonomous coverage as the core stack.',
  },
  {
    icon: UserCheck,
    title: 'Human-in-the-Loop Authorization',
    copy: 'Graduated trust keeps people in command: actions above 0.90 confidence run automatically, 0.70–0.90 requires human approval, and below 0.70 is alert-only.',
  },
]

export function FeatureGrid() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section id="features" className="border-b border-border py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <SectionKicker>Subsystems</SectionKicker>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Core subsystems
          </h2>
          <p className="mt-4 text-muted-foreground">
            Each subsystem is designed to be inspectable, safe, and grounded in
            real telemetry.
          </p>
        </div>

        <div ref={ref} className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, i) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className={`reveal${visible ? ' reveal-visible' : ''}`}
                style={{ animationDelay: `${i * 90}ms` }}
              >
                {/* Reveal lives on the wrapper: reveal-up's fill-forwards
                    transform would otherwise override child transitions. */}
                <div className="group h-full rounded-lg border border-border bg-card p-6 transition-all hover:-translate-y-0.5 hover:border-primary/40">
                  <div className="mb-4 flex items-center justify-between">
                    <span className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
                      <Icon className="h-6 w-6" aria-hidden="true" />
                    </span>
                    <span className="font-mono text-xs tracking-widest text-muted-foreground/60">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {feature.copy}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
