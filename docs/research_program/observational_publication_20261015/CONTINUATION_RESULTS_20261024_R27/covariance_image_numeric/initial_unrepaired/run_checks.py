"""One bounded GO-only execution; preparation must not invoke this file."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
PREPARATION = HERE / "PREPARATION.json"
ACK = HERE / "ACK.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_mib(pid: int) -> float:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    except FileNotFoundError:
        return 0.0
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ack-file", type=Path, required=True)
    args = parser.parse_args()
    if args.ack_file.resolve() != ACK.resolve():
        raise SystemExit("ACK path differs from the frozen command")
    prep = json.loads(PREPARATION.read_text())
    ack = json.loads(ACK.read_text())
    required = ("task_id", "decision", "worker_output_dir", "controller_packet_id",
                "controller_ack_id", "allocation_ref", "max_wall_seconds",
                "cumulative_wall_seconds_before", "max_rss_mib", "source_sha256")
    if any(key not in ack for key in required):
        raise SystemExit("HOLD: incomplete controller ACK")
    if ack["decision"] != "GO" or ack["task_id"] != prep["task_id"]:
        raise SystemExit("HOLD: no matching GO")
    if Path(ack["worker_output_dir"]).resolve() != HERE:
        raise SystemExit("HOLD: output directory mismatch")
    if not all(isinstance(ack[key], str) and ack[key] for key in
               ("controller_packet_id", "controller_ack_id", "allocation_ref")):
        raise SystemExit("HOLD: missing dispatch/accounting identity")
    if ack["source_sha256"] != prep["source_sha256"]:
        raise SystemExit("HOLD: source seal mismatch")
    for file_name, expected in prep["source_sha256"].items():
        path = Path(file_name)
        if digest(path) != expected:
            raise SystemExit(f"HOLD: input/source hash mismatch: {path}")
    available = min(float(ack["max_wall_seconds"]),
                    60.0 - float(ack["cumulative_wall_seconds_before"]))
    memory_cap = min(float(ack["max_rss_mib"]), 512.0)
    if available <= 0 or memory_cap <= 0:
        raise SystemExit("HOLD: cumulative check budget exhausted")
    if (HERE / "RAW_RECEIPT.json").exists():
        raise SystemExit("HOLD: receipt already exists; preserve first outcome")
    env = os.environ.copy()
    for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    command = [sys.executable, "-m", "unittest", "-v", "test_covariance_image"]
    start = time.monotonic()
    peak = 0.0
    stop_reason = None
    with (HERE / "RAW_STDOUT.txt").open("wb") as stdout, (HERE / "RAW_STDERR.txt").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=HERE, env=env, stdout=stdout,
                                   stderr=stderr, start_new_session=True)
        while process.poll() is None:
            peak = max(peak, rss_mib(process.pid))
            if peak > memory_cap:
                stop_reason = "RSS_CAP"
            elif time.monotonic() - start > available:
                stop_reason = "WALL_CAP"
            if stop_reason:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                break
            time.sleep(0.02)
    elapsed = time.monotonic() - start
    receipt = {
        "task_id": ack["task_id"], "controller_packet_id": ack["controller_packet_id"],
        "controller_ack_id": ack["controller_ack_id"], "allocation_ref": ack["allocation_ref"],
        "command": command, "cwd": str(HERE), "exit_code": process.returncode,
        "stop_reason": stop_reason, "wall_seconds": elapsed, "peak_rss_mib_observed": peak,
        "rss_measurement": "polled Linux proc VmRSS; sampling can miss transient peaks",
        "source_sha256": prep["source_sha256"], "scientific_scope": "synthetic exact finite fixtures only",
        "claim_status": "NOT_SCIENTIFIC_ADMISSION",
    }
    (HERE / "RAW_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return process.returncode if process.returncode >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
