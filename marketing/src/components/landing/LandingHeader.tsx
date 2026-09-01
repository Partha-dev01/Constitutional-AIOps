import { useEffect, useState } from 'react'
import { APP_URL, SHOW_SELFHOST } from '../../config'

// #self-host is only present when the SelfHostSection is rendered (post public
// flip), so its nav anchor is added conditionally to avoid a dead link.
const ANCHORS = [
  { href: '#features', label: 'Features' },
  { href: '#architecture', label: 'Architecture' },
  { href: '#live', label: 'Live demo' },
  { href: '#docs', label: 'Docs' },
  ...(SHOW_SELFHOST ? [{ href: '#self-host', label: 'Self-host' }] : []),
  { href: '#about', label: 'About' },
]

/**
 * Fixed glass header for the landing page. Transparent over the hero, gains
 * blur + tinted background + hairline once scrolled (rAF-throttled listener
 * toggling .is-scrolled — see .glass-header in styles/landing.css).
 *
 * Intentionally NOT a <nav>: the live e2e suite asserts the landing page has
 * zero <nav> elements (the only <nav> in the app belongs to the sidebar
 * Layout). Plain <a> anchors keep this a non-landmark header.
 */
export function LandingHeader() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    let frame = 0

    const apply = () => {
      frame = 0
      setScrolled(window.scrollY > 8)
    }

    const onScroll = () => {
      if (frame === 0) {
        frame = window.requestAnimationFrame(apply)
      }
    }

    apply()
    window.addEventListener('scroll', onScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', onScroll)
      if (frame !== 0) window.cancelAnimationFrame(frame)
    }
  }, [])

  return (
    <header className={`glass-header fixed inset-x-0 top-0 z-50${scrolled ? ' is-scrolled' : ''}`}>
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-6">
        {/* Brand (mirrors the app Layout wordmark) */}
        <a
          href="#top"
          className="flex items-center gap-2 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <img
            src="/logo-mark.png"
            alt=""
            aria-hidden="true"
            className="h-8 w-8"
          />
          <span className="text-base font-bold tracking-tight">Constitutional AIOps</span>
        </a>

        {/* Section anchors */}
        <div className="hidden items-center gap-1 md:flex">
          {ANCHORS.map((anchor) => (
            <a
              key={anchor.href}
              href={anchor.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {anchor.label}
            </a>
          ))}
        </div>

        {/* Primary pill */}
        <a
          href={APP_URL}
          data-testid="landing-signin"
          className="inline-flex items-center justify-center rounded-full bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          Sign in
        </a>
      </div>
    </header>
  )
}
