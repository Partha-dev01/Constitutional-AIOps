import { Check, MessageSquarePlus, X } from 'lucide-react'
import { EpisodicDetail, FocusTarget, SchemaSeverity, kindAccent } from './types'

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
  /** True when this node/edge is already in the Ask-AI context set. */
  inContext: boolean
  onClose: () => void
  onToggleAskAi: (target: FocusTarget) => void
  /**
   * Episodic view only: pre-formatted detail for the clicked episodic node/edge.
   * When present it REPLACES the service-centric body (so episodic nodes aren't
   * mislabelled "Episodes (window)" etc.). Absent on the platform path → the
   * drawer renders exactly as before. The Ask-AI hand-off is unchanged.
   */
  episodic?: EpisodicDetail
  /**
   * Platform view only: when provided, each "Recent episode" card becomes a
   * button that hands a ready-made investigation prompt to the host chat (the
   * Console cockpit) so an operator can ask the LLM about that exact episode.
   */
  onAskEpisode?: (prompt: string) => void
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
export function DetailDrawer({ target, inContext, onClose, onToggleAskAi, episodic, onAskEpisode }: DetailDrawerProps) {
  const isNode = target.type === 'node'
  const title = episodic
    ? episodic.title
    : isNode
      ? target.node.label
      : `${target.edge.source} → ${target.edge.target}`

  return (
    <div
      className="schema-drawer absolute inset-y-3 right-3 z-30 flex w-72 max-w-[calc(100%-1.5rem)] flex-col overflow-hidden rounded-xl border border-slate-600/50 bg-slate-900/70 shadow-2xl shadow-black/50 ring-1 ring-inset ring-white/10 backdrop-blur-xl"
      data-testid="schema-drawer"
    >
      <div className="flex items-start justify-between gap-2 border-b border-white/[0.06] bg-white/[0.03] p-3">
        <div className="min-w-0">
          <h4 className="truncate text-sm font-semibold text-slate-100">{title}</h4>
          <span
            className="mt-1 inline-block rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide"
            style={
              episodic
                ? {
                    backgroundColor: `hsl(${episodic.accent} / 0.16)`,
                    color: `hsl(${episodic.accent})`,
                  }
                : isNode
                  ? {
                      backgroundColor: `hsl(${kindAccent(target.node.kind)} / 0.16)`,
                      color: `hsl(${kindAccent(target.node.kind)})`,
                    }
                  : { backgroundColor: 'rgb(51 65 85 / 0.7)', color: 'rgb(203 213 225)' }
            }
          >
            {episodic
              ? episodic.chip
              : isNode
                ? target.node.kind
                : `${target.edge.relationship} · ${target.edge.kind}`}
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
        {episodic ? (
          <>
            <div className="space-y-1.5 rounded-lg border border-slate-700/50 bg-slate-950/50 p-2.5">
              {episodic.rows.length > 0 ? (
                episodic.rows.map((row) => (
                  <div key={row.label} className="flex items-start justify-between gap-3 text-xs">
                    <span className="shrink-0 text-slate-500">{row.label}</span>
                    <span
                      className="text-right"
                      style={row.accent ? { color: `hsl(${row.accent})` } : { color: 'rgb(203 213 225)' }}
                    >
                      {row.value}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500">No additional detail.</p>
              )}
            </div>
            {episodic.note && (
              <p className="text-xs leading-relaxed text-slate-400">{episodic.note}</p>
            )}
          </>
        ) : isNode ? (
          <>
            <div className="space-y-1.5 rounded-lg border border-slate-700/50 bg-slate-950/50 p-2.5">
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
                  {target.node.recent_episodes.map((ep) => {
                    // Slim on purpose: this lands verbatim as the user's chat
                    // bubble. MUST keep an investigation keyword (investigate /
                    // root cause / remediat…) so the backend forces the evidence
                    // bundle, and the service label so the service resolves.
                    const askPrompt = `Investigate the ${ep.severity} episode "${ep.title}" on ${target.node.label}. What are the root cause and remediation?`
                    const body = (
                      <>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-medium capitalize ${SEVERITY_CHIP[ep.severity] ?? SEVERITY_CHIP.info}`}
                          >
                            {ep.severity}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {new Date(ep.at).toLocaleString()}
                          </span>
                          {onAskEpisode && (
                            <span className="ml-auto flex items-center gap-0.5 text-[10px] text-blue-400 opacity-0 transition-opacity group-hover:opacity-100">
                              <MessageSquarePlus className="h-3 w-3" /> Ask AI
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-xs leading-snug text-slate-300">{ep.title}</p>
                      </>
                    )
                    return onAskEpisode ? (
                      <li key={ep.id}>
                        <button
                          type="button"
                          onClick={() => onAskEpisode(askPrompt)}
                          data-testid="schema-ask-episode"
                          className="group w-full rounded-lg border border-slate-700/50 bg-slate-950/50 p-2 text-left transition-colors hover:border-blue-500/50 hover:bg-blue-500/[0.06]"
                        >
                          {body}
                        </button>
                      </li>
                    ) : (
                      <li
                        key={ep.id}
                        className="rounded-lg border border-slate-700/50 bg-slate-950/50 p-2"
                      >
                        {body}
                      </li>
                    )
                  })}
                </ul>
              ) : (
                <p className="text-xs text-slate-500">No episodes in this window.</p>
              )}
            </div>
          </>
        ) : (
          <div className="space-y-1.5 rounded-lg border border-slate-700/50 bg-slate-950/50 p-2.5">
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

      <div className="border-t border-white/[0.06] bg-white/[0.02] p-3">
        <button
          type="button"
          onClick={() => onToggleAskAi(target)}
          data-testid="schema-add-to-askai"
          aria-pressed={inContext}
          className={`flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            inContext
              ? 'border border-blue-500/40 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20'
              : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }`}
        >
          {inContext ? (
            <>
              <Check className="h-4 w-4" />
              In Ask AI · remove
            </>
          ) : (
            <>
              <MessageSquarePlus className="h-4 w-4" />
              Add to Ask AI
            </>
          )}
        </button>
      </div>
    </div>
  )
}
