# Frontend Architecture

> **Version**: 0.6.1
> **Last Updated**: 2026-01-28
> **Framework**: React 18 + TypeScript + Vite
> **Source of Truth**: [KEY_METRICS.md](KEY_METRICS.md)

---

## Overview

The Constitutional AIOps frontend is a React single-page application providing:

- **Real-time Dashboard**: System health, incidents, agent status
- **Incident Management**: Create, view, analyze incidents with RCA
- **Action Approval Workflow**: Constitutional AI validation UI
- **Interactive Chat**: Multi-turn conversation with Reasoning Agent
- **Agent Monitoring**: Activity streams, telemetry, graph visualization
- **Graph Explorer**: Episodic knowledge graph with force-directed visualization (v0.5.0+)
- **Settings Management**: Constitutional thresholds, prompts, notifications

---

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI framework |
| TypeScript | 5.3.0 | Type safety |
| Vite | 5.0.0 | Build tool |
| React Router | 6.21.0 | Client-side routing |
| TanStack Query | 5.17.0 | Server state management |
| Zustand | 4.4.0 | Client state management |
| Tailwind CSS | 3.4.0 | Styling |
| Axios | 1.6.0 | HTTP client |
| Recharts | 2.10.0 | Charts |
| Lucide React | 0.300.0 | Icons |
| react-force-graph-2d | 1.25.x | Force-directed graph (v0.5.0+) |

---

## Project Structure

```
frontend/
├── index.html              # HTML entry point
├── package.json            # Dependencies
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript config
├── tailwind.config.js      # Tailwind theme
├── postcss.config.js       # PostCSS plugins
│
└── src/
    ├── main.tsx            # React bootstrap
    ├── App.tsx             # Root component with routes
    ├── index.css           # Global styles + CSS variables
    ├── vite-env.d.ts       # Environment type definitions
    │
    ├── pages/              # Route components
    │   ├── Dashboard.tsx   # System overview
    │   ├── Incidents.tsx   # Incident management
    │   ├── Chat.tsx        # Agent chat interface
    │   ├── Agents.tsx      # Agent hub (6 tabs)
    │   ├── Graph.tsx       # Episodic graph explorer (v0.6.0+)
    │   └── Settings.tsx    # Configuration (5 tabs)
    │
    ├── components/         # Shared components
    │   ├── Layout.tsx      # App shell with sidebar
    │   ├── IncidentTimeline.tsx
    │   ├── DependencyGraph.tsx
    │   ├── EpisodicGraphExplorer.tsx  # Force-directed graph (v0.5.0+)
    │   └── index.ts        # Exports
    │
    └── lib/                # Utilities
        ├── api.ts          # Type-safe API client
        ├── websocket.ts    # Real-time events
        └── utils.ts        # Helpers
```

---

## Configuration Files

### package.json
**Key Scripts**:
```json
{
  "dev": "vite",
  "build": "tsc && vite build",
  "lint": "eslint src --ext ts,tsx",
  "test": "vitest"
}
```

### vite.config.ts
**Key Settings**:
- Path alias: `@` → `./src`
- Dev server: port 3000
- API proxy: `/api` → `http://localhost:8000`
- WebSocket proxy: `/ws` → `ws://localhost:8000`

### tsconfig.json
**Key Settings**:
- Target: ES2020
- Strict mode enabled
- Path aliases configured

### tailwind.config.js
**Key Features**:
- Dark mode (class strategy)
- Custom HSL color variables
- Inter font family
- Typography plugin

---

## Pages

### Dashboard (`src/pages/Dashboard.tsx`)

**Purpose**: Main system overview and real-time status

**Features**:
- Stats grid (Active Incidents, Auto-Resolved, Avg Response Time, System Health)
- Pending approvals alert banner
- Model status cards (Fast & Reasoning agents)
- Remediation performance metrics
- Service availability with uptime history bars
- WebSocket event subscriptions

**State**:
```typescript
const [loading, setLoading] = useState(true);
const [stats, setStats] = useState<DashboardStats | null>(null);
const [health, setHealth] = useState<HealthResponse | null>(null);
const [services, setServices] = useState<ServiceStatus[]>([]);
const [error, setError] = useState<string | null>(null);
```

**WebSocket Events**:
- `INCIDENT_CREATED`, `INCIDENT_RESOLVED`
- `ACTION_CREATED`, `ACTION_APPROVED`, `ACTION_EXECUTED`
- `RCA_COMPLETED`, `ALERT`

