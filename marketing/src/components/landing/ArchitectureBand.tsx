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

/** Index of the Constitutional Validator stage (gets the pulsing ring). */
const VALIDATOR_INDEX = 3

export function ArchitectureBand() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section id="architecture" className="border-b border-border py-20 sm:py-28">
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

        <div ref={ref} className={`reveal${visible ? ' reveal-visible' : ''} relative`}>
          {/* Animated pipeline (lg+ only): a dashed flow line runs behind the
              stage cards, and a curved return path carries the outcome back
              toward the Neo4j memory pill below. Decorative; the cards are
              opaque so the line only shows in the joints between them. */}
          <svg
            className="absolute inset-0 hidden h-full w-full lg:block"
            viewBox="0 0 1000 100"
            preserveAspectRatio="none"
            aria-hidden="true"
            focusable="false"
          >
            <path
              d="M 15 31 H 985"
              fill="none"
              stroke="hsl(var(--primary) / 0.55)"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
              className="flow-line"
            />
            <path
              d="M 985 31 C 998 62, 900 90, 640 90"
              fill="none"
              stroke="hsl(262 83% 58% / 0.45)"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
              className="flow-return"
            />
          </svg>

          <div className="relative flex flex-col items-stretch gap-4 lg:flex-row lg:items-center lg:justify-between">
            {STAGES.map((stage, i) => {
              const Icon = stage.icon
              const isValidator = i === VALIDATOR_INDEX
              return (
                <div key={stage.title} className="flex flex-1 items-center gap-4 lg:flex-col lg:gap-3">
                  <div className="flex flex-1 flex-col items-center rounded-lg border border-border bg-card px-4 py-6 text-center transition-colors hover:border-primary/50 lg:w-full">
                    <div className="relative mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                      {isValidator && (
                        <span
                          className="validator-ring absolute inset-0 rounded-full border-2 border-primary/40"
                          aria-hidden="true"
                        />
                      )}
                      <Icon className="h-6 w-6" aria-hidden="true" />
                    </div>
                    <div className="text-sm font-semibold">{stage.title}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{stage.sub}</div>
                  </div>
                  {/* Mobile/tablet joints only — the SVG takes over on lg+. */}
                  {i < STAGES.length - 1 && (
                    <ChevronRight
                      className="h-5 w-5 shrink-0 rotate-90 text-muted-foreground lg:hidden"
                      aria-hidden="true"
                    />
                  )}
                </div>
              )
            })}
          </div>

          {/* Memory feedback loop — the curved return path lands here. */}
          <div className="relative mt-10 flex justify-center lg:mt-14">
            <div className="inline-flex items-center gap-3 rounded-lg border border-dashed border-primary/40 bg-primary/5 px-5 py-3 text-sm text-muted-foreground">
              <Database className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
              <span>
                <span className="font-semibold text-foreground">Neo4j graph-episodic memory</span>{' '}
                feeds past incidents back into the reasoning and validation stages.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
