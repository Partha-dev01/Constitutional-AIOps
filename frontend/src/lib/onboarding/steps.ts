/**
 * Constitutional AIOps - Onboarding wizard step model (pure).
 *
 * The ordered step list plus small pure helpers for navigation and for
 * mapping the persisted numeric ``step`` to/from a step id. Kept free of React
 * so it unit-tests in the node vitest environment.
 */

import type { WizardStepId } from './types'

export interface WizardStepMeta {
  id: WizardStepId
  title: string
  subtitle: string
  /** Shown as a numbered node in the progress rail (welcome/finish are bookends). */
  inRail: boolean
}

export const WIZARD_STEPS: readonly WizardStepMeta[] = [
  { id: 'welcome', title: 'Welcome', subtitle: 'What setup covers', inRail: false },
  { id: 'services', title: 'Services', subtitle: 'Name the services you run', inRail: true },
  { id: 'topology', title: 'Topology', subtitle: 'Generate and edit the map', inRail: true },
  { id: 'prompt', title: 'Base prompt', subtitle: 'Describe the platform', inRail: true },
  { id: 'llm', title: 'LLM endpoint', subtitle: 'Connect your model', inRail: true },
  { id: 'monitoring', title: 'Monitoring', subtitle: 'Point at your telemetry', inRail: true },
  { id: 'safety', title: 'Safety', subtitle: 'Choose how fixes run', inRail: true },
  { id: 'finish', title: 'Finish', subtitle: 'You are ready', inRail: false },
] as const

export const FIRST_STEP: WizardStepId = WIZARD_STEPS[0].id
export const LAST_STEP: WizardStepId = WIZARD_STEPS[WIZARD_STEPS.length - 1].id

/** The configuration steps shown as numbered nodes in the rail. */
export const RAIL_STEPS: readonly WizardStepMeta[] = WIZARD_STEPS.filter((s) => s.inRail)

export function stepIndex(id: WizardStepId): number {
  const i = WIZARD_STEPS.findIndex((s) => s.id === id)
  return i === -1 ? 0 : i
}

export function stepMeta(id: WizardStepId): WizardStepMeta {
  return WIZARD_STEPS[stepIndex(id)]
}

export function nextStepId(id: WizardStepId): WizardStepId {
  const i = stepIndex(id)
  return WIZARD_STEPS[Math.min(i + 1, WIZARD_STEPS.length - 1)].id
}

export function prevStepId(id: WizardStepId): WizardStepId {
  const i = stepIndex(id)
  return WIZARD_STEPS[Math.max(i - 1, 0)].id
}

export function isFirstStep(id: WizardStepId): boolean {
  return stepIndex(id) === 0
}

export function isLastStep(id: WizardStepId): boolean {
  return stepIndex(id) === WIZARD_STEPS.length - 1
}

/** Clamp a persisted numeric step index to a valid step id (resume point). */
export function stepIdFromIndex(index: number): WizardStepId {
  if (!Number.isFinite(index) || index < 0) return FIRST_STEP
  const clamped = Math.min(Math.floor(index), WIZARD_STEPS.length - 1)
  return WIZARD_STEPS[clamped].id
}