**Sub-components**:
- `StatCard`: Displays metric with icon and trend
- `ModelCard`: Shows agent status with latency

---

### Incidents (`src/pages/Incidents.tsx`)

**Purpose**: Incident management and monitoring

**Features**:
- Incident list with pagination
- Filters: status, severity, search
- Pending approvals banner
- Create incident modal
- Incident detail modal with RCA results
- Action approval workflow

**State**:
```typescript
const [incidents, setIncidents] = useState<Incident[]>([]);
const [pendingActions, setPendingActions] = useState<Action[]>([]);
const [filters, setFilters] = useState({
  status: 'all',
  severity: 'all',
  search: ''
});
const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
```

**Modals**:
- `IncidentCard`: List item with severity badge
- `IncidentDetailModal`: Full details, RCA, remediation plan
- `ApprovalModal`: Constitutional validation display, approve/reject
- `CreateIncidentModal`: Form with severity, category, services

**API Calls**:
- `api.incidents.list()`, `api.incidents.create()`
- `api.incidents.analyze()`, `api.actions.approve()`

---

### Chat (`src/pages/Chat.tsx`)

**Purpose**: Interactive conversation with Reasoning Agent

**Features**:
- Multi-turn conversation history
- User/assistant message display with avatars
- Markdown rendering (react-markdown + remark-gfm)
- Auto-scroll to latest message
- Error display inline
- New conversation button

**State**:
```typescript
const [messages, setMessages] = useState<ChatMessage[]>([]);
const [input, setInput] = useState('');
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [conversationId, setConversationId] = useState<string | null>(null);
```

**Message Format**:
```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
```

---

### Agents (`src/pages/Agents.tsx`)

**Purpose**: Agent Hub - monitor and manage dual-agent system

**Tabs** (6 total):

#### 1. Fast Agent Tab
- Activity stream for Qwen3-4B
- Telemetry annotation results
- Latency and success metrics

#### 2. Reasoning Agent Tab
- Activity stream for Qwen3-14B
- RCA and planning results
- Latency and success metrics

#### 3. Telemetry Tab
- Log viewer with filtering (level, service)
- Metrics summary from Prometheus
- LGTM stack integration

#### 4. Graph Explorer Tab
- Neo4j episodic memory visualization
- SVG-based circular graph layout
- Node selection with details panel
- Service dependency edges

#### 5. MCP Tools Tab
- Tool discovery and listing
- Risk level indicators
- Tool execution interface

#### 6. Infrastructure Tab
- Docker container monitoring
- Health status indicators
- Container selection for monitoring
- Real-time status updates

**State**:
```typescript
const [activeTab, setActiveTab] = useState('fast');
const [health, setHealth] = useState<HealthResponse | null>(null);
const [fastActivity, setFastActivity] = useState<AgentActivity[]>([]);
const [reasoningActivity, setReasoningActivity] = useState<AgentActivity[]>([]);
const [logs, setLogs] = useState<LogEntry[]>([]);
const [metrics, setMetrics] = useState<MetricPoint[]>([]);
const [graphNodes, setGraphNodes] = useState<ServiceNode[]>([]);
const [graphEdges, setGraphEdges] = useState<DependencyEdge[]>([]);
const [tools, setTools] = useState<ToolInfo[]>([]);
const [containers, setContainers] = useState<ContainerInfo[]>([]);
```

---

### Settings (`src/pages/Settings.tsx`)

**Purpose**: System configuration management

**Tabs** (5 total):

#### 1. Constitutional AI Tab
- Confidence threshold sliders (auto: 70-99%, approval: 50-89%)
- Max actions per minute limiter
- Authorization level visualization
- Safety compliance toggles (Tier 1 enforcement, audit logging)

#### 2. Notifications Tab
- Channel configuration (email, Slack, webhook)
- Event-based triggers
- Critical incident alerts

#### 3. Telemetry Tab
- LGTM stack URLs
- Data retention policy (7-365 days)
- Connection status

#### 4. Models Tab
- Model status display (Fast & Reasoning agents)
- Architecture info (VRAM usage, TTL settings)
- Neo4j health and fallback mode

#### 5. System Prompts Tab
- Fetch, edit, save, reset prompts
- Agent-specific prompts
- JSON metadata display

