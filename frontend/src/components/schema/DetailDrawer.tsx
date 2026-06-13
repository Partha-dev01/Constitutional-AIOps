import { MessageSquarePlus, X } from 'lucide-react'
import { FocusTarget, SchemaSeverity, kindAccent } from './types'

const SEVERITY_CHIP: Record<SchemaSeverity, string> = {
  info: 'bg-blue-500/15 text-blue-400',
  warning: 'bg-amber-500/15 text-amber-400',
  error: 'bg-orange-500/15 text-orange-400',
  critical: 'bg-red-500/15 text-red-400',
}

const HEALTH_TEXT: Record<string, string> = {
  healthy: 'text-green-400',
  warning: 'text-amber-400',
  critical: 'text-red-400',
  unknown: 'text-slate-400',
}

interface DetailDrawerProps {
  target: FocusTarget
  onClose: () => void
  onAddToAskAi: (target: FocusTarget) => void
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-start justify-between gap-3 text-xs">
      <span className="shrink-0 text-slate-500">{label}</span>
      <span className="text-right text-slate-300">{value}</span>
    </div>
  )
}

/**
 * Right slide-in drawer with the full detail of the clicked node or edge,
 * recent episodes with severity chips, and an "Add to Ask AI" hand-off.
 */
export function DetailDrawer({ target, onClose, onAddToAskAi }: DetailDrawerProps) {
  const isNode = target.type === 'node'
  const title = isNode ? target.node.label : `${target.edge.source} → ${target.edge.target}`

  return (
    <div
      className="schema-drawer absolute inset-y-0 right-0 z-30 flex w-72 flex-col overflow-hidden rounded-r-lg border-l border-slate-700/80 bg-slate-900/95 shadow-2xl backdrop-blur-md"
      data-testid="schema-drawer"
    >
      <div className="flex items-start justify-between gap-2 border-b border-slate-800 p-3">
        <div className="min-w-0">
          <h4 className="truncate text-sm font-semibold text-slate-100">{title}</h4>
          <span
            className="mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide"
            style={
              isNode
                ? {
                    backgroundColor: `hsl(${kindAccent(target.node.kind)} / 0.16)`,
                    color: `hsl(${kindAccent(target.node.kind)})`,
                  }
                : { backgroundColor: 'rgb(51 65 85 / 0.7)', color: 'rgb(203 213 225)' }
            }
          >
            {isNode ? target.node.kind : `${target.edge.relationship} · ${target.edge.kind}`}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close details"
          className="rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-slate-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
        {isNode ? (
          <>
            <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-950/40 p-2.5">
              <div className="flex items-start justify-between gap-3 text-xs">
                <span className="shrink-0 text-slate-500">Health</span>
                <span className={`font-medium capitalize ${HEALTH_TEXT[target.node.health] ?? HEALTH_TEXT.unknown}`}>
                  {target.node.health}
                </span>
              </div>
              {target.node.health_reason && (
                <p className="text-[11px] leading-snug text-slate-500">{target.node.health_reason}</p>
              )}
              <Row label="Episodes (window)" value={target.node.episode_count} />
              <Row label="Incidents" value={target.node.incident_count} />
              {target.node.last_episode_at && (
                <Row label="Last episode" value={new Date(target.node.last_episode_at).toLocaleString()} />
              )}
              {target.node.meta.port != null && <Row label="Port" value={`:${target.node.meta.port}`} />}
              {target.node.meta.edge_label && <Row label="Edge host" value={target.node.meta.edge_label} />}
            </div>

            {target.node.meta.description && (
              <p className="text-xs leading-relaxed text-slate-400">{target.node.meta.description}</p>
            )}

            <div>
              <h5 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Recent episodes
              </h5>
              {target.node.recent_episodes.length > 0 ? (
                <ul className="space-y-1.5">
                  {target.node.recent_episodes.map((ep) => (
                    <li
                      key={ep.id}
                      className="rounded-lg border border-slate-800 bg-slate-950/40 p-2"
                    >
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-medium capitalize ${SEVERITY_CHIP[ep.severity] ?? SEVERITY_CHIP.info}`}
                        >
                          {ep.severity}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {new Date(ep.at).toLocaleString()}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-snug text-slate-300">{ep.title}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">No episodes in this window.</p>
              )}
            </div>
          </>
        ) : (
          <div className="space-y-1.5 rounded-lg border border-slate-800 bg-slate-950/40 p-2.5">
            <Row label="Relationship" value={target.edge.relationship} />
            <Row label="Kind" value={target.edge.kind} />
            <Row label="Co-episodes (window)" value={target.edge.co_episode_count} />
            <p className="pt-1 text-[11px] leading-snug text-slate-500">
              {target.edge.relationship === 'SHIPS_TELEMETRY'
                ? 'Telemetry shipped from a dynamically discovered edge host.'
                : 'Static platform dependency from the topology seed.'}
            </p>
          </div>
        )}
      </div>

      <div className="border-t border-slate-800 p-3">
        <button
          type="button"
          onClick={() => onAddToAskAi(target)}
          data-testid="schema-add-to-askai"
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <MessageSquarePlus className="h-4 w-4" />
          Add to Ask AI
        </button>
      </div>
    </div>
  )
}
