# Constitutional AIOps — Marketing site

Standalone, fully static marketing/landing site for the **hosted** demo. It was
extracted from the app frontend so the two are cleanly separated:

- **This site (`marketing/`)** is our brand/marketing. It is served serverlessly
  (built to `dist/`, uploaded to S3, served at the front-door root behind
  CloudFront). It is **always on** and never needs the demo VM running.
- **The app (`frontend/`)** is the self-hostable product. It carries no branded
  marketing landing. Self-hosters deploy only `frontend/` + `backend`; our own
  hosted instance runs the exact same vanilla self-host (parity).

The landing makes **zero** network/API/websocket calls. It is deterministic and
renders identically with or without a live backend.

## Build

```bash
npm install
npm run build      # -> dist/
npm run dev        # local preview on :3100
```

## Configuration

The call-to-action buttons ("Sign in" / "Open the Dashboard" / "Launch demo")
point at `VITE_APP_URL`. In production this is the **front-door launch path**
that wakes the demo box on genuine human intent (wired in R2). Plain visits to
the marketing root must never wake the box.

```bash
VITE_APP_URL="https://<front-door-domain>/launch" npm run build
```

Default (unset): `/login?next=/` (relative), useful for local preview only.

## What lives here

- `src/pages/Landing.tsx` + `src/components/landing/*` — the landing sections.
- `src/hooks/useReveal.ts`, `src/lib/utils.ts` — small self-contained copies of
  the shared helpers (the app keeps its own copies; these are duplicated on
  purpose so the two projects are independent).
- `src/index.css` — the shared design tokens + animation keyframes (copied from
  the app so the extracted landing looks identical).
- `src/styles/landing.css` — landing-only styles.
- `public/` — favicon + landing screenshots.

Deployment (S3 + CloudFront path split, bot-filtered wake) is **R2**.
