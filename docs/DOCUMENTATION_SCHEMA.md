# Documentation Update Schema

> **Purpose**: Guidelines for maintaining consistent, accurate documentation
> **Last Updated**: 2025-12-28

---

## File Header Template

Every documentation file MUST start with a YAML-style header:

```markdown
# [Document Title]

> **Version**: [0.3.1]
> **Last Updated**: [YYYY-MM-DD]
> **Status**: [Production Ready | Draft | Deprecated]

---
```

---

## When to Update Documentation

| Event | Action | Files to Update |
|-------|--------|-----------------|
| Code change affects behavior | Update relevant docs | ARCHITECTURE.md, specific guide |
| New feature added | Document feature | CHANGELOG.md, relevant guide |
| Config option added | Add to config reference | DEPLOYMENT.md |
| Bug fixed | Add to changelog | CHANGELOG.md |
| Architecture change | Update design docs | ARCHITECTURE.md |
| Deployment process changes | Update deployment | DEPLOYMENT.md, specific guide |

---

## Update Checklist

When updating any documentation file:

- [ ] Update "Last Updated" date in file header
- [ ] Update [docs/INDEX.md](INDEX.md) table entry
- [ ] Add CHANGELOG.md entry if significant
- [ ] Remove any conflicting old information
- [ ] Verify all code examples still work
- [ ] Check all links are valid

---

## Validation Rules

### Before Committing Documentation

1. **Verify against code**: All technical claims must match actual implementation
2. **Check consistency**: Same information should not conflict across files
3. **Test examples**: Code snippets should be copy-paste executable
4. **Validate links**: All internal links should resolve

### Ground Truth Sources

When documentation conflicts with code, **code is the source of truth**:

| Topic | Source of Truth | Documentation |
|-------|-----------------|---------------|
| Model names | `src/config.py` | [BACKEND.md](BACKEND.md) |
| API endpoints | `src/api/routes/*.py` | [API.md](API.md) |
| Docker config | `docker-compose.yml` | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Environment variables | `.env` + `src/config.py` | [BACKEND.md](BACKEND.md) |
| LLM architecture | `src/agents/model_router.py` | [BACKEND.md](BACKEND.md) |
| Constitutional principles | `src/constitutional/principles.py` | [BACKEND.md](BACKEND.md) |
| Frontend components | `frontend/src/` | [FRONTEND.md](FRONTEND.md) |
| Complete file inventory | Entire codebase | [INDEX.md](INDEX.md) |

---

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Guide | UPPERCASE | `DEPLOYMENT.md` |
| Index | UPPERCASE | `INDEX.md` |
| Changelog | UPPERCASE | `CHANGELOG.md` |
| Schema | UPPERCASE | `DOCUMENTATION_SCHEMA.md` |

---

## Content Guidelines

### DO

- Use tables for structured information
- Include code examples where applicable
- Add "Last Updated" dates
- Cross-reference related documentation
- Keep descriptions concise

### DON'T

- Duplicate information across files
- Leave outdated information
- Use placeholder URLs (github.com/your-org)
- Include commented-out or "TODO" sections in production docs
- Reference deleted files

---

## Deprecated Files

The following files have been removed as redundant or outdated:

| File | Reason | Date Removed |
|------|--------|--------------|
| `MEGA_PROMPT.md` | Redundant with ARCHITECTURE.md | 2025-12-27 |
| `MEGA_PROMPT_PART2.md` | Contained outdated code examples | 2025-12-27 |
| `MEGA_PROMPT_PART3.md` | Redundant with existing docs | 2025-12-27 |
| `PROJECT_SUMMARY.md` | Historical, no longer needed | 2025-12-27 |
| `QUICKSTART.md` | Merged into README.md | 2025-12-27 |
| `Cloud_provider_discussions.md` | Historical research notes | 2025-12-27 |
| `JARVIS_LABS_TESTING_RESULTS.md` | Test results, not documentation | 2025-12-27 |
| `Simplified_AIOps_Documentation_v6.md` | Old consolidated draft | 2025-12-27 |

---

## AI Session Documentation

When Claude Code works on documentation:

1. **Read first**: Always read the file before editing
2. **Verify against code**: Check `src/` for ground truth
3. **Update INDEX.md**: After any doc changes
4. **Add CHANGELOG entry**: For significant updates

---

**Last Updated**: 2025-12-27
