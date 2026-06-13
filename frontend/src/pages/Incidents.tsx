import { useState, useEffect } from 'react'
import { AlertTriangle, CheckCircle, Clock, Search, Plus, Eye, Play, Loader2, RefreshCw } from 'lucide-react'
import { formatRelativeTime } from '../lib/utils'
import api, { Incident, IncidentSeverity, IncidentStatus, Action, IncidentCreate } from '../lib/api'
import { ActiveIncidentsPanel } from '../components/incidents/ActiveIncidentsPanel'
import { Modal } from '../components/ui/Modal'
import { useToast } from '../components/ui/toast'

export function Incidents() {
  const { showToast } = useToast()
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [pendingActions, setPendingActions] = useState<Action[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [selectedAction, setSelectedAction] = useState<Action | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [incidentData, actionData] = await Promise.all([
        api.incidents.list({
          page: 1,
          page_size: 50,
          status: statusFilter !== 'all' ? [statusFilter as IncidentStatus] : undefined,
          severity: severityFilter !== 'all' ? [severityFilter as IncidentSeverity] : undefined,
        }),
        api.actions.getPending(),
      ])
      setIncidents(incidentData.items)
      setPendingActions(actionData.actions)
    } catch (err) {
      console.error('Fetch error:', err)
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch incidents'
      setError(errorMessage)
      // Don't use mock data - show actual error state
      setIncidents([])
      setPendingActions([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [statusFilter, severityFilter])

  const filteredIncidents = incidents.filter((incident) => {
    const matchesSearch = incident.title.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesSearch
  })

  const handleApprove = async (action: Action, approved: boolean, comments?: string) => {
    try {
      await api.actions.approve(action.id, {
        approved,
        approved_by: 'current-user',
        comments,
      })
      setShowApprovalModal(false)
      setSelectedAction(null)
      fetchData()
    } catch (err) {
      console.error('Approval error:', err)
      showToast('Failed to process approval', 'error')
    }
  }

  const handleAnalyze = async (incidentId: string) => {
    try {
      await api.incidents.analyze(incidentId)
      fetchData()
    } catch (err) {
      console.error('Analysis error:', err)
      showToast('Failed to trigger analysis', 'error')
    }
  }

  const handleCreateIncident = async (data: IncidentCreate) => {
    setCreating(true)
    try {
      await api.incidents.create(data)
      setShowCreateModal(false)
      fetchData()
    } catch (err) {
      console.error('Create error:', err)
      showToast('Failed to create incident', 'error')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Incidents</h1>
          <p className="text-muted-foreground">
            Monitor and manage infrastructure incidents
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-muted disabled:opacity-50"
            aria-label="Refresh incidents"
            title="Refresh"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            New Incident
          </button>
        </div>
      </div>

      {/* Act on live incidents inline: approve & remediate / reject / open in chat. */}
      <ActiveIncidentsPanel />

      {/* Pending Approvals Banner */}
      {pendingActions.length > 0 && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Clock className="h-5 w-5 text-yellow-500" aria-hidden="true" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-600">
                {pendingActions.length} Actions Awaiting Approval
              </h3>
              <p className="text-sm text-yellow-600/80">
                These remediation actions require your review
              </p>
            </div>
          </div>
          <div className="mt-3 space-y-2">
            {pendingActions.slice(0, 3).map((action) => (
              <div key={action.id} className="flex items-center justify-between p-2 bg-yellow-500/5 rounded-lg">
                <div>
                  <p className="text-sm font-medium">{action.description}</p>
                  <p className="text-xs text-muted-foreground">
                    {action.target_service} • Confidence: {Math.round(action.confidence * 100)}%
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setSelectedAction(action)
                      setShowApprovalModal(true)
                    }}
                    className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                  >
                    Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600 text-sm" role="alert">
          Error: {error}. Please check that the backend is running.
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <label htmlFor="incident-search" className="sr-only">Search incidents</label>
          <input
            id="incident-search"
            type="text"
            placeholder="Search incidents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <label htmlFor="status-filter" className="sr-only">Filter by status</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">All Status</option>
          <option value="detecting">Detecting</option>
          <option value="analyzing">Analyzing</option>
          <option value="pending_approval">Needs Approval</option>
          <option value="remediating">Remediating</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
        <label htmlFor="severity-filter" className="sr-only">Filter by severity</label>
        <select
          id="severity-filter"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">All Severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
      </div>

      {/* Incidents List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 motion-safe:animate-spin text-muted-foreground" aria-hidden="true" />
            <span className="sr-only">Loading incidents…</span>
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-8">
            <div className="flex flex-col items-center text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mb-4" aria-hidden="true" />
              <h3 className="text-lg font-semibold text-green-600 mb-2">All Systems Operational</h3>
              <p className="text-muted-foreground mb-4">
                No active incidents. Your infrastructure is running smoothly.
              </p>
              <p className="text-sm text-muted-foreground">
                Click <strong>"New Incident"</strong> to create a test incident, or use <strong>"Demo Mode"</strong> from the Agents page to trigger real anomalies.
              </p>
            </div>
          </div>
        ) : (
          filteredIncidents.map((incident) => (
            <IncidentCard
              key={incident.id}
              incident={incident}
              onView={() => setSelectedIncident(incident)}
              onAnalyze={() => handleAnalyze(incident.id)}
            />
          ))
        )}
      </div>

      {/* Incident Detail Modal */}
      <Modal
        open={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title={selectedIncident?.id ?? ''}
        titleId="incident-detail-title"
        maxWidth="max-w-2xl"
      >
        {selectedIncident && (
          <IncidentDetailContent incident={selectedIncident} />
        )}
      </Modal>

      {/* Approval Modal */}
      {selectedAction && (
        <Modal
          open={showApprovalModal}
          onClose={() => {
            setShowApprovalModal(false)
            setSelectedAction(null)
          }}
          title="Review Action"
          titleId="approval-modal-title"
        >
          <ApprovalContent
            action={selectedAction}
            onApprove={(comments) => handleApprove(selectedAction, true, comments)}
            onReject={(comments) => handleApprove(selectedAction, false, comments)}
          />
        </Modal>
      )}

      {/* Create Incident Modal */}
      <Modal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Incident"
        titleId="create-incident-title"
      >
        <CreateIncidentContent
          onSubmit={handleCreateIncident}
          onClose={() => setShowCreateModal(false)}
          loading={creating}
        />
      </Modal>
    </div>
  )
}

function IncidentCard({
  incident,
  onView,
  onAnalyze,
}: {
  incident: Incident
  onView: () => void
  onAnalyze: () => void
}) {
  const severityColors: Record<string, string> = {
    critical: 'bg-red-500/10 text-red-500 border-red-500/20',
    high: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    low: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    info: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  }

  const statusIcons: Record<string, React.ElementType> = {
    detecting: AlertTriangle,
    analyzing: Clock,
    pending_approval: Eye,
    remediating: Play,
    resolved: CheckCircle,
    closed: CheckCircle,
  }

  const StatusIcon = statusIcons[incident.status] || AlertTriangle

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className={`p-2 rounded-lg shrink-0 ${severityColors[incident.severity] || severityColors.info}`}>
            <StatusIcon className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold">{incident.title}</h3>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-muted-foreground">
              <span>{incident.id}</span>
              <span>•</span>
              <span>{(incident.affected_services ?? []).map(s => s.name).join(', ')}</span>
              <span>•</span>
              <span>{formatRelativeTime(new Date(incident.created_at))}</span>
            </div>
            {incident.description && (
              <p className="text-sm text-muted-foreground mt-2">{incident.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`px-2 py-1 rounded-full text-xs capitalize ${
            incident.status === 'resolved' || incident.status === 'closed'
              ? 'bg-green-500/10 text-green-500'
              : incident.status === 'pending_approval' || incident.status === 'analyzing'
              ? 'bg-yellow-500/10 text-yellow-500'
              : 'bg-red-500/10 text-red-500'
          }`}>
            {incident.status}
          </span>
          <span className={`px-2 py-1 rounded-full text-xs capitalize ${severityColors[incident.severity] || ''}`}>
            {incident.severity}
          </span>
        </div>
      </div>

      {/* RCA Result if available */}
      {incident.rca && (
        <div className="mt-4 p-3 bg-muted/50 rounded-lg">
          <p className="text-sm font-medium">Root Cause Analysis</p>
          <p className="text-sm text-muted-foreground mt-1">{incident.rca.root_cause}</p>
          <p className="text-xs text-muted-foreground mt-1">
            Confidence: {Math.round(incident.rca.confidence * 100)}%
          </p>
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <button
          onClick={onView}
          className="px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/90"
        >
          View Details
        </button>
        {incident.status !== 'resolved' && incident.status !== 'closed' && (
          <button
            onClick={onAnalyze}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
          >
            <Play className="h-4 w-4 inline mr-1" aria-hidden="true" />
            Run Analysis
          </button>
        )}
      </div>
    </div>
  )
}

/** Content of the Incident Detail modal (Modal primitive supplies the wrapper + header) */
function IncidentDetailContent({ incident }: { incident: Incident }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-semibold text-lg">{incident.title}</h3>
        {incident.description && (
          <p className="text-muted-foreground mt-1">{incident.description}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Status</p>
          <p className="font-medium capitalize">{incident.status}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Severity</p>
          <p className="font-medium capitalize">{incident.severity}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Category</p>
          <p className="font-medium capitalize">{incident.category || 'Unknown'}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Created</p>
          <p className="font-medium">{new Date(incident.created_at).toLocaleString()}</p>
        </div>
      </div>

      <div>
        <p className="text-sm text-muted-foreground mb-2">Affected Services</p>
        <div className="flex flex-wrap gap-2">
          {(incident.affected_services ?? []).map((service, i) => (
            <span key={i} className="px-2 py-1 bg-muted rounded text-sm">
              {service.name}
            </span>
          ))}
        </div>
      </div>

      {incident.rca && (
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="font-semibold mb-2">Root Cause Analysis</h4>
          <p className="text-sm">{incident.rca.root_cause}</p>
          <p className="text-xs text-muted-foreground mt-2">
            Confidence: {Math.round(incident.rca.confidence * 100)}%
          </p>
          {(incident.rca.causal_chain?.length ?? 0) > 0 && (
            <div className="mt-3">
              <p className="text-sm font-medium">Causal Chain:</p>
              <ul className="list-disc list-inside text-sm text-muted-foreground">
                {(incident.rca.causal_chain ?? []).map((factor, i) => (
                  <li key={i}>{factor}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {incident.remediation_plan && (
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="font-semibold mb-2">Remediation Plan</h4>
          <div className="space-y-2">
            {(incident.remediation_plan.steps ?? []).map((step, i) => (
              <div key={step.order ?? i} className="flex items-start gap-2">
                <span className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center">
                  {step.order ?? i + 1}
                </span>
                <div>
                  <p className="text-sm font-medium">{step.action}</p>
                  {step.command && (
                    <p className="text-xs text-muted-foreground font-mono">{step.command}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/** Content of the Approval modal */
function ApprovalContent({
  action,
  onApprove,
  onReject,
}: {
  action: Action
  onApprove: (comments?: string) => void
  onReject: (comments?: string) => void
}) {
  const [comments, setComments] = useState('')

  return (
    <div className="space-y-4">
      <div className="p-4 bg-muted/50 rounded-lg">
        <p className="font-semibold">{action.description}</p>
        <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Type:</span>{' '}
            <span className="capitalize">{action.action_type.replace('_', ' ')}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Target:</span>{' '}
            {action.target_service}
          </div>
          <div>
            <span className="text-muted-foreground">Confidence:</span>{' '}
            {Math.round(action.confidence * 100)}%
          </div>
          <div>
            <span className="text-muted-foreground">Risk:</span>{' '}
            <span className="capitalize">
              {action.validation?.authorization_level || 'medium'}
            </span>
          </div>
        </div>
      </div>

      {action.validation && (
        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <p className="font-semibold text-blue-600 mb-2">Constitutional AI Validation</p>
          <p className="text-sm">{action.validation.explanation}</p>
          <div className="mt-2 flex gap-2">
            <span className={`px-2 py-1 rounded text-xs ${action.validation.tier1_passed ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
              Tier 1: {action.validation.tier1_passed ? 'Pass' : 'Fail'}
            </span>
            <span className={`px-2 py-1 rounded text-xs ${action.validation.tier2_passed ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'}`}>
              Tier 2: {action.validation.tier2_passed ? 'Pass' : 'Review'}
            </span>
          </div>
          {action.validation.warnings.length > 0 && (
            <div className="mt-2 text-sm text-yellow-600">
              <p className="font-medium">Warnings:</p>
              <ul className="list-disc list-inside">
                {action.validation.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div>
        <label htmlFor="approval-comments" className="block text-sm font-medium mb-1">Comments (optional)</label>
        <textarea
          id="approval-comments"
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          rows={3}
          placeholder="Add any notes or conditions..."
        />
      </div>

      <div className="flex gap-2 justify-end">
        <button
          onClick={() => onReject(comments)}
          className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600"
        >
          Reject
        </button>
        <button
          onClick={() => onApprove(comments)}
          className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600"
        >
          Approve &amp; Execute
        </button>
      </div>
    </div>
  )
}

/** Content of the Create Incident modal */
function CreateIncidentContent({
  onSubmit,
  onClose,
  loading,
}: {
  onSubmit: (data: IncidentCreate) => void
  onClose: () => void
  loading: boolean
}) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [severity, setSeverity] = useState<IncidentSeverity>('medium')
  const [category, setCategory] = useState('infrastructure')
  const [serviceName, setServiceName] = useState('nextcloud')
  const [autoAnalyze, setAutoAnalyze] = useState(true)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    onSubmit({
      title: title.trim(),
      description: description.trim() || undefined,
      severity,
      category,
      affected_services: [{ name: serviceName }],
      tags: [category, severity],
      auto_analyze: autoAnalyze,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="incident-title" className="block text-sm font-medium mb-1">Title *</label>
        <input
          id="incident-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="e.g., High CPU usage on database server"
          required
        />
      </div>

      <div>
        <label htmlFor="incident-description" className="block text-sm font-medium mb-1">Description</label>
        <textarea
          id="incident-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          rows={3}
          placeholder="Describe the incident in detail..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="incident-severity" className="block text-sm font-medium mb-1">Severity</label>
          <select
            id="incident-severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value as IncidentSeverity)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
        </div>
        <div>
          <label htmlFor="incident-category" className="block text-sm font-medium mb-1">Category</label>
          <select
            id="incident-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="infrastructure">Infrastructure</option>
            <option value="application">Application</option>
            <option value="database">Database</option>
            <option value="network">Network</option>
            <option value="security">Security</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="incident-service" className="block text-sm font-medium mb-1">Affected Service</label>
        <input
          id="incident-service"
          type="text"
          value={serviceName}
          onChange={(e) => setServiceName(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          placeholder="e.g., nextcloud, backend, neo4j"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="autoAnalyze"
          checked={autoAnalyze}
          onChange={(e) => setAutoAnalyze(e.target.checked)}
          className="rounded border-border"
        />
        <label htmlFor="autoAnalyze" className="text-sm">
          Auto-analyze with AI (triggers RCA after creation)
        </label>
      </div>

      <div className="flex gap-2 justify-end pt-4">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 bg-muted text-muted-foreground rounded-lg text-sm font-medium hover:bg-muted/80"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading || !title.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 motion-safe:animate-spin inline mr-2" aria-hidden="true" />
              Creating...
            </>
          ) : (
            'Create Incident'
          )}
        </button>
      </div>
    </form>
  )
}
