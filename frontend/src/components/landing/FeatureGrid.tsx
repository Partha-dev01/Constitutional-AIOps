import { Cpu, ShieldCheck, Network, Activity } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'

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
    copy: '12 principles across 3 tiers gate every action. Graduated authorization: automatic above 0.90 confidence, human approval between 0.70 and 0.90, and alert-only below 0.70.',
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
]

export function FeatureGrid() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section className="border-b border-border py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Four pillars, one autonomous operator
          </h2>
          <p className="mt-4 text-muted-foreground">
            Each subsystem is designed to be inspectable, safe, and grounded in
            real telemetry.
          </p>
        </div>

        <div ref={ref} className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature, i) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className={`reveal${visible ? ' reveal-visible' : ''} group rounded-lg border border-border bg-card p-6 transition-all hover:-translate-y-1 hover:border-primary/50`}
                style={{ animationDelay: `${i * 90}ms` }}
              >
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.copy}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
