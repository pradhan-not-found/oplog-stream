"""
generate_graphs.py
==================
Renders the README charts from the data recorded during a real test run.

Inputs  (written by the run):
    results/metrics.jsonl        atlas_monitor.py  - 1 s cluster samples
    results/pull_polls.jsonl     pull_script.py    - one line per poll
    results/pull_summary.json    pull_script.py    - consumer totals
    results/session_XX.json      push_script.py    - per-session insert stats

Outputs:
    assets/graph_*.svg
    results/summary.json         every headline number quoted in the README

Nothing here is synthesised: if an input is missing, that chart is skipped.
Run: python generate_graphs.py
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from svg_theme import (AXIS, BG, BORDER, CRITICAL, GOOD, GRID, INK_MUTED,
                       INK_PRIMARY, INK_SECONDARY, NEUTRAL, S1, S2, S3,
                       WARNING, style_block)

ROOT = Path(__file__).parent
RES = ROOT / "results"
ASSETS = ROOT / "assets"

W, H = 860, 300
PL, PR, PT, PB = 70, 28, 78, 44
PW, PH = W - PL - PR, H - PT - PB
SMOOTH = 5  # seconds, centred moving average for 1 s samples


# ---------------------------------------------------------------- loading
def load_jsonl(name: str) -> list[dict]:
    p = RES / name
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(name: str):
    p = RES / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def smooth(vals: list[float], k: int = SMOOTH) -> list[float]:
    h = k // 2
    out = []
    for i in range(len(vals)):
        win = vals[max(0, i - h): i + h + 1]
        out.append(sum(win) / len(win))
    return out


def pct(vals: list[float], q: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(q * len(s)))] if s else 0.0


def nice_max(v: float) -> float:
    if v <= 0:
        return 1.0
    import math
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.6, 2, 2.4, 3.2, 4, 6, 8, 10):
        if v <= m * exp:
            return m * exp
    return 10 * exp


def fmt_num(v: float, unit: str = "") -> str:
    if abs(v) >= 100 or float(v).is_integer():
        s = f"{v:,.0f}"
    elif abs(v) >= 10:
        s = f"{v:.1f}"
    else:
        s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s + unit


T0_EPOCH = 0.0  # set from the first monitor sample


def fmt_clock(sec: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(T0_EPOCH + sec, tz=timezone.utc).strftime("%H:%M:%S")


# ---------------------------------------------------------------- frame
def frame(title: str, subtitle: str, legend: list[tuple[str, str, str]], body: str,
          desc: str) -> str:
    leg = ""
    x = W - PR
    # right-aligned legend chips, laid out right-to-left
    items = []
    for label, value, color in reversed(legend):
        w_val = 7.0 * len(value) + 4
        w_lab = 6.4 * len(label) + 4
        x_val_end = x
        x_lab_end = x - w_val - 6
        x_dot = x_lab_end - w_lab - 8
        items.append(
            f'<circle cx="{x_dot:.1f}" cy="29" r="4.5" fill="{color}"/>'
            f'<text x="{x_lab_end:.1f}" y="33" font-size="12" fill="{INK_MUTED}" text-anchor="end">{label}</text>'
            f'<text x="{x_val_end:.1f}" y="33" font-size="12" font-weight="600" fill="{INK_PRIMARY}" text-anchor="end">{value}</text>'
        )
        x = x_dot - 18
    leg = "\n  ".join(items)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{title}">
  <title>{title}</title>
  <desc>{desc}</desc>
  {style_block()}
  <rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{BORDER}"/>
  <circle cx="31" cy="29" r="7" fill="none" stroke="{INK_MUTED}" stroke-width="1.3"/>
  <rect x="30.3" y="27.2" width="1.4" height="5.4" fill="{INK_MUTED}"/>
  <circle cx="31" cy="25.2" r="0.9" fill="{INK_MUTED}"/>
  <text x="46" y="34" font-size="15" font-weight="600" fill="{INK_PRIMARY}">{title}</text>
  <text x="46" y="54" font-size="11.5" fill="{INK_MUTED}">{subtitle}</text>
  <text x="{W - PR}" y="54" font-size="11" fill="{INK_MUTED}" text-anchor="end">Granularity: 1 s  ·  Time zone: UTC</text>
  {leg}
{body}
</svg>
"""


