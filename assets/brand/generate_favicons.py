"""Generate the app + marketing brand assets from the two masters in this folder.

Masters (checked in, do not edit by hand):
  logo.png              - full horizontal lockup (shield mark + wordmark)
  logo-mark-master.png  - the neon shield mark on its dark-navy square

Outputs (regenerated, checked in) into frontend/public/ and marketing/public/:
  logo.png        - copy of the full lockup
  logo-mark.png   - the mark CIRCLE-CUT: an inscribed circle, transparent
                    outside it, so the mark reads as a round coin on any
                    background (the corners it drops are only navy backdrop,
                    never the shield).
  favicon-16/32/48/192/512.png, favicon.ico - circular, transparent corners
  apple-touch-icon.png - kept OPAQUE square (iOS dislikes transparency and
                    applies its own rounded mask), flattened onto the navy.

Run:  python assets/brand/generate_favicons.py   (from the repo root)
"""
import os
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
src_logo = os.path.join(HERE, "logo.png")
src_mark = os.path.join(HERE, "logo-mark-master.png")

mkt_pub = os.path.join(REPO, "marketing", "public")
fe_pub = os.path.join(REPO, "frontend", "public")
for d in (mkt_pub, fe_pub):
    os.makedirs(d, exist_ok=True)


def square(im):
    """Center-crop to a square."""
    im = im.convert("RGBA")
    w, h = im.size
    s = min(w, h)
    return im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))


logo = Image.open(src_logo).convert("RGBA")
mark_sq = square(Image.open(src_mark))
bg = mark_sq.convert("RGB").getpixel((3, 3))  # dark-navy corner -> flatten colour


# Alpha key: the navy backdrop is near-uniform, the neon shield + glow are the
# only coloured/bright pixels. Alpha = how far each pixel sits from the navy,
# so the shield traces its own outline and the glow fades out naturally to
# transparent. LO zeroes backdrop noise; HI is where a pixel becomes fully
# opaque. Tuned so strokes/brain stay solid and only the outer glow is soft.
_LO, _HI = 16.0, 120.0


def traced(size):
    """The shield keyed onto transparency (navy backdrop removed)."""
    im = mark_sq.resize((size, size), Image.LANCZOS).convert("RGB")
    bg_img = Image.new("RGB", im.size, bg)
    r, g, b = ImageChops.difference(im, bg_img).split()  # |px - navy| per channel
    m = ImageChops.lighter(ImageChops.lighter(r, g), b)   # max channel distance
    alpha = m.point(lambda v: 0 if v <= _LO else min(255, int((v - _LO) * 255 / (_HI - _LO))))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    return out


def flatten_square(size):
    """Opaque navy square with the shield (favicons: always visible, any tab)."""
    im = mark_sq.resize((size, size), Image.LANCZOS).convert("RGBA")
    canvas = Image.new("RGB", (size, size), bg)
    canvas.paste(im, (0, 0), im)
    return canvas


# UI mark = traced shield on transparent (sits on dark app/marketing surfaces).
# Favicons = opaque navy tile (a thin-line transparent shield vanishes on a
# light browser tab), iOS icon likewise opaque.
favicon_pngs = {
    "favicon-16.png": 16, "favicon-32.png": 32, "favicon-48.png": 48,
    "favicon-192.png": 192, "favicon-512.png": 512,
}
mark_512 = traced(512)

for d in (mkt_pub, fe_pub):
    logo.save(os.path.join(d, "logo.png"))
    mark_512.save(os.path.join(d, "logo-mark.png"))
    for name, sz in favicon_pngs.items():
        flatten_square(sz).save(os.path.join(d, name))
    flatten_square(180).save(os.path.join(d, "apple-touch-icon.png"))
    flatten_square(256).save(os.path.join(d, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

print("mark size:", mark_sq.size, "navy bg:", bg)
for d in (mkt_pub, fe_pub):
    names = sorted(n for n in os.listdir(d) if n.startswith(("logo", "favicon", "apple")))
    print(" ", os.path.relpath(d, REPO), names)
