import {
  Radio,
  Zap,
  Brain,
  ShieldCheck,
  UserCheck,
  Database,
  ChevronRight,
  ChevronDown,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Fragment } from 'react'
import { useReveal } from '../../hooks/useReveal'
import { SectionKicker } from './SectionKicker'
import { GlassCard, Reveal } from '../ui'

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
    <section id="architecture" className="scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <SectionKicker>Pipeline</SectionKicker>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            How a signal becomes an action
          </h2>
          <p className="mt-4 text-muted-foreground">
            Every decision flows through the constitutional validator before it
            ever touches infrastructure.
          </p>
        </Reveal>

        {/* Cards row. The stages connect via chevrons that sit in the GAPS
            between cards (pointing down when stacked, right on lg+). The glass
            is see-through, so a connector must never run behind a card face. Each
            stage + joint reveals in turn (staggered) once the row scrolls in. */}
        <div ref={ref} className="flex flex-col gap-3 lg:flex-row lg:items-stretch">
          {STAGES.map((stage, i) => {
            const Icon = stage.icon
            const isValidator = i === VALIDATOR_INDEX
            return (
              <Fragment key={stage.title}>
                <GlassCard
                  hover
                  radius="xl"
                  className={`reveal${visible ? ' reveal-visible' : ''} flex flex-1 flex-col items-center px-4 py-6 text-center`}
                  style={{ animationDelay: `${i * 90}ms` }}
                >
                  <div className="mb-2 font-mono text-[10px] tracking-widest text-muted-foreground/60">
                    {String(i + 1).padStart(2, '0')}
                  </div>
                  <div className="relative mb-3 inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary ring-1 ring-inset ring-primary/20">
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
                </GlassCard>
                {i < STAGES.length - 1 && (
                  <div
                    className={`reveal${visible ? ' reveal-visible' : ''} flex shrink-0 items-center justify-center text-primary/50`}
                    style={{ animationDelay: `${i * 90 + 45}ms` }}
                    aria-hidden="true"
                  >
                    <ChevronRight className="h-5 w-5 rotate-90 lg:rotate-0" />
                  </div>
                )}
              </Fragment>
            )
          })}
        </div>

        {/* Memory feedback loop. A centered dashed connector (lg+) drops from
            the row into the pill, so the "feeds back" idea reads without any
            line crossing the pill text. */}
        <Reveal className="mt-8 flex flex-col items-center lg:mt-10">
          <span
            className="hidden h-6 border-l-2 border-dashed border-primary/40 lg:block"
            aria-hidden="true"
          />
          <ChevronDown
            className="hidden h-5 w-5 -mt-1 text-primary/60 lg:block"
            aria-hidden="true"
          />
          <div className="mt-2 inline-flex items-center gap-3 rounded-lg border border-dashed border-primary/40 bg-primary/5 px-5 py-3 text-sm text-muted-foreground">
            <Database className="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
            <span>
              <span className="font-semibold text-foreground">Neo4j graph-episodic memory</span>{' '}
              feeds past incidents back into the reasoning and validation stages.
            </span>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
