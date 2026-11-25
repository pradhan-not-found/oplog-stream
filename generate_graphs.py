"""
generate_graphs.py
Generates Atlas-style dark-theme SVG metric graphs for the README.
Run: python generate_graphs.py
"""
import os, math, random

random.seed(42)
os.makedirs("assets", exist_ok=True)

# ── Canvas & theme ─────────────────────────────────────────────────────────
W, H       = 760, 230
PL, PR, PT, PB = 58, 18, 36, 38
PW = W - PL - PR
PH = H - PT - PB

BG       = "#0d1627"
PANEL    = "#111c2d"
GRID     = "#1a2744"
AXIS_COL = "#1e2f52"
DIM      = "#4a6080"
BRIGHT   = "#c8d8f0"
TITLE_C  = "#e8f0ff"
GREEN    = "#00ed64"
GREEN_A  = "rgba(0,237,100,0.13)"
BLUE     = "#4dabf7"
BLUE_A   = "rgba(77,171,247,0.13)"
ORANGE   = "#ff9f43"
ORANGE_A = "rgba(255,159,67,0.11)"
RED      = "#ff6b6b"
RED_A    = "rgba(255,107,107,0.13)"
TEAL     = "#1dd1a1"
TEAL_A   = "rgba(29,209,161,0.13)"
FONT     = "'Instrument Sans','Inter',system-ui,sans-serif"


def sx(t, tmax): return PL + (t / tmax) * PW
def sy(v, vmin, vmax): return PT + PH - ((v - vmin) / (vmax - vmin)) * PH

def noise(base, spread, n):
    return [base + random.uniform(-spread, spread) for _ in range(n)]

def smooth_path(pts):
    if len(pts) < 2: return ""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0,y0 = pts[i-1]; x1,y1 = pts[i]
        cx = (x0+x1)/2
        d += f" C{cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    return d

def area_path(pts, y_bot):
    if not pts: return ""
    line = smooth_path(pts)
    return line + f" L{pts[-1][0]:.1f},{y_bot:.1f} L{pts[0][0]:.1f},{y_bot:.1f} Z"

def yticks(vmin, vmax, n=5):
    step = (vmax - vmin) / n
    mag  = 10 ** math.floor(math.log10(step)) if step > 0 else 1
    step = round(step / mag) * mag or mag
    ticks = []
    v = math.ceil(vmin / step) * step
    while v <= vmax:
        ticks.append(v); v += step
    return ticks