def axes(xmax: float, ymax: float, yfmt, xfmt=fmt_clock, xticks: int = 6) -> str:
    b = []
    for i in range(5):
        v = ymax * i / 4
        y = PT + PH - PH * i / 4
        b.append(f'  <line x1="{PL}" y1="{y:.1f}" x2="{W - PR}" y2="{y:.1f}" stroke="{GRID}"/>')
        b.append(f'  <text x="{PL - 10}" y="{y + 4:.1f}" font-size="11" fill="{INK_MUTED}" text-anchor="end">{yfmt(v)}</text>')
    for i in range(xticks + 1):
        v = xmax * i / xticks
        x = PL + PW * i / xticks
        anchor = "start" if i == 0 else ("end" if i == xticks else "middle")
        b.append(f'  <text x="{x:.1f}" y="{PT + PH + 22}" font-size="11" fill="{INK_MUTED}" text-anchor="{anchor}">{xfmt(v)}</text>')
    b.append(f'  <line x1="{PL}" y1="{PT + PH}" x2="{W - PR}" y2="{PT + PH}" stroke="{AXIS}"/>')
    return "\n".join(b)


def line(xs, ys, xmax, ymax, color, area=False) -> str:
    pts = [(PL + PW * x / xmax, PT + PH - PH * min(y, ymax) / ymax) for x, y in zip(xs, ys)]
    if len(pts) < 2:
        return ""
    gap_px = PW * 5 / xmax
    d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"
    for (px, _), (x, y) in zip(pts, pts[1:]):
        d += f" {'M' if x - px > gap_px else 'L'} {x:.1f},{y:.1f}"
    out = ""
    if area and " M " not in d:
        out += (f'  <path d="{d} L {pts[-1][0]:.1f},{PT + PH} L {pts[0][0]:.1f},{PT + PH} Z" '
                f'fill="{color}" fill-opacity="0.06"/>\n')
    out += (f'  <path d="{d}" fill="none" stroke="{color}" stroke-width="1.75" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')
    return out


def annotate(x, y, xmax, ymax, text, anchor="start") -> str:
    px = PL + PW * x / xmax
    py = PT + PH - PH * min(y, ymax) / ymax
    tx = px + (8 if anchor == "start" else -8)
    return (f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{BG}" stroke="{INK_PRIMARY}" stroke-width="2"/>\n'
            f'  <text x="{tx:.1f}" y="{py - 8:.1f}" font-size="11" font-weight="500" fill="{INK_SECONDARY}" text-anchor="{anchor}">{text}</text>')


def save(name: str, svg: str) -> None:
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print(f"[OK] assets/{name}")


# ---------------------------------------------------------------- charts
def run_window(metrics: list[dict]) -> tuple[float, float]:
    """First and last second with oplog inserts (the active write window)."""
    active = [m["t"] for m in metrics if m.get("oplog", {}).get("insert", 0) > 0]
    return (active[0], active[-1]) if active else (0.0, metrics[-1]["t"] if metrics else 0.0)


def chart_opcounters(m, summary):
    rows = [r for r in m if "ops" in r]
    if not rows:
        return
    t = [r["t"] for r in rows]
    ins = [r["ops"]["insert"] for r in rows]
    rd = [r["ops"]["query"] + r["ops"]["getmore"] for r in rows]
    ins_s, rd_s = smooth(ins), smooth(rd)
    xmax, ymax = t[-1], nice_max(max(ins_s + rd_s) * 1.1)
    a, b = summary["window_start_s"], summary["window_end_s"]
    steady = [v for tt, v in zip(t, ins) if a + 10 <= tt <= b - 5] or ins
    summary["opcounters"] = {
        "insert_peak_1s": max(ins), "insert_peak_5s": round(max(ins_s), 1),
        "insert_steady_mean": round(statistics.mean(steady), 1),
        "read_mean_active": round(statistics.mean(
            [v for tt, v in zip(t, rd) if a <= tt <= b] or [0]), 1),
    }
    pk = max(range(len(ins_s)), key=ins_s.__getitem__)
    body = "\n".join([
        axes(xmax, ymax, lambda v: fmt_num(v, "/s")),
        line(t, ins_s, xmax, ymax, S1, area=True),
        line(t, rd_s, xmax, ymax, S2),
        annotate(t[pk], ins_s[pk], xmax, ymax, f"peak {ins_s[pk]:.0f} inserts/s",
                 "end" if t[pk] > xmax * 0.7 else "start"),
    ])
    save("graph_opcounters.svg", frame(
        "Opcounters", f"serverStatus.opcounters, 1 s samples, {SMOOTH} s moving average",
        [("Insert", f"{summary['opcounters']['insert_steady_mean']:.0f}/s steady", S1),
         ("Query + getMore", f"{summary['opcounters']['read_mean_active']:.0f}/s", S2)],
        body, "Insert and read operations per second during the 20-session run"))


