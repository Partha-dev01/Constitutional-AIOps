import {
  Radio,
  Zap,
  Brain,
  ShieldCheck,
  UserCheck,
  Database,
  ChevronRight,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'

interface Stage {
  icon: LucideIcon
  title: string
  sub: string
}

const STAGES: Stage[] = [
  { icon: Radio, title: 'Telemetry', sub: 'Logs · metrics · traces' },
  { icon: Zap, title: 'Fast Agent', sub: 'Annotate & classify' },
  { icon: Brain, title: 'Reasoning Agent', sub: 'Root-cause analysis' },
  { icon: ShieldCheck, title: 'Constitutional Validator', sub: '12 principles · 3 tiers' },
  { icon: UserCheck, title: 'Human-in-loop / Auto', sub: 'Approve or remediate' },
]

export function ArchitectureBand() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section className="border-b border-border py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How a signal becomes an action
          </h2>
          <p className="mt-4 text-muted-foreground">
            Every decision flows through the constitutional validator before it
            ever touches infrastructure.
          </p>
        </div>

        <div
          ref={ref}
          className={`reveal${visible ? ' reveal-visible' : ''} flex flex-col items-stretch gap-4 lg:flex-row lg:items-center lg:justify-between`}
        >
          {STAGES.map((stage, i) => {
            const Icon = stage.icon
            return (
              <div key={stage.title} className="flex flex-1 items-center gap-4 lg:flex-col lg:gap-3">
                <div className="flex flex-1 flex-col items-center rounded-lg border border-border bg-card px-4 py-6 text-center transition-colors hover:border-primary/50 lg:w-full">
                  <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-semibold">{stage.title}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{stage.sub}</div>
                </div>
                {i < STAGES.length - 1 && (
                  <ChevronRight className="h-5 w-5 shrink-0 rotate-90 text-muted-foreground lg:rotate-0" />
                )}
              </div>
            )
          })}
        </div>

        {/* Memory feedback loop */}
        <div className="mt-8 flex justify-center">
          <div className="inline-flex items-center gap-3 rounded-lg border border-dashed border-primary/40 bg-primary/5 px-5 py-3 text-sm text-muted-foreground">
            <Database className="h-5 w-5 text-primary" />
            <span>
              <span className="font-semibold text-foreground">Neo4j graph-episodic memory</span>{' '}
              feeds past incidents back into the reasoning and validation stages.
            </span>
          </div>
        </div>
      </div>
    </section>
  )
}