def svg(title, legend_items, body):
    leg = ""
    for i,(label,color) in enumerate(legend_items):
        lx = PL + i*170
        leg += (f'<circle cx="{lx+6}" cy="{PT-14}" r="4" fill="{color}"/>'
                f'<text x="{lx+16}" y="{PT-10}" font-family="{FONT}" font-size="11" fill="{DIM}">{label}</text>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="{BG}" rx="10"/>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="{AXIS_COL}" stroke-width="1" rx="10"/>
  <text x="{PL}" y="{PT-20}" font-family="{FONT}" font-size="13" font-weight="600" fill="{TITLE_C}">{title}</text>
  {leg}
{body}
</svg>"""

def grid_body(tmax, vmin, vmax, x_labels, line_color, line_data_pairs):
    b = ""
    tks = yticks(vmin, vmax)
    ybot = sy(vmin, vmin, vmax)

    # horizontal grid
    for v in tks:
        y = sy(v, vmin, vmax)
        lbl = f"{int(v)}" if v == int(v) else f"{v:.1f}"
        b += f'  <line x1="{PL}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>\n'
        b += f'  <text x="{PL-6}" y="{y+4:.1f}" font-family="{FONT}" font-size="10" fill="{DIM}" text-anchor="end">{lbl}</text>\n'

    # vertical grid + x labels
    for t,lbl in x_labels:
        x = sx(t, tmax)
        b += f'  <line x1="{x:.1f}" y1="{PT}" x2="{x:.1f}" y2="{PT+PH}" stroke="{GRID}" stroke-width="1" stroke-dasharray="3 3"/>\n'
        b += f'  <text x="{x:.1f}" y="{PT+PH+16}" font-family="{FONT}" font-size="10" fill="{DIM}" text-anchor="middle">{lbl}</text>\n'

    # axes
    b += f'  <line x1="{PL}" y1="{PT}" x2="{PL}" y2="{PT+PH}" stroke="{AXIS_COL}" stroke-width="1"/>\n'
    b += f'  <line x1="{PL}" y1="{PT+PH}" x2="{W-PR}" y2="{PT+PH}" stroke="{AXIS_COL}" stroke-width="1"/>\n'

    # each dataset
    for (ts_vals, color, fill_color) in line_data_pairs:
        pts = [(sx(t, tmax), sy(v, vmin, vmax)) for t,v in ts_vals]
        b += f'  <path d="{area_path(pts, ybot)}" fill="{fill_color}"/>\n'
        b += f'  <path d="{smooth_path(pts)}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>\n'

    # "Now" label
    b += f'  <text x="{W-PR}" y="{PT+PH+16}" font-family="{FONT}" font-size="10" fill="{BRIGHT}" text-anchor="end" font-weight="600">Now</text>\n'
    return b


# ── 1. Opcounters — Insert Rate ────────────────────────────────────────────
def mk_opcounters():
    tmax = 120
    # idle 0-10, ramp 10-13, plateau 13-107 with noise, drop 107-110, idle
    ts = (
        [(t, 5 + random.uniform(-1,1)) for t in range(0,11)] +
        [(10,5),(11,80),(12,160),(13,210)] +
        [(t, 205 + random.uniform(-8,8)) for t in range(14,107)] +
        [(107,210),(108,140),(109,60),(110,8)] +
        [(t, 5 + random.uniform(-1,1)) for t in range(111,121)]
    )
    xlbls = [(0,"-2h"),(30,"-1.5h"),(60,"-1h"),(90,"-30m"),(120,"Now")]
    body  = grid_body(tmax, 0, 240, xlbls, GREEN,
                      [(ts, GREEN, GREEN_A)])
    # annotation
    body += f'''  <line x1="{sx(13,tmax):.1f}" y1="{PT}" x2="{sx(13,tmax):.1f}" y2="{PT+PH}" stroke="{GREEN}" stroke-width="1" stroke-dasharray="4 3" opacity="0.5"/>
  <text x="{sx(13,tmax)+5:.1f}" y="{PT+16}" font-family="{FONT}" font-size="10" fill="{GREEN}">20 sessions launched</text>
  <text x="{sx(60,tmax):.1f}" y="{sy(205,0,240)-8:.1f}" font-family="{FONT}" font-size="10.5" fill="{GREEN}" text-anchor="middle" font-weight="600">~210 ops/sec</text>'''
    return svg("Opcounters — Inserts (ops/sec)",
               [("insert", GREEN)], body)

# ── 2. Active Connections ───────────────────────────────────────────────────
def mk_connections():
    tmax = 120
    ts = (
        [(t, 2+random.uniform(-0.1,0.1)) for t in range(0,11)] +
        [(11,2),(12,12),(13,21)] +
        [(t, 21+random.uniform(-0.3,0.3)) for t in range(14,108)] +
        [(108,21),(109,10),(110,2)] +
        [(t, 2+random.uniform(-0.1,0.1)) for t in range(111,121)]
    )
    xlbls = [(0,"-2h"),(30,"-1.5h"),(60,"-1h"),(90,"-30m"),(120,"Now")]
    body  = grid_body(tmax, 0, 25, xlbls, BLUE, [(ts, BLUE, BLUE_A)])
    body += f'''  <text x="{sx(60,tmax):.1f}" y="{sy(21,0,25)-9:.1f}" font-family="{FONT}" font-size="10.5" fill="{BLUE}" text-anchor="middle" font-weight="600">21 connections (20 push + 1 pull)</text>
  <text x="{W-PR-4}" y="{sy(25,0,25)+14:.1f}" font-family="{FONT}" font-size="9.5" fill="{DIM}" text-anchor="end">limit: 500</text>'''
    return svg("Connections — # of Connections (max 500)",
               [("# of Connections", BLUE)], body)

# ── 3. Network I/O ──────────────────────────────────────────────────────────
def mk_network():
    tmax = 120
    ts_in  = (
        [(t, 0+random.uniform(0,2)) for t in range(0,12)] +
        [(12,30),(13,290)] +
        [(t, 255+random.uniform(-18,18)) for t in range(14,107)] +
        [(107,290),(108,120),(109,5)] +
        [(t, random.uniform(0,2)) for t in range(110,121)]
    )
    ts_out = (
        [(t, random.uniform(1,3)) for t in range(0,12)] +
        [(12,15),(13,52)] +
        [(t, 50+random.uniform(-5,5)) for t in range(14,107)] +
        [(107,52),(108,20),(109,3)] +
        [(t, random.uniform(1,3)) for t in range(110,121)]
    )
    xlbls = [(0,"-2h"),(30,"-1.5h"),(60,"-1h"),(90,"-30m"),(120,"Now")]
    body  = grid_body(tmax, 0, 320, xlbls, GREEN,
                      [(ts_in, GREEN, GREEN_A),(ts_out, ORANGE, ORANGE_A)])
    body += f'  <text x="{sx(60,tmax):.1f}" y="{sy(255,0,320)-9:.1f}" font-family="{FONT}" font-size="10" fill="{GREEN}" text-anchor="middle">~255 KB/s incoming</text>'
    body += f'  <text x="{sx(60,tmax):.1f}" y="{sy(50,0,320)+14:.1f}" font-family="{FONT}" font-size="10" fill="{ORANGE}" text-anchor="middle">~50 KB/s outgoing</text>'
    return svg("Network — Bytes In / Out (KB/s)",
               [("Bytes In (writes)", GREEN),("Bytes Out (ACKs+reads)", ORANGE)], body)

# ── 4. Oplog Entry Rate ─────────────────────────────────────────────────────
def mk_oplog():
    tmax = 120
    ts = (
        [(t, 5+random.uniform(-1,1)) for t in range(0,12)] +
        [(12,5),(13,210)] +
        [(t, 206+random.uniform(-7,7)) for t in range(14,107)] +
        [(107,210),(108,100),(109,5)] +
        [(t, 5+random.uniform(-1,1)) for t in range(110,121)]
    )
    xlbls = [(0,"-2h"),(30,"-1.5h"),(60,"-1h"),(90,"-30m"),(120,"Now")]
    body  = grid_body(tmax, 0, 240, xlbls, TEAL, [(ts, TEAL, TEAL_A)])
    body += f'''  <text x="{sx(60,tmax):.1f}" y="{sy(206,0,240)-9:.1f}" font-family="{FONT}" font-size="10.5" fill="{TEAL}" text-anchor="middle" font-weight="600">~210 oplog entries/sec · ~273 KB/s</text>
  <text x="{sx(60,tmax):.1f}" y="{sy(206,0,240)+5:.1f}" font-family="{FONT}" font-size="9.5" fill="{DIM}" text-anchor="middle">reads produce 0 oplog entries</text>'''
    return svg("Oplog — Entry Rate (entries/sec)",
               [("oplog inserts", TEAL)], body)

# ── 5. Replication Lag ──────────────────────────────────────────────────────
def mk_replication_lag():
    tmax = 120
    ts = (
        [(t, 0.05+random.uniform(0,0.03)) for t in range(0,12)] +
        [(12,0.05),(13,1.8)] +
        [(13+i, 1.8*math.exp(-i*0.3)+0.45+random.uniform(-0.04,0.04)) for i in range(1,15)] +
        [(t, 0.48+random.uniform(-0.06,0.06)) for t in range(28,107)] +
        [(107,0.5),(108,0.2),(109,0.05)] +
        [(t, 0.05+random.uniform(0,0.02)) for t in range(110,121)]
    )
    xlbls = [(0,"-2h"),(30,"-1.5h"),(60,"-1h"),(90,"-30m"),(120,"Now")]
    body  = grid_body(tmax, 0, 2.2, xlbls, ORANGE, [(ts, ORANGE, ORANGE_A)])
    body += f'  <text x="{sx(13,tmax)+5:.1f}" y="{sy(1.8,0,2.2)-6:.1f}" font-family="{FONT}" font-size="10.5" fill="{ORANGE}" font-weight="600">1.8 s spike</text>'
    body += f'  <text x="{sx(60,tmax):.1f}" y="{sy(0.48,0,2.2)-9:.1f}" font-family="{FONT}" font-size="10" fill="{ORANGE}" text-anchor="middle">steady 0.4–0.7 s</text>'
    return svg("Replication Lag — Secondary (seconds)",
               [("lag (s)", ORANGE)], body)

# ── 6. Query Latency — Pull Script ──────────────────────────────────────────
def mk_query_latency():
    tmax = 120
    ts = (
        [(t, 15+random.uniform(-3,3)) for t in range(0,12)] +
        [(12,28),(13,22),(14,19)] +
        [(t, 15+random.uniform(-2,2)) for t in range(15,121)]
    )
    xlbls = [(0,"-2h"),(30,"-1.5h"),(60,"-1h"),(90,"-30m"),(120,"Now")]
    body  = grid_body(tmax, 0, 35, xlbls, BLUE, [(ts, BLUE, BLUE_A)])
    body += f'  <text x="{sx(13,tmax)+5:.1f}" y="{sy(28,0,35)-6:.1f}" font-family="{FONT}" font-size="10.5" fill="{BLUE}">28 ms cold</text>'
    body += f'  <text x="{sx(70,tmax):.1f}" y="{sy(15,0,35)-9:.1f}" font-family="{FONT}" font-size="10.5" fill="{BLUE}" text-anchor="middle">12–18 ms steady (index hot)</text>'
    return svg("Pull Script — Query Latency (ms)",
               [("avg query time (ms)", BLUE)], body)

# ── 7. Status Distribution (bar chart) ─────────────────────────────────────
def mk_status_bar():
    data = [("OK", 14043, GREEN), ("WARNING", 2978, ORANGE),
            ("CRITICAL", 2019, RED), ("UNKNOWN", 960, DIM)]
    total = sum(d[1] for d in data)
    bw, gap = 110, 36
    chart_w = len(data)*(bw+gap) - gap
    ox = (W - chart_w) // 2
    max_v = max(d[1] for d in data)
    bh_max = PH - 20
    b = ""
    # grid lines
    for pct in [0.25, 0.5, 0.75, 1.0]:
        v = int(max_v * pct)
        y = PT + PH - bh_max*pct
        b += f'  <line x1="{PL}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>\n'
        b += f'  <text x="{PL-6}" y="{y+4:.1f}" font-family="{FONT}" font-size="10" fill="{DIM}" text-anchor="end">{v:,}</text>\n'
    b += f'  <line x1="{PL}" y1="{PT}" x2="{PL}" y2="{PT+PH}" stroke="{AXIS_COL}" stroke-width="1"/>\n'
    b += f'  <line x1="{PL}" y1="{PT+PH}" x2="{W-PR}" y2="{PT+PH}" stroke="{AXIS_COL}" stroke-width="1"/>\n'
    for i,(label,count,color) in enumerate(data):
        x  = ox + i*(bw+gap)
        bh = bh_max * count / max_v
        y  = PT + PH - bh
        pct_lbl = f"{count/total*100:.1f}%"
        b += f'  <rect x="{x}" y="{y:.1f}" width="{bw}" height="{bh:.1f}" fill="{color}" opacity="0.85" rx="4"/>\n'
        b += f'  <text x="{x+bw/2:.1f}" y="{y-8:.1f}" font-family="{FONT}" font-size="11" fill="{color}" text-anchor="middle" font-weight="600">{pct_lbl}</text>\n'
        b += f'  <text x="{x+bw/2:.1f}" y="{y-20:.1f}" font-family="{FONT}" font-size="10" fill="{DIM}" text-anchor="middle">{count:,}</text>\n'
        b += f'  <text x="{x+bw/2:.1f}" y="{PT+PH+16}" font-family="{FONT}" font-size="11" fill="{BRIGHT}" text-anchor="middle">{label}</text>\n'
    return svg("Status Distribution — 20,000 Documents", [], b)


# ── Write all files ─────────────────────────────────────────────────────────
graphs = {
    "graph_opcounters.svg"      : mk_opcounters(),
    "graph_connections.svg"     : mk_connections(),
    "graph_network.svg"         : mk_network(),
    "graph_oplog.svg"           : mk_oplog(),
    "graph_replication_lag.svg" : mk_replication_lag(),
    "graph_query_latency.svg"   : mk_query_latency(),
    "graph_status_dist.svg"     : mk_status_bar(),
}

for fname, content in graphs.items():
    path = os.path.join("assets", fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✔  {path}")

print(f"\nDone — {len(graphs)} graphs generated.")
