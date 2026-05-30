import { Link } from 'react-router-dom'
import { Shield, ArrowRight, Cpu } from 'lucide-react'

/**
 * Landing hero. Pure static — no network calls. The animated gradient/grid
 * backdrop is built from design-token colors so it tracks the dark theme.
 */
export function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b border-border">
      {/* Animated gradient wash */}
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          background:
            'radial-gradient(60% 50% at 50% 0%, hsl(var(--primary) / 0.25), transparent 70%), linear-gradient(120deg, hsl(var(--primary) / 0.10), transparent, hsl(var(--primary) / 0.10))',
          backgroundSize: '200% 200%',
          animation: 'gradient-drift 18s ease-in-out infinite',
        }}
        aria-hidden="true"
      />
      {/* Subtle grid overlay using the border token */}
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

      <div
        className="relative mx-auto flex max-w-5xl flex-col items-center px-6 py-24 text-center sm:py-32"
        style={{ animation: 'fade-in .8s ease-out both' }}
      >
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 text-xs font-medium text-muted-foreground backdrop-blur">
          <Cpu className="h-3.5 w-3.5 text-primary" />
          Simultaneous dual-model AIOps
        </div>

        <div className="mb-6 flex items-center justify-center gap-3">
          <Shield className="h-12 w-12 text-primary sm:h-16 sm:w-16" />
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            Constitutional <span className="text-primary">AIOps</span>
          </h1>
        </div>

        <p className="max-w-2xl text-balance text-lg text-muted-foreground sm:text-xl">
          An autonomous infrastructure-operations system built on a dual-agent LLM
          core, a 12-principle Constitutional AI safety framework, and graph-episodic
          memory for incident correlation.
        </p>

        <p className="mt-4 text-sm text-muted-foreground">
          A B.Tech final-year research project — [redacted]
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <Link
            to="/"
            className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5"
          >
            Open the Dashboard
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            to="/agents"
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:border-primary/50 hover:text-primary"
          >
            Explore the Agent Hub
          </Link>
        </div>
      </div>
    </section>
  )
}
