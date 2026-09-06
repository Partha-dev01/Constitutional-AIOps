/**
 * Pure helpers for the Dashboard "Awaiting approval" ticker (Track 2 widget).
 *
 * Turns the live pending-actions list into a bounded, oldest-first display model
 * carrying each action's constitutional confidence band and tier checks. Kept out
 * of the component so the mapping and the age/band logic are unit testable and no
 * LLM call is ever involved (this widget is purely a view over existing data).
 */

import type { Action, AuthorizationLevel } from './api'

export type ConfidenceBand = 'high' | 'medium' | 'low'

/**
 * Map a confidence score to a band using the constitutional authorization matrix:
 * >= 0.90 automatic (high), 0.70-0.90 approval required (medium), < 0.70 alert
 * only (low). Mirrors CONFIDENCE_THRESHOLD_AUTO / _APPROVAL on the backend.
 */
export function confidenceBand(confidence: number): ConfidenceBand {
  if (confidence >= 0.9) return 'high'
  if (confidence >= 0.7) return 'medium'
  return 'low'
}

export interface TierState {
  tier1: boolean
  tier2: boolean
  tier3: boolean
}

/** Which constitutional tiers the action's validation passed (default true when
 *  no validation is attached yet, so we never imply a failure we did not observe). */
export function tierState(action: Action): TierState {
  const v = action.validation
  return {
    tier1: v?.tier1_passed ?? true,
    tier2: v?.tier2_passed ?? true,
    tier3: v?.tier3_passed ?? true,
  }
}

/** Humanize how long an action has been waiting (s / m / h m / d). */
export function formatAge(fromIso: string, now: number = Date.now()): string {
  const start = new Date(fromIso).getTime()
  if (Number.isNaN(start)) return ''
  const secs = Math.max(0, Math.floor((now - start) / 1000))
  if (secs < 60) return `${secs}s`
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  const remMins = mins % 60
  if (hrs < 24) return remMins ? `${hrs}h ${remMins}m` : `${hrs}h`
  const days = Math.floor(hrs / 24)
  return `${days}d`
}

export interface TickerItem {
  id: string
  description: string
  target: string
  actionType: string
  confidence: number
  band: ConfidenceBand
  tiers: TierState
  authorizationLevel?: AuthorizationLevel
  createdAt: string
}

/**
 * Project the pending actions worth showing into ticker items, oldest-waiting
 * first so the most-aged (most urgent) approval surfaces at the top.
 */
export function toTickerItems(actions: readonly Action[]): TickerItem[] {
  return actions
    .filter((a) => a.requires_approval || a.status === 'awaiting_approval')
    .map((a) => ({
      id: a.id,
      description: a.description,
      target: a.target_service,
      actionType: a.action_type,
      confidence: a.confidence,
      band: confidenceBand(a.confidence),
      tiers: tierState(a),
      authorizationLevel: a.validation?.authorization_level,
      createdAt: a.created_at,
    }))
    .sort((x, y) => new Date(x.createdAt).getTime() - new Date(y.createdAt).getTime())
}