def chart_connections(m, summary):
    rows = [r for r in m if "connections" in r]
    if not rows:
        return
    t = [r["t"] for r in rows]
    c = [r["connections"] for r in rows]
    base = statistics.median(c[:5]) if len(c) >= 5 else c[0]
    summary["connections"] = {"baseline": base, "peak": max(c)}
    xmax, ymax = t[-1], nice_max(max(c) * 1.15)
    pk = c.index(max(c))
    body = "\n".join([
        axes(xmax, ymax, lambda v: fmt_num(v)),
        line(t, c, xmax, ymax, S2, area=True),
        annotate(t[pk], c[pk], xmax, ymax, f"peak {max(c)} of 500",
                 "end" if t[pk] > xmax * 0.7 else "start"),
    ])
    save("graph_connections.svg", frame(
        "Connections", "serverStatus.connections.current on the primary (includes Atlas internal + monitor)",
        [("Current", f"{base:.0f} → {max(c)}", S2)],
        body, "Open connections on the primary over the run"))


def chart_network(m, summary):
    rows = [r for r in m if "net_in_kbs" in r]
    if not rows:
        return
    t = [r["t"] for r in rows]
    i_s = smooth([r["net_in_kbs"] for r in rows])
    o_s = smooth([r["net_out_kbs"] for r in rows])
    a, b = summary["window_start_s"], summary["window_end_s"]
    act_in = [v for tt, v in zip(t, i_s) if a + 10 <= tt <= b - 5] or i_s
    act_out = [v for tt, v in zip(t, o_s) if a + 10 <= tt <= b - 5] or o_s
    summary["network"] = {"in_peak_kbs": round(max(i_s), 1), "out_peak_kbs": round(max(o_s), 1),
                          "in_steady_kbs": round(statistics.mean(act_in), 1),
                          "out_steady_kbs": round(statistics.mean(act_out), 1)}
    xmax, ymax = t[-1], nice_max(max(i_s + o_s) * 1.1)
    body = "\n".join([
        axes(xmax, ymax, lambda v: fmt_num(v, " KB/s")),
        line(t, i_s, xmax, ymax, S1, area=True),
        line(t, o_s, xmax, ymax, S2),
    ])
    save("graph_network.svg", frame(
        "Network", f"serverStatus.network bytesIn / bytesOut, {SMOOTH} s moving average",
        [("Bytes in", f"{summary['network']['in_steady_kbs']:.0f} KB/s", S1),
         ("Bytes out", f"{summary['network']['out_steady_kbs']:.0f} KB/s", S2)],
        body, "Network throughput into and out of the primary"))


