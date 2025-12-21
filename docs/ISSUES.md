# Constitutional AIOps - Issue Tracker

> **Last Updated**: 2025-12-20
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
| Resolved | 9 |

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
