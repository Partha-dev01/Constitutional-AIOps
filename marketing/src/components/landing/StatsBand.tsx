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
 * Real numbers from docs/KEY_METRICS.md (benchmark v3.0, 431 cases, and the
 * §15 vLLM gate). Static constants — the page makes no network calls.
 */
const STATS: Stat[] = [
  {
    value: 88.6,
    decimals: 1,
    suffix: '%',
    label: 'Overall accuracy',
    sub: '431-case benchmark v3.0',
  },
  {
    value: 94.8,
    decimals: 1,
    suffix: '%',
    label: 'Root-cause accuracy',
    sub: 'LEMMA-RCA · OpsEval',
  },
  {
    value: 1.51,
    decimals: 2,
    suffix: 'x',
    label: 'P95 speedup on vLLM',
    sub: 'vs Ollama baseline',
  },
  {
    value: 12,
    decimals: 0,
    suffix: '',
    label: 'Constitutional principles',
    sub: 'across 3 safety tiers',
  },
  {
    value: 2,
    decimals: 0,
    suffix: '',
    label: 'LLMs loaded at once',
    sub: 'on a single 24 GB GPU',
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
      <div
        ref={ref}
        className="mx-auto grid max-w-6xl grid-cols-2 gap-x-6 gap-y-10 px-6 py-14 sm:py-16 md:grid-cols-3 lg:grid-cols-5"
      >
        {STATS.map((stat) => (
          <StatItem key={stat.label} stat={stat} run={visible} />
        ))}
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
      <div className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
        {display.toFixed(stat.decimals)}
        <span className="text-primary">{stat.suffix}</span>
      </div>
      <div className="mt-2 text-sm font-medium text-foreground">{stat.label}</div>
      <div className="mt-0.5 text-xs text-muted-foreground">{stat.sub}</div>
    </div>
  )
}