def chart_oplog(m, summary):
    replay = load_json("oplog_replay.json")
    notify = [r["oplog_notify_ms_p50"] for r in m if "oplog_notify_ms_p50" in r]
    if replay:
        t = [p["t"] for p in replay["per_second"]]
        ins = [p["inserts"] for p in replay["per_second"]]
        source = "change-stream replay of local.oplog.rs from run start"
        other = sum(v for k, v in replay["op_counts"].items() if k != "insert")
    elif m:
        t = [r["t"] for r in m]
        ins = [r.get("oplog", {}).get("insert", 0) for r in m]
        source = "live change-stream tail"
        other = sum(sum(v for k, v in r.get("oplog", {}).items() if k != "insert") for r in m)
    else:
        return
    ins_s = smooth(ins)
    a, b = summary.get("window_start_s", 0), summary.get("window_end_s", t[-1])
    steady = [v for tt, v in zip(t, ins) if a + 10 <= tt <= b - 5] or ins
    summary["oplog"] = {"source": source, "insert_entries_total": sum(ins),
                        "non_insert_entries": other, "peak_1s": max(ins),
                        "peak_5s": round(max(ins_s), 1),
                        "steady_mean_per_s": round(statistics.mean(steady), 1),
                        "inserts_per_session": replay.get("inserts_per_session") if replay else None,
                        "live_tail_notify_ms_p50": round(statistics.median(notify), 1) if notify else None}
    xmax, ymax = t[-1], nice_max(max(ins_s) * 1.15)
    pk = max(range(len(ins_s)), key=ins_s.__getitem__)
    body = "\n".join([
        axes(xmax, ymax, lambda v: fmt_num(v, "/s")),
        line(t, ins_s, xmax, ymax, S1, area=True),
        annotate(t[pk], ins_s[pk], xmax, ymax, f"{ins_s[pk]:.0f} entries/s",
                 "end" if t[pk] > xmax * 0.7 else "start"),
    ])
    save("graph_oplog.svg", frame(
        "Oplog insert entries (event_streaming.sensor_events)",
        f"{source}, bucketed by clusterTime  ·  {SMOOTH} s moving average",
        [("op: i", f"{sum(ins):,} entries", S1)],
        body, "Oplog insert entries per second for the test namespace"))


def chart_repl_lag(m, summary):
    rows = [r for r in m if r.get("repl_lag_s")]
    if not rows:
        return
    names = sorted({k for r in rows for k in r["repl_lag_s"]})
    t_all = [r["t"] for r in m]
    xmax = t_all[-1]
    series, peaks = [], {}
    for name in names:
        pts = [(r["t"], r["repl_lag_s"][name]) for r in rows if name in r["repl_lag_s"]]
        series.append((name, pts))
        peaks[name] = max(v for _, v in pts)
    allv = [v for _, p in series for _, v in p]
    summary["replication_lag"] = {
        "per_secondary_peak_s": {k: round(v, 3) for k, v in peaks.items()},
        "p50_s": round(pct(allv, 0.5), 3), "p95_s": round(pct(allv, 0.95), 3),
        "max_s": round(max(allv), 3), "resolution": "lastWriteDate reported in whole seconds, 500 ms heartbeat",
    }
    ymax = nice_max(max(max(allv) * 1.15, 1.0))
    colors = [S1, S2, S3]
    body = [axes(xmax, ymax, lambda v: fmt_num(v, " s"))]
    for (name, pts), col in zip(series, colors):
        body.append(line([p[0] for p in pts], [p[1] for p in pts], xmax, ymax, col))
    legend = [(n.replace("ac-", "").split("-shard-")[-1].replace("00-", "node "),
               f"max {peaks[n]:.1f} s", c) for n, c in zip(names, colors)]
    save("graph_replication_lag.svg", frame(
        "Replication lag", "Primary − secondary lastWriteDate via 500 ms heartbeats  ·  1 s resolution",
        legend, "\n".join(body), "Per-secondary replication lag over the run"))


