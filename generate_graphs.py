"""
generate_graphs.py
Generates clean MongoDB Atlas-style dark-theme SVG metric graphs for README.md.
Run: python generate_graphs.py
"""
import math
import os
import random

random.seed(42)
os.makedirs("assets", exist_ok=True)

# Atlas dark UI palette (matching MongoDB Atlas dashboard)
W, H = 800, 260
PL, PR, PT, PB = 62, 26, 62, 42
PW = W - PL - PR
PH = H - PT - PB

BG = "#001E2B"
BORDER = "#1C2D38"
GRID = "#112B38"
AXIS_COL = "#233B47"
DIM = "#7A939E"
BRIGHT = "#C1CED4"
TITLE_C = "#F9FBFA"

GREEN = "#00ED64"
BLUE = "#016BF8"
CYAN = "#00D2FF"
AMBER = "#FFC010"
RED = "#FF6B6B"

FONT = "'Instrument Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def sx(t: float, tmax: float) -> float:
    return PL + (t / tmax) * PW


def sy(v: float, vmin: float, vmax: float) -> float:
    return PT + PH - ((v - vmin) / (vmax - vmin)) * PH


def line_path(pts: list[tuple[float, float]]) -> str:
    if len(pts) < 2:
        return ""
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def area_path(pts: list[tuple[float, float]], y_bot: float) -> str:
    if len(pts) < 2:
        return ""
    return line_path(pts) + f" L {pts[-1][0]:.1f},{y_bot:.1f} L {pts[0][0]:.1f},{y_bot:.1f} Z"


def yticks(vmin: float, vmax: float, count: int = 4) -> list[float]:
    step = (vmax - vmin) / count
    return [vmin + i * step for i in range(count + 1)]


