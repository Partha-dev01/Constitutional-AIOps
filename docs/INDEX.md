# Constitutional AIOps - Documentation Index

> **Version**: 0.3.1
> **Last Updated**: 2025-12-27
> **Status**: Production Ready

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [README](../README.md) | Quick start guide |
| [CHANGELOG](CHANGELOG.md) | Version history |
| [ISSUES](ISSUES.md) | Bug tracking |

---

## Documentation Map

### Core Documentation

| File | Last Updated | Description |
|------|--------------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 2025-12-27 | System architecture, components, data flow |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 2025-12-27 | Deployment overview (Jarvis Labs, Local, AWS) |
| [CHECKLIST.md](CHECKLIST.md) | 2025-12-27 | Development progress tracker |
| [CHANGELOG.md](CHANGELOG.md) | 2025-12-27 | Version history and release notes |
| [ISSUES.md](ISSUES.md) | 2025-12-27 | Active issues and blockers |

### Deployment Guides

| File | Last Updated | Description |
|------|--------------|-------------|
| [JARVIS_LABS_DEPLOYMENT.md](JARVIS_LABS_DEPLOYMENT.md) | 2025-12-27 | Detailed Jarvis Labs hybrid setup |
| [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) | 2025-12-27 | AWS g6.xlarge deployment guide |

### Project Files

| File | Location | Description |
|------|----------|-------------|
| [CLAUDE.md](../CLAUDE.md) | Root | AI session instructions |
| [.env](./.env) | Root | Environment configuration |
| [docker-compose.yml](../docker-compose.yml) | Root | Main Docker configuration |

---

## Documentation Structure

```
constitutional-aiops/
├── README.md                    # Quick Start (entry point)
├── CLAUDE.md                    # AI Session Guide
│
└── docs/
    ├── INDEX.md                 # THIS FILE - Master index
    ├── DOCUMENTATION_SCHEMA.md  # Update guidelines
    │
    ├── ARCHITECTURE.md          # System design
    ├── DEPLOYMENT.md            # Deployment overview
    │
    ├── JARVIS_LABS_DEPLOYMENT.md  # Detailed Jarvis Labs guide
    ├── AWS_DEPLOYMENT.md          # Detailed AWS guide
    │
    ├── CHECKLIST.md             # Progress tracker
    ├── CHANGELOG.md             # Version history
    ├── ISSUES.md                # Issue tracker
    │
    └── research/                # Academic materials
        ├── references.bib       # BibTeX citations
        └── diagrams/            # Architecture diagrams
```

---

## Current Architecture Summary

| Component | Technology | Notes |
|-----------|------------|-------|
| Fast Agent | Qwen3-4B | Telemetry annotation, <50ms |
| Reasoning Agent | Qwen3-14B | RCA, remediation, <200ms |
| LLM Hosting | Jarvis Labs Ollama | A5000 24GB, $0.49/hr |
| Graph Memory | Neo4j 5.x | Incident correlation |
| Backend | FastAPI | Python 3.11+ |
| Frontend | React 18 + TypeScript | Tailwind CSS |
| Observability | LGTM Stack | Loki, Grafana, Tempo, Prometheus |

---

## Update Protocol

When updating documentation:

1. **Edit the file** with new content
2. **Update header** - Change "Last Updated" date in file header
3. **Update this INDEX** - Modify the table entry for that file
4. **Add CHANGELOG entry** - If change is significant

See [DOCUMENTATION_SCHEMA.md](DOCUMENTATION_SCHEMA.md) for detailed guidelines.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.3.1 | 2025-12-27 | Complete documentation restructure |
| 0.3.0 | 2025-12-26 | Dashboard fixes, Demo Mode |
| 0.2.0 | 2025-12-20 | Jarvis Labs integration |
| 0.1.0 | 2025-12-14 | Initial architecture |

---

**Last Updated**: 2025-12-27
