import { Lock } from 'lucide-react'
import { useReveal } from '../../hooks/useReveal'

interface Shot {
  name: string
  alt: string
}

const SHOTS: Shot[] = [
  { name: 'dashboard', alt: 'Operations dashboard' },
  { name: 'agent-hub', alt: 'Agent hub' },
  { name: 'graph-explorer', alt: 'Episodic graph explorer' },
  { name: 'chat', alt: 'Reasoning-agent chat' },
  { name: 'metrics', alt: 'Metrics view' },
  { name: 'benchmark', alt: 'Benchmark results' },
]

/**
 * Screenshots are referenced as root-absolute paths under /screenshots and may
 * not exist yet (they are captured later). Each <img> hides itself on error so
 * the section degrades gracefully to a clean empty grid with zero broken icons.
 */
export function ProofSection() {
  const { ref, visible } = useReveal<HTMLDivElement>()

  return (
    <section className="border-b border-border py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-6 max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            See it running
          </h2>
          <p className="mt-4 text-muted-foreground">
            A live, self-hosted system — not a mockup.
          </p>
        </div>

        <div className="mb-12 flex justify-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-xs text-muted-foreground">
            <Lock className="h-3.5 w-3.5 text-primary" />
            Live system — basic-auth protected.
          </div>
        </div>

        <div
          ref={ref}
          className={`reveal${visible ? ' reveal-visible' : ''} grid gap-6 sm:grid-cols-2 lg:grid-cols-3`}
        >
          {SHOTS.map((shot) => (
            <figure
              key={shot.name}
              className="overflow-hidden rounded-lg border border-border bg-card transition-colors hover:border-primary/50"
            >
              <img
                src={`/screenshots/${shot.name}.png`}
                alt={shot.alt}
                loading="lazy"
                className="block w-full"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).style.display = 'none'
                }}
              />
              <figcaption className="px-4 py-3 text-sm font-medium text-muted-foreground">
                {shot.alt}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  )
}
