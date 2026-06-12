import { useEffect, useState } from 'react'
import { useReveal } from '../../hooks/useReveal'
import { prefersReducedMotion } from '../../lib/utils'

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

const COUNT_DURATION_MS = 1400

/**
 * Full-width hairline stats band. Each figure counts up via rAF when the band
 * scrolls into view; under prefers-reduced-motion the final values render
 * immediately with no animation.
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
          <CountUpStat key={stat.label} stat={stat} start={visible} />
        ))}
      </div>
    </section>
  )
}

function CountUpStat({ stat, start }: { stat: Stat; start: boolean }) {
  const [display, setDisplay] = useState(() =>
    prefersReducedMotion() ? stat.value : 0,
  )

  useEffect(() => {
    if (!start) return
    if (prefersReducedMotion()) {
      setDisplay(stat.value)
      return
    }

    let frame = 0
    const t0 = performance.now()

    const tick = (now: number) => {
      const progress = Math.min((now - t0) / COUNT_DURATION_MS, 1)
      // Ease-out cubic so the count decelerates into its final value.
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(stat.value * eased)
      if (progress < 1) {
        frame = window.requestAnimationFrame(tick)
      }
    }

    frame = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(frame)
  }, [start, stat.value])

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
