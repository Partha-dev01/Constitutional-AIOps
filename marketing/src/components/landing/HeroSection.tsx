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
          Two LLM agents read your telemetry and propose fixes. Every one clears the
          safety gate before it runs.
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
 * Detect -> constitution gate -> remediate, the core loop the product runs.
 * One unified panel split by hairline dividers into three stages, the gate
 * stage carrying a quiet primary accent. A single gentle fade-in on scroll; no
 * connectors, no looping animation.
 */
function HeroFlow() {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <div
      ref={ref}
      className={`reveal${visible ? ' reveal-visible' : ''} mt-12 w-full max-w-2xl`}
    >
      <div className="grid grid-cols-3 divide-x divide-border overflow-hidden rounded-xl border border-border bg-card/50 backdrop-blur">
        <FlowStage
          icon={<Radar className="h-4 w-4" aria-hidden="true" />}
          title="Detect"
          detail="logs · metrics · traces"
        />
        <FlowStage
          icon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />}
          title="Constitution gate"
          detail="12 principles · 3 tiers"
          highlight
        />
        <FlowStage
          icon={<Wrench className="h-4 w-4" aria-hidden="true" />}
          title="Remediate"
          detail="safe · reversible"
        />
      </div>
    </div>
  )
}

function FlowStage({
  icon,
  title,
  detail,
  highlight = false,
}: {
  icon: React.ReactNode
  title: string
  detail: string
  highlight?: boolean
}) {
  return (
    <div className="flex flex-col items-center gap-1.5 px-3 py-4 sm:px-5">
      <span
        className={`inline-flex h-7 w-7 items-center justify-center ${
          highlight ? 'text-primary' : 'text-muted-foreground'
        }`}
      >
        {icon}
      </span>
      <span className="text-xs font-semibold text-foreground sm:text-sm">{title}</span>
      <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground sm:text-[11px]">
        {detail}
      </span>
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
