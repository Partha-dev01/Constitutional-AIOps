/**
 * Sparkline — a tiny inline-SVG line/area chart with NO charting dependency.
 *
 * Plots only the real sampled points it is given (no interpolation, no
 * fabricated history): 0 points renders an honest empty baseline, 1 point
 * renders a single dot. The viewBox is a fixed 100xH coordinate space scaled to
 * the container via width:100%, so it stays crisp and responsive at any size.
 */

export interface SparklineProps {
  /** The real sampled values, oldest first. */
  values: number[]
  /** Fixed lower/upper bounds (e.g. 0..100 for a percentage). Omit to autoscale. */
  min?: number
  max?: number
  /** Stroke color (any CSS color). Defaults to currentColor. */
  color?: string
  /** Fill a soft area under the line. */
  area?: boolean
  /** Rendered height in px (the width fills the container). */
  height?: number
  className?: string
  /** Accessible label for screen readers. */
  ariaLabel?: string
}

const VIEW_W = 100

export function Sparkline({
  values,
  min,
  max,
  color = 'currentColor',
  area = true,
  height = 40,
  className = '',
  ariaLabel,
}: SparklineProps) {
  const H = 100 // internal viewBox height; scaled by the SVG's height attr
  const pad = 6 // keep the line off the very edge so the dot/stroke isn't clipped

  const clean = values.filter((v) => Number.isFinite(v))

  if (clean.length === 0) {
    return (
      <svg
        viewBox={`0 0 ${VIEW_W} ${H}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={ariaLabel || 'no data yet'}
        className={className}
        style={{ width: '100%', height, display: 'block' }}
      >
        <line
          x1={0}
          y1={H - pad}
          x2={VIEW_W}
          y2={H - pad}
          stroke="currentColor"
          strokeOpacity={0.15}
          strokeWidth={1}
          strokeDasharray="3 3"
        />
      </svg>
    )
  }

  const lo = min ?? Math.min(...clean)
  const hiRaw = max ?? Math.max(...clean)
  // Guard a flat series (lo === hi) so we don't divide by zero.
  const hi = hiRaw > lo ? hiRaw : lo + 1

  const n = clean.length
  const xFor = (i: number) => (n === 1 ? VIEW_W / 2 : (i / (n - 1)) * VIEW_W)
  const yFor = (v: number) => {
    const t = (v - lo) / (hi - lo)
    const clamped = Math.max(0, Math.min(1, t))
    return pad + (1 - clamped) * (H - pad * 2)
  }

  const points = clean.map((v, i) => `${xFor(i).toFixed(2)},${yFor(v).toFixed(2)}`)
  const linePath = `M ${points.join(' L ')}`
  const areaPath = `${linePath} L ${xFor(n - 1).toFixed(2)},${H} L ${xFor(0).toFixed(2)},${H} Z`

  const lastX = xFor(n - 1)
  const lastY = yFor(clean[n - 1])

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${H}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={ariaLabel || `${clean[n - 1].toFixed(1)} latest`}
      className={className}
      style={{ width: '100%', height, display: 'block', color }}
    >
      {area && n > 1 && (
        <path d={areaPath} fill={color} fillOpacity={0.12} stroke="none" />
      )}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={1.6}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={lastX} cy={lastY} r={2} fill={color} vectorEffect="non-scaling-stroke" />
    </svg>
  )
}
