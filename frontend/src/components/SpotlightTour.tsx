/**
 * SpotlightTour - the post-setup guided intro, rendered as a full-page coach
 * mark: a dimmed scrim with a spotlight cut out around the current target
 * element, plus a callout anchored beside it. State lives in lib/tour/store;
 * content in lib/tour/spotlightSteps.
 *
 * Robustness the plain-modal version did not need, because this one tracks real
 * DOM:
 *  - The target is resolved to the first on-screen match of its data-tour
 *    attribute, so the duplicated desktop/mobile sidebars never mislead it, and
 *    an off-canvas or display:none copy is ignored.
 *  - A step whose target is not on screen (icon rail, mobile drawer) degrades to
 *    a centered card rather than pointing at nothing.
 *  - The hole and callout re-measure on resize and scroll.
 *  - Auto-start is gated on navigator.webdriver by the caller, so E2E and
 *    synthetic sessions are never hijacked.
 */
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ArrowRight } from 'lucide-react'

import { SPOTLIGHT_STEPS } from '../lib/tour/spotlightSteps'
import { useProductTour } from '../lib/tour/store'

interface Rect {
  top: number
  left: number
  width: number
  height: number
}

const HOLE_PAD = 8
const GAP = 16
const MASK_ID = 'spotlight-tour-mask'

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

/** First on-screen element matching the data-tour value; null if none visible. */
function resolveTarget(target: string): Rect | null {
  const vw = window.innerWidth
  const vh = window.innerHeight
  const els = Array.from(document.querySelectorAll<HTMLElement>(`[data-tour="${target}"]`))
  for (const el of els) {
    const r = el.getBoundingClientRect()
    if (r.width <= 0 || r.height <= 0) continue
    const cx = r.left + r.width / 2
    const cy = r.top + r.height / 2
    // Ignore off-canvas / off-screen copies (e.g. the closed mobile drawer).
    if (cx < 0 || cx > vw || cy < 0 || cy > vh) continue
    return { top: r.top, left: r.left, width: r.width, height: r.height }
  }
  return null
}

/** Position the callout: beside a left-hand target if there is room, else below,
 * else above; centered when there is no target. */
function calloutStyle(rect: Rect | null, vw: number, vh: number): React.CSSProperties {
  const cardW = Math.min(360, vw - 32)
  if (!rect || vw === 0) {
    return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: cardW }
  }
  const roomRight = vw - (rect.left + rect.width)
  // Sidebar case: target on the left with room to its right.
  if (rect.left < vw * 0.45 && roomRight > cardW + GAP * 2) {
    return {
      left: rect.left + rect.width + GAP,
      top: clamp(rect.top - 8, GAP, Math.max(GAP, vh - 260)),
      width: cardW,
    }
  }
  const left = clamp(rect.left, GAP, Math.max(GAP, vw - cardW - GAP))
  const spaceBelow = vh - (rect.top + rect.height)
  if (spaceBelow > 260) {
    return { left, top: rect.top + rect.height + GAP, width: cardW }
  }
  return { left, bottom: vh - rect.top + GAP, width: cardW }
}

