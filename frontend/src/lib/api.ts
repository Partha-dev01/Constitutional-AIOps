/**
 * Constitutional AIOps - Frontend API Client
 *
 * Type-safe API client for communicating with the backend.
 */

// Use relative URL for nginx proxy, fallback to localhost:8080 for development without proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Types

export interface HealthComponent {
  name: string;
  healthy: boolean;
  latency_ms?: number;
  error?: string;
}

export interface HealthResponse {
  status: string;
  components: HealthComponent[];
  uptime_seconds?: number;
  version?: string;
}

// Helper function to check if a specific component is healthy
export function isComponentHealthy(health: HealthResponse | null, componentName: string): boolean {
  if (!health || !health.components) return false;
  const component = health.components.find((c) => c.name === componentName);
  return component?.healthy ?? false;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, unknown>;
}

/**
 * Structured per-tool results the backend now returns under
 * `ChatResponse.metadata.tools`. A key is present ONLY for a tool that
 * actually ran for the given turn.
 */
export interface TelemetryToolResult {
  service: string;
  log_count: number;
  error_count: number;
  metrics: { name: string; value: number }[];
  sample_logs: string[];
}

export interface SimilarToolResult {
  count: number;
  incidents: { id: string; summary: string; score: number | null }[];
}

export interface DependenciesToolResult {
  upstream: string[];
  downstream: string[];
}

export interface LogsToolResult {
  total_logs: number;
  error_count: number;
  warning_count: number;
  top_errors: { pattern: string; count: number }[];
}

export interface ChatToolResults {
  telemetry?: TelemetryToolResult;
  similar?: SimilarToolResult;
  dependencies?: DependenciesToolResult;
  logs?: LogsToolResult;
}

export interface ChatResponseMetadata {
  mode?: string;
  model_used?: string;
  tokens_used?: number | null;
  tools?: ChatToolResults;
  [key: string]: unknown;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  confidence?: number | null;
  suggested_actions?: string[] | null;
  related_incidents?: string[] | null;
  metadata?: ChatResponseMetadata | null;
}

// ---- Settings types ----
export interface ConstitutionalSettings {
  autoThreshold: number;
  approvalThreshold: number;
  maxActionsPerMinute: number;
  enableAuditLog: boolean;
  enableLearning: boolean;
  strictTier1: boolean;
}

export interface NotificationSettings {
  emailEnabled: boolean;
  slackEnabled: boolean;
  webhookEnabled: boolean;
  webhookUrl: string;
  notifyOnCritical: boolean;
  notifyOnApproval: boolean;
  notifyOnResolution: boolean;
}

export interface TelemetrySettings {
  lokiEnabled: boolean;
  lokiUrl: string;
  prometheusEnabled: boolean;
  prometheusUrl: string;
  tempoEnabled: boolean;
  tempoUrl: string;
  retentionDays: number;
}

export interface AllSettings {
  constitutional: ConstitutionalSettings;
  notifications: NotificationSettings;
  telemetry: TelemetrySettings;
}
// ---- end Settings types ----

