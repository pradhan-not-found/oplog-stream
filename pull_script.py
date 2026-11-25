"""
pull_script.py
==============
Continuously polls MongoDB Atlas for new documents and prints live statistics.
Run this in a SEPARATE environment / terminal while push_script.py sessions run.

Usage:
    python pull_script.py --batch 100 --interval 1.0
"""

import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING, errors
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_stats_panel(stats: dict, seen: int) -> Panel:
    """Render a live stats panel."""

    # --- Per-session table ---
    s_table = Table(title="Per-Session Counts", show_header=True, expand=True)
    s_table.add_column("Session", style="cyan", justify="center")
    s_table.add_column("Docs Seen", justify="right")
    for sid in sorted(stats["per_session"].keys()):
        s_table.add_row(str(sid), str(stats["per_session"][sid]))

    # --- Status breakdown ---
    status_table = Table(title="Status Distribution", show_header=True, expand=True)
    status_table.add_column("Status", style="bold")
    status_table.add_column("Count",  justify="right")
    color_map = {"OK": "green", "WARNING": "yellow",
                 "CRITICAL": "red", "UNKNOWN": "white"}
    for status, count in sorted(stats["status_counts"].items()):
        col = color_map.get(status, "white")
        status_table.add_row(f"[{col}]{status}[/]", str(count))

    # --- Aggregates ---
    agg_table = Table(title="Aggregates", show_header=True, expand=True)
    agg_table.add_column("Metric",  style="bold")
    agg_table.add_column("Value",   style="cyan")
    total = stats["total"]
    elapsed = time.time() - stats["start_time"]
    rate = total / elapsed if elapsed > 0 else 0
    agg_table.add_row("Total docs pulled",   str(total))
    agg_table.add_row("Avg temperature (°C)", f"{stats['avg_temp']:.2f}" if total else "—")
    agg_table.add_row("Avg latency (ms)",     f"{stats['avg_lat']:.2f}"  if total else "—")
    agg_table.add_row("Avg CPU usage (%)",    f"{stats['avg_cpu']:.2f}"  if total else "—")
    agg_table.add_row("Pull rate",            f"{rate:.2f} docs/s")
    agg_table.add_row("Active sessions",      str(len(stats["per_session"])))

    return Panel(
        Columns([s_table, status_table, agg_table], equal=True, expand=True),
        title=f"[bold cyan]MongoDB Atlas — Live Pull Dashboard[/]  "
              f"[dim]{datetime.now().strftime('%H:%M:%S')}[/]",
        border_style="bright_blue",
    )


# ---------------------------------------------------------------------------
# Main pull loop — tail-style using a bookmark cursor
# ---------------------------------------------------------------------------

def run_pull(collection, batch_size: int, interval: float) -> None:
    """
    Uses a 'last seen _id' bookmark to fetch only NEW documents
    each polling cycle — mimicking a Change-Stream tail without
    requiring a replica-set change stream (works on Atlas free tier too).
    """

    console.print("[bold]Starting live pull …[/]  Press Ctrl+C to stop.\n")

    # Determine starting point: ignore docs already in the collection
    latest = collection.find_one(sort=[("_id", DESCENDING)])
    bookmark = latest["_id"] if latest else None

    stats: dict = {
        "total":        0,
        "per_session":  defaultdict(int),
        "status_counts": Counter(),
        "avg_temp":     0.0,
        "avg_lat":      0.0,
        "avg_cpu":      0.0,
        "start_time":   time.time(),
    }
    seen = 0  # running count for running averages

    with Live(build_stats_panel(stats, seen), console=console,
              refresh_per_second=2, screen=False) as live:
        try:
            while True:
                query = {"_id": {"$gt": bookmark}} if bookmark else {}
                cursor = (
                    collection
                    .find(query)
                    .sort("_id", 1)
                    .limit(batch_size)
                )
                docs = list(cursor)

                if docs:
                    bookmark = docs[-1]["_id"]
                    for doc in docs:
                        seen += 1
                        stats["total"] += 1
                        stats["per_session"][doc.get("session_id", "?")] += 1
                        stats["status_counts"][doc.get("status", "UNKNOWN")] += 1

                        # Running averages (Welford-style)
                        delta_t = doc.get("temperature", 0) - stats["avg_temp"]
                        stats["avg_temp"] += delta_t / seen
                        delta_l = doc.get("latency_ms", 0) - stats["avg_lat"]
                        stats["avg_lat"] += delta_l / seen
                        delta_c = doc.get("cpu_usage", 0) - stats["avg_cpu"]
                        stats["avg_cpu"] += delta_c / seen

                    live.update(build_stats_panel(stats, seen))

                time.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Pull stopped by user.[/]")


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="MongoDB Atlas Pull Script")
    parser.add_argument("--batch",    type=int,   default=int(os.getenv("PULL_BATCH_SIZE", "100")))
    parser.add_argument("--interval", type=float, default=float(os.getenv("PULL_INTERVAL", "1.0")))
    parser.add_argument("--uri",      type=str,   default=os.getenv("MONGO_URI", ""))
    args = parser.parse_args()

    if not args.uri:
        console.print("[bold red]ERROR:[/] MONGO_URI not set.")
        sys.exit(1)

    client = MongoClient(args.uri, serverSelectionTimeoutMS=10_000)
    try:
        client.admin.command("ping")
        console.print("[bold green]✔ Connected to MongoDB Atlas[/]")
    except errors.ServerSelectionTimeoutError as exc:
        console.print(f"[bold red]✘ Connection failed:[/] {exc}")
        sys.exit(1)

    db         = client[os.getenv("DB_NAME", "event_streaming")]
    collection = db[os.getenv("COLLECTION_NAME", "sensor_events")]

    run_pull(collection, args.batch, args.interval)
    client.close()


if __name__ == "__main__":
    main()
