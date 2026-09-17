/**
 * Product tour steps (first-run guided intro).
 *
 * A short, modal-carousel walk-through of the app's main areas. Kept as plain
 * data (no JSX) so it reads at a glance and unit-tests without React. The tour
 * is deliberately NOT a DOM-spotlight over sidebar nodes: the sidebar is an
 * off-canvas drawer on mobile and a label-less icon rail when collapsed, so a
 * modal that never depends on a target element renders reliably everywhere.
 */
import {
  Rocket,
  LayoutDashboard,
  AlertTriangle,
  GitBranch,
  Sparkles,
  Settings,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface TourStep {
  id: string
  title: string
  body: string
  icon: LucideIcon
  /** Optional route the final CTA navigates to. */
  to?: string
  /** Optional label for the route CTA (only used with `to`). */
  cta?: string
}

export const TOUR_STEPS: TourStep[] = [
  {
    id: 'welcome',
    icon: Rocket,
    title: 'Welcome to Constitutional AIOps',
    body: 'A quick tour of the main areas. It takes under a minute and you can skip at any time.',
  },
  {
    id: 'overview',
    icon: LayoutDashboard,
    title: 'Dashboard and Command Center',
    body: 'The Dashboard is your system-health overview. The Command Center pulls live incidents, approvals and actions into one operator view.',
  },
  {
    id: 'incidents',
    icon: AlertTriangle,
    title: 'Incidents and the Chat copilot',
    body: 'Incidents group related signals into one timeline. Ask the Chat copilot to explain a root cause or propose a fix. Every action passes the constitutional gate before anything runs.',
  },
  {
    id: 'graph',
    icon: GitBranch,
    title: 'Graph-episodic memory',
    body: 'The Graph is the system memory. Past incidents, their root causes and the actions that worked feed future reasoning and validation.',
  },
  {
    id: 'insights',
    icon: Sparkles,
    title: 'AI insight widgets',
    body: 'Turn on AI insight widgets in Settings for opt-in, cost-fenced explanations across metrics, incidents and the graph. They stay useful with the model off and never run on their own.',
  },
  {
    id: 'finish',
    icon: Settings,
    title: 'You are set',
    body: 'Head to Settings to connect your model endpoint and tune remediation autonomy. Replay this tour any time from the command palette (Ctrl or Command K).',
    to: '/settings',
    cta: 'Open Settings',
  },
]

export default TOUR_STEPS
