/**
 * Constitutional AIOps - Onboarding wizard store (zustand).
 *
 * Holds the wizard's current step and the persisted onboarding state, and
 * drives navigation through the pure helpers in ./steps. Loading and saving go
 * through the settings API (GET/PUT /settings/onboarding); everything fails
 * soft so a cold or unreachable backend never traps the user in the wizard.
 */

import { create } from 'zustand'

import api from '../api'
import type { OnboardingState } from '../api'
import {
  FIRST_STEP,
  LAST_STEP,
  nextStepId,
  prevStepId,
  stepIdFromIndex,
  stepIndex,
} from './steps'
import { blankService, containersToServices } from './services'
import type { WizardService, WizardStepId } from './types'

export type WizardStatus = 'idle' | 'loading' | 'ready' | 'saving'

const DEFAULT_ONBOARDING: OnboardingState = { completed: false, skipped: false, step: 0 }

export interface WizardStoreState {
  status: WizardStatus
  currentStep: WizardStepId
  onboarding: OnboardingState | null
  error: string | null
  /** Fetch persisted state and resume at the furthest step reached. */
  load: () => Promise<void>
  /** Jump to a step and record it as the furthest reached (best-effort). */
  goTo: (id: WizardStepId) => void
  next: () => void
  back: () => void
  /** Mark setup skipped (persisted). */
  skip: () => Promise<void>
  /** Mark setup completed (persisted). */
  complete: () => Promise<void>

  // --- Services step (P3) ---
  /** Services entered or detected in the Services step (wizard-session state). */
  services: WizardService[]
  /** Lifecycle of the one-time live-container prefill. */
  servicesStatus: 'idle' | 'loading' | 'ready'
  setServices: (services: WizardService[]) => void
  addService: () => void
  updateService: (index: number, patch: Partial<WizardService>) => void
  removeService: (index: number) => void
  /** Seed the list from live containers once (best-effort; fails soft). */
  prefillServices: () => Promise<void>
}

async function persist(
  patch: Partial<OnboardingState>,
  current: OnboardingState | null,
): Promise<OnboardingState> {
  const base = current ?? DEFAULT_ONBOARDING
  return api.settings.saveOnboarding({ ...base, ...patch })
}

export const useWizardStore = create<WizardStoreState>((set, get) => ({
  status: 'idle',
  currentStep: FIRST_STEP,
  onboarding: null,
  error: null,
  services: [],
  servicesStatus: 'idle',

  load: async () => {
    if (get().status === 'loading') return
    set({ status: 'loading', error: null })
    try {
      const ob = await api.settings.getOnboarding()
      set({
        onboarding: ob,
        // Resume where the user left off, unless they already finished/skipped.
        currentStep: ob.completed || ob.skipped ? FIRST_STEP : stepIdFromIndex(ob.step),
        status: 'ready',
      })
    } catch (e) {
      // Fail soft: the wizard still runs; it just cannot resume/persist yet.
      set({
        onboarding: { ...DEFAULT_ONBOARDING },
        currentStep: FIRST_STEP,
        status: 'ready',
        error: e instanceof Error ? e.message : 'Failed to load setup state',
      })
    }
  },

  goTo: (id) => {
    set({ currentStep: id })
    // Best-effort record of the furthest step reached (fire-and-forget so
    // navigation never blocks on the network).
    const { onboarding } = get()
    const reached = Math.max(onboarding?.step ?? 0, stepIndex(id))
    if (reached !== (onboarding?.step ?? 0)) {
      void persist({ step: reached }, onboarding)
        .then((ob) => set({ onboarding: ob }))
        .catch(() => {
          /* resume-point persistence is best-effort */
        })
    }
  },

  next: () => {
    get().goTo(nextStepId(get().currentStep))
  },

  back: () => {
    set({ currentStep: prevStepId(get().currentStep) })
  },

  skip: async () => {
    set({ status: 'saving', error: null })
    try {
      const ob = await persist({ skipped: true }, get().onboarding)
      set({ onboarding: ob, status: 'ready' })
    } catch (e) {
      set({ status: 'ready', error: e instanceof Error ? e.message : 'Failed to skip setup' })
    }
  },

  complete: async () => {
    set({ status: 'saving', error: null })
    try {
      const ob = await persist(
        { completed: true, step: stepIndex(LAST_STEP) },
        get().onboarding,
      )
      set({ onboarding: ob, status: 'ready' })
    } catch (e) {
      set({ status: 'ready', error: e instanceof Error ? e.message : 'Failed to finish setup' })
    }
  },

  setServices: (services) => set({ services }),

  addService: () => set((s) => ({ services: [...s.services, blankService()] })),

  updateService: (index, patch) =>
    set((s) => ({
      services: s.services.map((svc, i) => (i === index ? { ...svc, ...patch } : svc)),
    })),

  removeService: (index) =>
    set((s) => ({ services: s.services.filter((_, i) => i !== index) })),

  prefillServices: async () => {
    // Once per wizard session; navigating back to the step never re-fetches.
    if (get().servicesStatus !== 'idle') return
    set({ servicesStatus: 'loading' })
    try {
      const resp = await api.infrastructure.getContainers()
      const detected = containersToServices(resp.containers ?? [])
      // Only seed from live containers when the user has not entered anything;
      // never clobber their edits.
      set((s) => ({
        services: s.services.length === 0 ? detected : s.services,
        servicesStatus: 'ready',
      }))
    } catch {
      // Fail soft: no detected services just means the user adds them by hand.
      set({ servicesStatus: 'ready' })
    }
  },
}))

export default useWizardStore
