/**
 * Episode Browser — drawer/hover detail builders.
 *
 * The shared DetailDrawer / HoverCard accept an optional pre-formatted
 * `EpisodicDetail` block so episodic nodes/edges read with episodic-appropriate
 * rows (severity, root cause, success rate…) instead of the service-centric
 * defaults. These pure builders pull those fields off the original record.
 */

import type { EpisodicLink, EpisodicNode } from '../EpisodicGraphExplorer'
import type { EpisodicDetail } from '../schema/types'
import { edgeAccentFor, nodeAccentFor, titleCase } from './episodeGraph'

export function nodeDetail(node: EpisodicNode): EpisodicDetail {
  const accent = nodeAccentFor(node.type, node.status)
  const rows: EpisodicDetail['rows'] = []

  if (node.status) rows.push({ label: 'Status', value: titleCase(node.status), accent })

  if (node.type === 'episode' || node.type === 'incident') {
    if (node.severity) rows.push({ label: 'Severity', value: titleCase(node.severity) })
    if (node.category) rows.push({ label: 'Category', value: titleCase(node.category) })
    if (node.rootCause) rows.push({ label: 'Root cause', value: titleCase(node.rootCause) })
    if (node.confidence !== undefined) {
      rows.push({ label: 'Confidence', value: `${Math.round(node.confidence * 100)}%` })
    }
    if (node.resolutionTime !== undefined) {
      rows.push({ label: 'Resolution', value: `${node.resolutionTime} min` })
    }
    if (node.timestamp) {
      rows.push({ label: 'Detected', value: new Date(node.timestamp).toLocaleString() })
    }
  } else if (node.type === 'root_cause') {
    if (node.frequency !== undefined) rows.push({ label: 'Occurrences', value: String(node.frequency) })
    if (node.avgResolutionTime !== undefined) {
      rows.push({ label: 'Avg resolution', value: `${node.avgResolutionTime} min` })
    }
    if (node.successRate !== undefined) {
      rows.push({ label: 'Success rate', value: `${Math.round(node.successRate * 100)}%` })
    }
  } else if (node.type === 'action') {
    if (node.usedCount !== undefined) rows.push({ label: 'Used', value: `${node.usedCount}×` })
    if (node.successRate !== undefined) {
      rows.push({ label: 'Success rate', value: `${Math.round(node.successRate * 100)}%` })
    }
    if (node.avgExecutionTime !== undefined) {
      rows.push({ label: 'Avg execution', value: `${node.avgExecutionTime}s` })
    }
  } else if (node.type === 'service') {
    if (node.incidentCount !== undefined) {
      rows.push({ label: 'Incidents', value: String(node.incidentCount) })
    }
    if (node.lastIncident) {
      rows.push({ label: 'Last incident', value: new Date(node.lastIncident).toLocaleString() })
    }
  } else if (node.type === 'entity') {
    if (node.relationCount !== undefined) {
      rows.push({ label: 'Relations', value: String(node.relationCount) })
    }
  }

  return { title: node.label, chip: titleCase(node.type), accent, rows }
}

export function edgeDetail(link: EpisodicLink): EpisodicDetail {
  const accent = edgeAccentFor(link)
  const relation = link.label ?? link.type ?? 'related'
  const rows: EpisodicDetail['rows'] = [
    { label: 'Relationship', value: titleCase(relation), accent },
  ]
  if (link.weight !== undefined) rows.push({ label: 'Weight', value: String(link.weight) })
  const source = typeof link.source === 'string' ? link.source : link.source.id
  const target = typeof link.target === 'string' ? link.target : link.target.id
  const isLlm = link.metadata?.extraction_method === 'llm'
  return {
    title: `${source} → ${target}`,
    chip: titleCase(relation),
    accent,
    rows,
    note: isLlm
      ? 'LLM-extracted relation from episodic memory.'
      : 'Causal/structural relation from episodic memory.',
  }
}

/**
 * A ready-made investigation prompt for the Console chat composer, built from a
 * focused episode (used by the "Ask AI about this episode" button).
 */
export function buildEpisodePrompt(node: EpisodicNode, services: string[], rootCause?: string): string {
  // Slim on purpose: this lands verbatim as the user's chat bubble. MUST keep
  // an investigation keyword (investigate / root cause / remediat…) plus a
  // service name so the backend forces the evidence bundle and resolves the
  // service; the date is dropped (it's already visible on the episode card).
  const sev = node.severity ? `${node.severity} ` : ''
  const on = services.length > 0 ? ` on ${services.join(', ')}` : ''
  const rc = rootCause
    ? ` (recorded root cause: "${rootCause.length > 90 ? `${rootCause.slice(0, 90)}…` : rootCause}")`
    : ''
  return `Investigate the ${sev}incident "${node.label}"${on}${rc}. What are the root cause and remediation?`
}
