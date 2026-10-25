#!/usr/bin/env python3
"""Append-only charged subprocess launch with wall guard and reaping."""
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "CONTINUED_BUDGET.jsonl"
CAP = 600.0
BASE = 41.02750632702373


def append(event):
    with LEDGER.open("a") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def main():
    label, script = sys.argv[1:3]
    events = [json.loads(line) for line in LEDGER.read_text().splitlines()] if LEDGER.exists() else []
    starts = [x for x in events if x["event"] == "START"]
    ends = [x for x in events if x["event"] == "END"]
    if len(starts) != len(ends):
        raise SystemExit("UNREAPED_OR_UNCHARGED_PRIOR_START")
    used = BASE + sum(x["elapsed_s"] for x in ends)
    remaining = CAP-used
    if remaining <= 0:
        raise SystemExit("CUMULATIVE_CAP_EXHAUSTED")
    limit = min(remaining, 550.0)
    cmd = ["/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python", "-B", str(HERE / script)]
    env = dict(os.environ)
    env.update({"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"})
    run_id = str(time.time_ns())
    out = HERE / f"{label}_{run_id}.stdout"
    err = HERE / f"{label}_{run_id}.stderr"
    wall0 = time.monotonic()
    with out.open("wb") as fo, err.open("wb") as fe:
        p = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=fo, stderr=fe, start_new_session=True)
        append({"event": "START", "run_id": run_id, "phase": label, "pid": p.pid,
                "utc": datetime.now(timezone.utc).isoformat(), "command": cmd,
                "script_sha256": hashlib.sha256((HERE / script).read_bytes()).hexdigest(),
                "prior_cumulative_s": used, "remaining_s": remaining, "wall_timeout_s": limit,
                "requested_runtime": "gpt-6-sol/high", "observed_runtime": "UNKNOWN"})
        timed_out = False
        try:
            rc = p.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            timed_out = True
            p.kill()
            rc = p.wait()
    elapsed = time.monotonic()-wall0
    hwm = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    append({"event": "END", "run_id": run_id, "phase": label, "elapsed_s": elapsed,
            "cumulative_s": used+elapsed, "exit_code": rc, "timed_out": timed_out,
            "pid": p.pid, "reaped": True, "child_peak_RSS_kB": hwm,
            "stdout": str(out), "stderr": str(err),
            "stdout_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "stderr_sha256": hashlib.sha256(err.read_bytes()).hexdigest()})
    print(json.dumps({"phase": label, "exit_code": rc, "elapsed_s": elapsed,
                      "cumulative_s": used+elapsed, "remaining_s": CAP-used-elapsed,
                      "timed_out": timed_out, "stdout": str(out), "stderr": str(err)}, indent=2))
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
