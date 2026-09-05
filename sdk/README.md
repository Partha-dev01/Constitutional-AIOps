# Constitutional AIOps SDKs

Official client libraries for the Constitutional AIOps REST API. Two packages
live here:

- `python/` — the Python client (`constitutional-aiops` on PyPI, planned).
- `typescript/` — the TypeScript / JavaScript client
  (`@constitutional-aiops/sdk` on npm, planned).

## Status: pre-release scaffold

These are hand-written thin clients that talk to the app's `/api/v1` REST
surface. They are usable today against an instance where you can reach the API,
and they are the seed for the generated clients described in the developer-platform
spec. Two pieces of that spec are not built yet and are called out where they
matter:

1. **Generated core.** The final clients will be generated from the app's OpenAPI
   schema (`openapi-python-client` for Python, `openapi-typescript` +
   `openapi-fetch` for TypeScript), with this hand-written layer kept as the
   ergonomic surface on top. Until then these packages implement a small,
   dependency-free subset by hand.
2. **Personal access tokens.** The clean programmatic auth path is a per-user
   personal access token sent as `Authorization: Bearer`. That endpoint is not
   built yet. Until it lands you can use the SDK against an instance running with
   `AUTH_REQUIRED` unset (the default single-user / local mode), or pass a session
   token you already hold.

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
