/**
 * Constitutional AIOps - Onboarding wizard Services-step helpers (pure).
 *
 * Turns live container status into editable wizard services, and normalises the
 * user's service list before it is handed to topology/prompt generation (P4).
 * Kept free of React and network I/O so it unit-tests in the node vitest
 * environment.
 */

import type { InfrastructureContainer } from '../api'
import type { WizardService } from './types'

/** An empty service row for the "Add service" affordance. */
export function blankService(): WizardService {
  return { name: '', role: '', dependsOn: [] }
}

/** Strip the deployment's ``aiops-`` prefix for a friendlier default name. */
function friendlyName(container: InfrastructureContainer): string {
  const raw = (container.service || container.name || '').trim()
  return raw.startsWith('aiops-') ? raw.slice('aiops-'.length) : raw
}

/**
 * Map live containers to editable services, de-duplicated by name
 * (case-insensitive, first wins). Containers without any usable name are
 * skipped. Role and dependencies are left for the user to fill; the topology
 * generator infers a node kind from the name when the role is blank.
 */
export function containersToServices(
  containers: readonly InfrastructureContainer[],
): WizardService[] {
  const seen = new Set<string>()
  const out: WizardService[] = []
  for (const c of containers) {
    const name = friendlyName(c)
    if (!name) continue
    const key = name.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ name, role: '', dependsOn: [] })
  }
  return out
}

/**
 * Normalise the user's service list for generation: trim, drop nameless rows,
 * de-duplicate by name (case-insensitive, first wins), and keep only
 * dependencies that point at another named service in the surviving set
 * (self-references and unknown targets dropped).
 */
export function cleanServices(services: readonly WizardService[]): WizardService[] {
  const kept: WizardService[] = []
  const keys = new Set<string>()
  for (const s of services) {
    const name = (s.name || '').trim()
    if (!name) continue
    const key = name.toLowerCase()
    if (keys.has(key)) continue
    keys.add(key)
    kept.push({
      name,
      role: (s.role || '').trim(),
      tier: s.tier ?? null,
      port: s.port ?? null,
      dependsOn: (s.dependsOn || []).map((d) => (d || '').trim()).filter(Boolean),
    })
  }

  const canonical = new Map<string, string>()
  for (const k of kept) canonical.set(k.name.toLowerCase(), k.name)

  return kept.map((k) => ({
    ...k,
    dependsOn: Array.from(
      new Set(
        k.dependsOn
          .map((d) => canonical.get(d.toLowerCase()))
          .filter((d): d is string => Boolean(d) && d !== k.name),
      ),
    ),
  }))
}
