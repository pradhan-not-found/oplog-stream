"""
generate_stats_strip.py
Renders assets/stack-strip.svg: the stack and headline run figures as one
image strip that sits under the banner (replaces shield badges).

Run: python generate_stats_strip.py
"""
import json
from pathlib import Path

from svg_theme import style_block

ROOT = Path(__file__).parent
W, H = 1500, 132
BG = "#FDFCF8"
LINE = "#E4E6E1"
INK = "#14201B"
INK_3 = "#7C8781"
GREEN = "#1F9E5A"

summary_p = ROOT / "results" / "summary.json"
s = json.loads(summary_p.read_text(encoding="utf-8")) if summary_p.exists() else {}
docs = f'{s["sessions"]["success"]:,}' if s.get("sessions") else "-"
p50 = f'{s["sessions"]["insert_p50_ms_median"]:.1f} ms' if s.get("sessions") else "-"

items = [
    ("PYTHON", "3.13"),
    ("MONGODB ATLAS", "M0 · 8.0"),
    ("PYMONGO", "4.7.3"),
    ("CONCURRENT SESSIONS", "20"),
    ("DOCUMENTS WRITTEN", docs),
    ("INSERT P50", p50),
]

col = (W - 100) / len(items)
parts = [f'<line x1="50" y1="0.5" x2="{W - 50}" y2="0.5" stroke="{LINE}"/>',
         f'<line x1="50" y1="{H - 0.5}" x2="{W - 50}" y2="{H - 0.5}" stroke="{LINE}"/>']
for i, (label, value) in enumerate(items):
    x = 50 + i * col
    if i:
        parts.append(f'<line x1="{x:.1f}" y1="34" x2="{x:.1f}" y2="{H - 34}" stroke="{LINE}"/>')
    tx = x + (0 if i == 0 else 28)
    parts.append(f'<rect x="{tx:.1f}" y="44" width="7" height="7" fill="{GREEN}"/>')
    parts.append(f'<text x="{tx + 15:.1f}" y="51" font-size="12" font-weight="600" letter-spacing="1.3" fill="{INK_3}">{label}</text>')
    parts.append(f'<text x="{tx:.1f}" y="88" font-size="28" fill="{INK}">{value}</text>')

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Python 3.13, MongoDB Atlas M0 8.0, PyMongo 4.7.3, 20 sessions, {docs} documents written, insert p50 {p50}">
  <title>Stack and run figures</title>
  {style_block()}
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {''.join(parts)}
</svg>
"""
(ROOT / "assets" / "stack-strip.svg").write_text(svg, encoding="utf-8")
print("[OK] assets/stack-strip.svg")
