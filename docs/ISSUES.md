# Constitutional AIOps - Issue Tracker

> **Last Updated**: 2025-12-21
> **Open Issues**: 0
> **Blockers**: 0

---

## 🚫 Blockers

None currently.

---

## ⚠️ High Priority

None currently.

---

## 📝 Open Issues

None - All core functionality implemented and tested.

### Optional Enhancements (Not Blocking)

1. **User Authentication**
   - Status: NOT STARTED (Optional)
   - Impact: Currently no auth required
   - Files: Would need new auth middleware
   - Note: For demo purposes, auth is optional

---

## ✅ Resolved Issues

### 2025-12-21 (Session 2) - UX & Functionality Fixes

1. **[RESOLVED-014] Success Rate Shows N/A**
   - Status: RESOLVED
   - Priority: MEDIUM
   - Impact: Success Rate showed "N/A" when no actions existed instead of 100%
   - Files: `frontend/src/pages/Dashboard.tsx`
   - Solution: Changed to show "100%" by default, decreasing when failures occur

2. **[RESOLVED-015] New Incident Button Non-Functional**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: "New Incident" button had no onClick handler
   - Files: `frontend/src/pages/Incidents.tsx`
   - Solution: Added CreateIncidentModal component and handler for creating incidents

3. **[RESOLVED-016] Empty Incidents State Unclear**
   - Status: RESOLVED
   - Priority: LOW
   - Impact: Empty state just showed "No incidents found" - not encouraging
   - Files: `frontend/src/pages/Incidents.tsx`
   - Solution: Shows "All Systems Operational" with green checkmark and helpful text

4. **[RESOLVED-017] Demo Mode Not Creating Real Incidents**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: Demo mode only logged to console, didn't create actual incidents
   - Files: `src/api/routes/demo.py`
   - Solution: Demo mode now creates 5 real incidents with appropriate severity, category, and triggers RCA analysis

### 2025-12-21 - Frontend/Backend Integration Fixes

1. **[RESOLVED-008] Incidents Page NetworkError**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: Incidents page showed "NetworkError when attempting to fetch resource"
   - Files: `docker-compose.yml`
   - Root Cause: `VITE_API_URL=http://localhost:8000` hardcoded in frontend environment - doesn't work inside Docker container
   - Solution: Removed VITE_API_URL from docker-compose.yml; frontend now uses relative `/api/v1` path which nginx proxies correctly

2. **[RESOLVED-009] Infrastructure Tab "Unknown" Status**
   - Status: RESOLVED
   - Priority: MEDIUM
   - Impact: grafana, loki, prometheus, nextcloud showed "unknown" health status
   - Files: `src/api/routes/infrastructure.py`
   - Root Cause: Containers without HEALTHCHECK directive had health=None, which was passed as-is to frontend
   - Solution: Treat running containers with health=None as "healthy" instead of "unknown"

3. **[RESOLVED-010] Dashboard Hardcoded 45min MTTR**
   - Status: RESOLVED
   - Priority: MEDIUM
   - Impact: "Avg Response Time" always showed "45min" regardless of actual performance
   - Files: `frontend/src/lib/api.ts`, `frontend/src/pages/Dashboard.tsx`
   - Root Cause: `mttr_minutes: 45` hardcoded in api.ts getStats() function
   - Solution: Calculate actual response time from LLM health endpoint latency_ms values

4. **[RESOLVED-011] Dashboard Empty State Handling**
   - Status: RESOLVED
   - Priority: LOW
   - Impact: Remediation Performance showed "0%" and "0" when no actions existed
   - Files: `frontend/src/pages/Dashboard.tsx`
   - Solution: Display "N/A" / "None" / "No actions today" for empty states

5. **[RESOLVED-012] Graph Explorer No Edges**
   - Status: RESOLVED
   - Priority: MEDIUM
   - Impact: Graph showed "9 nodes, 0 edges" - no service dependencies visible
   - Files: `src/api/routes/graph.py`
   - Root Cause: Default dependencies only added when services list was empty
   - Solution: Always add default service dependencies regardless of data source

6. **[RESOLVED-013] Service Availability Bars Wrong Color**
   - Status: RESOLVED
   - Priority: LOW
   - Impact: Running containers showed gray/red bars instead of green
   - Files: `frontend/src/pages/Dashboard.tsx`, `src/api/routes/infrastructure.py`
   - Solution: Fixed health status mapping; running containers now display green bars

