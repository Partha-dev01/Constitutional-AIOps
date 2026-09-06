# Constitutional AIOps SDKs

Official client libraries for the Constitutional AIOps REST API. Two packages
live here:

- `python/` — the Python client (`constitutional-aiops` on PyPI, planned).
- `typescript/` — the TypeScript / JavaScript client
  (`@constitutional-aiops/sdk` on npm, planned).

## Status: pre-release, not yet published

Each package ships two layers:

1. **Ergonomic client** (`AIOpsClient`) — a hand-written, dependency-free surface
   over the app's `/api/v1` REST API: a pagination helper over the uniform list
   envelope, chat streaming, and typed errors including `ConstitutionalRefusal`.
   Stdlib `urllib` in Python, global `fetch` in TypeScript. This surface is stable.
2. **Generated typed core** — the full API, typed from the committed OpenAPI
   snapshot (`openapi/openapi.json`): `openapi-python-client` for Python
   (`constitutional_aiops_client`, optional `typed` extra, rides on httpx) and
   `openapi-typescript` + `openapi-fetch` for TypeScript (`createTypedClient`).
   Both are committed so the packages build offline, and are regenerated from the
   snapshot (see each package's README for the `generate` command). CI checks the
   checked-in output against a fresh regen.

**Auth.** The clean programmatic auth path is a per-user personal access token
(`aiops_pat_...`), created in the app (Settings, or `POST /api/v1/auth/tokens`)
and sent as `Authorization: Bearer`. It resolves to the real user even when
`AUTH_REQUIRED` is off, so SDK calls are attributed and cost-fenced. Against a
single-user instance with `AUTH_REQUIRED` unset a token is optional.

Neither package is published yet. Publishing is gated on the repository going
public. See the developer-platform guide in the docs site for the full plan.

## Design goals

- Zero required runtime dependencies in the hand-written layer (stdlib `urllib`
  in Python, global `fetch` in TypeScript), so the scaffold installs and runs
  anywhere the app does.
- The same shape in both languages: construct a client, list with a pagination
  helper over the `{items, total, page, page_size, has_more}` envelope, stream a
  chat, and get typed errors including a `ConstitutionalRefusal` for actions the
  safety gate blocks or holds for approval.
- Honest about the constitutional gate: an action the SDK submits still passes the
  same validator and human-approval flow as the UI. The SDK does not bypass it.

## Versioning

Client `MAJOR.MINOR` tracks the API `MAJOR.MINOR` (so a `1.0.x` client targets
Constitutional AIOps API `1.0.x`); `PATCH` is independent for client-only fixes.
