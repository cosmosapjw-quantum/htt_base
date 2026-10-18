"""Charge one finite-fixture test command to the shared 600-second budget."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "SCIENTIFIC_BUDGET.jsonl"
records = [json.loads(line) for line in LEDGER.read_text().splitlines()] if LEDGER.exists() else []
if records and records[-1]["event"] != "END":
    raise SystemExit("HOLD: prior launched budget unit lacks completion; reconcile before continuation")
used = sum(row["elapsed_s"] for row in records if row["event"] == "END")
remaining = 600.-used
if remaining <= 0:
    raise SystemExit("Scientific 600-second cumulative limit reached")
command = [sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_sdss_estimator.py", "-v"]
run_id = str(time.time_ns())


def record(row):
    with LEDGER.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True)+"\n")


record({"event": "START", "run_id": run_id, "phase": "PURE_FINITE_FIXTURES_NOT_MOCK_CAMPAIGN",
        "command": command, "prior_cumulative_s": used, "remaining_s": remaining,
        "requested_model": "gpt-6.1-sol", "requested_effort": "high", "observed_model": "UNKNOWN"})
started = time.monotonic()
exit_code = 1
try:
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=remaining)
    exit_code = result.returncode
    output = result.stdout+result.stderr
except subprocess.TimeoutExpired as error:
    output = repr(error)
    exit_code = 124
finally:
    elapsed = time.monotonic()-started
    record({"event": "END", "run_id": run_id, "phase": "PURE_FINITE_FIXTURES_NOT_MOCK_CAMPAIGN",
            "elapsed_s": elapsed, "cumulative_s": used+elapsed, "exit_code": exit_code})
with (HERE / f"MATH_TESTS_{run_id}.txt").open("x") as stream:
    stream.write(output)
print(output)
print(f"Charged {elapsed:.6f}s; cumulative {used+elapsed:.6f}/600s")
raise SystemExit(exit_code)
