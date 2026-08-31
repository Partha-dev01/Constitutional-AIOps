/**
 * Constitutional AIOps - Frontend API Client
 *
 * Type-safe API client for communicating with the backend.
 */

import type { TopologyResponse } from '../components/schema/types';

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
  /**
   * Per-assistant-turn metadata the backend persists on each stored message so
   * a conversation reloaded from history can replay its tool-call timeline +
   * insight/proposed cards (otherwise reloaded chats show only the text).
   * Absent on user turns and on conversations created before this was added.
   */
  metadata?: ChatMessageMetadata | null;
}

/** The replay payload stored on a persisted assistant message (see ChatMessage). */
export interface ChatMessageMetadata {
  confidence?: number | null;
  suggested_actions?: string[] | null;
  related_incidents?: string[] | null;
  proposed_action?: ProposedAction | null;
  /** The same ChatResponse.metadata (tools, model_used, tokens_used) for the turn. */
  metadata?: ChatResponseMetadata | null;
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

/**
 * A single tool the backend agent actually executed for a chat turn. The
 * ordered list (`ChatResponseMetadata.tool_calls`) is the truthful source of
 * what ran — the chat timeline renders these directly (real name + arguments +
 * structured result) instead of a heuristic checklist.
 */
export interface ChatToolCall {
  id?: string;
  name: string;
  arguments?: Record<string, unknown> | null;
  status?: 'ok' | 'error' | 'needs_param' | string;
  result?: unknown;
  error?: string | null;
  duration_ms?: number | null;
}

export interface ChatResponseMetadata {
  mode?: string;
  model_used?: string;
  tokens_used?: number | null;
  tools?: ChatToolResults;
  /** Ordered list of every tool the agent ran this turn (source of truth). */
  tool_calls?: ChatToolCall[];
  [key: string]: unknown;
}

/**
 * An AI-proposed remediation action attached to a chat turn. The card in the
 * chat (ProposedActionCard) lets a human approve/reject it (mode "approve"),
 * or shows the outcome read-only when it was auto-executed or blocked.
 */
export interface ProposedAction {
  id: string;
  tool_name: string;
  parameters: { service_name: string; reason: string; target_replicas?: number };
  target: 't3' | 'local';
  title: string;
  rationale: string;
  mode: 'approve' | 'auto';
  /**
   * proposed/auto_executed/blocked are set when the turn is created;
   * executed/rejected/refused are written back onto the persisted conversation
   * after a human decision, so reloaded chats render the outcome read-only.
   */
  status: 'proposed' | 'auto_executed' | 'blocked' | 'executed' | 'rejected' | 'refused';
  verdict: Record<string, unknown> | null;
  execution_result: Record<string, unknown> | null;
}

/** Result of a human decision on a proposed action (approve/reject). */
export interface ActionDecisionResponse {
  action_id: string;
  status: 'executed' | 'refused' | 'rejected';
  success: boolean;
  error_code: string | null;
  verdict: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
}

export interface ChatResponse {
  conversation_id: string;
  message: ChatMessage;
  confidence?: number | null;
  suggested_actions?: string[] | null;
  related_incidents?: string[] | null;
  metadata?: ChatResponseMetadata | null;
  /** Optional AI-proposed remediation for this turn (may be null/absent). */
  proposed_action?: ProposedAction | null;
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

export type RemediationMode = 'diagnose' | 'approve' | 'auto';

export interface RemediationSettings {
  mode: RemediationMode;
  /** Min confidence (70..99) for auto-execution. Default 90. */
  autoConfidenceThreshold: number;
  /** Require telemetry evidence before auto-executing. Default true. */
  requireEvidenceForAuto: boolean;
  /** Action tools allowed to auto-execute in auto mode; others always need consent. */
  autoToolAllowlist: ActionToolName[];
  /** Base URL of the t3 demo agent. */
  demoTargetUrl: string;
}

/** The mutating MCP action tools (everything else is read-only). */
export type ActionToolName = 'restart_service' | 'scale_service';

export interface AllSettings {
  constitutional: ConstitutionalSettings;
  notifications: NotificationSettings;
  telemetry: TelemetrySettings;
  remediation: RemediationSettings;
}

export type ServingSwapStatus = 'idle' | 'pending' | 'swapping' | 'error';

/** GET/POST /settings/serving-mode — Mode 1 ⇄ Mode 2 swap channel. */
export interface ServingModeStatus {
  mode: number;
  single_engine: boolean;
  requested_mode: number | null;
  swap_status: ServingSwapStatus;
  detail: string | null;
  requested_at: string | null;
  updated_at: string | null;
}
// ---- end Settings types ----

// ---- Demo / Chaos types ----
export interface DemoScenario {
  id: string;
  label: string;
  description: string;
}

export interface DemoStatus {
  target_url: string;
  reachable: boolean;
  scenarios: Record<string, { active: boolean }>;
  containers: Record<string, { running: boolean }>;
}

export interface DemoChaosResult {
  scenario: string;
  action: 'start' | 'heal';
  success: boolean;
  detail: string;
}
// ---- end Demo / Chaos types ----

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
// Matches the backend IncidentStatus enum (src/api/schemas/incident.py).
export type IncidentStatus = 'detecting' | 'analyzing' | 'pending_approval' | 'remediating' | 'resolved' | 'closed';

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
  tags?: string[];
  source?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  /** Root-cause analysis as returned by the live API. Matches the backend
   *  RCAResult schema (src/api/schemas/incident.py:129-138). */
  rca?: RCAResult | null;
  remediation_plan?: RemediationPlan | null;
}

/** Result of POST /incidents/{id}/remediate (approve-and-remediate). */
export interface IncidentRemediateResult {
  incident_id: string;
  status: 'resolved' | 'refused';
  success: boolean;
  /** demo_heal = t3 chaos heal; restart_service = gated executor. */
  method: 'demo_heal' | 'restart_service';
  error_code?: string | null;
  detail?: string;
  verdict?: Record<string, unknown> | null;
  incident: Incident;
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

// Matches the backend RCAResult schema (src/api/schemas/incident.py:129-138).
export interface RCAResult {
  root_cause: string;
  causal_chain: string[];
  confidence: number;
  reasoning?: string | null;
  similar_incidents?: string[] | null;
}

// Matches the backend RemediationStep schema (src/api/schemas/incident.py:141-150).
export interface RemediationStep {
  order: number;
  action: string;
  command?: string | null;
  risk: 'low' | 'medium' | 'high';
  requires_approval: boolean;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  executed_at?: string | null;
  result?: string | null;
}

// Matches the backend RemediationPlan schema (src/api/schemas/incident.py:153-163).
export interface RemediationPlan {
  plan_id: string;
  incident_id: string;
  created_at: string;
  steps: RemediationStep[];
  overall_risk: 'low' | 'medium' | 'high';
  estimated_duration?: string | null;
  requires_approval: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
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
    /** Active incidents = detecting + analyzing + pending_approval + remediating. */
    active: number;
    /** In-progress subset = analyzing + remediating. */
    in_progress: number;
    /** Incidents resolved without human intervention (auto-resolved). */
    resolved_total: number;
    /**
     * Average LLM response latency in MILLISECONDS, sourced from the /health
     * agent component checks. Null when no agent reported a latency (card shows
     * "N/A"). Named `mttr_minutes` for historical reasons — it is the dashboard's
     * "Avg Response Time" value, not an incident MTTR.
     */
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
  /** Public self-service signup available (hosted demo only). */
  signup_enabled: boolean;
  /** '' when disabled, else 'turnstile' | 'hcaptcha'. */
  captcha_provider: string;
  /** Public captcha site key for the widget ('' when no provider). */
  captcha_site_key: string;
}

export interface LoginResponse {
  user: AuthUser;
  expires_at: string;
}

export interface SignupResponse {
  user: AuthUser;
  expires_at: string;
  email_verification: string;
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

// ---------------------------------------------------------------------------
// Chat streaming (Mode 2 plan, Phase 4): SSE over fetch — no new dependency.
// ---------------------------------------------------------------------------

/** `meta` event of POST /chat/stream. */
export interface ChatStreamMeta {
  conversation_id: string;
  /** False on a Mode 1 backend: the answer then arrives as ONE delta. */
  streaming: boolean;
  mode: number;
}

/** One executed tool call, same shape as `metadata.tool_calls` entries. */
export type ChatStreamToolResult = Record<string, unknown>;

export interface ChatStreamCallbacks {
  onMeta?: (meta: ChatStreamMeta) => void;
  onToolResult?: (record: ChatStreamToolResult) => void;
  onDelta?: (text: string) => void;
  /** e.g. {kind: "refusal_replaced"} — done.message.content superseded the stream. */
  onNotice?: (notice: { kind: string }) => void;
  /**
   * Fired last on success with the full ChatResponse — identical contract to
   * api.chat.send. `done.message.content` is ALWAYS authoritative; replace
   * any streamed text with it.
   */
  onDone: (response: ChatResponse) => void;
  onError?: (detail: string) => void;
}

/**
 * POST /chat/stream and dispatch its Server-Sent Events to typed callbacks.
 *
 * Works against BOTH modes (a Mode 1 backend emits meta -> tool_result* ->
 * one delta -> done), so callers can probe /health/serving for
 * features.streaming purely as a UX decision, not a correctness one.
 * Resolves after `done`/`error`; rejects on transport/HTTP failures.
 */
async function streamChat(
  req: ChatRequest,
  callbacks: ChatStreamCallbacks,
  timeoutMs: number = 300_000
): Promise<void> {
  const url = `${API_BASE_URL}/chat/stream`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(req),
    });
  } catch (err) {
    clearTimeout(timer);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(
        `Stream timed out after ${Math.round(timeoutMs / 1000)}s. The server may be busy or unreachable.`,
        0
      );
    }
    throw new ApiError(err instanceof Error ? err.message : 'Network request failed', 0);
  }

  try {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // Ignore JSON parse errors
      }
      if (response.status === 401) {
        handleUnauthorized();
      }
      throw new ApiError(errorMessage, response.status);
    }
    if (!response.body) {
      throw new ApiError('Streaming not supported by this browser/transport', 0);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    const dispatch = (frame: string): void => {
      let eventName = '';
      let dataLine = '';
      for (const line of frame.split(/\r?\n/)) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim();
        else if (line.startsWith('data:')) dataLine += line.slice(5).trim();
      }
      if (!eventName || !dataLine) return;
      switch (eventName) {
        case 'meta':
          callbacks.onMeta?.(JSON.parse(dataLine) as ChatStreamMeta);
          break;
        case 'tool_result':
          callbacks.onToolResult?.(JSON.parse(dataLine) as ChatStreamToolResult);
          break;
        case 'delta':
          callbacks.onDelta?.((JSON.parse(dataLine) as { text: string }).text);
          break;
        case 'notice':
          callbacks.onNotice?.(JSON.parse(dataLine) as { kind: string });
          break;
        case 'done':
          callbacks.onDone(JSON.parse(dataLine) as ChatResponse);
          break;
        case 'error':
          callbacks.onError?.((JSON.parse(dataLine) as { detail: string }).detail);
          break;
        default:
          break; // Forward-compatible: ignore unknown events.
      }
    };

    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sep = buffer.indexOf('\n\n');
      while (sep !== -1) {
        dispatch(buffer.slice(0, sep));
        buffer = buffer.slice(sep + 2);
        sep = buffer.indexOf('\n\n');
      }
    }
    if (buffer.trim()) dispatch(buffer);
  } finally {
    clearTimeout(timer);
  }
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

    /**
     * SSE streaming variant of send (Phase 4). UI adoption is deferred until
     * the live SSE-through-Caddy pass; the contract is stable either way —
     * onDone delivers the same ChatResponse send() returns.
     */
    stream: (req: ChatRequest, callbacks: ChatStreamCallbacks, timeoutMs?: number) =>
      streamChat(req, callbacks, timeoutMs),

    getConversation: (id: string) =>
      request<ConversationHistory>(`/chat/conversations/${id}`),

    listConversations: () =>
      request<ConversationListResponse>('/chat/conversations'),

    deleteConversation: (id: string) =>
      request<void>(`/chat/conversations/${id}`, { method: 'DELETE' }),

    /** Approve (or reject) an AI-proposed remediation action from a chat turn. */
    decideAction: (actionId: string, approved: boolean, comment?: string) =>
      request<ActionDecisionResponse>(`/chat/actions/${actionId}/decision`, {
        method: 'POST',
        body: JSON.stringify(comment === undefined ? { approved } : { approved, comment }),
      }),
  },

  // Demo / Chaos (t3 demo agent orchestration)
  demo: {
    scenarios: () => request<{ scenarios: DemoScenario[] }>('/demo/scenarios'),

    status: () => request<DemoStatus>('/demo/status'),

    start: (scenario: string) =>
      request<DemoChaosResult>(`/demo/chaos/${scenario}/start`, { method: 'POST' }),

    heal: (scenario: string) =>
      request<DemoChaosResult>(`/demo/chaos/${scenario}/heal`, { method: 'POST' }),

    setTarget: (url: string) =>
      request<{ target_url: string }>('/demo/target', {
        method: 'PUT',
        body: JSON.stringify({ url }),
      }),
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
      request<Incident>(`/incidents/${id}/analyze`, {
        method: 'POST',
      }),

    getSimilar: (id: string) =>
      request<{ similar: Incident[] }>(`/incidents/${id}/similar`),

    /** Approve-and-remediate: demo incidents heal on the t3, real incidents
     *  restart the affected service through the constitutional gate. */
    remediate: (id: string) =>
      request<IncidentRemediateResult>(`/incidents/${id}/remediate`, {
        method: 'POST',
      }),

    /** Reject the remediation and archive the incident (status -> closed). */
    dismiss: (id: string) =>
      request<Incident>(`/incidents/${id}/dismiss`, { method: 'POST' }),

    getStats: () =>
      request<{
        total: number;
        // by_status keys are IncidentStatus values (src/api/schemas/incident.py:24-31).
        by_status: Partial<Record<IncidentStatus, number>>;
        by_severity: Partial<Record<IncidentSeverity, number>>;
        /** Incidents the system resolved without human intervention. */
        auto_resolved_count: number;
        /** Mean time to resolution in minutes (null when nothing has resolved). */
        mean_time_to_resolution: number | null;
      }>('/incidents/stats'),
  },

  // Actions
  actions: {
    create: (action: ActionCreate) =>
      request<Action>('/actions/', {
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

      // Real LLM response latency from the /health component checks (ms). Average
      // only the agent latencies that actually reported a positive value; if none
      // did, leave it null so the card shows "N/A" rather than a misleading 0.
      const agentLatencies = ['fast_agent', 'reasoning_agent']
        .map((name) => health?.components?.find((c: { name: string }) => c.name === name)?.latency_ms ?? 0)
        .filter((ms) => ms > 0);
      const avgResponseTimeMs =
        agentLatencies.length > 0
          ? Math.round(agentLatencies.reduce((sum, ms) => sum + ms, 0) / agentLatencies.length)
          : null;

      // Count healthy components
      const healthyComponents = health?.components?.filter((c: { healthy: boolean }) => c.healthy).length || 0;
      const totalComponents = health?.components?.length || 0;

      // Map the real IncidentStatus buckets (src/api/schemas/incident.py:24-31).
      // There is no 'open' / 'investigating' status backend-side.
      const byStatus = incidentStats.by_status;
      const activeIncidents =
        (byStatus.detecting || 0) +
        (byStatus.analyzing || 0) +
        (byStatus.pending_approval || 0) +
        (byStatus.remediating || 0);
      const inProgressIncidents = (byStatus.analyzing || 0) + (byStatus.remediating || 0);

      return {
        incidents: {
          active: activeIncidents,
          in_progress: inProgressIncidents,
          // Total incidents in the resolved state. Reflects demo heals (which
          // are operator-approved, so they don't count as auto-resolved); the
          // dedicated auto_resolved_count stays available on the stats type.
          resolved_total: byStatus.resolved || 0,
          // Real LLM response latency in milliseconds (null -> card shows "N/A").
          mttr_minutes: avgResponseTimeMs,
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

    signup: (payload: {
      username: string
      email: string
      password: string
      captcha_token?: string
    }) =>
      request<SignupResponse>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    logout: (everywhere = false) =>
      request<LogoutResponse>('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ everywhere }),
      }),
  },

  // Graph — schema-mode platform topology (FROZEN payload contract; see
  // components/schema/types.ts and e2e/fixtures/topology.json).
  graph: {
    topology: (params?: { window_hours?: number; buckets?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.window_hours) searchParams.set('window_hours', String(params.window_hours));
      if (params?.buckets) searchParams.set('buckets', String(params.buckets));
      const qs = searchParams.toString();
      return request<TopologyResponse>(`/graph/topology${qs ? `?${qs}` : ''}`);
    },
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
    servingMode: () => request<ServingModeStatus>('/settings/serving-mode'),
    requestServingMode: (mode: 1 | 2) =>
      request<ServingModeStatus>('/settings/serving-mode', {
        method: 'POST',
        body: JSON.stringify({ mode }),
      }),
  },
};

export default api;
