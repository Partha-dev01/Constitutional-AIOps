/**
 * Constitutional AIOps - Onboarding wizard shared types.
 *
 * The persisted wire state lives in lib/api.ts (OnboardingState); UI-only
 * shapes live here so the shell and the individual step components share one
 * definition.
 */

export type { OnboardingState } from '../api'

/** The ordered wizard steps (bookends welcome/finish plus 5 config steps). */
export type WizardStepId =
  | 'welcome'
  | 'services'
  | 'topology'
  | 'prompt'
  | 'llm'
  | 'monitoring'
  | 'finish'

/** One service as entered in the wizard's Services step (populated in P3). */
export interface WizardService {
  name: string
  role: string
  tier?: number | null
  port?: number | null
  dependsOn: string[]
}
