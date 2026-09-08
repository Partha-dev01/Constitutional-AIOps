import { useEffect, useState } from 'react'
import { useReveal } from '../../hooks/useReveal'

interface Stat {
  value: number
  decimals: number
  suffix: string
  label: string
  sub: string
}

/**
 * Product facts about the safety model and architecture. No benchmark or paper
 * figures here (the dedicated Benchmark page covers evaluation). Static
 * constants; the band makes no network calls.
 */
const STATS: Stat[] = [
  {
    value: 12,
    decimals: 0,
    suffix: '',
    label: 'Constitutional principles',
    sub: 'across 3 safety tiers',
  },
  {
    value: 3,
    decimals: 0,
    suffix: '',
    label: 'Authorization tiers',
    sub: 'automatic · approve · alert',
  },
  {
    value: 2,
    decimals: 0,
    suffix: '',
    label: 'LLM agents',
    sub: 'fast annotate + deep reasoning',
  },
  {
    value: 3,
    decimals: 0,
    suffix: '',
    label: 'Telemetry signals',
    sub: 'logs · metrics · traces',
  },
  {
    value: 1,
    decimals: 0,
    suffix: '',
    label: 'Safety gate',
    sub: 'every action must pass it',
  },
]

/**
 * Full-width hairline stats band. The figures count up from zero once the band
 * scrolls into view (easeOutCubic over ~1.4s); under reduced motion they render
 * at their final value immediately.
 */
export function StatsBand() {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <section className="border-b border-border bg-card/30">
      <div className="mx-auto max-w-6xl px-6 py-14 sm:py-16">
        <p className="mb-10 text-center font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          The system at a glance
        </p>
        <div
          ref={ref}
          className="grid grid-cols-2 gap-x-6 gap-y-10 md:grid-cols-3 lg:grid-cols-5"
        >
          {STATS.map((stat) => (
            <StatItem key={stat.label} stat={stat} run={visible} />
          ))}
        </div>
      </div>
    </section>
  )
}

function StatItem({ stat, run }: { stat: Stat; run: boolean }) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (!run) return
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) {
      setDisplay(stat.value)
      return
    }
    let raf = 0
    const start = performance.now()
    const duration = 1400
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3) // easeOutCubic
      setDisplay(stat.value * eased)
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [run, stat.value])

  return (
    <div className="text-center">
      <div className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
        {display.toFixed(stat.decimals)}
        <span className="text-primary">{stat.suffix}</span>
      </div>
      <div className="mt-2 text-sm font-medium text-foreground">{stat.label}</div>
      <div className="mt-0.5 text-xs text-muted-foreground">{stat.sub}</div>
    </div>
  )
}
