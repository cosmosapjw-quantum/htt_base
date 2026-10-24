#!/usr/bin/env python3
"""One actual bounded invocation: controls, consumer, render, durable receipt.

The controller's API whole-call wall is also required for final charging; use
max(API whole wall, this outer monotonic wall) and count every started attempt.
"""
import time
OUTER_START_NS = time.monotonic_ns()  # Before the child imports anything.

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PYTHON = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python")
LIMIT_SECONDS = 120.0
CHILD_LIMIT_SECONDS = 114.0  # Reserve six seconds for durable closeout.
RSS_LIMIT_BYTES = 2 * 1024**3
STARTABLE = ("test_controls.py", "consume.py")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rss(pid):
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (FileNotFoundError, ProcessLookupError):
        return 0
    return 0


def fsync_file(path):
    if path.is_file():
        with path.open("rb") as f:
            os.fsync(f.fileno())


def main():
    actual = HERE / "actual_run"
    if actual.exists():
        raise RuntimeError(f"CREATE_ONLY_ACTUAL_RUN_EXISTS {actual}")
    actual.mkdir()
    if not PYTHON.is_file():
        raise RuntimeError(f"OFFICIAL_VENV_PYTHON_MISSING {PYTHON}")
    env = dict(os.environ)
    for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
                 "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Repo root is explicit; consume.py imports each sealed source by its absolute path.
    env["PYTHONPATH"] = "/home/cosmosapjw/Dropbox/bianchi/htt_base"
    receipt = {"schema": "htt.cf4_support_quotient_actual_invocation/1",
               "status": "STARTED", "requested_worker": "gpt-6-sol/high",
               "observed_worker": "UNKNOWN", "all_started_commands": [],
               "source_sha256": {p: sha(HERE / p) for p in ("consume.py", "test_controls.py", "runner.py", "INPUT.json")},
               "clock": "time.monotonic_ns on outer Python; controller API whole-wall remains separate",
               "limit_seconds": LIMIT_SECONDS, "child_limit_seconds": CHILD_LIMIT_SECONDS,
               "rss_limit_bytes": RSS_LIMIT_BYTES}
    try:
        for script in STARTABLE:
            left = CHILD_LIMIT_SECONDS - (time.monotonic_ns() - OUTER_START_NS) / 1e9
            if left <= 0:
                receipt["status"] = "TIME_LIMIT_BEFORE_CHILD"
                break
            name = script.removesuffix(".py")
            stdout_path, stderr_path = actual / f"{name}.stdout", actual / f"{name}.stderr"
            started = time.monotonic_ns()
            entry = {"argv": [str(PYTHON), "-B", str(HERE / script)],
                     "stdout": str(stdout_path), "stderr": str(stderr_path)}
            receipt["all_started_commands"].append(entry)
            with stdout_path.open("xb") as out, stderr_path.open("xb") as err:
                child = subprocess.Popen(entry["argv"], cwd=HERE, env=env, stdout=out, stderr=err)
                peak = 0
                reason = None
                while child.poll() is None:
                    peak = max(peak, rss(child.pid))
                    elapsed = (time.monotonic_ns() - OUTER_START_NS) / 1e9
                    if peak > RSS_LIMIT_BYTES:
                        reason = "RSS_LIMIT_EXCEEDED"
                        child.kill()
                        break
                    if elapsed > CHILD_LIMIT_SECONDS:
                        reason = "CHILD_TIME_LIMIT"
                        child.kill()
                        break
                    time.sleep(.05)
                code = child.wait()  # Exit and reap before claiming a result.
                out.flush(); err.flush()
                os.fsync(out.fileno()); os.fsync(err.fileno())
            entry.update({"returncode": code, "reason": reason,
                          "observed_monotonic_seconds": (time.monotonic_ns() - started) / 1e9,
                          "peak_polled_rss_bytes": peak})
            if code != 0 or reason:
                receipt["status"] = reason or "FIRST_CHILD_FAILURE"
                break
        else:
            receipt["status"] = "CHILDREN_EXITED_ZERO"
        for path in actual.rglob("*"):
            fsync_file(path)
        directory_fd = os.open(actual, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception as exc:
        receipt["status"] = "OUTER_RUNNER_FAILURE"
        receipt["exception"] = repr(exc)
    receipt["observed_monotonic_through_products_fsync_seconds"] = (time.monotonic_ns() - OUTER_START_NS) / 1e9
    receipt["charge_rule"] = "max(controller API whole invocation wall, observed outer monotonic wall); no attempt omitted"
    receipt_path = actual / "WHOLE_COMMAND_RECEIPT.json"
    with receipt_path.open("x") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    final_wall = (time.monotonic_ns() - OUTER_START_NS) / 1e9
    print(json.dumps({"status": receipt["status"], "raw_receipt": str(receipt_path),
                      "outer_monotonic_after_receipt_fsync_seconds": final_wall}), flush=True)
    if final_wall > LIMIT_SECONDS:
        return 124
    return 0 if receipt["status"] == "CHILDREN_EXITED_ZERO" else 1


if __name__ == "__main__":
    sys.exit(main())
