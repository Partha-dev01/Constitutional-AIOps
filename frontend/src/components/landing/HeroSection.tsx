import { Link } from 'react-router-dom'
import { Shield, ArrowRight, Cpu } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { useParallax } from '../../hooks/useParallax'
import { ShotFrame } from './ShotFrame'

/**
 * Landing hero. Pure static — no network calls. Aurora blobs + masked grid
 * are decorative (aria-hidden); the h1 text content is exactly
 * "Constitutional AIOps" (word-stagger spans only), which the live e2e suite
 * depends on.
 */
export function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      {/* Drifting aurora blobs (primary blue / violet / cyan) */}
      <div className="aurora aurora-a" aria-hidden="true" />
      <div className="aurora aurora-b" aria-hidden="true" />
      <div className="aurora aurora-c" aria-hidden="true" />

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
        <div
          className="hero-enter mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 text-xs font-medium text-muted-foreground"
        >
          <Cpu className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
          Simultaneous dual-model AIOps on a single GPU
        </div>

        <div className="mb-6 flex items-center justify-center gap-3">
          <Shield
            className="float-slow h-12 w-12 shrink-0 text-primary sm:h-16 sm:w-16"
            aria-hidden="true"
          />
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            <span className="hero-word" style={{ animationDelay: '80ms' }}>
              Constitutional
            </span>{' '}
            <span className="hero-word text-gradient" style={{ animationDelay: '240ms' }}>
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
          <Link
            to="/login?next=/"
            className="cta-glow group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Open the Dashboard
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              aria-hidden="true"
            />
          </Link>
          <a
            href="#architecture"
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            See how it works
          </a>
        </div>

        <HeroShowcase />
      </div>
    </section>
  )
}

/**
 * Dashboard screenshot in a glass browser frame: scroll-reveal entrance plus
 * a slight upward parallax drift (rAF-throttled; disabled entirely under
 * prefers-reduced-motion inside useParallax).
 */
function HeroShowcase() {
  const { ref, visible } = useReveal<HTMLDivElement>()
  const parallaxRef = useParallax<HTMLDivElement>(-0.06)

  return (
    <div ref={ref} className={`reveal${visible ? ' reveal-visible' : ''} mt-16 w-full sm:mt-20`}>
      <div ref={parallaxRef} className="mx-auto w-full max-w-4xl">
        <ShotFrame
          src="/screenshots/dashboard.png"
          alt="Constitutional AIOps operations dashboard showing live agent status, incidents, and telemetry"
          eager
        />
      </div>
    </div>
  )
}
