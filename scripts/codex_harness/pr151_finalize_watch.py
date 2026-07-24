#!/usr/bin/env python3
"""PR-151 auto-finalize watcher: poll for the acquire terminal, then run finalize ONCE.

Safety contract (this watcher NEVER writes to the acquisition target):
  * read-only `--phase progress` polling until the terminal is reached;
  * fires `--phase finalize` only when BOTH the acquire process has exited AND
    `acquisition_ready` is true -- so it never runs concurrently with acquire;
  * even if that gate were wrong, the phase writer_lock is a non-blocking flock
    that makes a concurrent finalize fail cleanly (rc 4) rather than second-write;
  * it never touches .part files, never restarts acquire, never deletes anything;
  * idempotent: exits immediately if finalization is already complete;
  * if the acquire process is gone but acquisition_ready is false (acquire failed
    or died), it does NOT finalize -- it flags the anomaly for owner inspection.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

try:  # package import in tests
    from .pr151_progress import DEFAULT_LOG as DEFAULT_PROGRESS_LOG, DEFAULT_TARGET
except ImportError:  # direct script execution
    from pr151_progress import DEFAULT_LOG as DEFAULT_PROGRESS_LOG, DEFAULT_TARGET

REPO = Path(__file__).resolve().parents[2]
PY = sys.executable
PHASE = str(REPO / "scripts/codex_harness/pr151_phase.py")
DEFAULT_LOG = REPO / "workdir/pr151_finalize_watch.log"
INTERVAL = 300              # 5-minute poll
HEARTBEAT_EVERY = 12        # log a heartbeat once per hour
MAX_WAIT_S = 14 * 24 * 3600  # 14-day safety cap


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--progress-log", type=Path, default=DEFAULT_PROGRESS_LOG)
    parser.add_argument("--interval", type=int, default=INTERVAL)
    parser.add_argument("--max-wait-seconds", type=int, default=MAX_WAIT_S)
    return parser.parse_args(argv)


def log(msg: str, log_path: Path) -> None:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}\n"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="", flush=True)


def progress(target: Path, progress_log: Path) -> dict | None:
    r = subprocess.run([PY, "-B", PHASE, "--phase", "progress",
                        "--target", str(target), "--log", str(progress_log),
                        "--compact"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def acquire_running(target: Path) -> bool:
    r = subprocess.run(["pgrep", "-af", "pr151_phase.py --phase acquire"],
                       capture_output=True, text=True)
    return r.returncode == 0 and str(target) in r.stdout


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.target.expanduser().resolve()
    log_path = args.log.expanduser().resolve()
    progress_log = args.progress_log.expanduser().resolve()
    if args.interval <= 0 or args.max_wait_seconds <= 0:
        raise SystemExit("interval and max-wait-seconds must be positive")

    def write_log(message: str) -> None:
        log(message, log_path)

    write_log("watcher start; read-only polling for PR-151 acquire terminal "
              "(fires finalize once, never touches the acquire writer)")
    start = time.time()
    beat = 0
    while True:
        if time.time() - start > args.max_wait_seconds:
            write_log("SAFETY CAP reached; exiting WITHOUT finalize")
            return 1
        p = progress(target, progress_log)
        if p is None:
            write_log("progress probe failed; retry in %ds" % args.interval)
            time.sleep(args.interval)
            continue
        term = p.get("terminal", {})
        if term.get("finalization_complete"):
            write_log("finalization already complete; nothing to do; exit")
            return 0
        ready = bool(term.get("acquisition_ready"))
        running = acquire_running(target)

        if ready and not running:
            write_log("ACQUIRE TERMINAL detected (acquisition_ready=true, "
                      "acquire process gone); running `--phase finalize` ONCE")
            r = subprocess.run([PY, "-B", PHASE, "--phase", "finalize",
                                "--target", str(target)],
                               cwd=REPO, capture_output=True, text=True)
            write_log(f"finalize rc={r.returncode}")
            if r.stdout.strip():
                write_log("finalize stdout tail: " + r.stdout.strip()[-600:])
            if r.stderr.strip():
                write_log("finalize stderr tail: " + r.stderr.strip()[-600:])
            done = (progress(target, progress_log) or {}).get(
                "terminal", {}).get("finalization_complete")
            if done:
                write_log(
                    "FINALIZE COMPLETE — PR-151 terminal reached. NOTE: the "
                    "downstream science steps (PR-226 DESI-lane close, "
                    "PR-155->158) are a SEPARATE owner/manual step, not this "
                    "watcher.")
                return 0
            write_log(
                "finalize did NOT reach complete; leaving for owner inspection")
            return r.returncode or 6

        if not running and not ready:
            write_log(
                "ANOMALY: acquire process is gone but acquisition_ready=false "
                "(acquire may have failed or died). NOT finalizing. Owner "
                "inspection required; exiting.")
            return 2

        beat += 1
        if beat % HEARTBEAT_EVERY == 1:
            counts = p.get("counts") or p.get("progress") or {}
            write_log(
                f"waiting: acquisition_ready={ready} acquire_running={running} "
                f"counts={json.dumps(counts, sort_keys=True)[:200]}")
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