**State**:
```typescript
const [activeTab, setActiveTab] = useState('constitutional');
const [health, setHealth] = useState<HealthResponse | null>(null);
const [constitutionalSettings, setConstitutionalSettings] = useState({
  autoThreshold: 90,
  approvalThreshold: 70,
  maxActionsPerMinute: 10
});
const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
const [editingPrompt, setEditingPrompt] = useState<string | null>(null);
```

---

### Graph (`src/pages/Graph.tsx`) - v0.6.0+

**Purpose**: Dedicated episodic knowledge graph visualization page

**Features**:
- Full-page force-directed graph visualization
- Refresh and loading states
- Error handling with retry
- Responsive layout

**Data Transformation**:
Transforms backend graph data to visualization format:
```typescript
interface GraphNode {
  id: string;
  label: string;
  type: 'service' | 'episode' | 'incident' | 'action' | 'root_cause' | 'entity';
  status?: 'healthy' | 'warning' | 'critical' | 'detected' | 'analyzing' | 'remediating' | 'resolved';
  confidence?: number;
  severity?: string;
  category?: string;
  rootCause?: string;
}

interface GraphLink {
  source: string;
  target: string;
  label?: string;
  type?: string;
  weight?: number;
}
```

**API Endpoint**: `GET /api/v1/graph/episodes`

---

## Components

### Layout (`src/components/Layout.tsx`)

**Purpose**: Application shell with sidebar navigation

**Features**:
- Fixed left sidebar (264px width)
- Logo with Constitutional AIOps branding
- Navigation menu (5 items)
- Active route highlighting
- Health status polling (every 30s)
- Demo mode controls (Start, Reset)
- System health indicator

**Props**:
```typescript
interface LayoutProps {
  children: React.ReactNode;
}
```

**Navigation Items**:
| Label | Path | Icon |
|-------|------|------|
| Dashboard | `/` | LayoutDashboard |
| Agents | `/agents` | Cpu |
| Incidents | `/incidents` | AlertTriangle |
| Chat | `/chat` | MessageSquare |
| Settings | `/settings` | Settings |

---

### IncidentTimeline (`src/components/IncidentTimeline.tsx`)

**Purpose**: Visual timeline of incident events

**Features**:
- Event type icons with color coding
- Expandable event details
- Actor information (user, system, agent)
- Relative timestamp formatting
- Vertical timeline connector

**Props**:
```typescript
interface IncidentTimelineProps {
  events: TimelineEvent[];
  onEventClick?: (event: TimelineEvent) => void;
}
```

**Event Types** (11):
```typescript
type TimelineEventType =
  | 'created' | 'updated' | 'status_change'
  | 'rca_started' | 'rca_completed'
  | 'action_created' | 'action_approved' | 'action_rejected' | 'action_executed'
  | 'resolved' | 'comment';
```

**Helper Function**:
```typescript
function generateTimelineFromIncident(incident: Incident): TimelineEvent[]
```

---

### DependencyGraph (`src/components/DependencyGraph.tsx`)

**Purpose**: Service dependency visualization

**Features**:
- Interactive SVG-based graph
- Layered layout (gateway → api → worker → database)
- Service type icons
- Status color coding
- Hover effects and zoom controls
- Click to select and view details
- Metrics display (CPU, memory, latency, error rate)
- Dependency listing
- Legend showing status meanings

**Props**:
```typescript
interface DependencyGraphProps {
  services: ServiceNode[];
  edges?: DependencyEdge[];
  onServiceClick?: (service: ServiceNode) => void;
  selectedService?: string;
}
```

**Types**:
```typescript
type ServiceType = 'api' | 'database' | 'cache' | 'queue' | 'gateway' | 'worker' | 'external';
type ServiceStatus = 'healthy' | 'degraded' | 'down' | 'unknown';

interface ServiceNode {
  name: string;
  type: ServiceType;
  status: ServiceStatus;
  dependencies: string[];
  metrics?: {
    cpu: number;
    memory: number;
    latency: number;
    errorRate: number;
  };
}
```

---

### EpisodicGraphExplorer (`src/components/EpisodicGraphExplorer.tsx`) - v0.5.0+

**Purpose**: Force-directed episodic knowledge graph visualization using react-force-graph-2d

**Features**:
- Interactive force-directed layout with D3 physics
- Pan to clicked node (800ms animation)
- Node type filtering controls
- Edge visibility toggles (SIMILAR_TO, entities)
- Stats overlay showing node/edge counts
- Interactive legend with color coding
- Pause/resume animation control

