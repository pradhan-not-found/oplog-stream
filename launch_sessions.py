"""
launch_sessions.py
==================
Spawns 20 concurrent push_script.py processes — one per session — using
Python's subprocess module. Each session gets its own Windows terminal
(or runs headless if --no-window is passed).

Usage:
    python launch_sessions.py                   # 20 sessions, new windows
    python launch_sessions.py --sessions 5      # only 5 sessions
    python launch_sessions.py --no-window       # headless (logs to files)
    python launch_sessions.py --total 500       # 500 docs per session
    python launch_sessions.py --interval 0.2    # 0.2 s between inserts
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console(legacy_windows=False)
LOG_DIR = Path(__file__).parent / "logs"


def launch_sessions(
    num_sessions: int,
    total: int,
    interval: float,
    new_window: bool,
    uri: str,
) -> list[subprocess.Popen]:
    LOG_DIR.mkdir(exist_ok=True)
    processes: list[subprocess.Popen] = []

    console.rule("[bold cyan]Launching push sessions[/]")

    for sid in range(1, num_sessions + 1):
        cmd = [
            sys.executable, "push_script.py",
            "--session-id", str(sid),
            "--total",      str(total),
            "--interval",   str(interval),
            "--uri",        uri,
        ]

        log_file = LOG_DIR / f"session_{sid:02d}.log"

        if new_window and sys.platform == "win32":
            # Open each session in its own Windows console window
            proc = subprocess.Popen(
                ["cmd", "/c", "start", f"Session-{sid:02d}",
                 "cmd", "/k", " ".join(cmd)],
                cwd=str(Path(__file__).parent),
                env={**os.environ, "SESSION_ID": str(sid), "PYTHONIOENCODING": "utf-8"},
            )
        else:
            # Headless: stdout + stderr -> individual log files
            log_fh = open(log_file, "w", encoding="utf-8")
            proc = subprocess.Popen(
                cmd,
                cwd=str(Path(__file__).parent),
                stdout=log_fh,
                stderr=log_fh,
                env={**os.environ, "SESSION_ID": str(sid), "PYTHONIOENCODING": "utf-8"},
            )
            console.print(f"  [green]Session {sid:02d}[/] PID={proc.pid}  -> {log_file}")

        processes.append(proc)
        time.sleep(0.05)   # slight stagger to avoid thundering-herd on Atlas

    console.print(f"\n[bold][OK] {len(processes)} sessions launched.[/]\n")
    return processes


def wait_for_all(processes: list[subprocess.Popen]) -> None:
    console.print("[dim]Waiting for all sessions to finish …[/]")
    for proc in processes:
        proc.wait()

    table = Table(title="Session Exit Codes", show_header=True)
    table.add_column("Session", justify="center")
    table.add_column("PID",     justify="right")
    table.add_column("Exit",    justify="center")

    for idx, proc in enumerate(processes, start=1):
        code  = proc.returncode
        style = "green" if code == 0 else "red"
        table.add_row(str(idx), str(proc.pid), f"[{style}]{code}[/]")

    console.print(table)
    console.print("[bold green]All sessions finished.[/]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch 20 push sessions")
    parser.add_argument("--sessions",   type=int,   default=20)
    parser.add_argument("--total",      type=int,   default=1000,
                        help="Docs per session")
    parser.add_argument("--interval",   type=float, default=0.1,
                        help="Seconds between inserts per session")
    parser.add_argument("--no-window",  action="store_true",
                        help="Run headless (log to files instead of new windows)")
    parser.add_argument("--uri",        type=str,
                        default=os.getenv("MONGO_URI", ""),
                        help="Atlas URI (overrides .env)")
    args = parser.parse_args()

    if not args.uri:
        # Try loading from .env
        from dotenv import load_dotenv
        load_dotenv()
        args.uri = os.getenv("MONGO_URI", "")

    if not args.uri:
        console.print("[bold red]ERROR:[/] MONGO_URI not set.")
        sys.exit(1)

    new_window = not args.no_window

    console.print(f"[bold]Config:[/] sessions={args.sessions}  "
                  f"docs/session={args.total}  "
                  f"interval={args.interval}s  "
                  f"new_window={new_window}")
    console.print(f"[bold]Total documents that will be inserted:[/] "
                  f"[cyan]{args.sessions * args.total:,}[/]\n")

    procs = launch_sessions(
        num_sessions=args.sessions,
        total=args.total,
        interval=args.interval,
        new_window=new_window,
        uri=args.uri,
    )

    if not new_window:
        # In headless mode we can wait and show exit codes
        wait_for_all(procs)
    else:
        console.print("[dim]Sessions running in separate windows. "
                      "Close windows or press Ctrl+C here to stop.[/]")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]Launcher stopped.[/]")


if __name__ == "__main__":
    main()
