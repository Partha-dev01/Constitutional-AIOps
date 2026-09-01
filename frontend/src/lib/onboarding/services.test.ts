import { describe, it, expect } from 'vitest'

import type { InfrastructureContainer } from '../api'
import { blankService, cleanServices, containersToServices } from './services'

function container(partial: Partial<InfrastructureContainer>): InfrastructureContainer {
  return {
    name: 'x',
    service: 'x',
    status: 'running',
    health: null,
    port: null,
    image: null,
    description: null,
    monitored: false,
    ...partial,
  }
}

describe('wizard services helpers', () => {
  it('blankService is an empty editable row', () => {
    expect(blankService()).toEqual({ name: '', role: '', dependsOn: [] })
  })

  it('maps containers to services, stripping the aiops- prefix', () => {
    const out = containersToServices([
      container({ name: 'aiops-backend', service: 'aiops-backend' }),
      container({ name: 'nextcloud', service: 'nextcloud' }),
    ])
    expect(out).toEqual([
      { name: 'backend', role: '', dependsOn: [] },
      { name: 'nextcloud', role: '', dependsOn: [] },
    ])
  })

  it('prefers the service field, de-dupes case-insensitively, skips nameless', () => {
    const out = containersToServices([
      container({ name: 'aiops-loki-1', service: 'loki' }),
      container({ name: 'LOKI', service: 'LOKI' }),
      container({ name: '', service: '' }),
    ])
    expect(out).toEqual([{ name: 'loki', role: '', dependsOn: [] }])
  })

  it('cleanServices trims, drops nameless rows and de-dupes by name', () => {
    const out = cleanServices([
      { name: '  api  ', role: ' backend ', dependsOn: [] },
      { name: '', role: 'x', dependsOn: [] },
      { name: 'API', role: 'dupe', dependsOn: [] },
    ])
    expect(out).toEqual([
      { name: 'api', role: 'backend', tier: null, port: null, dependsOn: [] },
    ])
  })

  it('cleanServices keeps only dependencies pointing at a known service', () => {
    const out = cleanServices([
      { name: 'web', role: '', dependsOn: ['api', 'ghost', 'web'] },
      { name: 'api', role: '', dependsOn: [] },
    ])
    expect(out[0].dependsOn).toEqual(['api'])
    expect(out[1].dependsOn).toEqual([])
  })
})