export interface ConversationSummary {
  conversation_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  preview: string | null;
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ConversationHistory {
  conversation_id: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
  context?: Record<string, unknown> | null;
}

export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type IncidentStatus = 'open' | 'investigating' | 'identified' | 'monitoring' | 'resolved' | 'closed';

export interface ServiceInfo {
  name: string;
  namespace?: string;
}

export interface Incident {
  id: string;
  title: string;
  description?: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  category?: string;
  affected_services: ServiceInfo[];
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  rca_result?: RCAResult;
  remediation_plan?: RemediationPlan;
}

export interface IncidentCreate {
  title: string;
  description?: string;
  severity: IncidentSeverity;
  category?: string;
  affected_services: ServiceInfo[];
  tags?: string[];
  auto_analyze?: boolean;
}

export interface RCAResult {
  root_cause: string;
  confidence: number;
  contributing_factors: string[];
  evidence: string[];
}

export interface RemediationStep {
  step_number: number;
  action: string;
  description: string;
  estimated_duration_minutes?: number;
  requires_approval: boolean;
}

export interface RemediationPlan {
  plan_id: string;
  steps: RemediationStep[];
  estimated_resolution_minutes: number;
  confidence: number;
}

export interface IncidentList {
  items: Incident[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export type ActionType = 'restart_service' | 'scale_up' | 'scale_down' | 'modify_config' | 'rollback' | 'failover' | 'drain_node' | 'custom';
export type ActionStatus = 'pending' | 'validating' | 'awaiting_approval' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed' | 'cancelled' | 'expired';
export type AuthorizationLevel = 'automatic' | 'approval_required' | 'alert_only';

export interface ConstitutionalValidation {
  passed: boolean;
  authorization_level: AuthorizationLevel;
  confidence: number;
  tier1_passed: boolean;
  tier2_passed: boolean;
  tier3_passed: boolean;
  violations: Array<{ principle_id: string; reason: string }>;
  warnings: string[];
  explanation: string;
}

export interface Action {
  id: string;
  action_type: ActionType;
  description: string;
  target_service: string;
  target_instance?: string;
  parameters?: Record<string, unknown>;
  incident_id?: string;
  confidence: number;
  status: ActionStatus;
  requires_approval: boolean;
  validation?: ConstitutionalValidation;
  created_at: string;
  updated_at: string;
  approved_by?: string;
  approved_at?: string;
  execution_result?: {
    success: boolean;
    output?: string;
    error?: string;
    duration_ms: number;
  };
}

export interface ActionCreate {
  action_type: ActionType;
  description: string;
  target_service: string;
  target_instance?: string;
  parameters?: Record<string, unknown>;
  incident_id?: string;
  confidence: number;
  reason?: string;
}

export interface ActionApproval {
  approved: boolean;
  approved_by: string;
  comments?: string;
  modifications?: Record<string, unknown>;
}

export interface ActionList {
  items: Action[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface PendingApprovals {
  count: number;
  actions: Action[];
  oldest_pending?: string;
  urgency_breakdown: Record<string, number>;
}

export interface Tool {
  name: string;
  description: string;
  category: 'query' | 'action' | 'analysis';
  parameters: Record<string, unknown>;
  requires_approval: boolean;
  risk_level: 'low' | 'medium' | 'high';
}

export interface ToolCallResult {
  success: boolean;
  data: unknown;
  error?: string;
  execution_time_ms: number;
  metadata?: Record<string, unknown>;
}

export interface DashboardStats {
  incidents: {
    open: number;
    investigating: number;
    resolved_today: number;
    mttr_minutes: number | null;
  };
  actions: {
    pending_approval: number;
    executed_today: number;
    success_rate: number;
  };
  system: {
    health_score: number;
    services_healthy: number;
    services_degraded: number;
    services_down: number;
  };
}

// ---- Auth types ----
export interface AuthUser {
  username: string;
  role: string;
}

export interface AuthConfigResponse {
  auth_required: boolean;
}

export interface LoginResponse {
  user: AuthUser;
  expires_at: string;
}

export interface LogoutResponse {
  ok: boolean;
  everywhere: boolean;
}
// ---- end Auth types ----

/**
 * Window event dispatched when any non-auth API call comes back 401, so the
 * auth store (lib/auth.ts) can clear the cached user without api.ts importing
 * it (avoids a module cycle).
 */
export const AUTH_UNAUTHORIZED_EVENT = 'aiops:unauthorized';

/**
 * Global 401 handler: notify the auth store and send the browser to /login,
 * preserving the current location as ?next=. Guarded so a 401 while already
 * on /login can never cause a redirect loop.
 */
function handleUnauthorized(): void {
  try {
    window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT));
  } catch {
    // Event dispatch is best-effort only.
  }
  const { pathname, search } = window.location;
  if (pathname === '/login') return;
  const next = encodeURIComponent(`${pathname}${search}`);
  window.location.assign(`/login?next=${next}`);
}

// API Error
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Default per-request timeout (ms). Generous because a single reasoning turn
 * on the 14B model can legitimately take tens of seconds; we still want to
 * fail with a clear message rather than hang forever if the LLM stalls or the
 * connection drops.
 */
const DEFAULT_TIMEOUT_MS = 90_000;

// HTTP client helper
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Abort the request if it exceeds the timeout so callers get a deterministic
  // error instead of an indefinitely-pending promise.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      // Send the httpOnly session cookie on every same-origin API call.
      credentials: 'same-origin',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  } catch (err) {
    // A timeout surfaces as an AbortError; translate it into a clear message.
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        `Request timed out after ${Math.round(timeoutMs / 1000)}s. The server may be busy or unreachable.`,
        0
      );
    }
    // Network failures (server down, DNS, CORS) reach here too.
    throw new ApiError(
      err instanceof Error ? err.message : 'Network request failed',
      0
    );
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Ignore JSON parse errors
    }
    // A 401 on any non-auth endpoint means the session expired or was
    // revoked: clear the cached user and route to the login page. Auth
    // endpoints handle their own 401s (e.g. bad credentials on /auth/login,
    // the probe on /auth/me) and must NOT trigger a global redirect.
    if (response.status === 401 && !endpoint.startsWith('/auth/')) {
      handleUnauthorized();
    }
    throw new ApiError(errorMessage, response.status);
  }

  // 204 No Content (and other empty-body responses) have no JSON to parse.
  // Returning undefined here keeps DELETE-style calls from throwing on an
  // empty body, while still satisfying the generic Promise<T> contract.
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// API Client

