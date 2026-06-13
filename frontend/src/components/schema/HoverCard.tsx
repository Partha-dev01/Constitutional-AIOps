import { FocusTarget } from './types'

const HEALTH_TEXT: Record<string, string> = {
  healthy: 'text-green-400',
  warning: 'text-amber-400',
  critical: 'text-red-400',
  unknown: 'text-slate-400',
}

interface HoverCardProps {
  target: FocusTarget
  /** Position in px, relative to the svg host container. */
  x: number
  y: number
}

/**
 * Lightweight hover tooltip. Rendered as an HTML overlay div positioned over
 * the svg host (NOT a foreignObject), pointer-events disabled so it can never
 * steal canvas interactions.
 */
export function HoverCard({ target, x, y }: HoverCardProps) {
  return (
    <div
      className="schema-hover-card pointer-events-none absolute z-20 max-w-[240px] rounded-lg border border-slate-700/80 bg-slate-900/95 px-3 py-2 text-xs shadow-xl backdrop-blur-sm"
      style={{ left: x + 14, top: y + 10 }}
      data-testid="schema-hover-card"
    >
      {target.type === 'node' ? (
        <>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-100">{target.node.label}</span>
            <span className="rounded bg-slate-700/70 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
              {target.node.kind}
            </span>
          </div>
          <div className="mt-1 space-y-0.5 text-slate-400">
            <div>
              Health:{' '}
              <span className={`capitalize ${HEALTH_TEXT[target.node.health] ?? HEALTH_TEXT.unknown}`}>
                {target.node.health}
              </span>
            </div>
            <div>
              {target.node.episode_count} episode{target.node.episode_count === 1 ? '' : 's'} ·{' '}
              {target.node.incident_count} incident{target.node.incident_count === 1 ? '' : 's'}
            </div>
            {target.node.last_episode_at && (
              <div>Last: {new Date(target.node.last_episode_at).toLocaleString()}</div>
            )}
          </div>
        </>
      ) : (
        <>
          <div className="font-semibold text-slate-100">
            {target.edge.source} → {target.edge.target}
          </div>
          <div className="mt-1 space-y-0.5 text-slate-400">
            <div>
              {target.edge.relationship === 'SHIPS_TELEMETRY' ? 'ships telemetry' : 'depends on'} ·{' '}
              {target.edge.kind}
            </div>
            <div>
              {target.edge.co_episode_count} co-episode
              {target.edge.co_episode_count === 1 ? '' : 's'} in window
            </div>
          </div>
        </>
      )}
    </div>
  )
}
