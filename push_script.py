"""
push_script.py
==============
Generates a document with 20 variables and pushes it to MongoDB Atlas.
Designed to run in 20 concurrent sessions simultaneously.

Usage:
    python push_script.py --session-id 1 --total 1000 --interval 0.5
"""

import argparse
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

console = Console(legacy_windows=False)

# ---------------------------------------------------------------------------
# 20-variable document generator
# ---------------------------------------------------------------------------

DEVICE_TYPES  = ["sensor", "gateway", "edge_node", "controller", "actuator"]
REGIONS       = ["us-east-1", "eu-west-1", "ap-south-1", "us-west-2", "sa-east-1"]
STATUS_VALUES = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]
PROTOCOLS     = ["MQTT", "CoAP", "HTTP", "WebSocket", "AMQP"]


def generate_document(session_id: int, sequence: int) -> dict:
    """
    Builds a document with exactly 20 payload variables plus metadata.

    Variables
    ---------
    1.  session_id        – which of the 20 parallel sessions produced this doc
    2.  sequence          – monotonically increasing counter per session
    3.  device_id         – unique device identifier (UUID)
    4.  device_type       – category of IoT device
    5.  region            – geographic region of the device
    6.  temperature       – simulated temperature reading (°C)
    7.  humidity          – relative humidity (%)
    8.  pressure          – atmospheric pressure (hPa)
    9.  voltage           – supply voltage (V)
    10. current           – electrical current draw (A)
    11. cpu_usage         – CPU utilisation (%)
    12. memory_usage      – RAM utilisation (%)
    13. disk_usage        – Disk utilisation (%)
    14. packet_loss       – network packet loss rate (%)
    15. latency_ms        – round-trip latency (ms)
    16. signal_strength   – RSSI dBm value
    17. error_code        – simulated error/status code
    18. protocol          – communication protocol used
    19. payload_size_kb   – size of the outgoing payload (KB)
    20. status            – operational status of the device
    """
    now = datetime.now(tz=timezone.utc)
    return {
        # --- metadata ---
        "event_id":        str(uuid.uuid4()),
        "timestamp":       now,
        "pushed_at_epoch": now.timestamp(),

        # --- 20 payload variables ---
        "session_id":      session_id,                               # var 1
        "sequence":        sequence,                                 # var 2
        "device_id":       f"dev-{session_id:02d}-{sequence:06d}",  # var 3
        "device_type":     random.choice(DEVICE_TYPES),             # var 4
        "region":          random.choice(REGIONS),                  # var 5
        "temperature":     round(random.uniform(-10.0, 85.0), 2),   # var 6
        "humidity":        round(random.uniform(10.0, 100.0), 2),   # var 7
        "pressure":        round(random.uniform(950.0, 1050.0), 2), # var 8
        "voltage":         round(random.uniform(3.0, 5.0), 3),      # var 9
        "current":         round(random.uniform(0.05, 2.5), 3),     # var 10
        "cpu_usage":       round(random.uniform(0.0, 100.0), 1),    # var 11
        "memory_usage":    round(random.uniform(0.0, 100.0), 1),    # var 12
        "disk_usage":      round(random.uniform(0.0, 100.0), 1),    # var 13
        "packet_loss":     round(random.uniform(0.0, 10.0), 2),     # var 14
        "latency_ms":      round(random.uniform(1.0, 500.0), 1),    # var 15
        "signal_strength": random.randint(-100, -30),               # var 16
        "error_code":      random.choice([0, 0, 0, 1, 2, 3, 404,   # var 17
                                          500, 503]),
        "protocol":        random.choice(PROTOCOLS),                 # var 18
        "payload_size_kb": round(random.uniform(0.1, 64.0), 2),     # var 19
        "status":          random.choices(                           # var 20
                               STATUS_VALUES,
                               weights=[70, 15, 10, 5]
                           )[0],
    }


# ---------------------------------------------------------------------------
# Main push loop
# ---------------------------------------------------------------------------

