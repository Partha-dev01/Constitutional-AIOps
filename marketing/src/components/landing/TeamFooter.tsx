import { GraduationCap, ArrowRight } from 'lucide-react'
import { APP_URL } from '../../config'

// Full page sitemap. Standalone content pages by their own URL; the live demo
// stays a landing-section anchor (absolute, so it resolves from any page).
const SECTION_LINKS = [
  { href: '/features.html', label: 'Features' },
  { href: '/architecture.html', label: 'Architecture' },
  { href: '/safety.html', label: 'Safety' },
  { href: '/benchmark.html', label: 'Benchmark' },
  { href: '/usecases.html', label: 'Use cases' },
  { href: '/faq.html', label: 'FAQ' },
  { href: '/docs.html', label: 'Docs' },
  { href: '/opensource.html', label: 'Open source' },
  { href: '/#live', label: 'Live demo' },
]

export function TeamFooter() {
  return (
    <footer id="about" className="relative border-t border-border pb-12 pt-20 sm:pt-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-12 md:grid-cols-3">
          {/* Brand */}
          <div>
            <div className="mb-4 flex items-center gap-2">
              <img
                src="/logo-mark.png"
                alt=""
                aria-hidden="true"
                className="h-8 w-8"
              />
              <span className="text-lg font-bold">Constitutional AIOps</span>
            </div>
            <p className="max-w-xs text-sm leading-relaxed text-muted-foreground">
              Autonomous infrastructure operations gated by a constitutional
              safety framework — dual LLM agents, graph memory, and graduated
              human trust.
            </p>
          </div>

          {/* Section links */}
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Explore
            </h3>
            <ul className="space-y-2">
              {SECTION_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="rounded-md text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* About */}
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-xs font-medium text-muted-foreground">
              <GraduationCap className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
              Academic research project
            </div>
            <p className="max-w-xs text-sm leading-relaxed text-muted-foreground">
              An engineering research project exploring constitutional safety
              for autonomous, LLM-driven infrastructure operations.
            </p>
          </div>
        </div>

        <div className="mt-14 flex flex-col items-center gap-8 border-t border-border pt-10 sm:flex-row sm:justify-between">
          <a
            href={APP_URL}
            className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Open the Dashboard
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              aria-hidden="true"
            />
          </a>

          <p className="text-xs text-muted-foreground">
            Constitutional AIOps · v1.0.0
          </p>
        </div>
      </div>
    </footer>
  )
}
