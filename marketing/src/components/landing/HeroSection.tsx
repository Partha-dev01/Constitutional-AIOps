import { Radar, ShieldCheck, Wrench } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { ShotFrame } from './ShotFrame'
import { CtaButton, GlassCard } from '../ui'
import { APP_URL, DEMO_URL } from '../../config'

/**
 * Landing hero (translucent redesign). Pure static — no network calls. The
 * masked grid is decorative (aria-hidden); the h1 text content is exactly
 * "Constitutional AIOps" (word-stagger spans only), which the live e2e suite
 * depends on.
 *
 * Composition: the glowing wordmark, the product promise, the launch CTAs
 * (Sign in carries APP_URL), a floating glass "detect → gate → remediate" flow
 * strip, then the product showcase floating on an accent glow. No claim/badge
 * pills and no stat duplicated here — the numbers live in the StatsBand below.
 */
export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Subtle grid overlay using the border token, masked to the hero core */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.1]"
        style={{
          backgroundImage:
            'linear-gradient(hsl(var(--border)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--border)) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(72% 60% at 50% 26%, black, transparent 78%)',
          WebkitMaskImage: 'radial-gradient(72% 60% at 50% 26%, black, transparent 78%)',
        }}
        aria-hidden="true"
      />

      <div className="relative mx-auto flex max-w-5xl flex-col items-center px-6 pb-20 pt-32 text-center sm:pb-28 sm:pt-40">
        <img
          src="/logo-mark.png"
          alt=""
          aria-hidden="true"
          className="logo-glow h-20 w-20 shrink-0 sm:h-24 sm:w-24"
        />

        <h1 className="mt-6 text-5xl font-extrabold leading-[0.98] tracking-tight sm:text-8xl">
          <span className="hero-word" style={{ animationDelay: '80ms' }}>
            Constitutional
          </span>{' '}
          <span
            className="hero-word bg-gradient-to-br from-primary via-[hsl(230_90%_66%)] to-[hsl(268_88%_68%)] bg-clip-text text-transparent"
            style={{ animationDelay: '240ms' }}
          >
            AIOps
          </span>
        </h1>

        <p
          className="hero-enter mt-6 max-w-2xl text-balance text-lg font-medium text-foreground sm:text-2xl"
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
          <CtaButton href={APP_URL} arrow>
            Sign in
          </CtaButton>
          <CtaButton href={DEMO_URL} variant="secondary">
            Demo mode
          </CtaButton>
        </div>

        <HeroFlow />

        <HeroShowcase />
      </div>
    </section>
  )
}

/**
 * Detect → constitution gate → remediate, the core loop the product runs. One
 * floating glass panel split by hairline dividers into three stages, the gate
 * stage carrying a quiet primary accent. A single gentle fade-in on scroll.
 */
function HeroFlow() {
  const { ref, visible } = useReveal<HTMLDivElement>()
  return (
    <div
      ref={ref}
      className={`reveal${visible ? ' reveal-visible' : ''} mt-14 w-full max-w-2xl`}
    >
      <GlassCard className="grid grid-cols-3 divide-x divide-white/10 overflow-hidden" radius="2xl">
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
      </GlassCard>
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
        className={`inline-flex h-8 w-8 items-center justify-center rounded-full ${
          highlight ? 'bg-primary/15 text-primary' : 'bg-white/5 text-muted-foreground'
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
 * Dashboard screenshot floating on a soft accent glow, in a glass browser
 * frame: a single scroll-reveal entrance (fade + slight rise) when the showcase
 * enters the viewport. A faint offset backing panel adds depth (upscayl-style).
 */
function HeroShowcase() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <div ref={ref} className={`reveal${visible ? ' reveal-visible' : ''} relative mt-20 w-full sm:mt-28`}>
      {/* Accent glow behind the product panel */}
      <div
        className="glow-halo left-1/2 top-2 h-72 w-[86%] -translate-x-1/2"
        aria-hidden="true"
      />
      <div className="relative mx-auto w-full max-w-4xl">
        {/* Offset backing panel peeking behind for layered depth */}
        <div
          className="glass absolute -inset-x-4 -bottom-5 top-8 -z-10 rounded-3xl opacity-70 sm:-inset-x-10"
          aria-hidden="true"
        />
        <ShotFrame
          src="/screenshots/dashboard.png"
          alt="Constitutional AIOps operations dashboard showing live agent status, incidents, and telemetry"
          eager
        />
      </div>
    </div>
  )
}
