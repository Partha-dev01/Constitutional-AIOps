import { Shield, ArrowRight } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'
import { ShotFrame } from './ShotFrame'
import { APP_URL } from '../../config'

/**
 * Landing hero. Pure static — no network calls. The masked grid is
 * decorative (aria-hidden); the h1 text content is exactly
 * "Constitutional AIOps" (word-stagger spans only), which the live e2e suite
 * depends on.
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
        <div className="mb-6 flex items-center justify-center gap-3">
          <Shield
            className="h-12 w-12 shrink-0 text-primary sm:h-16 sm:w-16"
            aria-hidden="true"
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
            Open the Dashboard
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              aria-hidden="true"
            />
          </a>
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
