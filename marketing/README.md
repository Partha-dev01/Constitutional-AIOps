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
`/launch` — a relative path on the same front-door domain that routes to the
wake Lambda and starts the demo box on genuine human intent. Plain visits to the
marketing root (`/`) are served from S3 and never wake the box.

```bash
VITE_APP_URL=/launch npm run build
```

Default (unset): `/login?next=/` (relative), useful for local preview only.

## Deploy / redeploy (S3 + CloudFront, bot-filtered wake)

The site is the CDN **default** origin (always-on); `/launch` is a separate
behavior that routes to the wake Lambda. The concrete bucket name and
distribution ID are deployment-specific and live in the gitignored
`terraform/lite/terraform.tfvars` (and the private ops notes), not in this repo.
Export them, then:

```bash
MARKETING_BUCKET=<your-marketing-bucket>
DIST_ID=<your-cdn-distribution-id>

# 1. Build with the production launch path.
VITE_APP_URL=/launch npm run build

# 2. Sync to the private marketing bucket (removes stale files).
#    --exclude "demo/*" is MANDATORY: the no-login demo lives under demo/ in the
#    same bucket and is deployed separately, so a --delete sync without it wipes
#    the demo.
aws s3 sync dist/ "s3://$MARKETING_BUCKET/" --delete --exclude "demo/*" --profile <deploy-profile>

# 3. Invalidate so viewers get the new build immediately (cache is optimized).
aws cloudfront create-invalidation --distribution-id "$DIST_ID" \
  --paths '/*' --profile <deploy-profile>
```

The bucket is private (all public access blocked, ACLs off, SSE-S3); only this
distribution can read it, via an S3-type Origin Access Control. The bucket, its
policy and the OAC are drift-tracked in `../terraform/lite/marketing.tf`. The
distribution's origins/behaviors and `DefaultRootObject=index.html` were set out
of band during the R2 cutover (the wake Lambda's code+env are managed the same
way); Terraform references the distribution read-only.

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
