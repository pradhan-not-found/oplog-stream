"""
atlas_monitor.py
================
Records real cluster telemetry while the 20 push sessions run.

Every second it samples:
  * serverStatus      -> opcounters, connections, network bytes in/out
  * oplog (via change stream on the collection) -> oplog entries/s by op type
  * replica-set heartbeats (hello.lastWrite) -> secondary replication lag

Output: results/metrics.jsonl (one JSON object per second)

Usage:
    python atlas_monitor.py --duration 600          # stop after 600 s
    python atlas_monitor.py --until-idle 20         # stop after 20 s with no inserts
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from collections import Counter
from datetime import timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, errors

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
RESULTS = Path(__file__).parent / "results"


class OplogTail(threading.Thread):
    """Counts oplog events for the namespace through a change stream."""

    def __init__(self, collection):
        super().__init__(daemon=True)
        self.collection = collection
        self.lock = threading.Lock()
        self.counts: Counter = Counter()
        self.lag_ms: list[float] = []          # wallTime(commit) -> received
        self.error: str | None = None
        self.restarts = 0
        self.stop_flag = threading.Event()

    def run(self) -> None:
        resume_token = None
        while not self.stop_flag.is_set():
            try:
                with self.collection.watch(max_await_time_ms=500,
                                           resume_after=resume_token) as stream:
                    while not self.stop_flag.is_set():
                        change = stream.try_next()
                        if change is None:
                            continue
                        resume_token = stream.resume_token
                        now = time.time()
                        with self.lock:
                            self.counts[change["operationType"]] += 1
                            wall = change.get("wallTime")
                            if wall is not None:
                                wall_epoch = wall.replace(tzinfo=timezone.utc).timestamp()
                                self.lag_ms.append((now - wall_epoch) * 1000.0)
            except errors.PyMongoError as exc:
                # Network blips (e.g. access-list changes) - resume from last token
                self.error = str(exc)
                self.restarts += 1
                time.sleep(1)

    def drain(self) -> tuple[dict, list[float]]:
        with self.lock:
            c, l = dict(self.counts), list(self.lag_ms)
            self.counts.clear()
            self.lag_ms.clear()
        return c, l


def _epoch(v) -> float:
    return v.timestamp() if hasattr(v, "timestamp") else float(v)


def replication_lag(client: MongoClient) -> dict:
    """Primary.lastWriteDate - Secondary.lastWriteDate, from SDAM heartbeats."""
    desc = client.topology_description
    primary = next((s for s in desc.server_descriptions().values()
                    if s.server_type_name == "RSPrimary"), None)
    out = {}
    if primary is None or primary.last_write_date is None:
        return out
    for addr, s in desc.server_descriptions().items():
        if s.server_type_name == "RSSecondary" and s.last_write_date:
            lag = _epoch(primary.last_write_date) - _epoch(s.last_write_date)
            out[addr[0].split(".")[0]] = max(0.0, lag)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=0, help="hard stop after N s")
    ap.add_argument("--until-idle", type=float, default=0,
                    help="stop once inserts were 0 for N s (after activity began)")
    ap.add_argument("--uri", default=os.getenv("MONGO_URI", ""))
    ap.add_argument("--out", default="metrics.jsonl", help="file name inside results/")
    args = ap.parse_args()

    client = MongoClient(args.uri, serverSelectionTimeoutMS=15_000,
                         heartbeatFrequencyMS=500, appname="atlas-monitor")
    client.admin.command("ping")
    coll = client[os.getenv("DB_NAME", "event_streaming")][
        os.getenv("COLLECTION_NAME", "sensor_events")]

    RESULTS.mkdir(exist_ok=True)
    out = open(RESULTS / args.out, "w", encoding="utf-8")

    tail = OplogTail(coll)
    tail.start()

    prev = None
    t0 = time.time()
    active_seen = False
    idle_since = None
    print("[monitor] recording -> results/metrics.jsonl")

    try:
        while True:
            loop_start = time.time()
            rec: dict = {"t": round(loop_start - t0, 2), "epoch": loop_start}
            try:
                ss = client.admin.command("serverStatus")
                cur = {
                    "op": ss["opcounters"],
                    "conn": ss["connections"]["current"],
                    "bin": ss["network"]["bytesIn"],
                    "bout": ss["network"]["bytesOut"],
                    "ts": loop_start,
                }
                rec["connections"] = cur["conn"]
                if prev:
                    dt = cur["ts"] - prev["ts"]
                    rec["ops"] = {k: round((cur["op"][k] - prev["op"][k]) / dt, 2)
                                  for k in ("insert", "query", "getmore", "command")}
                    rec["net_in_kbs"] = round((cur["bin"] - prev["bin"]) / dt / 1024, 2)
                    rec["net_out_kbs"] = round((cur["bout"] - prev["bout"]) / dt / 1024, 2)
                prev = cur
            except errors.PyMongoError as exc:
                rec["serverStatus_error"] = str(exc)[:200]

            counts, lags = tail.drain()
            rec["oplog"] = counts
            if lags:
                lags.sort()
                rec["oplog_notify_ms_p50"] = round(lags[len(lags) // 2], 1)
            if tail.error:
                rec["oplog_error"] = tail.error[:200]
            rec["repl_lag_s"] = replication_lag(client)

            out.write(json.dumps(rec) + "\n")
            out.flush()

            ins = counts.get("insert", 0)
            # Activity = oplog inserts OR serverStatus inserts, so a dropped
            # change stream can never end the recording early.
            if ins or rec.get("ops", {}).get("insert", 0) >= 1:
                active_seen, idle_since = True, None
            elif active_seen and "ops" in rec:
                idle_since = idle_since or loop_start

            el = loop_start - t0
            if int(el) % 10 == 0:
                print(f"[monitor] t={el:6.1f}s  oplog inserts/s={ins:4d}  "
                      f"conns={rec.get('connections')}  lag={rec['repl_lag_s']}")
            if args.duration and el >= args.duration:
                break
            if args.until_idle and idle_since and loop_start - idle_since >= args.until_idle:
                break
            time.sleep(max(0.0, 1.0 - (time.time() - loop_start)))
    except KeyboardInterrupt:
        pass
    finally:
        tail.stop_flag.set()
        out.close()
        client.close()
        print("[monitor] stopped")


if __name__ == "__main__":
    main()