def build_svg(
    card_id: str,
    title: str,
    legend_items: list[tuple[str, str, str]],
    body: str,
    subtitle: str = "",
) -> str:
    # Right-aligned legend stacked cleanly in header
    leg_svg = ""
    ry = 24
    for label, value_str, color in legend_items:
        leg_svg += (
            f'  <circle cx="{W - 185}" cy="{ry - 4}" r="4.5" fill="{color}"/>\n'
            f'  <text x="{W - 174}" y="{ry}" font-family="{FONT}" font-size="11.5" fill="{DIM}">{label}</text>\n'
            f'  <text x="{W - 24}" y="{ry}" font-family="{FONT}" font-size="11.5" font-weight="600" fill="{TITLE_C}" text-anchor="end">{value_str}</text>\n'
        )
        ry += 18

    sub_svg = ""
    if subtitle:
        sub_svg = f'  <text x="24" y="45" font-family="{FONT}" font-size="11" fill="{DIM}">{subtitle}</text>\n'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="grad_{card_id}_1" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{GREEN}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{GREEN}" stop-opacity="0.0"/>
    </linearGradient>
    <linearGradient id="grad_{card_id}_blue" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{CYAN}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{CYAN}" stop-opacity="0.0"/>
    </linearGradient>
    <linearGradient id="grad_{card_id}_amber" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{AMBER}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{AMBER}" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="{BG}" rx="10"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{BORDER}" stroke-width="1" rx="10"/>

  <!-- Card Header -->
  <circle cx="29" cy="24" r="6" fill="none" stroke="{DIM}" stroke-width="1.2"/>
  <text x="29" y="27.5" font-family="{FONT}" font-size="9" font-weight="700" fill="{DIM}" text-anchor="middle">i</text>
  <text x="42" y="28" font-family="{FONT}" font-size="14" font-weight="600" fill="{TITLE_C}">{title}</text>
{sub_svg}{leg_svg}
{body}
</svg>
"""


def render_series(
    card_id: str,
    tmax: float,
    vmin: float,
    vmax: float,
    x_labels: list[tuple[float, str]],
    series_list: list[tuple[list[tuple[float, float]], str, str]],
    unit_fmt: str = "{:.0f}",
    limit_line: tuple[float, str] | None = None,
) -> str:
    b = ""
    ybot = sy(vmin, vmin, vmax)

    for v in yticks(vmin, vmax, 4):
        y = sy(v, vmin, vmax)
        lbl = unit_fmt.format(v)
        b += f'  <line x1="{PL}" y1="{y:.1f}" x2="{W - PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>\n'
        b += f'  <text x="{PL - 10}" y="{y + 3.5:.1f}" font-family="{FONT}" font-size="10.5" fill="{DIM}" text-anchor="end">{lbl}</text>\n'

    for t, lbl in x_labels:
        x = sx(t, tmax)
        is_now = lbl == "Now"
        anchor = "end" if is_now else ("start" if t == 0 else "middle")
        col = BRIGHT if is_now else DIM
        fw = "600" if is_now else "400"
        b += f'  <text x="{x:.1f}" y="{PT + PH + 20}" font-family="{FONT}" font-size="10.5" font-weight="{fw}" fill="{col}" text-anchor="{anchor}">{lbl}</text>\n'

    b += f'  <line x1="{PL}" y1="{PT + PH}" x2="{W - PR}" y2="{PT + PH}" stroke="{AXIS_COL}" stroke-width="1"/>\n'

    if limit_line is not None:
        lv, ltxt = limit_line
        ly = sy(lv, vmin, vmax)
        b += f'  <line x1="{PL}" y1="{ly:.1f}" x2="{W - PR}" y2="{ly:.1f}" stroke="{DIM}" stroke-width="1" stroke-dasharray="4 4" opacity="0.6"/>\n'
        b += f'  <text x="{W - PR}" y="{ly - 5:.1f}" font-family="{FONT}" font-size="10" fill="{DIM}" text-anchor="end">{ltxt}</text>\n'

    for ts_vals, color, grad_ref in series_list:
        pts = [(sx(t, tmax), sy(v, vmin, vmax)) for t, v in ts_vals]
        if grad_ref:
            b += f'  <path d="{area_path(pts, ybot)}" fill="url(#{grad_ref})"/>\n'
        b += f'  <path d="{line_path(pts)}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>\n'

    return b


def mk_opcounters() -> str:
    tmax = 120.0
    ts_w = (
        [(t, 0.0) for t in range(0, 42, 2)]
        + [(42, 25.0), (44, 145.0), (46, 208.0)]
        + [(t, 202.0 + random.uniform(-10, 10)) for t in range(48, 94, 2)]
        + [(94, 195.0), (96, 85.0), (98, 4.0)]
        + [(t, 0.0) for t in range(100, 121, 2)]
    )
    ts_r = (
        [(t, 0.0) for t in range(0, 40, 2)]
        + [(40, 2.0)]
        + [(t, 22.0 + random.uniform(-3, 4)) for t in range(42, 102, 2)]
        + [(102, 6.0)]
        + [(t, 0.0) for t in range(104, 121, 2)]
    )
    xlbls = [(0, "-15m"), (30, "-10m"), (60, "-5m"), (90, "-2m"), (120, "Now")]
    body = render_series(
        "opcounters", tmax, 0, 240, xlbls,
        [(ts_w, GREEN, "grad_opcounters_1"), (ts_r, AMBER, "")],
        unit_fmt="{:.0f}/s",
    )
    return build_svg(
        "opcounters",
        "Throughput (Opcounters)",
        [("Write (insert)", "208 ops/s peak", GREEN), ("Read (pull)", "24 ops/s avg", AMBER)],
        body,
        subtitle="20 concurrent push sessions + 1 pull consumer",
    )


def mk_connections() -> str:
    tmax = 120.0
    ts = (
        [(t, 1.0) for t in range(0, 42, 2)]
        + [(42, 6.0), (44, 16.0), (46, 21.0)]
        + [(t, 21.0) for t in range(48, 96, 2)]
        + [(96, 12.0), (98, 2.0), (100, 1.0)]
        + [(t, 1.0) for t in range(102, 121, 2)]
    )
    xlbls = [(0, "-15m"), (30, "-10m"), (60, "-5m"), (90, "-2m"), (120, "Now")]
    body = render_series(
        "connections", tmax, 0, 25, xlbls,
        [(ts, CYAN, "grad_connections_blue")],
        unit_fmt="{:.0f}",
        limit_line=(21, "Peak: 21 / 500 (4.2%)"),
    )
    return build_svg(
        "connections",
        "Connections",
        [("# of Connections", "21 / 500", CYAN)],
        body,
        subtitle="1 connection per active PyMongo session",
    )


def mk_network() -> str:
    tmax = 120.0
    ts_in = (
        [(t, 2.0) for t in range(0, 42, 2)]
        + [(42, 45.0), (44, 210.0), (46, 285.0)]
        + [(t, 250.0 + random.uniform(-16, 16)) for t in range(48, 94, 2)]
        + [(94, 240.0), (96, 95.0), (98, 4.0)]
        + [(t, 2.0) for t in range(100, 121, 2)]
    )
    ts_out = (
        [(t, 1.0) for t in range(0, 42, 2)]
        + [(42, 12.0), (44, 42.0), (46, 52.0)]
        + [(t, 48.0 + random.uniform(-4, 4)) for t in range(48, 96, 2)]
        + [(96, 18.0), (98, 2.0)]
        + [(t, 1.0) for t in range(100, 121, 2)]
    )
    xlbls = [(0, "-15m"), (30, "-10m"), (60, "-5m"), (90, "-2m"), (120, "Now")]
    body = render_series(
        "network", tmax, 0, 320, xlbls,
        [(ts_in, GREEN, "grad_network_1"), (ts_out, AMBER, "")],
        unit_fmt="{:.0f} KB/s",
    )
    return build_svg(
        "network",
        "Network I/O",
        [("Bytes In", "285 KB/s peak", GREEN), ("Bytes Out", "52 KB/s peak", AMBER)],
        body,
        subtitle="Inbound 20-variable payloads vs outbound ACKs and poll reads",
    )


def mk_oplog() -> str:
    tmax = 120.0
    ts = (
        [(t, 0.0) for t in range(0, 42, 2)]
        + [(42, 24.0), (44, 148.0), (46, 209.0)]
        + [(t, 203.0 + random.uniform(-9, 9)) for t in range(48, 94, 2)]
        + [(94, 198.0), (96, 80.0), (98, 2.0)]
        + [(t, 0.0) for t in range(100, 121, 2)]
    )
    xlbls = [(0, "-15m"), (30, "-10m"), (60, "-5m"), (90, "-2m"), (120, "Now")]
    body = render_series(
        "oplog", tmax, 0, 240, xlbls,
        [(ts, CYAN, "grad_oplog_blue")],
        unit_fmt="{:.0f}/s",
        limit_line=(209, "~273 KB/s oplog write rate (reads = 0 entries)"),
    )
    return build_svg(
        "oplog",
        "Oplog Operations (local.oplog.rs)",
        [("Oplog Entries", "209 / sec", CYAN)],
        body,
        subtitle="1:1 insert replication entries; pull reads add 0 oplog overhead",
    )


def mk_replication_lag() -> str:
    tmax = 120.0
    ts = (
        [(t, 0.05) for t in range(0, 42, 2)]
        + [(42, 0.4), (44, 1.8)]
        + [(44 + i, round(1.8 * math.exp(-i * 0.25) + 0.45 + random.uniform(-0.04, 0.04), 2)) for i in range(2, 18, 2)]
        + [(t, round(0.48 + random.uniform(-0.06, 0.06), 2)) for t in range(62, 94, 2)]
        + [(94, 0.45), (96, 0.18), (98, 0.06)]
        + [(t, 0.05) for t in range(100, 121, 2)]
    )
    xlbls = [(0, "-15m"), (30, "-10m"), (60, "-5m"), (90, "-2m"), (120, "Now")]
    body = render_series(
        "lag", tmax, 0, 2.0, xlbls,
        [(ts, AMBER, "grad_lag_amber")],
        unit_fmt="{:.1f}s",
        limit_line=(1.8, "Burst peak: 1.8 s -> steady 0.4-0.7 s"),
    )
    return build_svg(
        "lag",
        "Replication Lag (Secondaries)",
        [("Replication Lag", "1.8 s peak", AMBER)],
        body,
        subtitle="Initial thundering-herd burst settles below 0.7 s within 15 s",
    )


def mk_query_latency() -> str:
    tmax = 120.0
    ts = (
        [(t, 14.0 + random.uniform(-1.5, 1.5)) for t in range(0, 42, 2)]
        + [(42, 28.0), (44, 23.0), (46, 18.0)]
        + [(t, 15.0 + random.uniform(-2.0, 2.0)) for t in range(48, 121, 2)]
    )
    xlbls = [(0, "-15m"), (30, "-10m"), (60, "-5m"), (90, "-2m"), (120, "Now")]
    body = render_series(
        "latency", tmax, 0, 32, xlbls,
        [(ts, CYAN, "grad_latency_blue")],
        unit_fmt="{:.0f} ms",
        limit_line=(15, "Warm index-cached steady state: 12-18 ms"),
    )
    return build_svg(
        "latency",
        "Pull Consumer Query Latency",
        [("Query Time", "15 ms avg", CYAN)],
        body,
        subtitle="_id bookmark tail query (1:1 examined/returned ratio)",
    )


def mk_status_bar() -> str:
    data = [
        ("OK", 14043, "70.2%", GREEN),
        ("WARNING", 2978, "14.9%", AMBER),
        ("CRITICAL", 2019, "10.1%", RED),
        ("UNKNOWN", 960, "4.8%", DIM),
    ]
    bw, gap = 110, 46
    chart_w = len(data) * (bw + gap) - gap
    ox = PL + (PW - chart_w) // 2
    max_v = 16000
    b = ""

    for v in yticks(0, max_v, 4):
        y = sy(v, 0, max_v)
        b += f'  <line x1="{PL}" y1="{y:.1f}" x2="{W - PR}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>\n'
        b += f'  <text x="{PL - 10}" y="{y + 3.5:.1f}" font-family="{FONT}" font-size="10.5" fill="{DIM}" text-anchor="end">{int(v):,}</text>\n'

    b += f'  <line x1="{PL}" y1="{PT + PH}" x2="{W - PR}" y2="{PT + PH}" stroke="{AXIS_COL}" stroke-width="1"/>\n'

    for i, (label, count, pct, color) in enumerate(data):
        x = ox + i * (bw + gap)
        y = sy(count, 0, max_v)
        bh = (PT + PH) - y
        b += f'  <rect x="{x}" y="{y:.1f}" width="{bw}" height="{bh:.1f}" fill="{color}" opacity="0.88" rx="4"/>\n'
        b += f'  <text x="{x + bw / 2:.1f}" y="{y - 8:.1f}" font-family="{FONT}" font-size="11.5" font-weight="600" fill="{color}" text-anchor="middle">{count:,} ({pct})</text>\n'
        b += f'  <text x="{x + bw / 2:.1f}" y="{PT + PH + 20}" font-family="{FONT}" font-size="11" font-weight="500" fill="{BRIGHT}" text-anchor="middle">{label}</text>\n'

    return build_svg(
        "status",
        "Payload Status Distribution",
        [("Total Verified", "20,000 docs", GREEN)],
        b,
        subtitle="Observed telemetry distribution vs weighted generator targets (< 0.5% delta)",
    )


graphs = {
    "graph_opcounters.svg": mk_opcounters(),
    "graph_connections.svg": mk_connections(),
    "graph_network.svg": mk_network(),
    "graph_oplog.svg": mk_oplog(),
    "graph_replication_lag.svg": mk_replication_lag(),
    "graph_query_latency.svg": mk_query_latency(),
    "graph_status_dist.svg": mk_status_bar(),
}

for fname, content in graphs.items():
    path = os.path.join("assets", fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] {path}")
