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
 * Figures from the camera-ready paper (COMSYS 2026, 431-case benchmark under
 * matched-substring evaluation): Table 2 (82.4% overall, 82.0% RCA), Table 6
 * cross-system comparison (RCA beats Llama-3.3-70B by 10.8pp), and the
 * preliminary vLLM AWQ gate in Sec 5.5 (about 1.5x). Static constants; the page
 * makes no network calls.
 */
const STATS: Stat[] = [
  {
    value: 82.4,
    decimals: 1,
    suffix: '%',
    label: 'Overall accuracy',
    sub: '431-case benchmark, 6 sources',
  },
  {
    value: 82.0,
    decimals: 1,
    suffix: '%',
    label: 'Root-cause accuracy',
    sub: 'beats Llama-3.3-70B by 10.8pp',
  },
  {
    value: 1.5,
    decimals: 1,
    suffix: 'x',
    label: 'Faster inference on vLLM',
    sub: 'preliminary AWQ gate',
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
      <div className="mx-auto max-w-6xl px-6 py-14 sm:py-16">
        <p className="mb-10 text-center font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          From the COMSYS 2026 benchmark · 431 cases · 6 sources
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