def chart_query_latency(polls, summary):
    rows = [p for p in polls if p["n"] > 0]
    if not rows:
        return
    t = [p["t"] for p in polls]
    q = [p["query_ms"] for p in polls]
    q_s = smooth(q, 9)
    summary["pull_query"] = {"polls": len(polls), "polls_with_docs": len(rows),
                             "p50_ms": round(pct(q, .5), 1), "p95_ms": round(pct(q, .95), 1),
                             "p99_ms": round(pct(q, .99), 1), "max_ms": round(max(q), 1),
                             "docs_per_poll_mean": round(statistics.mean(p["n"] for p in rows), 1)}
    xmax, ymax = t[-1], nice_max(pct(q, .99) * 1.2)
    body = "\n".join([
        axes(xmax, ymax, lambda v: fmt_num(v, " ms")),
        line(t, q_s, xmax, ymax, S2, area=True),
    ])
    save("graph_query_latency.svg", frame(
        "Pull consumer query time", "find({_id: {$gt: bookmark}}).sort({_id: 1}).limit(100), client round trip, 9-poll moving average",
        [("p50", f"{summary['pull_query']['p50_ms']:.0f} ms", S2),
         ("p95", f"{summary['pull_query']['p95_ms']:.0f} ms", INK_MUTED)],
        body, "Client-observed latency of each pull query"))

    e = [(p["t"], p["e2e_ms_p50"]) for p in polls if p.get("e2e_ms_p50") is not None]
    if e:
        ev = [v for _, v in e]
        summary["end_to_end"] = {"p50_ms": round(pct(ev, .5), 0), "p95_ms": round(pct(ev, .95), 0),
                                 "max_ms": round(max(p.get("e2e_ms_max") or 0 for p in polls), 0)}
        ymax = nice_max(pct(ev, .99) * 1.2)
        es = smooth(ev, 9)
        body = "\n".join([
            axes(xmax, ymax, lambda v: fmt_num(v / 1000, " s") if v >= 1000 else fmt_num(v, " ms")),
            line([x for x, _ in e], es, xmax, ymax, S1, area=True),
        ])
        save("graph_end_to_end.svg", frame(
            "End-to-end delay (push → pull)", "now − pushed_at_epoch for each pulled document, median per poll, 9-poll moving average",
            [("p50", f"{summary['end_to_end']['p50_ms']:,.0f} ms", S1),
             ("p95", f"{summary['end_to_end']['p95_ms']:,.0f} ms", INK_MUTED)],
            body, "Time from a document's creation to the pull consumer reading it"))


def chart_sessions(sessions, summary):
    if not sessions:
        return
    sessions = sorted(sessions, key=lambda s: s["session_id"])
    p50 = [s["insert_ms"]["p50"] for s in sessions]
    p95 = [s["insert_ms"]["p95"] for s in sessions]
    ymax = nice_max(max(p95) * 1.15)
    n = len(sessions)
    slot = PW / n
    bw = slot * 0.56
    b = [axes(n, ymax, lambda v: fmt_num(v, " ms"), xfmt=lambda v: "", xticks=1)]
    for i, s in enumerate(sessions):
        x = PL + slot * i + (slot - bw) / 2
        h50 = PH * p50[i] / ymax
        y95 = PT + PH - PH * min(p95[i], ymax) / ymax
        b.append(f'  <path d="M{x:.1f},{PT + PH} V{PT + PH - h50 + 4:.1f} '
                 f'Q{x:.1f},{PT + PH - h50:.1f} {x + 4:.1f},{PT + PH - h50:.1f} H{x + bw - 4:.1f} '
                 f'Q{x + bw:.1f},{PT + PH - h50:.1f} {x + bw:.1f},{PT + PH - h50 + 4:.1f} V{PT + PH} Z" fill="{S1}"/>')
        b.append(f'  <line x1="{x + 2:.1f}" y1="{y95:.1f}" x2="{x + bw - 2:.1f}" y2="{y95:.1f}" '
                 f'stroke="{S2}" stroke-width="3" stroke-linecap="round"/>')
        b.append(f'  <text x="{x + bw / 2:.1f}" y="{PT + PH + 22}" font-size="11" fill="{INK_MUTED}" '
                 f'text-anchor="middle">{s["session_id"]:02d}</text>')
    allp50 = statistics.median(p50)
    summary["sessions"] = {
        "count": n, "success": sum(s["success"] for s in sessions),
        "failed": sum(s["failed"] for s in sessions),
        "insert_p50_ms_median": round(allp50, 1),
        "insert_p50_ms_range": [round(min(p50), 1), round(max(p50), 1)],
        "insert_p95_ms_range": [round(min(p95), 1), round(max(p95), 1)],
        "insert_p99_ms_max": round(max(s["insert_ms"]["p99"] for s in sessions), 1),
        "insert_max_ms": round(max(s["insert_ms"]["max"] for s in sessions), 1),
        "rate_per_session_mean": round(statistics.mean(s["rate_docs_s"] for s in sessions), 2),
        "elapsed_s_range": [round(min(s["elapsed_s"] for s in sessions), 1),
                            round(max(s["elapsed_s"] for s in sessions), 1)],
        "launch_spread_s": round(max(s["start_epoch"] for s in sessions)
                                 - min(s["start_epoch"] for s in sessions), 2),
    }
    save("graph_session_latency.svg", frame(
        "insert_one latency by session", "Client round trip per acknowledged insert (w: majority), sessions 01–20",
        [("p50 (bar)", f"{allp50:.0f} ms median", S1),
         ("p95 (tick)", f"{statistics.median(p95):.0f} ms median", S2)],
        "\n".join(b), "Median and 95th percentile insert latency for each of the 20 sessions"))


