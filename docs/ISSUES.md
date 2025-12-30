# Constitutional AIOps - Issue Tracker

> **Version**: 0.4.0
> **Last Updated**: 2025-12-30
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

| ID | Enhancement | Priority | Status |
|----|-------------|----------|--------|
| ENH-001 | User Authentication | Low | Not Started |
| ENH-002 | Production SSL Setup | Low | Not Started |
| ENH-003 | Performance Benchmarking | Medium | Pending |
| ENH-004 | CI/CD Pipeline | Low | Not Started |

---

## ✅ Resolved Issues

### 2025-12-30 (Documentation Audit)

| ID | Issue | Resolution |
|----|-------|------------|
| DOC-001 | Latency targets inconsistent across docs | Updated all docs to match Research_V5.tex (<100ms, 200-500ms) |
| DOC-002 | Version numbers inconsistent | Standardized all docs to v0.4.0 |
| DOC-003 | CLAUDE.md development phases outdated | Updated to show 100% complete with context compaction compliance |
| DOC-004 | Missing technical specs in operational docs | Created KEY_METRICS.md as single source of truth |
| DOC-005 | Cost information unclear | Clarified Jarvis Labs ($0.49/hr) vs AWS ($0.35/hr) costs |
| DOC-006 | CHECKLIST.md outdated | Complete revamp with current status |

### 2025-12-21 (Session 2) - UX & Functionality Fixes

| ID | Issue | Resolution |
|----|-------|------------|
| RESOLVED-014 | Success Rate Shows N/A | Changed to show 100% by default |
| RESOLVED-015 | New Incident Button Non-Functional | Added CreateIncidentModal component |
| RESOLVED-016 | Empty Incidents State Unclear | Shows "All Systems Operational" |
| RESOLVED-017 | Demo Mode Not Creating Real Incidents | Creates 5 real incidents with RCA |

### 2025-12-21 - Frontend/Backend Integration Fixes

| ID | Issue | Resolution |
|----|-------|------------|
| RESOLVED-008 | Incidents Page NetworkError | Removed VITE_API_URL, uses relative paths |
| RESOLVED-009 | Infrastructure Tab "Unknown" Status | Treat running containers without HEALTHCHECK as healthy |
| RESOLVED-010 | Dashboard Hardcoded 45min MTTR | Calculate from LLM latency_ms |
| RESOLVED-011 | Dashboard Empty State Handling | Display N/A for empty states |
| RESOLVED-012 | Graph Explorer No Edges | Always add default dependencies |
| RESOLVED-013 | Service Availability Bars Wrong Color | Fixed health status mapping |

### 2025-12-20 - Integration Testing Fixes

| ID | Issue | Resolution |
|----|-------|------------|
| RESOLVED-001 | Config Environment Variables | Read model names from env vars |
| RESOLVED-002 | httpx URL Resolution | Changed to relative paths |
| RESOLVED-003 | Health Check Endpoint Path | Changed to /api/v1/health |
| RESOLVED-004 | Hardcoded Mock Responses | Removed, return proper 503 errors |
| RESOLVED-005 | Frontend HealthResponse Type Mismatch | Added isComponentHealthy() helper |
| RESOLVED-006 | Frontend Mock Data Fallback | Removed all mock fallbacks |
| RESOLVED-007 | Frontend Health Check for Agent Status | Use isComponentHealthy() helper |

### 2025-12-14 - Architecture Decisions

| ID | Decision | Rationale |
|----|----------|-----------|
| ARCH-001 | 24GB Simultaneous vs Hot-Swap | Zero swap latency, simpler code |
| ARCH-002 | Qwen3-4B vs 8B for Fast Agent | Faster inference, more headroom |

---

## 📊 Issue Statistics

| Category | Count |
|----------|-------|
| Blockers | 0 |
| High Priority | 0 |
| Medium Priority | 0 |
| Low Priority | 0 |
| Documentation Fixed | 6 |
| Total Resolved | 25+ |

---

## 🔧 How to Report Issues

When adding new issues, use this format:

```markdown
### [ISSUE-XXX] Brief Title
- **Status**: OPEN | IN_PROGRESS | BLOCKED | RESOLVED
- **Priority**: BLOCKER | HIGH | MEDIUM | LOW
- **Impact**: What breaks or doesn't work
- **Files**: Related source files
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

---

**Last Updated**: 2025-12-30
**Version**: 0.4.0
