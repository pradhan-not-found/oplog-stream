"""
generate_architecture.py
Renders assets/architecture-overview.svg: push environment -> Atlas replica set ->
pull environment, plus the observer. Grey surface, white cards, Instrument Sans.

Run: python generate_architecture.py
"""
from pathlib import Path

from svg_theme import style_block

ROOT = Path(__file__).parent
W, H = 1500, 690
BG = "#EDEEEB"
CARD = "#FFFFFF"
LINE = "#D5D8D3"
INK = "#14201B"
INK_2 = "#3D4A44"
INK_3 = "#7C8781"
GREEN = "#1F9E5A"
GREEN_SOFT = "#E3F3E9"
BLUE = "#3D7FE0"
BLUE_SOFT = "#E6EEFB"
GREY_FLOW = "#9AA39E"


def card(x, y, w, h, label, sub=""):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{CARD}" stroke="{LINE}"/>'
         f'<text x="{x + 24}" y="{y + 36}" font-size="13" font-weight="600" letter-spacing="1.2" fill="{INK_3}">{label}</text>')
    if sub:
        s += f'<text x="{x + 24}" y="{y + 56}" font-size="13" fill="{INK_3}">{sub}</text>'
    return s


def node(x, y, w, h, title, sub, fill, stroke, mono=False):
    fam = "font-family=\"ui-monospace, 'SFMono-Regular', Consolas, monospace\"" if mono else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}"/>'
            f'<text x="{x + 16}" y="{y + 26}" font-size="15" font-weight="600" fill="{INK}" {fam}>{title}</text>'
            f'<text x="{x + 16}" y="{y + 46}" font-size="12.5" fill="{INK_2}">{sub}</text>')


def arrow(d, color, label="", lx=0, ly=0, dashed=False, anchor="middle"):
    """Thin connector: rounded caps, start dot, open chevron head, pill label."""
    dash = ' stroke-dasharray="4 5"' if dashed else ""
    start = d.split()[0][1:].split(",")
    s = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} '
         f'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow-{color[1:]})"/>'
         f'<circle cx="{start[0]}" cy="{start[1]}" r="3" fill="{color}"/>')
    if label:
        w = 7.0 * len(label) + 20
        x0 = lx - w / 2 if anchor == "middle" else (lx - w + 10 if anchor == "end" else lx - 10)
        s += (f'<rect x="{x0:.1f}" y="{ly - 16}" width="{w:.1f}" height="24" rx="12" '
              f'fill="{BG}" stroke="{LINE}"/>'
              f'<text x="{x0 + w / 2:.1f}" y="{ly}" font-size="12.5" fill="{INK_2}" text-anchor="middle">{label}</text>')
    return s


def tiles(x, y, width, items, fill, stroke, h=68, gap=10):
    """Button-style stat tiles: value on top, caption below, evenly split."""
    w = (width - gap * (len(items) - 1)) / len(items)
    out = ""
    for i, (value, caption) in enumerate(items):
        tx = x + i * (w + gap)
        out += (f'<rect x="{tx:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="10" fill="{fill}" '
                f'stroke="{stroke}" stroke-opacity="0.45"/>'
                f'<text x="{tx + 14:.1f}" y="{y + 32}" font-size="21" font-weight="600" fill="{INK}">{value}</text>'
                f'<text x="{tx + 14:.1f}" y="{y + 52}" font-size="11.5" fill="{INK_2}">{caption}</text>')
    return out


def marker(color):
    return (f'<marker id="arrow-{color[1:]}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" '
            f'stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>')


parts = []

# ---- push environment ------------------------------------------------------
parts.append(card(40, 40, 430, 610, "PUSH ENVIRONMENT", "launch_sessions.py starts 20 processes"))
for i in range(20):
    r, c = divmod(i, 4)
    x, y = 64 + c * 98, 124 + r * 66
    parts.append(f'<rect x="{x}" y="{y}" width="86" height="54" rx="7" fill="{GREEN_SOFT}" stroke="{GREEN}" stroke-opacity="0.45"/>'
                 f'<text x="{x + 43}" y="{y + 24}" font-size="13" font-weight="600" fill="{INK}" text-anchor="middle">session {i + 1:02d}</text>'
                 f'<text x="{x + 43}" y="{y + 42}" font-size="11" fill="{INK_3}" text-anchor="middle">push_script</text>')
