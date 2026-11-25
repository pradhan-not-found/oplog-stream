"""
oplog_replay.py
===============
Re-reads the oplog for the test window after the run.

Opens a change stream with startAtOperationTime = run start, which makes the
server replay every oplog entry for the namespace from local.oplog.rs, and
buckets the entries by their cluster time (second resolution).

Output: results/oplog_replay.json
Usage:  python oplog_replay.py            (window taken from results/metrics.jsonl)
"""
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from bson.timestamp import Timestamp
from dotenv import load_dotenv
from pymongo import MongoClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()
RES = Path(__file__).parent / "results"


def main() -> None:
    rows = sorted((json.loads(line) for f in RES.glob("metrics*.jsonl")
                   for line in f.read_text(encoding="utf-8").splitlines() if line.strip()),
                  key=lambda r: r["epoch"])
    first, last = rows[0], rows[-1]
    start_epoch, end_epoch = int(first["epoch"]), int(last["epoch"]) + 1
    t0 = first["epoch"]

    client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=15_000)
    coll = client[os.getenv("DB_NAME", "event_streaming")][
        os.getenv("COLLECTION_NAME", "sensor_events")]

    per_sec: Counter = Counter()
    ops: Counter = Counter()
    sessions: Counter = Counter()
    started = time.time()
    with coll.watch(start_at_operation_time=Timestamp(start_epoch, 0),
                    max_await_time_ms=1000, batch_size=1000) as stream:
        idle = 0
        while True:
            ch = stream.try_next()
            if ch is None:
                idle += 1
                if idle >= 3:
                    break
                continue
            idle = 0
            ct = ch["clusterTime"].time
            if ct > end_epoch:
                break
            ops[ch["operationType"]] += 1
            if ch["operationType"] == "insert":
                per_sec[ct] += 1
                sessions[ch["fullDocument"].get("session_id")] += 1

    series = [{"t": round(s - t0, 2), "inserts": per_sec.get(s, 0)}
              for s in range(start_epoch, end_epoch + 1)]
    out = {"source": "change stream replay of local.oplog.rs (startAtOperationTime)",
           "window_epoch": [start_epoch, end_epoch], "op_counts": dict(ops),
           "inserts_per_session": {str(k): v for k, v in sorted(sessions.items(), key=lambda kv: str(kv[0]))},
           "per_second": series, "replay_seconds": round(time.time() - started, 1)}
    (RES / "oplog_replay.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"[OK] replayed {sum(ops.values()):,} oplog entries {dict(ops)} "
          f"in {out['replay_seconds']} s -> results/oplog_replay.json")
    client.close()


if __name__ == "__main__":
    main()