export function SpotlightTour() {
  const open = useProductTour((s) => s.open)
  const index = useProductTour((s) => s.index)
  const next = useProductTour((s) => s.next)
  const back = useProductTour((s) => s.back)
  const close = useProductTour((s) => s.close)
  const navigate = useNavigate()

  const step = SPOTLIGHT_STEPS[index]
  const [rect, setRect] = useState<Rect | null>(null)
  const [vp, setVp] = useState({ w: 0, h: 0 })
  const primaryRef = useRef<HTMLButtonElement>(null)

  // Measure the target and viewport, and keep them current while the tour runs.
  useLayoutEffect(() => {
    if (!open || !step) return
    const el = step.target
      ? document.querySelector<HTMLElement>(`[data-tour="${step.target}"]`)
      : null
    el?.scrollIntoView({ block: 'center', inline: 'nearest' })

    const measure = () => {
      setVp({ w: window.innerWidth, h: window.innerHeight })
      setRect(step.target ? resolveTarget(step.target) : null)
    }
    measure()
    const raf = window.requestAnimationFrame(measure)
    window.addEventListener('resize', measure)
    window.addEventListener('scroll', measure, true)
    return () => {
      window.cancelAnimationFrame(raf)
      window.removeEventListener('resize', measure)
      window.removeEventListener('scroll', measure, true)
    }
  }, [open, index, step])

  // Move focus to the primary action on each step so keyboard users follow along.
  useEffect(() => {
    if (open) primaryRef.current?.focus()
  }, [open, index])

  // Esc leaves the tour.
  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') close()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, close])

  if (!open || !step) return null

  const isLast = index === SPOTLIGHT_STEPS.length - 1
  const Icon = step.icon
  const primaryLabel = isLast ? step.cta ?? 'Done' : 'Next'

  const onPrimary = () => {
    if (isLast && step.to) navigate(step.to)
    next()
  }

  const hole = rect
    ? {
        x: Math.max(rect.left - HOLE_PAD, 0),
        y: Math.max(rect.top - HOLE_PAD, 0),
        w: rect.width + HOLE_PAD * 2,
        h: rect.height + HOLE_PAD * 2,
      }
    : null

  return (
    <div
      className="fixed inset-0 z-120"
      role="dialog"
      aria-modal="true"
      aria-labelledby="spotlight-tour-title"
    >
      {/* Dimmed scrim with the spotlight hole punched out (visual only). */}
      {vp.w > 0 && (
        <svg
          className="pointer-events-none absolute inset-0"
          width={vp.w}
          height={vp.h}
          aria-hidden="true"
        >
          <defs>
            <mask id={MASK_ID}>
              <rect x="0" y="0" width={vp.w} height={vp.h} fill="white" />
              {hole && (
                <rect x={hole.x} y={hole.y} width={hole.w} height={hole.h} rx="12" fill="black" />
              )}
            </mask>
          </defs>
          <rect
            x="0"
            y="0"
            width={vp.w}
            height={vp.h}
            fill="rgb(2 6 23 / 0.72)"
            mask={`url(#${MASK_ID})`}
          />
          {hole && (
            <rect
              x={hole.x}
              y={hole.y}
              width={hole.w}
              height={hole.h}
              rx="12"
              fill="none"
              strokeWidth="2"
              className="stroke-primary motion-safe:animate-pulse"
            />
          )}
        </svg>
      )}

      {/* Callout card. */}
      <div
        className="absolute max-h-[85vh] overflow-y-auto rounded-2xl border border-border bg-card p-5 text-left shadow-xl"
        style={calloutStyle(rect, vp.w, vp.h)}
      >
        <div className="flex items-start gap-4">
          <div
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary ring-1 ring-inset ring-primary/20"
            aria-hidden="true"
          >
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h2 id="spotlight-tour-title" className="text-sm font-semibold text-foreground">
              {step.title}
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground" aria-live="polite">
              {step.body}
            </p>
          </div>
        </div>

        {/* Progress dots */}
        <div className="mt-5 flex items-center justify-center gap-1.5" aria-hidden="true">
          {SPOTLIGHT_STEPS.map((s, i) => (
            <span
              key={s.id}
              className={
                i === index
                  ? 'h-1.5 w-5 rounded-full bg-primary transition-all'
                  : 'h-1.5 w-1.5 rounded-full bg-muted-foreground/30 transition-all'
              }
            />
          ))}
        </div>

        {/* Footer */}
        <div className="mt-5 flex items-center justify-between gap-3">
          <span className="text-xs text-muted-foreground">
            Step {index + 1} of {SPOTLIGHT_STEPS.length}
          </span>
          <div className="flex items-center gap-2">
            {!isLast && (
              <button
                type="button"
                onClick={close}
                className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/40"
              >
                Skip
              </button>
            )}
            {index > 0 && (
              <button
                type="button"
                onClick={back}
                className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/40"
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
                Back
              </button>
            )}
            <button
              ref={primaryRef}
              type="button"
              onClick={onPrimary}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-hidden focus:ring-2 focus:ring-primary/40"
            >
              {primaryLabel}
              {isLast && step.to && <ArrowRight className="h-4 w-4" aria-hidden="true" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SpotlightTour
