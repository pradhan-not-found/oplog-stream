"""
generate_banner.py
Renders assets/banner.svg: a light, minimal banner set in Instrument Sans
(embedded) with a pixel-mosaic arch.

The arch is a grid of squares inside concentric bands; outer bands are dense
and inner bands dither away, like a stream thinning out as it is consumed.
If results/run_meta.json exists, a one-line run caption is added.

Run: python generate_banner.py
"""
import json

from pathlib import Path

from mosaic import arch_cells, to_svg
from svg_theme import style_block

ROOT = Path(__file__).parent
W, H = 1500, 500
BG = "#FDFCF8"
INK = "#14201B"
INK_2 = "#3D4A44"
INK_3 = "#7C8781"
MOSAIC = "#9FD9B4"      # soft green
MOSAIC_DEEP = "#7FC79B"


meta_p = ROOT / "results" / "run_meta.json"
summary_p = ROOT / "results" / "summary.json"
meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
summary = json.loads(summary_p.read_text(encoding="utf-8")) if summary_p.exists() else {}


# Bands: (inner radius, outer radius, density)  - clear gaps between rings
CX, CY = 1115, 500
BANDS = [
    (418, 482, 1.00),
    (350, 398, 0.94),
    (292, 330, 0.80),
    (240, 272, 0.66),
    (193, 220, 0.52),
    (150, 173, 0.40),
    (112, 130, 0.30),
]


cells = [c for c in arch_cells(CX, CY, BANDS, CX - 500, W, H, MOSAIC) if c[1] < H]

mosaic = to_svg(cells)

# Pixel glyph: a small database cylinder with a stream arrow (8px grid)
G = 6
glyph_map = [
    "..XXXXXX..",
    ".X......X.",
    "X.XXXXXX.X",
    "X........X",
    "X.XXXXXX.X",
    "X........X",
    ".XXXXXXXX.",
]
glyph = "".join(
    f'<rect x="{50 + c * G}" y="{404 + r * G}" width="{G - 1}" height="{G - 1}" fill="{MOSAIC_DEEP}"/>'
    for r, row in enumerate(glyph_map) for c, ch in enumerate(row) if ch == "X")

caption = ""
if meta and summary.get("sessions"):
    s = summary["sessions"]
    caption = (f'<text x="50" y="218" font-size="14" fill="{INK_3}">'
               f'Measured on MongoDB Atlas M0 · {meta["sessions"]} sessions · '
               f'{s["success"]:,} documents · {s["failed"]} write errors</text>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="oplog-stream">
  <title>oplog-stream</title>
  {style_block()}
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {mosaic}
  <text x="50" y="65" font-size="16" fill="{INK_2}">pradhan-not-found / oplog-stream</text>
  <text x="49" y="135" font-size="30" fill="{INK}">oplog-stream</text>
  <text x="50" y="163" font-size="17" fill="{INK_2}">20 concurrent producers streaming 20-variable telemetry into MongoDB Atlas,</text>
  <text x="50" y="187" font-size="17" fill="{INK_2}">tailed in real time by an isolated pull consumer</text>
  {caption}
  {glyph}
</svg>
"""
(ROOT / "assets" / "banner.svg").write_text(svg, encoding="utf-8")
print(f"[OK] assets/banner.svg ({len(cells)} cells)")
