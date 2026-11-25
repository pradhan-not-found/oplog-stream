"""
generate_stats_strip.py
Python and MongoDB marks: Simple Icons (CC0 1.0), https://simpleicons.org
Renders assets/stack-bar.svg: the stack and headline run figures as one
image strip that sits under the banner (replaces shield badges).

Run: python generate_stats_strip.py
"""
import json
from pathlib import Path

from svg_theme import MONGODB_GREEN, MONGODB_PATH, PYTHON_BLUE, PYTHON_PATH, style_block

ROOT = Path(__file__).parent
W, H = 1500, 150
BG = "#FDFCF8"
LINE = "#E4E6E1"
INK = "#14201B"
INK_3 = "#7C8781"
GREEN = "#1F9E5A"

summary_p = ROOT / "results" / "summary.json"
s = json.loads(summary_p.read_text(encoding="utf-8")) if summary_p.exists() else {}
docs = f'{s["sessions"]["success"]:,}' if s.get("sessions") else "-"
p50 = f'{s["sessions"]["insert_p50_ms_median"]:.1f} ms' if s.get("sessions") else "-"




def icon(kind: str, x: float, y: float, s: float = 22) -> str:
    """Icon of size s at (x, y). Brand marks are filled paths; the rest are 1.8px strokes."""
    k = s / 24
    g = f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.4f})">'
    st = f'fill="none" stroke="{INK}" stroke-width="{1.8 / k * k:.2f}" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "python":
        return g + f'<path d="{PYTHON_PATH}" fill="{PYTHON_BLUE}"/></g>'
    if kind == "mongodb":
        return g + f'<path d="{MONGODB_PATH}" fill="{MONGODB_GREEN}"/></g>'
    if kind == "pymongo":  # python mark with a leaf badge
        return (g + f'<path d="{PYTHON_PATH}" fill="{PYTHON_BLUE}"/></g>'
                + f'<g transform="translate({x + s * 0.52:.1f},{y + s * 0.48:.1f}) scale({k * 0.55:.4f})">'
                  f'<circle cx="12" cy="12" r="13" fill="#E7EFF8"/><path d="{MONGODB_PATH}" fill="{MONGODB_GREEN}"/></g>')
    if kind == "sessions":  # 3x3 grid of session squares
        cells = "".join(f'<rect x="{2 + c * 7.5}" y="{2 + r * 7.5}" width="5.5" height="5.5" rx="1" fill="{GREEN}"/>'
                        for r in range(3) for c in range(3))
        return g + cells + "</g>"
    if kind == "documents":  # page with folded corner and lines
        return (g + f'<path d="M6 2.5h8l5 5V21a.5.5 0 0 1-.5.5h-12A.5.5 0 0 1 6 21z" {st}/>'
                f'<path d="M14 2.5V7.5h5" {st}/><path d="M9 12.5h7M9 16.5h7" {st}/></g>')
    if kind == "latency":  # stopwatch
        return (g + f'<circle cx="12" cy="13.5" r="8" {st}/><path d="M12 13.5V9.5M9.5 2.5h5M12 2.5v3" {st}/></g>')
    return ""

items = [
    ("python", "PYTHON", "3.13"),
    ("mongodb", "MONGODB ATLAS", "M0 · 8.0"),
    ("pymongo", "PYMONGO", "4.7.3"),
    ("sessions", "SESSIONS", "20"),
    ("documents", "DOCUMENTS", docs),
    ("latency", "INSERT P50", p50),
]

col = (W - 100) / len(items)
parts = [f'<line x1="50" y1="0.5" x2="{W - 50}" y2="0.5" stroke="{LINE}"/>',
         f'<line x1="50" y1="{H - 0.5}" x2="{W - 50}" y2="{H - 0.5}" stroke="{LINE}"/>']
for i, (kind, label, value) in enumerate(items):
    x = 50 + i * col
    if i:
        parts.append(f'<line x1="{x:.1f}" y1="50" x2="{x:.1f}" y2="{H - 50}" stroke="{LINE}"/>')
    tx = x + (0 if i == 0 else 26)
    chip = {"python": "#E7EFF8", "pymongo": "#E7EFF8", "mongodb": "#E6F4EC",
            "sessions": "#E6F4EC"}.get(kind, "#F0F1EE")
    parts.append(f'<rect x="{tx:.1f}" y="53" width="44" height="44" rx="11" fill="{chip}"/>')
    parts.append(icon(kind, tx + 11, 64, 22))
    parts.append(f'<text x="{tx + 60:.1f}" y="69" font-size="11.5" font-weight="600" letter-spacing="1.3" fill="{INK_3}">{label}</text>')
    parts.append(f'<text x="{tx + 60:.1f}" y="96" font-size="24" fill="{INK}">{value}</text>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Python 3.13, MongoDB Atlas M0 8.0, PyMongo 4.7.3, 20 sessions, {docs} documents written, insert p50 {p50}">
  <title>Stack and run figures</title>
  {style_block()}
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {''.join(parts)}
</svg>
"""
(ROOT / "assets" / "stack-bar.svg").write_text(svg, encoding="utf-8")
print("[OK] assets/stack-bar.svg")
