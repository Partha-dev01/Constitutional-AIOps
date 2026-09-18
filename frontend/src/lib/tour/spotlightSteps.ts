/**
 * Spotlight tour steps (post-setup guided intro).
 *
 * Unlike the old plain-modal steps, each step may point at a real DOM element by
 * a stable `target` (its data-tour attribute). The SpotlightTour overlay dims the
 * page, cuts a hole around that element and anchors a callout beside it. A step
 * with no target renders a centered card, which is also the graceful fallback
 * when a target is not on screen (a collapsed icon rail or a mobile drawer).
 *
 * Steps point at sidebar navigation, not page content, so they resolve on any
 * route the tour happens to start from (the sidebar persists across pages).
 */
import { Rocket, LayoutDashboard, AlertTriangle, GitBranch, Settings } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface SpotlightStep {
  id: string
  title: string
  body: string
  icon: LucideIcon
  /** data-tour value of the element to highlight; omit for a centered card. */
  target?: string
  /** Optional route the final CTA navigates to. */
  to?: string
  /** Optional label for the route CTA (only used with `to`). */
  cta?: string
}

export const SPOTLIGHT_STEPS: SpotlightStep[] = [
  {
    id: 'welcome',
    icon: Rocket,
    title: 'You are set up',
    body: 'Here is a quick tour of where everything lives. It takes under a minute, and you can skip at any time.',
  },
  {
    id: 'dashboard',
    icon: LayoutDashboard,
    title: 'Your live overview',
    body: 'The Dashboard is system health at a glance: service status, measured agent latency and the computed insight widgets, all from real telemetry.',
    target: 'dashboard',
  },
  {
    id: 'incidents',
    icon: AlertTriangle,
    title: 'Incidents and remediation',
    body: 'Related signals group into one incident timeline. Ask the copilot to explain a cause or propose a fix, and every action clears the constitutional gate before it runs.',
    target: 'incidents',
  },
  {
    id: 'graph',
    icon: GitBranch,
    title: 'Graph-episodic memory',
    body: 'Past incidents, their root causes and the fixes that worked live in the graph, and feed the reasoning behind every new proposal.',
    target: 'graph',
  },
  {
    id: 'settings',
    icon: Settings,
    title: 'Tune it in Settings',
    body: 'Adjust remediation autonomy, connect or change your model endpoint, and turn on the opt-in AI insight widgets whenever you are ready.',
    target: 'settings',
    to: '/settings',
    cta: 'Open Settings',
  },
]

export default SPOTLIGHT_STEPS