def run_push(collection: Collection, session_id: int,
             total: int, interval: float) -> None:
    """Push `total` documents to MongoDB, sleeping `interval` seconds between each."""

    stats = {"success": 0, "failed": 0, "start": time.time()}
    latencies_ms: list[float] = []

    console.rule(f"[bold cyan]Session {session_id:02d} — Push started[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("OK {task.fields[ok]}  FAIL {task.fields[fail]}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task(
            f"[green]Session {session_id:02d}",
            total=total,
            ok=0,
            fail=0,
        )

        for seq in range(1, total + 1):
            doc = generate_document(session_id, seq)
            try:
                t_ins = time.perf_counter()
                collection.insert_one(doc)
                latencies_ms.append((time.perf_counter() - t_ins) * 1000.0)
                stats["success"] += 1
            except errors.PyMongoError as exc:
                stats["failed"] += 1
                console.log(f"[red]Session {session_id:02d} | seq {seq} | ERROR: {exc}[/]")

            progress.update(task, advance=1,
                            ok=stats["success"], fail=stats["failed"])

            if interval > 0:
                time.sleep(interval)

    elapsed = time.time() - stats["start"]
    rate    = stats["success"] / elapsed if elapsed > 0 else 0

    # Summary table
    table = Table(title=f"Session {session_id:02d} — Summary", show_header=True)
    table.add_column("Metric",  style="bold")
    table.add_column("Value",   style="cyan")
    table.add_row("Total pushed",    str(total))
    table.add_row("Successful inserts", str(stats["success"]))
    table.add_row("Failed inserts",  str(stats["failed"]))
    table.add_row("Elapsed time",    f"{elapsed:.2f} s")
    table.add_row("Insert rate",     f"{rate:.2f} docs/s")
    console.print(table)

    # Machine-readable summary for the simulation report
    lat = sorted(latencies_ms)
    pct = lambda q: round(lat[min(len(lat) - 1, int(q * len(lat)))], 2) if lat else None
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    with open(results_dir / f"session_{session_id:02d}.json", "w", encoding="utf-8") as fh:
        json.dump({
            "session_id": session_id,
            "total": total,
            "success": stats["success"],
            "failed": stats["failed"],
            "start_epoch": stats["start"],
            "elapsed_s": round(elapsed, 3),
            "rate_docs_s": round(rate, 3),
            "insert_ms": {"min": pct(0), "p50": pct(0.50), "p95": pct(0.95),
                          "p99": pct(0.99), "max": pct(1.0),
                          "mean": round(sum(lat) / len(lat), 2) if lat else None},
        }, fh, indent=2)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="MongoDB Atlas Push Script")
    parser.add_argument("--session-id", type=int,
                        default=int(os.getenv("SESSION_ID", "1")),
                        help="Session identifier (1-20)")
    parser.add_argument("--total", type=int,
                        default=int(os.getenv("TOTAL_RECORDS", "1000")),
                        help="Total documents to push")
    parser.add_argument("--interval", type=float,
                        default=float(os.getenv("PUSH_INTERVAL", "0.1")),
                        help="Sleep seconds between inserts (0 = no sleep)")
    parser.add_argument("--uri", type=str,
                        default=os.getenv("MONGO_URI", ""),
                        help="MongoDB Atlas URI (overrides .env)")
    args = parser.parse_args()

    if not args.uri:
        console.print("[bold red]ERROR:[/] MONGO_URI not set. "
                      "Copy .env.example to .env and fill in your Atlas credentials.")
        sys.exit(1)

    console.print(f"[bold]Connecting to Atlas...[/]  session_id={args.session_id}")
    client = MongoClient(args.uri, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
        console.print("[bold green][OK] Connected to MongoDB Atlas[/]")
    except errors.ServerSelectionTimeoutError as exc:
        console.print(f"[bold red][FAIL] Connection failed:[/] {exc}")
        sys.exit(1)

    db         = client[os.getenv("DB_NAME", "event_streaming")]
    collection = db[os.getenv("COLLECTION_NAME", "sensor_events")]

    # Create indexes once (safe if multiple sessions race on initial startup)
    if args.session_id == 1:
        try:
            collection.create_index([("session_id", 1), ("sequence", 1)])
            collection.create_index([("timestamp", -1)])
            collection.create_index([("status", 1)])
        except errors.PyMongoError as exc:
            console.log(f"[yellow]Index setup note: {exc}[/]")

    run_push(collection, args.session_id, args.total, args.interval)
    client.close()


if __name__ == "__main__":
    main()
