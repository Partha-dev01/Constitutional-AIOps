# Constitutional AIOps - Issue Tracker

> **Last Updated**: 2025-12-14
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

### TODO: Pending Implementation

1. **API Routes Not Implemented**
   - Status: PENDING
   - Impact: Frontend cannot connect to backend
   - Files: `src/api/routes/*.py`
   - Next: Implement health, chat, incidents, actions routes

2. **Neo4j Client Not Implemented**
   - Status: PENDING
   - Impact: No graph-episodic memory
   - Files: `src/memory/*.py`
   - Next: Implement Neo4j connection and episode storage

3. **Telemetry Processing Not Implemented**
   - Status: PENDING
   - Impact: No OTEL integration
   - Files: `src/telemetry/*.py`
   - Next: Implement collector, compressor, aggregator

4. **MCP Tools Not Implemented**
   - Status: PENDING
   - Impact: No remediation actions
   - Files: `src/mcp/tools/*.py`
   - Next: Implement 5 core tools (Phase 2)

---

## ✅ Resolved Issues

### 2025-12-14

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
| Medium Priority | 4 |
| Low Priority | 0 |
| Resolved | 2 |

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
