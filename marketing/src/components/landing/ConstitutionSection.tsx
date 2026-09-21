import { ShieldCheck, UserCheck, GraduationCap } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { SectionKicker } from './SectionKicker'
import { GlassCard, Reveal } from '../ui'

/**
 * "The constitution, in three tiers" — the substance behind the "12 principles ·
 * 3 tiers" label the hero strip and the pipeline both reference. The FeatureGrid
 * introduces the safety gate and the confidence→action matrix; this section is
 * the one place the actual principles are spelled out, so it explains rather
 * than repeats. Fully static, no network calls, no <nav>.
 *
 * Principles mirror the product's constitutional framework verbatim (Tier 1
 * safety-critical, Tier 2 operational, Tier 3 learning).
 * tests/test_principles_docs.py fails if any line here drifts from
 * src/constitutional/principles.py.
 */

interface Tier {
  icon: LucideIcon
  tag: string
  title: string
  enforcement: string
  enforcementClass: string
  principles: string[]
}

const TIERS: Tier[] = [
  {
    icon: ShieldCheck,
    tag: 'Tier 1',
    title: 'Safety-critical',
    enforcement: 'Never violated',
    enforcementClass: 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20',
    principles: [
      'Never execute actions that could cause data loss or corruption',
      'Never take destructive actions during active incidents without explicit approval',
      'Never exceed resource limits that could cause cascade failures',
      'Never modify security configurations',
    ],
  },
  {
    icon: UserCheck,
    tag: 'Tier 2',
    title: 'Operational',
    enforcement: 'Requires approval',
    enforcementClass: 'bg-primary/10 text-primary ring-1 ring-primary/20',
    principles: [
      'Prefer the smallest effective action to resolve issues',
      'Require telemetry evidence before taking action',
      'Log all actions for audit and rollback capability',
      'Escalate to humans when confidence is below threshold',
    ],
  },
  {
    icon: GraduationCap,
    tag: 'Tier 3',
    title: 'Learning',
    enforcement: 'Soft guidance',
    enforcementClass: 'bg-muted text-muted-foreground ring-1 ring-border',
    principles: [
      'Track outcomes of actions for continuous improvement',
      'Learn from human corrections and overrides',
      'Optimize for long-term system health over short-term fixes',
      'Occasionally explore alternative solutions to prevent local optima',
    ],
  },
]

export function ConstitutionSection() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section id="constitution" className="scroll-mt-24 py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto mb-14 max-w-2xl text-center">
          <SectionKicker>Safety model</SectionKicker>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Twelve principles. Three tiers.
          </h2>
          <p className="mt-4 text-muted-foreground">
            The gate is not a prompt. Every proposed action is checked against a
            fixed constitution, and the tier a principle sits in decides what
            happens when it is at stake.
          </p>
        </Reveal>

        <div ref={ref} className="grid gap-6 lg:grid-cols-3">
          {TIERS.map((tier, i) => {
            const Icon = tier.icon
            return (
              <div
                key={tier.tag}
                className={`reveal${visible ? ' reveal-visible' : ''}`}
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <GlassCard hover className="flex h-full flex-col p-6">
                  <div className="mb-4 flex items-center gap-3">
                    <span className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-6 w-6" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <div className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground/70">
                        {tier.tag}
                      </div>
                      <div className="text-lg font-semibold">{tier.title}</div>
                    </div>
                  </div>

                  <span
                    className={`mb-5 inline-flex w-fit items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${tier.enforcementClass}`}
                  >
                    {tier.enforcement}
                  </span>

                  <ul className="space-y-2.5 text-sm text-muted-foreground">
                    {tier.principles.map((p) => (
                      <li key={p} className="flex gap-2.5">
                        <span
                          className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60"
                          aria-hidden="true"
                        />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </GlassCard>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default ConstitutionSection
