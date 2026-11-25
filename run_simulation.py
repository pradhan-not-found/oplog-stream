"""
run_simulation.py
=================
One-command real test against MongoDB Atlas:

  1. atlas_monitor.py   - samples cluster telemetry + tails the oplog   (background)
  2. pull_script.py     - separate consumer process, records every poll (background)
  3. launch_sessions.py - 20 concurrent push_script.py sessions          (foreground)
  4. oplog_replay.py   - re-reads the run window from local.oplog.rs
  5. generate_graphs.py - renders assets/graph_*.svg + results/summary.json

Usage:
    python run_simulation.py --sessions 20 --total 1000 --interval 0.1
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
RES = ROOT / "results"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", type=int, default=20)
    ap.add_argument("--total", type=int, default=1000)
    ap.add_argument("--interval", type=float, default=0.1)
    ap.add_argument("--warmup", type=float, default=30, help="idle baseline before push (s)")
    ap.add_argument("--cooldown", type=float, default=30, help="idle tail after push (s)")
    args = ap.parse_args()

    if RES.exists():
        shutil.rmtree(RES)
    RES.mkdir()
    (ROOT / "logs").mkdir(exist_ok=True)

    started = datetime.now(timezone.utc)
    py = sys.executable
    mon_log = open(ROOT / "logs" / "monitor.log", "w", encoding="utf-8")
    pull_log = open(ROOT / "logs" / "pull.log", "w", encoding="utf-8")

    print(f"[run] monitor + pull starting, {args.warmup:.0f} s baseline")
    mon = subprocess.Popen([py, "atlas_monitor.py", "--until-idle", str(args.cooldown)],
                           cwd=ROOT, env=ENV, stdout=mon_log, stderr=subprocess.STDOUT)
    pull = subprocess.Popen([py, "pull_script.py", "--batch", "100", "--interval", "1.0",
                             "--until-idle", str(args.cooldown)],
                            cwd=ROOT, env=ENV, stdout=pull_log, stderr=subprocess.STDOUT)
    time.sleep(args.warmup)

    print(f"[run] launching {args.sessions} push sessions x {args.total} docs")
    t_push = time.time()
    subprocess.run([py, "launch_sessions.py", "--sessions", str(args.sessions),
                    "--total", str(args.total), "--interval", str(args.interval),
                    "--no-window"], cwd=ROOT, env=ENV, check=False)
    push_s = time.time() - t_push
    print(f"[run] push phase finished in {push_s:.1f} s, waiting for cooldown")

    pull.wait()
    mon.wait()
    mon_log.close()
    pull_log.close()

    (RES / "run_meta.json").write_text(json.dumps({
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sessions": args.sessions, "docs_per_session": args.total,
        "interval_s": args.interval, "push_phase_s": round(push_s, 1),
        "warmup_s": args.warmup, "cooldown_s": args.cooldown,
        "python": sys.version.split()[0],
    }, indent=2), encoding="utf-8")

    subprocess.run([py, "oplog_replay.py"], cwd=ROOT, env=ENV, check=False)
    subprocess.run([py, "generate_graphs.py"], cwd=ROOT, env=ENV, check=False)
    print("[run] done -> results/summary.json, assets/graph_*.svg")


if __name__ == "__main__":
    main()
