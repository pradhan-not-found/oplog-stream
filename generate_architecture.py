"""
generate_architecture.py
Renders assets/architecture.svg: push environment -> Atlas replica set ->
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
    dash = ' stroke-dasharray="5 5"' if dashed else ""
    s = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash} '
         f'marker-end="url(#arrow-{color[1:]})"/>')
    if label:
        s += f'<text x="{lx}" y="{ly}" font-size="12.5" fill="{INK_2}" text-anchor="{anchor}">{label}</text>'
    return s


def marker(color):
    return (f'<marker id="arrow-{color[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')


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
             f'<line x1="64" y1="556" x2="446" y2="556" stroke="{LINE}"/>'
             f'<text x="64" y="594" font-size="24" font-weight="600" fill="{INK}">19,978</text>'
             f'<text x="64" y="616" font-size="12" fill="{INK_3}">acknowledged inserts</text>'
             f'<text x="230" y="594" font-size="24" font-weight="600" fill="{INK}">107 ms</text>'
             f'<text x="230" y="616" font-size="12" fill="{INK_3}">insert p50</text>'
             f'<text x="352" y="594" font-size="24" font-weight="600" fill="{INK}">22</text>'
             f'<text x="352" y="616" font-size="12" fill="{INK_3}">failed</text>')

# ---- atlas -------------------------------------------------------------------
parts.append(card(560, 40, 400, 610, "MONGODB ATLAS", "M0 · MongoDB 8.0 · 3-node replica set"))
parts.append(node(590, 124, 340, 62, "Primary", "event_streaming.sensor_events", "#FFFFFF", GREEN))
parts.append(node(590, 218, 340, 62, "local.oplog.rs", "1 insert entry per write · 19,978 in run", GREEN_SOFT, GREEN, mono=True))
parts.append(node(590, 360, 160, 62, "Secondary", "node 00", "#FFFFFF", LINE))
parts.append(node(770, 360, 160, 62, "Secondary", "node 02", "#FFFFFF", LINE))
parts.append(arrow("M760,186 V212", GREEN))
parts.append(arrow("M700,280 V354", GREY_FLOW, "replicate", 640, 322, dashed=True, anchor="start"))
parts.append(arrow("M820,280 V354", GREY_FLOW, "", dashed=True))
parts.append(f'<line x1="584" y1="462" x2="936" y2="462" stroke="{LINE}"/>'
             f'<text x="590" y="494" font-size="13" fill="{INK_2}">Replication lag p50 0 s, p95 1 s</text>'
             f'<text x="590" y="514" font-size="13" fill="{INK_2}">Connections 43 → 204 at peak (limit 500)</text>'
             f'<text x="590" y="534" font-size="13" fill="{INK_2}">Steady 46 inserts/s, peak 90/s</text>')

# ---- pull + observer -------------------------------------------------------
parts.append(card(1050, 40, 410, 280, "PULL ENVIRONMENT", "separate process"))
parts.append(node(1074, 124, 362, 62, "pull_script.py", "find(_id > bookmark).sort(_id).limit(100)", BLUE_SOFT, BLUE, mono=True))
parts.append(f'<text x="1074" y="232" font-size="24" font-weight="600" fill="{INK}">79.8%</text>'
             f'<text x="1074" y="254" font-size="12" fill="{INK_3}">of documents received</text>'
             f'<text x="1220" y="232" font-size="24" font-weight="600" fill="{INK}">1.05 s</text>'
             f'<text x="1220" y="254" font-size="12" fill="{INK_3}">push → pull p50</text>'
             f'<text x="1074" y="292" font-size="12.5" fill="{INK_2}">ObjectId order ≠ commit order across 20 clients</text>')

parts.append(card(1050, 370, 410, 280, "OBSERVER", "metrics and oplog evidence"))
parts.append(node(1074, 454, 362, 62, "atlas_monitor.py", "serverStatus · change stream · heartbeats, 1 s", "#FFFFFF", LINE, mono=True))
parts.append(node(1074, 540, 362, 62, "oplog_replay.py", "startAtOperationTime → 100% of entries", GREEN_SOFT, GREEN, mono=True))

# ---- flows -----------------------------------------------------------------------
parts.append(arrow("M470,250 C525,250 530,155 584,155", GREEN, "insert_one", 480, 276, anchor="start"))
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
(ROOT / "assets" / "architecture.svg").write_text(svg, encoding="utf-8")
print("[OK] assets/architecture.svg")
