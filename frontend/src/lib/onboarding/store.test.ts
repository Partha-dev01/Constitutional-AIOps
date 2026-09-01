import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock the API client so the store's load/persist calls hit vitest fns, not
// the network. (node vitest environment — no DOM, no fetch.)
vi.mock('../api', () => ({
  default: {
    settings: {
      getOnboarding: vi.fn(),
      saveOnboarding: vi.fn(),
    },
    infrastructure: {
      getContainers: vi.fn(),
    },
  },
}))

import api from '../api'
import { FIRST_STEP } from './steps'
import { useWizardStore } from './store'

const getOnboarding = vi.mocked(api.settings.getOnboarding)
const saveOnboarding = vi.mocked(api.settings.saveOnboarding)
const getContainers = vi.mocked(api.infrastructure.getContainers)

beforeEach(() => {
  vi.clearAllMocks()
  useWizardStore.setState({
    status: 'idle',
    currentStep: FIRST_STEP,
    onboarding: null,
    error: null,
    services: [],
    servicesStatus: 'idle',
  })
  saveOnboarding.mockResolvedValue({ completed: false, skipped: false, step: 1 })
  getContainers.mockResolvedValue({ containers: [], total: 0, healthy: 0, unhealthy: 0 })
})

describe('wizard store', () => {
  it('load resumes at the persisted step', async () => {
    getOnboarding.mockResolvedValue({ completed: false, skipped: false, step: 2 })
    await useWizardStore.getState().load()
    const s = useWizardStore.getState()
    expect(s.status).toBe('ready')
    expect(s.currentStep).toBe('topology')
    expect(s.onboarding).toEqual({ completed: false, skipped: false, step: 2 })
  })

  it('load starts at welcome when already completed', async () => {
    getOnboarding.mockResolvedValue({ completed: true, skipped: false, step: 5 })
    await useWizardStore.getState().load()
    expect(useWizardStore.getState().currentStep).toBe('welcome')
  })

  it('load fails soft (still ready, records error, defaults)', async () => {
    getOnboarding.mockRejectedValue(new Error('backend cold'))
    await useWizardStore.getState().load()
    const s = useWizardStore.getState()
    expect(s.status).toBe('ready')
    expect(s.error).toBe('backend cold')
    expect(s.currentStep).toBe('welcome')
    expect(s.onboarding).toEqual({ completed: false, skipped: false, step: 0 })
  })

  it('next advances and records the furthest step', () => {
    useWizardStore.setState({
      status: 'ready',
      onboarding: { completed: false, skipped: false, step: 0 },
    })
    useWizardStore.getState().next()
    expect(useWizardStore.getState().currentStep).toBe('services')
    expect(saveOnboarding).toHaveBeenCalledWith({ completed: false, skipped: false, step: 1 })
  })

  it('back does not persist', () => {
    useWizardStore.setState({
      status: 'ready',
      currentStep: 'topology',
      onboarding: { completed: false, skipped: false, step: 2 },
    })
    useWizardStore.getState().back()
    expect(useWizardStore.getState().currentStep).toBe('services')
    expect(saveOnboarding).not.toHaveBeenCalled()
  })

  it('skip marks skipped (persisted)', async () => {
    saveOnboarding.mockResolvedValue({ completed: false, skipped: true, step: 0 })
    useWizardStore.setState({
      status: 'ready',
      onboarding: { completed: false, skipped: false, step: 0 },
    })
    await useWizardStore.getState().skip()
    expect(saveOnboarding).toHaveBeenCalledWith({ completed: false, skipped: true, step: 0 })
    expect(useWizardStore.getState().onboarding?.skipped).toBe(true)
  })

  it('complete marks completed at the last step index', async () => {
    saveOnboarding.mockResolvedValue({ completed: true, skipped: false, step: 6 })
    useWizardStore.setState({
      status: 'ready',
      onboarding: { completed: false, skipped: false, step: 0 },
    })
    await useWizardStore.getState().complete()
    expect(saveOnboarding).toHaveBeenCalledWith({ completed: true, skipped: false, step: 6 })
    expect(useWizardStore.getState().onboarding?.completed).toBe(true)
  })
})

function containerRow(name: string, service = name) {
  return {
    name,
    service,
    status: 'running',
    health: null,
    port: null,
    image: null,
    description: null,
    monitored: true,
  }
}

describe('wizard store - services', () => {
  it('prefill seeds services from live containers exactly once', async () => {
    getContainers.mockResolvedValue({
      containers: [containerRow('aiops-backend')],
      total: 1,
      healthy: 1,
      unhealthy: 0,
    })
    await useWizardStore.getState().prefillServices()
    const s = useWizardStore.getState()
    expect(s.servicesStatus).toBe('ready')
    expect(s.services).toEqual([{ name: 'backend', role: '', dependsOn: [] }])
    // A second call is a no-op once the prefill has run.
    await useWizardStore.getState().prefillServices()
    expect(getContainers).toHaveBeenCalledTimes(1)
  })

  it('prefill fails soft (ready, empty, no throw)', async () => {
    getContainers.mockRejectedValue(new Error('no docker'))
    await useWizardStore.getState().prefillServices()
    const s = useWizardStore.getState()
    expect(s.servicesStatus).toBe('ready')
    expect(s.services).toEqual([])
  })

  it('prefill never clobbers services the user already entered', async () => {
    useWizardStore.setState({ services: [{ name: 'mine', role: '', dependsOn: [] }] })
    getContainers.mockResolvedValue({
      containers: [containerRow('aiops-backend')],
      total: 1,
      healthy: 1,
      unhealthy: 0,
    })
    await useWizardStore.getState().prefillServices()
    expect(useWizardStore.getState().services).toEqual([{ name: 'mine', role: '', dependsOn: [] }])
  })

  it('add/update/remove edit the service list by index', () => {
    const { addService } = useWizardStore.getState()
    addService()
    addService()
    expect(useWizardStore.getState().services).toHaveLength(2)
    useWizardStore.getState().updateService(0, { name: 'api', role: 'backend' })
    expect(useWizardStore.getState().services[0]).toEqual({
      name: 'api',
      role: 'backend',
      dependsOn: [],
    })
    useWizardStore.getState().removeService(0)
    expect(useWizardStore.getState().services).toHaveLength(1)
    expect(useWizardStore.getState().services[0].name).toBe('')
  })

  it('setServices replaces the whole list', () => {
    useWizardStore.getState().setServices([{ name: 'a', role: '', dependsOn: [] }])
    expect(useWizardStore.getState().services).toEqual([{ name: 'a', role: '', dependsOn: [] }])
  })
})
