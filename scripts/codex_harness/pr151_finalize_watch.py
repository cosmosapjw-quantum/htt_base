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

import datetime
import json
import subprocess
import time
from pathlib import Path

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
TARGET = Path("/mnt/sn850x2t/htt_base_e2e/workdir/raw/desi_dr1_mocks")
PY = str(REPO / "venv/bin/python")
PHASE = str(REPO / "scripts/codex_harness/pr151_phase.py")
LOG = REPO / "workdir/pr151_finalize_watch.log"
INTERVAL = 300              # 5-minute poll
HEARTBEAT_EVERY = 12        # log a heartbeat once per hour
MAX_WAIT_S = 14 * 24 * 3600  # 14-day safety cap


def log(msg: str) -> None:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="", flush=True)


def progress() -> dict | None:
    r = subprocess.run([PY, "-B", PHASE, "--phase", "progress",
                        "--target", str(TARGET), "--compact"],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def acquire_running() -> bool:
    r = subprocess.run(["pgrep", "-f", "pr151_phase.py --phase acquire"],
                       capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    log("watcher start; read-only polling for PR-151 acquire terminal "
        "(fires finalize once, never touches the acquire writer)")
    start = time.time()
    beat = 0
    while True:
        if time.time() - start > MAX_WAIT_S:
            log("SAFETY CAP reached (14d); exiting WITHOUT finalize")
            return 1
        p = progress()
        if p is None:
            log("progress probe failed; retry in %ds" % INTERVAL)
            time.sleep(INTERVAL)
            continue
        term = p.get("terminal", {})
        if term.get("finalization_complete"):
            log("finalization already complete; nothing to do; exit")
            return 0
        ready = bool(term.get("acquisition_ready"))
        running = acquire_running()

        if ready and not running:
            log("ACQUIRE TERMINAL detected (acquisition_ready=true, acquire "
                "process gone); running `--phase finalize` ONCE")
            r = subprocess.run([PY, "-B", PHASE, "--phase", "finalize",
                                "--target", str(TARGET)],
                               cwd=REPO, capture_output=True, text=True)
            log(f"finalize rc={r.returncode}")
            if r.stdout.strip():
                log("finalize stdout tail: " + r.stdout.strip()[-600:])
            if r.stderr.strip():
                log("finalize stderr tail: " + r.stderr.strip()[-600:])
            done = (progress() or {}).get("terminal", {}).get("finalization_complete")
            if done:
                log("FINALIZE COMPLETE — PR-151 terminal reached. NOTE: the "
                    "downstream science steps (PR-226 DESI-lane close, "
                    "PR-155->158) are a SEPARATE owner/manual step, not this watcher.")
                return 0
            log("finalize did NOT reach complete; leaving for owner inspection")
            return r.returncode or 6

        if not running and not ready:
            log("ANOMALY: acquire process is gone but acquisition_ready=false "
                "(acquire may have failed or died). NOT finalizing. Owner "
                "inspection required; exiting.")
            return 2

        beat += 1
        if beat % HEARTBEAT_EVERY == 1:
            counts = p.get("counts") or p.get("progress") or {}
            log(f"waiting: acquisition_ready={ready} acquire_running={running} "
                f"counts={json.dumps(counts, sort_keys=True)[:200]}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
