import { describe, it, expect } from 'vitest'

import {
  FIRST_STEP,
  LAST_STEP,
  RAIL_STEPS,
  WIZARD_STEPS,
  isFirstStep,
  isLastStep,
  nextStepId,
  prevStepId,
  stepIdFromIndex,
  stepIndex,
  stepMeta,
} from './steps'

describe('wizard step model', () => {
  it('runs welcome -> finish with six config steps between', () => {
    expect(WIZARD_STEPS[0].id).toBe('welcome')
    expect(WIZARD_STEPS[WIZARD_STEPS.length - 1].id).toBe('finish')
    expect(WIZARD_STEPS).toHaveLength(8)
    expect(FIRST_STEP).toBe('welcome')
    expect(LAST_STEP).toBe('finish')
  })

  it('rail excludes the welcome/finish bookends', () => {
    expect(RAIL_STEPS.map((s) => s.id)).toEqual([
      'services',
      'topology',
      'prompt',
      'llm',
      'monitoring',
      'safety',
    ])
  })

  it('next/prev clamp at the ends', () => {
    expect(nextStepId('finish')).toBe('finish')
    expect(prevStepId('welcome')).toBe('welcome')
    expect(nextStepId('welcome')).toBe('services')
    expect(prevStepId('finish')).toBe('safety')
  })

  it('walks the whole flow forward', () => {
    let id = FIRST_STEP
    const seen = [id]
    for (let i = 0; i < 7; i += 1) {
      id = nextStepId(id)
      seen.push(id)
    }
    expect(seen).toEqual([
      'welcome',
      'services',
      'topology',
      'prompt',
      'llm',
      'monitoring',
      'safety',
      'finish',
    ])
  })

  it('flags first and last', () => {
    expect(isFirstStep('welcome')).toBe(true)
    expect(isFirstStep('services')).toBe(false)
    expect(isLastStep('finish')).toBe(true)
    expect(isLastStep('monitoring')).toBe(false)
  })

  it('maps a persisted index to a step id (clamped)', () => {
    expect(stepIdFromIndex(0)).toBe('welcome')
    expect(stepIdFromIndex(2)).toBe('topology')
    expect(stepIdFromIndex(6)).toBe('safety')
    expect(stepIdFromIndex(7)).toBe('finish')
    expect(stepIdFromIndex(99)).toBe('finish')
    expect(stepIdFromIndex(-3)).toBe('welcome')
    expect(stepIdFromIndex(Number.NaN)).toBe('welcome')
  })

  it('stepIndex/stepMeta agree', () => {
    expect(stepIndex('prompt')).toBe(3)
    expect(stepMeta('prompt').title).toBe('Base prompt')
  })
})