### 2025-12-20 - Integration Testing Fixes

1. **[RESOLVED-001] Config Environment Variables**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: Model names hardcoded, ignoring env vars
   - Files: `src/config.py`
   - Solution: Changed `fast_agent_model` and `reasoning_agent_model` to read from `FAST_AGENT_MODEL` and `REASONING_AGENT_MODEL` env vars using `field(default_factory=lambda: os.getenv(...))`
   - Also fixed timeout values to read from env vars

2. **[RESOLVED-002] httpx URL Resolution**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: 404 errors when calling remote Ollama API
   - Files: `src/agents/model_router.py`, `docker/docker-compose.hybrid.yml`
   - Solution: Changed absolute paths (`/chat/completions`) to relative paths (`chat/completions`) and added trailing slash to base URL in docker-compose.hybrid.yml

3. **[RESOLVED-003] Health Check Endpoint Path**
   - Status: RESOLVED
   - Priority: MEDIUM
   - Impact: Backend container marked as unhealthy
   - Files: `docker-compose.yml`
   - Solution: Changed healthcheck from `/health` to `/api/v1/health`

4. **[RESOLVED-004] Hardcoded Mock Responses**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: Mock responses could mask real LLM errors
   - Files: `src/api/routes/chat.py`
   - Solution: Removed `_mock_chat_response()` and `_mock_analysis_response()` functions. Replaced with proper HTTP 503 error responses with clear error messages.

5. **[RESOLVED-005] Frontend HealthResponse Type Mismatch**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: Agents showed as "offline" even when healthy
   - Files: `frontend/src/lib/api.ts`
   - Root Cause: Frontend expected `components: { fast_agent: boolean; ... }` (object) but backend returns `components: [{ name: "fast_agent", healthy: true, ... }]` (array)
   - Solution: Changed `HealthResponse` type to use `HealthComponent[]` array. Added `isComponentHealthy()` helper function for checking component status.

6. **[RESOLVED-006] Frontend Mock Data Fallback**
   - Status: RESOLVED
   - Priority: HIGH
   - Impact: Dashboard showed mock data instead of real API errors
   - Files: `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Chat.tsx`
   - Solution: Removed mock data fallbacks. Now shows proper error messages when API calls fail.

7. **[RESOLVED-007] Frontend Health Check for Agent Status**
   - Status: RESOLVED
   - Priority: MEDIUM
   - Impact: Model status cards showed "offline" for all agents
   - Files: `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/Settings.tsx`
   - Solution: Updated all health checks to use `isComponentHealthy(health, 'component_name')` helper function.

### 2025-12-14 - Architecture Decisions

1. **Architecture Decision: Hot-Swap vs Simultaneous**
   - Resolution: Chose 24GB simultaneous loading
   - Rationale: Zero swap latency, simpler code
   - Cost: +$14/month justified

2. **Model Selection: 8B vs 4B for Fast Agent**
   - Resolution: Chose Qwen3-4B
   - Rationale: Faster inference, more headroom

---

## 📊 Issue Statistics

| Category | Count |
|----------|-------|
| Blockers | 0 |
| High Priority | 0 |
| Medium Priority | 0 |
| Low Priority | 0 |
| Resolved | 19 |

---

## 🔧 How to Report Issues

When adding new issues, use this format:

```markdown
### [ISSUE-XXX] Brief Title
- **Status**: OPEN | IN_PROGRESS | BLOCKED | RESOLVED
- **Priority**: BLOCKER | HIGH | MEDIUM | LOW
- **Assignee**: (optional)
- **Impact**: What breaks or doesn't work
- **Files**: Related source files
- **Reproduction**: Steps to reproduce (if applicable)
- **Proposed Solution**: How to fix (if known)
```

---

## 🏷️ Labels

- `[BLOCKER]` - Prevents all progress
- `[HIGH]` - Critical functionality
- `[MEDIUM]` - Important but not blocking
- `[LOW]` - Nice to have
- `[BUG]` - Something broken
- `[FEATURE]` - New functionality
- `[DOCS]` - Documentation
- `[INFRA]` - Infrastructure/DevOps
