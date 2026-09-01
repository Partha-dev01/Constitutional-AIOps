# Brand assets

Canonical source masters for the Constitutional AIOps logo, plus the script
that derives the web assets served by the app and the marketing site.

## Masters (edit these, then regenerate)

| File | What it is |
|------|-----------|
| `logo.png` | Full horizontal lockup: neon shield-brain mark + wordmark. |
| `logo-mark-master.png` | The neon shield-brain mark on its dark-navy square, uncropped. |

## Generated assets (do not hand-edit)

`generate_favicons.py` reads the two masters and writes, into **both**
`frontend/public/` and `marketing/public/`:

- `logo.png` - copy of the full lockup.
- `logo-mark.png` - the mark **circle-cut**: an inscribed circle with an
  anti-aliased edge, transparent outside it, so the mark renders as a round
  coin on any background. The dropped corners are only navy backdrop, never
  the shield. UI wrappers pair it with `rounded-full`.
- `favicon-16/32/48/192/512.png`, `favicon.ico` - circular, transparent corners.
- `apple-touch-icon.png` - kept an **opaque** navy square (iOS dislikes icon
  transparency and applies its own rounded mask).

## Regenerate

From the repo root:

```
python assets/brand/generate_favicons.py
```

Requires Pillow. The navy flatten colour is sampled from the master's corner
(`#050c1c`), matching the sites' `theme-color`.
