"""
generate_banner.py
Generates a pixel-art SVG banner in the Instrument Sans / mosaic style.
Run:  python generate_banner.py
Output: assets/banner.svg
"""
import math, random, os

random.seed(7)

W, H = 1200, 300
BG   = "#f9f6f1"
SQ   = 11          # square size px
GAP  = 3           # gap between squares
CELL = SQ + GAP    # 14 px grid

# --- arch centre: bottom-right corner ---
CX, CY = 1095, H

# MongoDB green palette — inner bright, outer fades
PALETTE = ["#00ED64", "#00D65A", "#00BE50", "#00A846", "#009040", "#007830"]

rects = []
for r_idx, r in enumerate(range(55, 310, 28)):
    n = max(6, int(math.pi * r / CELL))
    for i in range(n + 1):
        theta = math.pi * i / n          # 0 → π  (left to right)
        x = CX - r * math.cos(theta)     # arch opens leftward
        y = CY - r * math.sin(theta)

        if y < -SQ or x < 390 or x > W + SQ:
            continue

        # dissolve: outer rings get progressively sparse
        if r > 140:
            keep_prob = max(0.15, 1.0 - (r - 140) / 240.0)
            if random.random() > keep_prob:
                continue

        # add extra scatter dots on outermost rings
        if r > 220 and random.random() < 0.4:
            ox = x + random.randint(-18, 18)
            oy = y + random.randint(-14, 14)
            if 390 < ox < W and 0 < oy < H:
                rects.append((ox, oy, PALETTE[-1], 0.25))

        col   = PALETTE[min(r_idx, len(PALETTE) - 1)]
        alpha = round(max(0.22, 1.0 - (r - 55) / 340.0), 2)
        rects.append((round(x - SQ / 2, 1), round(y - SQ / 2, 1), col, alpha))

rect_svg = "\n".join(
    f'  <rect x="{x}" y="{y}" width="{SQ}" height="{SQ}" '
    f'fill="{c}" opacity="{a}" rx="1.5"/>'
    for x, y, c, a in rects
)

svg = f"""\
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}">

  <!-- background -->
  <rect width="{W}" height="{H}" fill="{BG}"/>

  <!-- pixel-art arch -->
{rect_svg}

  <!-- repo path -->
  <text x="58" y="52"
        font-family="'Instrument Sans','Inter',system-ui,sans-serif"
        font-size="12.5" fill="#999" letter-spacing="0.3">
    pradhan-not-found / oplog-stream
  </text>

  <!-- title -->
  <text x="56" y="128"
        font-family="'Instrument Sans','Inter',system-ui,sans-serif"
        font-size="52" font-weight="650" fill="#111" letter-spacing="-1">
    oplog-stream
  </text>

  <!-- subtitle line 1 -->
  <text x="58" y="167"
        font-family="'Instrument Sans','Inter',system-ui,sans-serif"
        font-size="15.5" fill="#555" letter-spacing="0.1">
    High-throughput MongoDB Atlas event streaming pipeline
  </text>

  <!-- subtitle line 2 -->
  <text x="58" y="192"
        font-family="'Instrument Sans','Inter',system-ui,sans-serif"
        font-size="15.5" fill="#888" letter-spacing="0.1">
    20 concurrent sessions &#xB7; 20-variable IoT documents &#xB7; real-time pull consumer
  </text>

  <!-- bottom tag -->
  <text x="58" y="264"
        font-family="'Instrument Sans','Inter',system-ui,sans-serif"
        font-size="13" fill="#00C851" letter-spacing="0.5" font-weight="500">
    MongoDB Atlas &#x2219; PyMongo &#x2219; Python 3.13
  </text>

</svg>
"""

os.makedirs("assets", exist_ok=True)
out = os.path.join("assets", "banner.svg")
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Written → {out}  ({len(rects)} squares)")