**Physics Constants (v0.6.0)**:
```typescript
const CHARGE_STRENGTH = -300;  // Node repulsion force

// Variable link distances by relationship type
const LINK_DISTANCES = {
  'similar_to': 80,      // Similar episodes nearby
  'affects': 120,        // Service impact
  'involves': 120,       // Service involvement
  'caused_by': 100,      // Causal relationships
  'experienced': 100,    // Root cause experience
  'resolved_by': 130,    // Resolution actions
  'remediates': 130,     // Remediation
  'relates': 90          // LLM-extracted relations
};

// Node sizes by type
const NODE_SIZES = {
  'episode': 9,
  'root_cause': 7,
  'service': 6,
  'entity': 6,
  'action': 5
};
```

**D3 Force Configuration**:
```typescript
{
  cooldownTicks: 100,
  d3AlphaDecay: 0.02,
  d3VelocityDecay: 0.4,
  d3AlphaMin: 0.01,
  nodeRelSize: 8
}
```

**Props**:
```typescript
interface EpisodicGraphExplorerProps {
  nodes: GraphNode[];
  links: GraphLink[];
  onNodeClick?: (node: GraphNode) => void;
  selectedNode?: string;
  height?: number;
}
```

**Node Color Scheme**:
| Node Type | Color |
|-----------|-------|
| Service (healthy) | Blue (#3B82F6) |
| Service (warning) | Amber (#F59E0B) |
| Service (critical) | Red (#EF4444) |
| Episode (resolved) | Green (#10B981) |
| Episode (analyzing) | Blue (#3B82F6) |
| Root Cause | Orange (#F97316) |
| Action | Cyan (#06B6D4) |
| Entity | Pink (#EC4899) |

**Edge Color Scheme**:
| Edge Type | Color |
|-----------|-------|
| depends_on | Blue |
| affects/involves | Red |
| caused_by/experienced | Orange |
| resolved_by/remediates | Green |
| similar_to | Purple |
| LLM relations | Pink |

**Controls**:
- Show/Hide SIMILAR_TO edges
- Show/Hide Entity nodes
- Pause/Resume animation
- Node type filter checkboxes

---

## Libraries

### api.ts (`src/lib/api.ts`)

**Purpose**: Type-safe API client for backend communication

**Base URL**: Uses `VITE_API_URL` env var, defaults to `/api/v1`

**Namespaces**:

#### api.health
```typescript
check(): Promise<HealthResponse>
ready(): Promise<ReadinessResponse>
live(): Promise<LivenessResponse>
```

#### api.chat
```typescript
send(request: ChatRequest): Promise<ChatResponse>
getConversation(id: string): Promise<ConversationHistory>
listConversations(limit?: number): Promise<ConversationList>
deleteConversation(id: string): Promise<void>
```

#### api.incidents
```typescript
create(data: IncidentCreate): Promise<Incident>
list(filters?: IncidentFilters): Promise<IncidentList>
get(id: string): Promise<Incident>
update(id: string, data: IncidentUpdate): Promise<Incident>
delete(id: string): Promise<void>
analyze(id: string): Promise<RCAResult>
getSimilar(id: string): Promise<SimilarIncident[]>
getStats(): Promise<IncidentStats>
```

#### api.actions
```typescript
create(data: ActionCreate): Promise<Action>
list(filters?: ActionFilters): Promise<ActionList>
get(id: string): Promise<Action>
getPending(): Promise<PendingApprovals>
getStats(): Promise<ActionStats>
approve(id: string, approval: ActionApproval): Promise<Action>
execute(id: string): Promise<ActionExecutionResult>
cancel(id: string): Promise<void>
```

#### api.tools
```typescript
list(): Promise<ToolListResponse>
get(name: string): Promise<ToolInfo>
call(request: ToolCallRequest): Promise<ToolCallResponse>
```

#### api.dashboard
```typescript
getStats(): Promise<DashboardStats>  // Aggregates incident, action, health data
```

**Key Types** (30+):
```typescript
interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: Record<string, ComponentHealth>;
  uptime_seconds: number;
}

interface Incident {
  id: string;
  title: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  category: IncidentCategory;
  rca?: RCAResult;
  remediation_plan?: RemediationPlan;
  // ...
}

interface ConstitutionalValidation {
  passed: boolean;
  authorization_level: 'automatic' | 'approval_required' | 'alert_only';
  confidence: number;
  tier1_passed: boolean;
  tier2_passed: boolean;
  tier3_passed: boolean;
  violations: string[];
  warnings: string[];
  explanation: string;
}
```

---

### websocket.ts (`src/lib/websocket.ts`)

**Purpose**: Real-time event streaming via WebSocket

**Main Hook**:
```typescript
function useWebSocket(options?: UseWebSocketOptions): {
  isConnected: boolean;
  connectionState: ConnectionState;
  subscribe: (eventTypes: EventType[], callback: EventCallback) => () => void;
  send: (message: any) => void;
}
```

**Options**:
```typescript
interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  url?: string;
}
```

**Event Types** (14):
```typescript
enum EventType {
  // Connection
  CONNECTED = 'connected',
  PING = 'ping',
  PONG = 'pong',

  // Incidents
  INCIDENT_CREATED = 'incident.created',
  INCIDENT_UPDATED = 'incident.updated',
  INCIDENT_RESOLVED = 'incident.resolved',
  INCIDENT_DELETED = 'incident.deleted',

  // Actions
  ACTION_CREATED = 'action.created',
  ACTION_APPROVED = 'action.approved',
  ACTION_REJECTED = 'action.rejected',
  ACTION_EXECUTED = 'action.executed',
  ACTION_FAILED = 'action.failed',

  // Analysis
  RCA_STARTED = 'rca.started',
  RCA_COMPLETED = 'rca.completed',
  REMEDIATION_PLANNED = 'remediation.planned',

  // System
  SYSTEM_HEALTH = 'system.health',
  AGENT_STATUS = 'agent.status',
  ALERT = 'alert'
}
```

**Specialized Hooks**:
```typescript
function useIncidentEvents(callback: (event: WebSocketEvent) => void)
function useActionEvents(callback: (event: WebSocketEvent) => void)
function useSystemEvents(callback: (event: WebSocketEvent) => void)
```

**Features**:
- Auto-connect option
- Automatic reconnection (configurable attempts/interval)
- Event-type filtering with wildcards
- Ping/pong keep-alive
- Room-based subscriptions

---

### utils.ts (`src/lib/utils.ts`)

**Purpose**: Common utility functions

**Exports**:

```typescript
// Tailwind class merging
function cn(...inputs: ClassValue[]): string

// Date formatting
function formatDate(date: Date | string): string
// Output: "Dec 27, 2025 10:30"

// Relative time
function formatRelativeTime(date: Date | string): string
// Output: "5m ago", "2h ago", "3d ago"
```

---

## Styling

### Theme System

**CSS Variables** (index.css):
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --secondary: 210 40% 96.1%;
  --muted: 210 40% 96.1%;
  --accent: 210 40% 96.1%;
  --destructive: 0 84.2% 60.2%;
  --border: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... dark overrides */
}
```

### Layout Constants
- Sidebar width: 264px
- Content padding: 1.5rem (24px)
- Card border-radius: 0.5rem (8px)
- Spacing scale: Tailwind defaults

### Color Semantics
| Color | Usage |
|-------|-------|
| Primary | Actions, links, focus |
| Secondary | Subtle backgrounds |
| Muted | Disabled, placeholders |
| Destructive | Errors, critical severity |
| Accent | Highlights |

---

## Environment Variables

```bash
# .env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

**Type Definitions** (vite-env.d.ts):
```typescript
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
}
```

---

## Build & Development

### Development
```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:3000
```

### Production Build
```bash
npm run build
# Output: frontend/dist/
```

### Docker
```dockerfile
# Build stage
FROM node:20-alpine
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

---

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| Dashboard.tsx | ~420 | System overview |
| Incidents.tsx | ~720 | Incident management |
| Chat.tsx | ~210 | Agent chat |
| Agents.tsx | ~1400 | Agent hub (6 tabs) |
| Graph.tsx | ~300 | Episodic graph page (v0.6.0+) |
| Settings.tsx | ~810 | Configuration (5 tabs) |
| Layout.tsx | ~250 | App shell |
| IncidentTimeline.tsx | ~390 | Timeline visualization |
| DependencyGraph.tsx | ~480 | Service graph |
| EpisodicGraphExplorer.tsx | ~600 | Force-directed graph (v0.5.0+) |
| api.ts | ~460 | API client |
| websocket.ts | ~385 | Real-time events |
| utils.ts | ~35 | Utilities |

---

**See Also**:
- [API.md](API.md) - REST API reference
- [BACKEND.md](BACKEND.md) - Backend architecture