export const api = {
  // Health
  health: {
    check: () => request<HealthResponse>('/health'),
    ready: () => request<{ ready: boolean }>('/health/ready'),
    live: () => request<{ alive: boolean }>('/health/live'),
  },

  // Chat
  chat: {
    send: (req: ChatRequest) =>
      request<ChatResponse>('/chat/', {
        method: 'POST',
        body: JSON.stringify(req),
      }),

    getConversation: (id: string) =>
      request<ConversationHistory>(`/chat/conversations/${id}`),

    listConversations: () =>
      request<ConversationListResponse>('/chat/conversations'),

    deleteConversation: (id: string) =>
      request<void>(`/chat/conversations/${id}`, { method: 'DELETE' }),
  },

  // Incidents
  incidents: {
    create: (incident: IncidentCreate) =>
      request<Incident>('/incidents/', {
        method: 'POST',
        body: JSON.stringify(incident),
      }),

    list: (params?: {
      page?: number;
      page_size?: number;
      status?: IncidentStatus[];
      severity?: IncidentSeverity[];
    }) => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', String(params.page));
      if (params?.page_size) searchParams.set('page_size', String(params.page_size));
      params?.status?.forEach(s => searchParams.append('status', s));
      params?.severity?.forEach(s => searchParams.append('severity', s));
      return request<IncidentList>(`/incidents/?${searchParams}`);
    },

    get: (id: string) => request<Incident>(`/incidents/${id}`),

    update: (id: string, updates: Partial<Incident>) =>
      request<Incident>(`/incidents/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      }),

    delete: (id: string) =>
      request<void>(`/incidents/${id}`, { method: 'DELETE' }),

    analyze: (id: string) =>
      request<{ rca: RCAResult; plan: RemediationPlan }>(`/incidents/${id}/analyze`, {
        method: 'POST',
      }),

    getSimilar: (id: string) =>
      request<{ similar: Incident[] }>(`/incidents/${id}/similar`),

    getStats: () =>
      request<{ total: number; by_status: Record<string, number>; by_severity: Record<string, number> }>('/incidents/stats'),
  },

  // Actions
  actions: {
    create: (action: ActionCreate) =>
      request<Action>('/actions', {
        method: 'POST',
        body: JSON.stringify(action),
      }),

    list: (params?: {
      page?: number;
      page_size?: number;
      status?: ActionStatus[];
      requires_approval?: boolean;
    }) => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', String(params.page));
      if (params?.page_size) searchParams.set('page_size', String(params.page_size));
      params?.status?.forEach(s => searchParams.append('status', s));
      if (params?.requires_approval !== undefined) {
        searchParams.set('requires_approval', String(params.requires_approval));
      }
      return request<ActionList>(`/actions/?${searchParams}`);
    },

    get: (id: string) => request<Action>(`/actions/${id}`),

    getPending: () => request<PendingApprovals>('/actions/pending'),

    getStats: () =>
      request<{
        total: number;
        by_status: Record<string, number>;
        success_rate: number;
      }>('/actions/stats'),

    approve: (id: string, approval: ActionApproval) =>
      request<Action>(`/actions/${id}/approve`, {
        method: 'POST',
        body: JSON.stringify(approval),
      }),

    execute: (id: string) =>
      request<Action>(`/actions/${id}/execute`, { method: 'POST' }),

    cancel: (id: string, reason?: string) =>
      request<Action>(`/actions/${id}/cancel?reason=${encodeURIComponent(reason || '')}`, {
        method: 'POST',
      }),
  },

  // Tools
  tools: {
    list: () => request<{ tools: Tool[]; total: number }>('/tools'),

    get: (name: string) => request<Tool>(`/tools/${name}`),

    call: (toolName: string, parameters: Record<string, unknown>, context?: Record<string, unknown>) =>
      request<ToolCallResult>('/tools/call', {
        method: 'POST',
        body: JSON.stringify({
          tool_name: toolName,
          parameters,
          context,
        }),
      }),
  },

  // Dashboard (aggregated stats)
  dashboard: {
    getStats: async (): Promise<DashboardStats> => {
      // Fetch stats from multiple endpoints
      const [incidentStats, actionStats, health] = await Promise.all([
        api.incidents.getStats(),
        api.actions.getStats(),
        api.health.check(),
      ]);

      // Check component health from array
      const fastAgentHealthy = isComponentHealthy(health, 'fast_agent');
      const reasoningAgentHealthy = isComponentHealthy(health, 'reasoning_agent');

      // Calculate actual response time from LLM latencies (in seconds)
      const fastLatency = health?.components?.find((c: { name: string }) => c.name === 'fast_agent')?.latency_ms || 0;
      const reasoningLatency = health?.components?.find((c: { name: string }) => c.name === 'reasoning_agent')?.latency_ms || 0;
      const avgResponseTimeMs = (fastLatency + reasoningLatency) / 2;
      // Convert to seconds for display (mttr_minutes is actually seconds for response time)
      const avgResponseTimeSec = avgResponseTimeMs > 0 ? Math.round(avgResponseTimeMs / 1000 * 10) / 10 : null;

      // Count healthy components
      const healthyComponents = health?.components?.filter((c: { healthy: boolean }) => c.healthy).length || 0;
      const totalComponents = health?.components?.length || 0;

      return {
        incidents: {
          open: incidentStats.by_status['open'] || 0,
          investigating: incidentStats.by_status['investigating'] || 0,
          resolved_today: incidentStats.by_status['resolved'] || 0,
          mttr_minutes: avgResponseTimeSec, // Actual LLM response time in seconds
        },
        actions: {
          pending_approval: actionStats.by_status['awaiting_approval'] || 0,
          executed_today: actionStats.by_status['completed'] || 0,
          success_rate: actionStats.success_rate || 0,
        },
        system: {
          health_score: fastAgentHealthy && reasoningAgentHealthy ? 0.95 : 0.7,
          services_healthy: healthyComponents,
          services_degraded: totalComponents - healthyComponents,
          services_down: 0,
        },
      };
    },
  },
  // Auth (login/session). NOTE: /auth/config is public; the rest ride the
  // httpOnly session cookie set by login.
  auth: {
    config: () => request<AuthConfigResponse>('/auth/config'),

    me: () => request<AuthUser>('/auth/me'),

    login: (username: string, password: string) =>
      request<LoginResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),

    logout: (everywhere = false) =>
      request<LogoutResponse>('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ everywhere }),
      }),
  },

  // Settings
  settings: {
    get: () => request<AllSettings>('/settings/'),
    save: (body: AllSettings) =>
      request<AllSettings>('/settings/', {
        method: 'PUT',
        body: JSON.stringify(body),
      }),
    reset: () =>
      request<AllSettings>('/settings/reset', { method: 'POST' }),
  },
};

export default api;
