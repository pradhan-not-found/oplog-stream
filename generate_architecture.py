"""
generate_architecture.py
Renders assets/architecture-pipeline.svg: a 3 x 2 grid of identical cards.

  row 1 (data path):     Producers  ->  Atlas primary  ->  Pull consumer
  row 2 (oplog path):    Secondaries <-  Oplog         ->  Observer

Run: python generate_architecture.py
"""
from pathlib import Path

from svg_theme import (MONGODB_GREEN, MONGODB_PATH, PYTHON_BLUE, PYTHON_PATH,
                       style_block)

ROOT = Path(__file__).parent
W, H = 1500, 470
BG = "#EDEEEB"
CARD = "#FFFFFF"
STROKE = "#DCDFDA"
INK = "#14201B"
INK_2 = "#5B6661"
INK_3 = "#8A948F"
LINK = "#9AA39E"
CHIP_GREEN = "#E6F4EC"
CHIP_BLUE = "#E7EFF8"
CHIP_GREY = "#F0F1EE"
GREEN = "#1F9E5A"

CW, CH = 330, 116                      # card size
COLS = [125, 585, 1045]                # card x
ROWS = [96, 306]                      # card y
p: list[str] = []


def glyph(kind: str, x: float, y: float) -> str:
    """44x44 chip with a 24px icon centred."""
    chip = {"python": CHIP_BLUE, "mongodb": CHIP_GREEN, "oplog": CHIP_GREEN}.get(kind, CHIP_GREY)
    out = f'<rect x="{x}" y="{y}" width="44" height="44" rx="11" fill="{chip}"/>'
    ix, iy = x + 10, y + 10
    if kind == "python":
        out += f'<path transform="translate({ix},{iy})" d="{PYTHON_PATH}" fill="{PYTHON_BLUE}"/>'
    elif kind == "mongodb":
        out += f'<path transform="translate({ix},{iy})" d="{MONGODB_PATH}" fill="{MONGODB_GREEN}"/>'
    elif kind == "grid":
        out += "".join(f'<rect x="{ix + 1 + c * 6}" y="{iy + 1 + r * 6}" width="4.4" height="4.4" rx="0.8" fill="{GREEN}"/>'
                       for r in range(4) for c in range(4))
    elif kind == "oplog":  # stacked log lines
        out += "".join(f'<rect x="{ix + 2}" y="{iy + 3 + i * 6}" width="{20 - (i % 2) * 6}" height="3" rx="1.5" fill="{GREEN}"/>'
                       for i in range(4))
    elif kind == "replica":  # two linked nodes
        out += (f'<circle cx="{ix + 6}" cy="{iy + 12}" r="4.5" fill="none" stroke="{INK_2}" stroke-width="1.8"/>'
                f'<circle cx="{ix + 18}" cy="{iy + 12}" r="4.5" fill="none" stroke="{INK_2}" stroke-width="1.8"/>'
                f'<path d="M{ix + 10.5},{iy + 12} H{ix + 13.5}" stroke="{INK_2}" stroke-width="1.8"/>')
    elif kind == "observer":  # pulse line
        out += (f'<path d="M{ix},{iy + 13} h5 l3,-7 l4,14 l3,-9 l2,2 h7" fill="none" stroke="{INK_2}" '
                f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
    return out


def card(col: int, row: int, kind: str, eyebrow: str, title: str, caption: str) -> None:
    x, y = COLS[col], ROWS[row]
    p.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="16" fill="{CARD}" stroke="{STROKE}" filter="url(#lift)"/>')
    p.append(glyph(kind, x + 24, y + 24))
    p.append(f'<text x="{x + 84}" y="{y + 38}" font-size="11.5" font-weight="600" letter-spacing="1.3" fill="{INK_3}">{eyebrow}</text>')
    p.append(f'<text x="{x + 84}" y="{y + 64}" font-size="19" font-weight="500" fill="{INK}">{title}</text>')
    p.append(f'<text x="{x + 24}" y="{y + 96}" font-size="13.5" fill="{INK_2}">{caption}</text>')


def link(x1, y1, x2, y2, text, dashed=False):
    dash = ' stroke-dasharray="3 5"' if dashed else ""
    p.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{LINK}" stroke-width="1.5"{dash} marker-end="url(#head)"/>')
    p.append(f'<circle cx="{x1}" cy="{y1}" r="3" fill="{LINK}"/>')
    if text:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        w = 7.2 * len(text) + 22
        p.append(f'<rect x="{mx - w / 2:.1f}" y="{my - 13}" width="{w:.1f}" height="26" rx="13" fill="{BG}" stroke="{STROKE}"/>')
        p.append(f'<text x="{mx:.1f}" y="{my + 4.5}" font-size="12.5" fill="{INK_2}" text-anchor="middle">{text}</text>')


# column headers
for x, t in zip(COLS, ("PUSH ENVIRONMENT", "MONGODB ATLAS", "PULL ENVIRONMENT")):
    p.append(f'<text x="{x}" y="58" font-size="12" font-weight="600" letter-spacing="1.6" fill="{INK_3}">{t}</text>')
p.append(f'<line x1="125" y1="70" x2="1375" y2="70" stroke="{STROKE}"/>')

# row 1 - data path
card(0, 0, "grid", "20 PROCESSES", "Producers", "push_script.py  ·  20-variable documents")
card(1, 0, "mongodb", "REPLICA SET PRIMARY", "Atlas M0", "event_streaming.sensor_events")
card(2, 0, "python", "SEPARATE PROCESS", "Pull consumer", "pull_script.py  ·  _id bookmark polling")
# row 2 - oplog path
card(0, 1, "replica", "2 NODES", "Secondaries", "apply oplog entries asynchronously")
card(1, 1, "oplog", "LOCAL.OPLOG.RS", "Oplog", "one insert entry per acknowledged write")
card(2, 1, "observer", "OBSERVER", "Monitor + replay", "atlas_monitor.py  ·  oplog_replay.py")

g = 130  # horizontal gap between cards
link(COLS[0] + CW, ROWS[0] + CH / 2, COLS[1] - 6, ROWS[0] + CH / 2, "insert_one")
link(COLS[1] + CW, ROWS[0] + CH / 2, COLS[2] - 6, ROWS[0] + CH / 2, "find  ·  1 s")
link(COLS[1] + CW / 2, ROWS[0] + CH, COLS[1] + CW / 2, ROWS[1] - 6, "")
link(COLS[1], ROWS[1] + CH / 2, COLS[0] + CW + 6, ROWS[1] + CH / 2, "replicate", dashed=True)
link(COLS[1] + CW, ROWS[1] + CH / 2, COLS[2] - 6, ROWS[1] + CH / 2, "change stream", dashed=True)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="oplog-stream architecture">
  <title>oplog-stream architecture</title>
  <desc>Twenty producers insert into the Atlas primary; a separate consumer polls it. Each write becomes one oplog entry, which secondaries replicate and an observer reads through a change stream.</desc>
  {style_block()}
  <defs>
    <filter id="lift" x="-10%" y="-20%" width="120%" height="150%">
      <feDropShadow dx="0" dy="2" stdDeviation="5" flood-color="#14201B" flood-opacity="0.07"/>
    </filter>
    <marker id="head" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M1,1 L9,5 L1,9" fill="none" stroke="{LINK}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {''.join(p)}
</svg>
"""
(ROOT / "assets" / "architecture-pipeline.svg").write_text(svg, encoding="utf-8")
print("[OK] assets/architecture-pipeline.svg")
