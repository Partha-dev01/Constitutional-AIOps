import { ArrowRight, Radar, ShieldCheck, Wrench } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { ShotFrame } from './ShotFrame'
import { APP_URL, DEMO_URL } from '../../config'

/**
 * Landing hero. Pure static — no network calls. The masked grid is
 * decorative (aria-hidden); the h1 text content is exactly
 * "Constitutional AIOps" (word-stagger spans only), which the live e2e suite
 * depends on.
 *
 * Flagship pass: the wordmark, product promise, CTAs, a compact
 * "detect -> constitution gate -> remediate" control-room flow strip that
 * echoes the ArchitectureBand, then the product showcase. No stat or badge in
 * the hero itself — the numbers live in the StatsBand below.
 */
export function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      {/* Subtle grid overlay using the border token, masked to the hero core */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.12]"
        style={{
          backgroundImage:
            'linear-gradient(hsl(var(--border)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--border)) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(70% 60% at 50% 30%, black, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(70% 60% at 50% 30%, black, transparent 80%)',
        }}
        aria-hidden="true"
      />

      <div className="relative mx-auto flex max-w-5xl flex-col items-center px-6 pb-20 pt-32 text-center sm:pb-24 sm:pt-40">
        <div className="mb-6 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <img
            src="/logo-mark.png"
            alt=""
            aria-hidden="true"
            className="logo-glow h-20 w-20 shrink-0 sm:h-24 sm:w-24"
          />
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            <span className="hero-word" style={{ animationDelay: '80ms' }}>
              Constitutional
            </span>{' '}
            <span className="hero-word text-primary" style={{ animationDelay: '240ms' }}>
              AIOps
            </span>
          </h1>
        </div>

        <p
          className="hero-enter max-w-2xl text-balance text-lg font-medium text-foreground sm:text-2xl"
          style={{ animationDelay: '350ms' }}
        >
          Autonomous infrastructure operations with a constitution it cannot break.
        </p>

        <p
          className="hero-enter mt-4 max-w-2xl text-balance text-sm text-muted-foreground sm:text-base"
          style={{ animationDelay: '450ms' }}
        >
          A dual-agent LLM core, a 12-principle Constitutional AI safety framework, and
          Neo4j graph-episodic memory — correlating logs, metrics, and traces into safe,
          explainable remediation.
        </p>

        <div
          className="hero-enter mt-10 flex flex-col gap-3 sm:flex-row"
          style={{ animationDelay: '550ms' }}
        >
          <a
            href={APP_URL}
            className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Sign in
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              aria-hidden="true"
            />
          </a>
          <a
            href={DEMO_URL}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Demo mode
          </a>
        </div>

        <HeroFlow />

        <HeroShowcase />
      </div>
    </section>
  )
}

/**
 * Control-room flow strip: detect -> constitution gate -> remediate, the core
 * loop the product runs. Once it scrolls into view a telemetry signal runs the
 * pipeline on a continuous loop: each stage charges (glow + lift, its icon
 * flares) in sequence as a bright packet travels the connectors, and the gate
 * fires a validator ring-ping as the signal passes through it. Timing is one
 * shared 3.4s loop; every element offsets via a --flow-delay CSS var so the
 * cascade stays in order. .flow-run (added on scroll-in) arms the loop, and the
 * whole thing is reduced-motion-killed.
 */
function HeroFlow() {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <div
      ref={ref}
      className={`reveal${visible ? ' reveal-visible flow-run' : ''} mt-12 w-full max-w-3xl`}
    >
      <div className="flex items-stretch justify-center gap-1 sm:gap-3">
        <FlowNode
          icon={<Radar className="h-4 w-4" aria-hidden="true" />}
          title="Detect"
          detail="logs · metrics · traces"
          delay={0}
        />
        <FlowConnector delay={300} />
        <FlowNode
          icon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />}
          title="Constitution gate"
          detail="12 principles · 3 tiers"
          highlight
          delay={750}
        />
        <FlowConnector delay={1050} />
        <FlowNode
          icon={<Wrench className="h-4 w-4" aria-hidden="true" />}
          title="Remediate"
          detail="safe · reversible"
          delay={1500}
        />
      </div>
    </div>
  )
}

function FlowNode({
  icon,
  title,
  detail,
  highlight = false,
  delay,
}: {
  icon: React.ReactNode
  title: string
  detail: string
  highlight?: boolean
  delay: number
}) {
  return (
    <div
      className={`flow-node flex flex-1 flex-col items-center gap-1.5 rounded-xl border bg-card/60 px-2 py-3 backdrop-blur sm:px-4 ${
        highlight ? 'border-primary/40' : 'border-border'
      }`}
      style={{ '--flow-delay': `${delay}ms` } as React.CSSProperties}
    >
      <span className="flow-icon relative inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
        {highlight && (
          <span
            className="validator-ring absolute inset-0 rounded-lg ring-2 ring-primary/50"
            aria-hidden="true"
          />
        )}
        {icon}
      </span>
      <span className="text-xs font-semibold text-foreground sm:text-sm">{title}</span>
      <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground sm:text-[11px]">
        {detail}
      </span>
    </div>
  )
}

/** Connector between flow nodes: a faint marching-dash rail carrying a bright
 *  signal packet that travels toward the arrow, timed off the shared
 *  --flow-delay so it hands the signal to the next stage on the beat. */
function FlowConnector({ delay }: { delay: number }) {
  return (
    <div
      className="flex items-center gap-1"
      style={{ '--flow-delay': `${delay}ms` } as React.CSSProperties}
      aria-hidden="true"
    >
      <span className="relative flex h-2 w-8 items-center sm:w-16">
        <span className="flow-wire absolute inset-x-0 top-1/2 -translate-y-1/2" />
        <span className="flow-spark" />
      </span>
      <ArrowRight className="h-3.5 w-3.5 text-primary/70" />
    </div>
  )
}

/**
 * Dashboard screenshot in a glass browser frame: a single scroll-reveal
 * entrance (fade + slight rise) when the showcase enters the viewport.
 */
function HeroShowcase() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <div ref={ref} className={`reveal${visible ? ' reveal-visible' : ''} mt-16 w-full sm:mt-20`}>
      <div className="mx-auto w-full max-w-4xl">
        <ShotFrame
          src="/screenshots/dashboard.png"
          alt="Constitutional AIOps operations dashboard showing live agent status, incidents, and telemetry"
          eager
        />
      </div>
    </div>
  )
}
