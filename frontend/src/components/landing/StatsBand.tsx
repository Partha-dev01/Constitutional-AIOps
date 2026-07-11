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
 * Full-width hairline stats band. Renders the final figures directly — no
 * animation.
 */
export function StatsBand() {
  return (
    <section className="border-b border-border bg-card/30">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-x-6 gap-y-10 px-6 py-14 sm:py-16 md:grid-cols-3 lg:grid-cols-5">
        {STATS.map((stat) => (
          <StatItem key={stat.label} stat={stat} />
        ))}
      </div>
    </section>
  )
}

function StatItem({ stat }: { stat: Stat }) {
  return (
    <div className="text-center">
      <div className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
        {stat.value.toFixed(stat.decimals)}
        <span className="text-primary">{stat.suffix}</span>
      </div>
      <div className="mt-2 text-sm font-medium text-foreground">{stat.label}</div>
      <div className="mt-0.5 text-xs text-muted-foreground">{stat.sub}</div>
    </div>
  )
}
