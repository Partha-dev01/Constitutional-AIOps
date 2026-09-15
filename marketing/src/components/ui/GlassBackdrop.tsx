/**
 * The fixed, decorative page backdrop: a static blue+indigo radial mesh over
 * the near-black base with two slowly drifting colour fields on top (see
 * `.aurora` in styles/landing.css). Rendered first on every page and pinned
 * behind everything via a negative z-index. One component so the backdrop can
 * gain layers later without touching every page.
 */
export function GlassBackdrop() {
  return <div className="aurora" aria-hidden="true" />
}

export default GlassBackdrop
