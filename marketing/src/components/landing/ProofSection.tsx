import { Lock, Check } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { ShotFrame } from './ShotFrame'

interface ProofRow {
  shot: string
  alt: string
  title: string
  blurb: string
  bullets: [string, string, string]
}

const ROWS: ProofRow[] = [
  {
    shot: 'chat',
    alt: 'Reasoning-agent chat with streaming tool-call timeline',
    title: 'Ask the reasoning agent anything',
    blurb:
      'Converse with the 14B reasoning agent about live incidents in plain language. Every tool it invokes is traced in an inline timeline as the answer streams in.',
    bullets: [
      'Streaming tool-call timeline for full transparency',
      'Markdown RCA reports grounded in real telemetry',
      'Constitutional gate on every proposed action',
    ],
  },
  {
    shot: 'graph-explorer',
    alt: 'Episodic graph explorer visualizing incident knowledge in Neo4j',
    title: 'Explore the episodic memory graph',
    blurb:
      'Past incidents live in Neo4j as semantic triplets the agents can recall. Walk the graph to see how causes, symptoms, and remediations connect across time.',
    bullets: [
      'Hybrid vector + graph retrieval of precedents',
      'Incident → cause → remediation triplets',
      'Interactive force-directed exploration',
    ],
  },
  {
    shot: 'metrics',
    alt: 'Metrics view with agent latency and system performance panels',
    title: 'Monitor agent performance',
    blurb:
      'Latency, throughput, and resource panels expose exactly what both agents are doing. Nothing is a black box — every inference is measured.',
    bullets: [
      'Per-agent P50/P95 latency percentiles',
      'Prometheus-backed live dashboards',
      'GPU and VRAM utilization at a glance',
    ],
  },
  {
    shot: 'agent-hub',
    alt: 'Agent hub showing both LLM agents with health and controls',
    title: 'Command both agents from one hub',
    blurb:
      'The fast annotator and the deep reasoner are managed side by side. Health, model status, and autonomy levels are always one screen away.',
    bullets: [
      'Qwen3-4B annotator + Qwen3-14B reasoner together',
      'Live health and model status per agent',
      'Graduated autonomy controls with human override',
    ],
  },
]

/**
 * Alternating feature rows: copy on one side, a real product screenshot in a
 * glass browser frame on the other. Screenshots self-hide on error (see
 * ShotFrame) so the section degrades cleanly if a PNG is missing.
 */
export function ProofSection() {
  return (
    <section id="live" className="border-b border-border py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-6 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            See it running
          </h2>
          <p className="mt-4 text-muted-foreground">
            A live, self-hosted system — not a mockup.
          </p>
        </div>

        <div className="mb-16 flex justify-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-xs text-muted-foreground">
            <Lock className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            Live system — basic-auth protected.
          </div>
        </div>

        <div className="flex flex-col gap-20 sm:gap-24">
          {ROWS.map((row, i) => (
            <ProofRowItem key={row.shot} row={row} reversed={i % 2 === 1} />
          ))}
        </div>
      </div>
    </section>
  )
}

function ProofRowItem({ row, reversed }: { row: ProofRow; reversed: boolean }) {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <div
      ref={ref}
      className={`reveal${visible ? ' reveal-visible' : ''} flex flex-col items-center gap-8 lg:gap-14 ${
        reversed ? 'lg:flex-row-reverse' : 'lg:flex-row'
      }`}
    >
      <div className="w-full lg:w-5/12">
        <h3 className="text-2xl font-bold tracking-tight sm:text-3xl">{row.title}</h3>
        <p className="mt-4 leading-relaxed text-muted-foreground">{row.blurb}</p>
        <ul className="mt-6 space-y-3">
          {row.bullets.map((bullet) => (
            <li key={bullet} className="flex items-start gap-3 text-sm text-foreground">
              <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                <Check className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
              {bullet}
            </li>
          ))}
        </ul>
      </div>

      <div className="w-full lg:w-7/12">
        <ShotFrame src={`/screenshots/${row.shot}.png`} alt={row.alt} />
      </div>
    </div>
  )
}