parts.append(f'<text x="64" y="488" font-size="13" fill="{INK_2}">One MongoClient per process</text>'
             f'<text x="64" y="508" font-size="13" fill="{INK_2}">20-variable document per loop iteration</text>'
             f'<text x="64" y="528" font-size="13" fill="{INK_2}">insert_one, w: majority, 100 ms sleep</text>'
             + tiles(64, 554, 382, [("19,978", "acknowledged"), ("107 ms", "insert p50"), ("22", "failed")],
                     GREEN_SOFT, GREEN))

# ---- atlas -------------------------------------------------------------------
parts.append(card(560, 40, 400, 610, "MONGODB ATLAS", "M0 · MongoDB 8.0 · 3-node replica set"))
parts.append(node(590, 124, 340, 62, "Primary", "event_streaming.sensor_events", "#FFFFFF", GREEN))
parts.append(node(590, 218, 340, 62, "local.oplog.rs", "1 insert entry per write · 19,978 in run", GREEN_SOFT, GREEN, mono=True))
parts.append(node(590, 360, 160, 62, "Secondary", "node 00", "#FFFFFF", LINE))
parts.append(node(770, 360, 160, 62, "Secondary", "node 02", "#FFFFFF", LINE))
parts.append(arrow("M760,186 V212", GREEN))
parts.append(arrow("M700,280 V354", GREY_FLOW, "replicate", 760, 322, dashed=True))
parts.append(arrow("M820,280 V354", GREY_FLOW, "", dashed=True))
parts.append(tiles(584, 554, 352, [("46/s", "steady inserts"), ("204", "peak connections"), ("1 s", "lag p95")],
                   "#F3F4F1", LINE))

# ---- pull + observer -------------------------------------------------------
parts.append(card(1050, 40, 410, 280, "PULL ENVIRONMENT", "separate process"))
parts.append(node(1074, 124, 362, 62, "pull_script.py", "find(_id > bookmark).sort(_id).limit(100)", BLUE_SOFT, BLUE, mono=True))
parts.append(tiles(1074, 202, 362, [("79.8%", "documents received"), ("1.05 s", "push → pull p50")],
                   BLUE_SOFT, BLUE)
             + f'<text x="1074" y="296" font-size="12.5" fill="{INK_2}">ObjectId order ≠ commit order across 20 clients</text>')

parts.append(card(1050, 370, 410, 280, "OBSERVER", "metrics and oplog evidence"))
parts.append(node(1074, 454, 362, 62, "atlas_monitor.py", "serverStatus · change stream · heartbeats, 1 s", "#FFFFFF", LINE, mono=True))
parts.append(node(1074, 540, 362, 62, "oplog_replay.py", "startAtOperationTime → 100% of entries", GREEN_SOFT, GREEN, mono=True))

# ---- flows -----------------------------------------------------------------------
parts.append(arrow("M470,250 C525,250 530,155 584,155", GREEN, "insert_one", 515, 145))
parts.append(arrow("M930,155 C990,155 1000,155 1068,155", BLUE, "poll every 1 s", 999, 145))
parts.append(arrow("M930,249 C990,249 990,571 1068,571", GREY_FLOW, "change stream", 996, 350, dashed=True, anchor="start"))

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="oplog-stream architecture">
  <title>oplog-stream architecture</title>
  <desc>20 producer sessions insert into the Atlas primary; the oplog replicates to two secondaries; a separate pull consumer polls by _id; an observer samples metrics and replays the oplog.</desc>
  {style_block()}
  <defs>{marker(GREEN)}{marker(BLUE)}{marker(GREY_FLOW)}</defs>
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {''.join(parts)}
</svg>
"""
(ROOT / "assets" / "architecture-overview.svg").write_text(svg, encoding="utf-8")
print("[OK] assets/architecture-overview.svg")
