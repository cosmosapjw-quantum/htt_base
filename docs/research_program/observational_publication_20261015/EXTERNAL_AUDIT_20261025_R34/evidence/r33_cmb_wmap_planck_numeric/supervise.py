#!/usr/bin/env python3
"""Controller-gated one-use R33 producer supervisor. No implicit GO or retry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import traceback

ROOT = Path(__file__).resolve().parent
FRAME = Path("/mnt/extdrive/workdir/htt_open_data/r33_cmb_additional_frequency_framing")
INPUT = Path("/mnt/extdrive/workdir/htt_open_data/r33_wmap_planck_dispatch/INPUT.json")
OLD = Path("/mnt/extdrive/workdir/htt_open_data/r30_cmb_spectral_response_numeric/attempt_38cdf6b948a41ee9/RESULT.json")
TASK = "R33-CMB-WMAP-PLANCK-F2-EXTENSION"
WALL = 180.0
RSS = 1073741824
MIN_MEM = 4294967296
MIN_DISK = 2147483648
EXPECTED = {
    INPUT: "d1ef7598449adff41ba8f950d048b5290efaf0f66ae056e61c8549544c763ce1",
    FRAME/"WMAP_PLANCK_F2_CONTRACT.md": "986e558508ef7691d3286e9eb6cab48a38c9ded6645fe8c3e1486280a2e14686",
    FRAME/"RESULT.json": "40dad683edcd49bea3a2ef8999d7c9ed0ce76830459112f977a8e382afce3540",
    FRAME/"BANDPASS_SOURCE_METADATA.json": "06f2449ec8041dd968e1b9f85bf81649434dc93763dc8931ceb562a6ef6801f1",
    FRAME/"sources/wmap_bandpass_v5.tar.gz": "5f3a3d29dd2346a31f7d4d215f3d7564c0a11b5af283737a6c14edfe6f152feb",
    OLD: "b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f",
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def check_source():
    for path, expected in EXPECTED.items():
        assert sha(path) == expected, ("immutable source mismatch", str(path))
    metadata = json.loads((FRAME/"BANDPASS_SOURCE_METADATA.json").read_text())
    entries = {x["file"]: x for x in metadata["entries"]}
    assert len(entries) == 20
    archive = FRAME/"sources/wmap_bandpass_v5.tar.gz"
    with tarfile.open(archive, "r:gz") as tf:
        names = set(tf.getnames())
        assert names == set(entries)
        for name, entry in entries.items():
            content = tf.extractfile(name).read()
            disk = (FRAME/"sources"/"bandpasses"/name).read_bytes()
            assert content == disk and hashlib.sha256(disk).hexdigest() == entry["sha256"], name


def available_mem():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1])*1024
    raise RuntimeError("MemAvailable unavailable")


def group_rss(pgid):
    total = 0
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            if os.getpgid(int(item.name)) != pgid:
                continue
            for line in (item/"status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    total += int(line.split()[1])*1024
                    break
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return total


def atomic_json(path, obj):
    tmp = path.with_name(path.name+".tmp")
    with open(tmp, "x") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def external_gate(path, digest, expected_status):
    path = Path(path).resolve(strict=True)
    assert ROOT not in path.parents and path != ROOT
    assert sha(path) == digest
    packet = json.loads(path.read_text())
    assert packet["task_id"] == TASK and packet["status"] == expected_status
    assert packet["scientific_input_sha256"] == EXPECTED[INPUT]
    assert packet["preparation_sha256"] == sha(ROOT/"PREPARATION.json")
    return packet


def main():
    invocation_started = time.monotonic()
    ap = argparse.ArgumentParser()
    ap.add_argument("--ack", required=True, help="external controller ACK JSON")
    ap.add_argument("--ack-sha256", required=True)
    ap.add_argument("--go", required=True, help="external controller GO JSON")
    ap.add_argument("--go-sha256", required=True)
    ap.add_argument("--attempt", required=True, help="new empty output dir below ROOT")
    args = ap.parse_args()
    assert len(args.ack_sha256) == len(args.go_sha256) == 64
    check_source()
    prep = json.loads((ROOT/"PREPARATION.json").read_text())
    assert prep["source_sha256"]["produce.py"] == sha(ROOT/"produce.py")
    assert prep["source_sha256"]["supervise.py"] == sha(ROOT/"supervise.py")
    ack = external_gate(args.ack, args.ack_sha256, "ACK")
    go = external_gate(args.go, args.go_sha256, "GO")
    assert go["ack_sha256"] == args.ack_sha256
    assert ack["account_head_sha256"] == go["account_head_sha256"]
    assert ack["account_head_sha256"] and len(ack["account_head_sha256"]) == 64
    assert go["attempt_path"] == args.attempt
    assert go["producer_wall_limit_seconds"] == WALL and go["producer_rss_limit_bytes"] == RSS
    attempt = Path(args.attempt).resolve()
    assert attempt.parent == ROOT and not attempt.exists()
    assert available_mem() >= MIN_MEM
    assert shutil.disk_usage(ROOT).free >= MIN_DISK
    assert set(("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS")) <= set(os.environ)
    assert all(os.environ[k] == "1" for k in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"))
    # Dependency readiness is checked before the one-use science child starts.
    import importlib.util
    for name in ("numpy", "mpmath"):
        assert importlib.util.find_spec(name) is not None, name
    attempt.mkdir()
    command = [sys.executable, str(ROOT/"produce.py"), "--output", str(attempt/"RESULT.json")]
    receipt = {"task_id": TASK, "scientific_input_sha256": EXPECTED[INPUT],
               "preparation_sha256": sha(ROOT/"PREPARATION.json"),
               "ack_sha256": args.ack_sha256, "go_sha256": args.go_sha256,
               "account_head_sha256": ack["account_head_sha256"],
               "command": command, "cwd": str(ROOT), "wall_cap_seconds": WALL,
               "rss_cap_bytes": RSS, "start_status": "NOT_STARTED"}
    atomic_json(attempt/"START.json", receipt)
    peak = 0
    reason = None
    code = None
    launch_error = None
    with open(attempt/"stdout.log", "xb", buffering=0) as out, open(attempt/"stderr.log", "xb", buffering=0) as err:
        def child_limit():
            resource.setrlimit(resource.RLIMIT_AS, (RSS, RSS))
        try:
            proc = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err,
                                    start_new_session=True, preexec_fn=child_limit,
                                    env=os.environ.copy())
            receipt["pid"] = proc.pid
            receipt["start_status"] = "STARTED"
            atomic_json(attempt/"STARTED.json", receipt)
            while proc.poll() is None:
                elapsed = time.monotonic()-invocation_started
                peak = max(peak, group_rss(proc.pid))
                if peak > RSS:
                    reason = "RSS_LIMIT"
                elif elapsed > WALL:
                    reason = "WALL_LIMIT"
                if reason:
                    os.killpg(proc.pid, signal.SIGKILL)
                    break
                time.sleep(.1)
            code = proc.wait()
        except BaseException:
            launch_error = traceback.format_exc()
            err.write(launch_error.encode())
            reason = "SUPERVISOR_FAILURE"
            if "proc" in locals() and proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                code = proc.wait()
    elapsed = time.monotonic()-invocation_started
    if code == 0 and not reason and not (attempt/"RESULT.json").is_file():
        reason = "RESULT_MISSING"
    done = {**receipt, "elapsed_seconds": elapsed, "peak_tree_rss_bytes": peak,
            "exit_code": code, "stop_reason": reason or ("SUCCESS" if code == 0 else "CHILD_FAILURE"),
            "supervisor_failure": launch_error,
            "result_sha256": sha(attempt/"RESULT.json") if (attempt/"RESULT.json").exists() else None,
            "requested_runtime": {"model": "gpt-6-sol", "effort": "high"},
            "observed_runtime": "UNKNOWN", "account_increment_per_existing_frequency_seconds": elapsed/7,
            "scientific_admission": "PENDING_INDEPENDENT_CHECK_AND_REVIEW"}
    atomic_json(attempt/"RAW_RECEIPT.json", done)
    if code != 0 or reason:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
