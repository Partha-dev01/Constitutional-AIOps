import type { EpisodicLink, EpisodicNode } from '../EpisodicGraphExplorer'
import { EpisodeBrowser } from '../episodic/EpisodeBrowser'
import type { SelectedItem } from './types'

// ---------------------------------------------------------------------------
// Episodic view — thin adapter.
//
// The Console's episodic toggle used to render every episode, root cause,
// service, action and entity (plus the dense similar_to web) onto the shared
// platform topology canvas at once. That produced an unreadable hairball with
// truncated titles and confusing "+N hidden" filter pills.
//
// The episodic experience is now the EpisodeBrowser (a searchable episode list
// + per-episode focused causal subgraph). This module stays as the named export
// the Console lazy-imports, so the page wiring is unchanged; it simply forwards
// to the browser. The shared schema canvas / drawer / hover card are reused by
// the browser WITHOUT modification, so the platform topology and /graph page are
// untouched.
// ---------------------------------------------------------------------------

interface EpisodicSchemaGraphProps {
  nodes: EpisodicNode[]
  links: EpisodicLink[]
  loading?: boolean
  /** Explicit pane height (the Console measures its pane and feeds this). */
  height?: number
  /** Notified whenever the canvas selection set changes (Console → chat ctx). */
  onSelectionChange?: (items: SelectedItem[]) => void
  /** When provided, "Ask AI" seeds the host chat composer with an episode prompt. */
  onAskEpisode?: (prompt: string) => void
}

/**
 * Episodic memory, rendered as a browsable master/detail experience. A direct
 * swap-in for the Console's episodic branch (same props as before, plus an
 * optional `onAskEpisode` hand-off).
 */
export function EpisodicSchemaGraph({
  nodes,
  links,
  loading = false,
  height = 520,
  onSelectionChange,
  onAskEpisode,
}: EpisodicSchemaGraphProps) {
  return (
    <EpisodeBrowser
      nodes={nodes}
      links={links}
      loading={loading}
      height={height}
      onSelectionChange={onSelectionChange}
      onAskEpisode={onAskEpisode}
    />
  )
}

export default EpisodicSchemaGraph
