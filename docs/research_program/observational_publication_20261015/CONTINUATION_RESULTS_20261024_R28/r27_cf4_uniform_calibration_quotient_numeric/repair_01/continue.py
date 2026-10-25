#!/usr/bin/env python3
"""One bounded repair selector followed by the unchanged, unstarted consumer."""
import time
OUTER_START_NS = time.monotonic_ns()  # Before child imports/tests/consumer.

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NUMERIC = HERE.parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
PYTHON = REPO / ".venv/bin/python"
LIMIT_SECONDS = 116.515
CHILD_LIMIT_SECONDS = 110.515
RSS_LIMIT_BYTES = 2 * 1024**3
SELECTOR = "test_controls_repair.QuotientControls.test_full_rank_uniform_invariance_and_cross_covariance"
REPAIR_CONTRACT = Path("/mnt/extdrive/workdir/htt_open_data/r27_cf4_uniform_controls_repair_research/REPAIR_CONTRACT.md")
FIRST_RECEIPT = NUMERIC / "actual_run/WHOLE_COMMAND_RECEIPT.json"
FIRST_STDERR = NUMERIC / "actual_run/test_controls.stderr"
EXPECTED = {
    NUMERIC / "consume.py": "d8c3a7526f97f196bcc29b5fbd0ead26aadb1a0230268ea9f2736074c8fcf798",
    NUMERIC / "INPUT.json": "570383ac224808090c57b356ee21cc7f114a27d712ee725c5c42850bf00d61fd",
    NUMERIC / "test_controls.py": "9999b21ba314ba9cf2cc1724155f5dbaae56dbe5dcaa56e693760053fd4f064b",
    FIRST_RECEIPT: "25df7205e60f5ec707b3cff1b2e55ac88c495c74121506214c043fe786290a5c",
    FIRST_STDERR: "6fa4a6eb07357c158548857e32cfb7065323b5bd928cc64c5a010f2ca2cf0a77",
    REPAIR_CONTRACT: "fbf868f1f0087b0b7520f6237703e11ba76186f5e6baff04f45a9086ca7630e1",
}


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


def fsync_tree(root):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file():
            with path.open("rb") as f:
                os.fsync(f.fileno())
    fd = os.open(root, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    actual = HERE / "actual_run"
    if actual.exists():
        raise RuntimeError(f"CREATE_ONLY_REPAIR_ACTUAL_RUN_EXISTS {actual}")
    actual.mkdir()
    receipt = {
        "schema": "htt.cf4_support_quotient_repair_continuation/1",
        "status": "STARTED", "task_id": "R27-CF4-UNIFORM-SUPPORT-CALIBRATION-QUOTIENT",
        "input_identitysha256": EXPECTED[NUMERIC / "INPUT.json"],
        "requested_worker": "gpt-6-sol/high", "observed_worker": "UNKNOWN",
        "original_first_receipt": str(FIRST_RECEIPT),
        "original_first_stderr": str(FIRST_STDERR),
        "original_three_pass_methods_reused": ["test_exact_support_decomposition",
                                                "test_rank4_rank0_and_unstable",
                                                "test_stf_decode_rotation"],
        "source_sha256": {str(p): sha(p) for p in [*EXPECTED, HERE / "test_controls_repair.py", HERE / "continue.py"]},
        "expected_source_sha256": {str(p): h for p, h in EXPECTED.items()},
        "all_started_commands": [],
        "limit_seconds": LIMIT_SECONDS, "child_limit_seconds": CHILD_LIMIT_SECONDS,
        "rss_limit_bytes": RSS_LIMIT_BYTES,
        "clock": "time.monotonic_ns outer; controller caller whole wall separate and may be nonmonotonic",
        "external_resource_receipt": str(HERE / "ACTUAL_LIFETIME_RESOURCE.txt")
    }
    try:
        if not PYTHON.is_file():
            raise RuntimeError(f"OFFICIAL_VENV_PYTHON_MISSING {PYTHON}")
        for path, expected in EXPECTED.items():
            found = receipt["source_sha256"][str(path)]
            if found != expected:
                raise RuntimeError(f"FROZEN_SOURCE_DRIFT path={path} expected={expected} found={found}")
        if (NUMERIC / "actual_run/products").exists():
            raise RuntimeError("ORIGINAL_CONSUMER_ALREADY_STARTED_OR_PRODUCTS_EXISTS")
        env = dict(os.environ)
        for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
                     "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
            env[name] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(NUMERIC) + os.pathsep + str(REPO)
        commands = [
            ("corrected_failed_control", [str(PYTHON), "-B", "-m", "unittest", "-v", SELECTOR]),
            ("first_original_consumer", [str(PYTHON), "-B", str(NUMERIC / "consume.py")]),
        ]
        for label, argv in commands:
            if (time.monotonic_ns() - OUTER_START_NS) / 1e9 >= CHILD_LIMIT_SECONDS:
                receipt["status"] = "CHILD_DEADLINE_BEFORE_START"
                break
            outpath, errpath = actual / f"{label}.stdout", actual / f"{label}.stderr"
            entry = {"label": label, "argv": argv, "stdout": str(outpath), "stderr": str(errpath)}
            receipt["all_started_commands"].append(entry)
            started_ns = time.monotonic_ns()
            with outpath.open("xb") as out, errpath.open("xb") as err:
                child = subprocess.Popen(argv, cwd=HERE, env=env, stdout=out, stderr=err)
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
                        reason = "CHILD_DEADLINE_EXCEEDED"
                        child.kill()
                        break
                    time.sleep(.05)
                code = child.wait()
                out.flush(); err.flush()
                os.fsync(out.fileno()); os.fsync(err.fileno())
            entry.update({"returncode": code, "stop_reason": reason,
                          "observed_monotonic_seconds": (time.monotonic_ns() - started_ns) / 1e9,
                          "peak_polled_rss_bytes": peak})
            if code != 0 or reason:
                receipt["status"] = reason or "FIRST_CONTINUATION_FAILURE"
                break
        else:
            receipt["status"] = "BOTH_CHILDREN_EXITED_ZERO"
        fsync_tree(NUMERIC / "actual_run/products")
        fsync_tree(actual)
    except Exception as exc:
        receipt["status"] = "OUTER_CONTINUATION_FAILURE"
        receipt["exception"] = repr(exc)
    receipt["observed_monotonic_through_products_and_logs_fsync_seconds"] = (time.monotonic_ns() - OUTER_START_NS) / 1e9
    receipt["charge_rule"] = "max(controller whole API/caller, kernel whole wall, outer monotonic); overlapping envelopes charged once"
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
    return 0 if receipt["status"] == "BOTH_CHILDREN_EXITED_ZERO" else 1


if __name__ == "__main__":
    sys.exit(main())
