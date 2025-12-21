/**
 * Constitutional AIOps - Incident Timeline Component
 *
 * Visual history of incident events including status changes,
 * RCA analysis, actions, and resolutions.
 */

import { useState } from 'react'
import {
  AlertTriangle,
  Search,
  CheckCircle,
  Clock,
  Wrench,
  Brain,
  Shield,
  User,
  Bot,
  ChevronDown,
  ChevronUp,
  XCircle,
} from 'lucide-react'

// Timeline event types
export type TimelineEventType =
  | 'created'
  | 'updated'
  | 'status_change'
  | 'rca_started'
  | 'rca_completed'
  | 'action_created'
  | 'action_approved'
  | 'action_rejected'
  | 'action_executed'
  | 'resolved'
  | 'comment'

export interface TimelineEvent {
  id: string
  type: TimelineEventType
  timestamp: Date
  title: string
  description?: string
  actor?: {
    type: 'user' | 'system' | 'agent'
    name: string
  }
  metadata?: Record<string, unknown>
}

interface IncidentTimelineProps {
  incidentId: string
  events: TimelineEvent[]
  className?: string
}

// Event type configuration
const eventConfig: Record<
  TimelineEventType,
  {
    icon: React.ElementType
    color: string
    bgColor: string
    label: string
  }
> = {
  created: {
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    label: 'Incident Created',
  },
  updated: {
    icon: Clock,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    label: 'Updated',
  },
  status_change: {
    icon: Clock,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    label: 'Status Changed',
  },
  rca_started: {
    icon: Search,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    label: 'RCA Started',
  },
  rca_completed: {
    icon: Brain,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'RCA Completed',
  },
  action_created: {
    icon: Wrench,
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    label: 'Action Proposed',
  },
  action_approved: {
    icon: Shield,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Action Approved',
  },
  action_rejected: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    label: 'Action Rejected',
  },
  action_executed: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Action Executed',
  },
  resolved: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    label: 'Resolved',
  },
  comment: {
    icon: User,
    color: 'text-gray-500',
    bgColor: 'bg-gray-500/10',
    label: 'Comment',
  },
}

export function IncidentTimeline({ incidentId: _incidentId, events, className = '' }: IncidentTimelineProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set())

  const toggleExpanded = (eventId: string) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev)
      if (next.has(eventId)) {
        next.delete(eventId)
      } else {
        next.add(eventId)
      }
      return next
    })
  }

  const formatTimestamp = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getActorIcon = (actor?: TimelineEvent['actor']) => {
    if (!actor) return null

    switch (actor.type) {
      case 'user':
        return <User className="h-3 w-3" />
      case 'agent':
        return <Bot className="h-3 w-3" />
      case 'system':
        return <Shield className="h-3 w-3" />
      default:
        return null
    }
  }

  if (events.length === 0) {
    return (
      <div className={`text-center py-8 text-muted-foreground ${className}`}>
        <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No timeline events yet</p>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

      {/* Events */}
      <div className="space-y-4">
        {events.map((event, index) => {
          const config = eventConfig[event.type]
          const Icon = config.icon
          const isExpanded = expandedEvents.has(event.id)
          const hasDetails = event.description || event.metadata

          return (
            <div key={event.id} className="relative pl-10">
              {/* Event icon */}
              <div
                className={`absolute left-0 w-8 h-8 rounded-full flex items-center justify-center ${config.bgColor} border-2 border-background`}
              >
                <Icon className={`h-4 w-4 ${config.color}`} />
              </div>

              {/* Event content */}
              <div
                className={`bg-card rounded-lg border border-border p-3 ${
                  hasDetails ? 'cursor-pointer hover:border-primary/50' : ''
                }`}
                onClick={() => hasDetails && toggleExpanded(event.id)}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
                      {event.actor && (
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          {getActorIcon(event.actor)}
                          {event.actor.name}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium mt-0.5">{event.title}</p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-muted-foreground">{formatTimestamp(event.timestamp)}</span>
                    {hasDetails && (
                      <button className="p-0.5 hover:bg-muted rounded">
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        )}
                      </button>
                    )}
                  </div>
                </div>

                {/* Expanded details */}
                {isExpanded && hasDetails && (
                  <div className="mt-3 pt-3 border-t border-border">
                    {event.description && (
                      <p className="text-sm text-muted-foreground mb-2">{event.description}</p>
                    )}

                    {event.metadata && (
                      <div className="bg-muted/50 rounded p-2 text-xs font-mono overflow-x-auto">
                        <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Connector to next event */}
              {index < events.length - 1 && (
                <div className="absolute left-4 top-8 h-4 w-0.5 bg-border" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Helper to generate timeline events from incident data
export function generateTimelineFromIncident(incident: {
  id: string
  title: string
  status: string
  severity: string
  created_at: string
  updated_at?: string
  resolved_at?: string
  rca_result?: {
    root_cause?: string
    confidence?: number
  }
  actions?: Array<{
    id: string
    action_type: string
    status: string
    description?: string
    created_at: string
    approved_at?: string
    executed_at?: string
    approved_by?: string
  }>
}): TimelineEvent[] {
  const events: TimelineEvent[] = []

  // Incident created
  events.push({
    id: `${incident.id}-created`,
    type: 'created',
    timestamp: new Date(incident.created_at),
    title: incident.title,
    description: `Severity: ${incident.severity}`,
    actor: { type: 'system', name: 'Detection System' },
  })

  // RCA if available
  if (incident.rca_result) {
    events.push({
      id: `${incident.id}-rca`,
      type: 'rca_completed',
      timestamp: new Date(incident.created_at), // Approximate
      title: 'Root Cause Analysis Complete',
      description: incident.rca_result.root_cause,
      actor: { type: 'agent', name: 'Reasoning Agent' },
      metadata: {
        confidence: incident.rca_result.confidence,
      },
    })
  }

  // Actions
  if (incident.actions) {
    for (const action of incident.actions) {
      // Action created
      events.push({
        id: `${action.id}-created`,
        type: 'action_created',
        timestamp: new Date(action.created_at),
        title: `${action.action_type} action proposed`,
        description: action.description,
        actor: { type: 'agent', name: 'Reasoning Agent' },
      })

      // Action approved/rejected
      if (action.approved_at) {
        events.push({
          id: `${action.id}-approved`,
          type: 'action_approved',
          timestamp: new Date(action.approved_at),
          title: `${action.action_type} action approved`,
          actor: action.approved_by
            ? { type: 'user', name: action.approved_by }
            : { type: 'system', name: 'Auto-approval' },
        })
      }

      // Action executed
      if (action.executed_at) {
        events.push({
          id: `${action.id}-executed`,
          type: 'action_executed',
          timestamp: new Date(action.executed_at),
          title: `${action.action_type} action executed`,
          actor: { type: 'system', name: 'Execution Engine' },
        })
      }
    }
  }

  // Resolved
  if (incident.resolved_at) {
    events.push({
      id: `${incident.id}-resolved`,
      type: 'resolved',
      timestamp: new Date(incident.resolved_at),
      title: 'Incident resolved',
      actor: { type: 'system', name: 'System' },
    })
  }

  // Sort by timestamp (newest first for display)
  return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
}

export default IncidentTimeline
