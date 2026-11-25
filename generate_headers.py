"""
generate_headers.py
Section heading strips for the README, in the same style as the banner:
warm off-white surface, Instrument Sans, a slice of the pixel-mosaic arch.

Run: python generate_headers.py   ->  assets/section_*.svg
"""
from pathlib import Path

from mosaic import arch_cells, to_svg
from svg_theme import style_block

ROOT = Path(__file__).parent
W, H = 1500, 150
BG = "#EDEEEB"
INK = "#14201B"
INK_3 = "#7C8781"
MOSAIC = "#B9C9BF"
CELL, SQ = 8, 7

SECTIONS = [
    ("overview", "01", "Overview", "What the pipeline does and what was measured"),
    ("architecture", "02", "Architecture", "Push environment, Atlas replica set, pull environment"),
    ("report", "03", "Simulation report", "Real run on MongoDB Atlas, every number measured"),
    ("observations", "04", "Atlas and oplog observations", "Cluster telemetry recorded second by second"),
    ("findings", "05", "Findings and recommendations", "What the data says to change"),
    ("setup", "06", "Setup and reproduction", "Run the same test against your own cluster"),
    ("schema", "07", "Document schema", "The 20 generated variables"),
    ("layout", "08", "Repository layout", "Where everything lives"),
]

# A small arch whose centre sits below the strip, so only the crown shows.
BANDS = [(176, 212, 1.0), (138, 164, 0.9), (104, 126, 0.72), (76, 92, 0.55), (52, 64, 0.4)]


def strip(slug: str, idx: str, title: str, sub: str, seed_shift: int) -> str:
    cx = 1280 + seed_shift
    cells = arch_cells(cx, H + 62, BANDS, cx - 230, W, H, MOSAIC,
                       jitter=3.0, cell=CELL, sq=SQ)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}">
  <title>{title}</title>
  {style_block()}
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {to_svg(cells, SQ)}
  <text x="48" y="80" font-size="34" fill="{INK}">{title}</text>
  <text x="50" y="110" font-size="16" fill="{INK_3}">{sub}</text>
</svg>
"""


def main() -> None:
    for n, (slug, idx, title, sub) in enumerate(SECTIONS):
        path = ROOT / "assets" / f"section_{slug}.svg"
        path.write_text(strip(slug, idx, title, sub, (n % 3) * 24), encoding="utf-8")
        print(f"[OK] {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