def chart_status(pull, summary):
    if not pull or not pull.get("status_counts"):
        return
    order = [("OK", GOOD, 70), ("WARNING", WARNING, 15), ("CRITICAL", CRITICAL, 10), ("UNKNOWN", NEUTRAL, 5)]
    counts = pull["status_counts"]
    total = sum(counts.values())
    summary["status"] = {k: {"count": counts.get(k, 0),
                             "pct": round(100 * counts.get(k, 0) / total, 2), "target_pct": tgt}
                         for k, _, tgt in order}
    ymax = nice_max(max(counts.values()) * 1.15)
    n = len(order)
    slot = PW / n
    bw = min(120, slot * 0.5)
    b = [axes(n, ymax, lambda v: fmt_num(v), xfmt=lambda v: "", xticks=1)]
    for i, (k, col, tgt) in enumerate(order):
        c = counts.get(k, 0)
        x = PL + slot * i + (slot - bw) / 2
        h = PH * c / ymax
        top = PT + PH - h
        b.append(f'  <path d="M{x:.1f},{PT + PH} V{top + 4:.1f} Q{x:.1f},{top:.1f} {x + 4:.1f},{top:.1f} '
                 f'H{x + bw - 4:.1f} Q{x + bw:.1f},{top:.1f} {x + bw:.1f},{top + 4:.1f} V{PT + PH} Z" fill="{col}"/>')
        b.append(f'  <text x="{x + bw / 2:.1f}" y="{top - 9:.1f}" font-size="12" font-weight="600" '
                 f'fill="{INK_PRIMARY}" text-anchor="middle">{c:,}  ({100 * c / total:.1f}%)</text>')
        b.append(f'  <text x="{x + bw / 2:.1f}" y="{PT + PH + 22}" font-size="11.5" font-weight="500" '
                 f'fill="{INK_SECONDARY}" text-anchor="middle">{k}  ·  target {tgt}%</text>')
    save("graph_status_dist.svg", frame(
        "status field distribution", f"Counted by the pull consumer across {total:,} documents",
        [("Documents", f"{total:,}", NEUTRAL)], "\n".join(b),
        "Observed status values versus generator weights"))


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    # The monitor may have been restarted mid-run: merge all parts by epoch
    metrics = sorted((r for f in sorted(RES.glob("metrics*.jsonl")) for r in load_jsonl(f.name)),
                     key=lambda r: r["epoch"])
    if metrics:
        e0 = metrics[0]["epoch"]
        for r in metrics:
            r["t"] = round(r["epoch"] - e0, 2)
    polls = load_jsonl("pull_polls.jsonl")
    pull = load_json("pull_summary.json")
    sessions = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RES.glob("session_*.json"))]

    summary: dict = {}
    global T0_EPOCH
    if metrics:
        T0_EPOCH = metrics[0]["epoch"]
        a, b = run_window(metrics)
        summary.update(window_start_s=a, window_end_s=b, window_s=round(b - a, 1),
                       monitor_samples=len(metrics),
                       serverStatus_available=any("ops" in r for r in metrics),
                       oplog_error=next((r["oplog_error"] for r in metrics if "oplog_error" in r), None))
        chart_opcounters(metrics, summary)
        chart_connections(metrics, summary)
        chart_network(metrics, summary)
        chart_oplog(metrics, summary)
        chart_repl_lag(metrics, summary)
    chart_query_latency(polls, summary)
    chart_sessions(sessions, summary)
    chart_status(pull, summary)
    if pull:
        summary["pull"] = {k: pull[k] for k in ("total_pulled", "field_means", "elapsed_s")}
        summary["pull"]["sessions_complete"] = sum(
            1 for v in pull.get("unique_sequences_per_session", {}).values()
            if sessions and v == sessions[0]["total"])
    (RES / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("[OK] results/summary.json")


if __name__ == "__main__":
    main()
