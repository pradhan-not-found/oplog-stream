"""
generate_architecture.py
Renders assets/architecture-flow.svg: a minimal left-to-right flow
(20 producers -> Atlas primary + oplog -> pull consumer), with the
replica set and the observer as secondary paths. Grey surface, Instrument Sans.

Run: python generate_architecture.py
"""
from pathlib import Path

from svg_theme import style_block

ROOT = Path(__file__).parent
W, H = 1500, 560
BG = "#EDEEEB"
CARD = "#FFFFFF"
LINE = "#D9DCD7"
INK = "#14201B"
INK_2 = "#4A5650"
INK_3 = "#8A948F"
GREEN = "#1F9E5A"
GREEN_SOFT = "#E6F4EC"
BLUE = "#3D7FE0"
FLOW = "#A3ABA7"

p = []


def label(x, y, text):
    p.append(f'<text x="{x}" y="{y}" font-size="12" font-weight="600" letter-spacing="1.4" fill="{INK_3}">{text}</text>')


def box(x, y, w, h, title, sub, accent=None, fill=CARD):
    stroke = accent or LINE
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
    if accent:
        p.append(f'<rect x="{x}" y="{y + 14}" width="3" height="{h - 28}" rx="1.5" fill="{accent}"/>')
    p.append(f'<text x="{x + 22}" y="{y + h / 2 - 3}" font-size="17" font-weight="600" fill="{INK}">{title}</text>')
    p.append(f'<text x="{x + 22}" y="{y + h / 2 + 18}" font-size="13" fill="{INK_2}">{sub}</text>')


def flow(d, color, text="", tx=0, ty=0, dashed=False, anchor="middle"):
    dash = ' stroke-dasharray="4 5"' if dashed else ""
    p.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#m{color[1:]})"/>')
    if text:
        p.append(f'<text x="{tx}" y="{ty}" font-size="12.5" fill="{INK_2}" text-anchor="{anchor}">{text}</text>')


def stat(x, y, value, caption):
    p.append(f'<text x="{x}" y="{y}" font-size="26" font-weight="500" fill="{INK}">{value}</text>')
    p.append(f'<text x="{x}" y="{y + 22}" font-size="12.5" fill="{INK_3}">{caption}</text>')


# --- producers: 20 sessions as a pixel grid --------------------------------
label(60, 70, "PUSH ENVIRONMENT")
p.append(f'<rect x="60" y="92" width="300" height="236" rx="12" fill="{CARD}" stroke="{LINE}" stroke-width="1.2"/>')
for i in range(20):
    r, c = divmod(i, 5)
    x, y = 86 + c * 52, 116 + r * 46
    p.append(f'<rect x="{x}" y="{y}" width="40" height="34" rx="6" fill="{GREEN_SOFT}" stroke="{GREEN}" stroke-opacity="0.35"/>')
    p.append(f'<text x="{x + 20}" y="{y + 22}" font-size="12.5" font-weight="500" fill="{INK}" text-anchor="middle">{i + 1:02d}</text>')
p.append(f'<text x="86" y="316" font-size="13" fill="{INK_2}">20 × push_script.py · insert_one · w: majority</text>')
stat(60, 392, "19,978", "acknowledged of 20,000")
stat(230, 392, "107 ms", "insert p50")

# --- atlas ---------------------------------------------------------------------------
label(500, 70, "MONGODB ATLAS · M0 REPLICA SET")
box(500, 92, 420, 92, "Primary", "event_streaming.sensor_events", accent=GREEN)
box(500, 236, 420, 92, "local.oplog.rs", "one insert entry per write", accent=GREEN, fill=GREEN_SOFT)
flow("M710,184 V230", GREEN)
box(500, 380, 200, 80, "Secondary", "node 00")
box(720, 380, 200, 80, "Secondary", "node 02")
flow("M600,328 V374", FLOW, dashed=True)
flow("M820,328 V374", FLOW, dashed=True)
p.append(f'<text x="934" y="424" font-size="12.5" fill="{INK_2}">lag p95 1 s</text>')

# --- consumers -------------------------------------------------------------------------
label(1080, 70, "PULL ENVIRONMENT")
box(1080, 92, 360, 92, "pull_script.py", "find(_id &gt; bookmark) every 1 s", accent=BLUE)
stat(1080, 236, "79.8%", "of documents received")
stat(1250, 236, "1.05 s", "push → pull p50")

label(1080, 330, "OBSERVER")
box(1080, 352, 360, 72, "atlas_monitor.py", "serverStatus · change stream")
box(1080, 438, 360, 72, "oplog_replay.py", "100% of oplog entries", accent=GREEN)

# --- main flows ------------------------------------------------------------------------
flow("M360,138 H494", GREEN, "insert_one", 427, 128)
flow("M920,138 H1074", BLUE, "poll", 997, 128)
flow("M920,282 C1000,282 1000,474 1074,474", FLOW, "change stream", 968, 362, dashed=True, anchor="end")

markers = "".join(
    f'<marker id="m{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
    for c in (GREEN, BLUE, FLOW))

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="oplog-stream architecture">
  <title>oplog-stream architecture</title>
  <desc>20 producer sessions insert into the Atlas primary; each write becomes one oplog entry replicated to two secondaries; a separate pull consumer polls by _id; an observer samples metrics and replays the oplog.</desc>
  {style_block()}
  <defs>{markers}</defs>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {''.join(p)}
</svg>
"""
(ROOT / "assets" / "architecture-flow.svg").write_text(svg, encoding="utf-8")
print("[OK] assets/architecture-flow.svg")
