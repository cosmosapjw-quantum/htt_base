#!/usr/bin/env python3
"""One bounded controls+consumer call; final dispatch input is mandatory.

Root charges max of its whole API/host wall and this persistent outer monotonic
receipt once. An external /usr/bin/time -v supplies kernel time and max RSS.
"""

import time
OUTER_START_NS = time.monotonic_ns()

import json
import os
from pathlib import Path
import subprocess
import sys

from factor import sha256


HERE = Path(__file__).resolve().parent
PYTHON = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python")
LIMIT_SECONDS = 60.0
CHILD_DEADLINE_SECONDS = 55.0
RSS_LIMIT_BYTES = 2 * 1024**3


def elapsed():
    return (time.monotonic_ns() - OUTER_START_NS) / 1e9


def rss(pid):
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (FileNotFoundError, ProcessLookupError):
        return 0
    return 0


def fsync_file(path):
    with path.open("rb") as f:
        os.fsync(f.fileno())


def verify_input():
    inp = json.loads((HERE / "INPUT.json").read_text())
    if inp["schema"] != "htt.cf4_exact_factor_actual_input/1" or inp["state"] != "FROZEN_SCIENCE_INPUT":
        raise RuntimeError("INPUT_NOT_FINAL")
    for role in ("carrier", "result"):
        obj = inp["source"][role]
        if sha256(obj["path"]) != obj["sha256"]:
            raise RuntimeError(f"{role.upper()}_SHA_MISMATCH")
    if sha256(inp["contract"]["path"]) != inp["contract"]["sha256"]:
        raise RuntimeError("CONTRACT_SHA_MISMATCH")
    source = inp["source"]
    for role in ("source_input", "source_contract", "source_clarification"):
        obj = source[role]
        if sha256(obj["path"]) != obj["sha256"]:
            raise RuntimeError(f"{role.upper()}_SHA_MISMATCH")
    if source["reviewed_usable"] is not True or sha256(source["final_review_path"]) != source["final_review_sha256"]:
        raise RuntimeError("FINAL_SOURCE_REVIEW_MISSING")
    review = json.loads(Path(source["final_review_path"]).read_text())
    if review.get("status") != "SCOPED_PASS" or review.get("acceptance_met") is not True:
        raise RuntimeError("FINAL_SOURCE_REVIEW_NOT_PASSED")
    if review.get("candidate_identity") != "sha256:" + source["result"]["sha256"]:
        raise RuntimeError("FINAL_SOURCE_REVIEW_DIFFERENT_CANDIDATE")
    account = inp["parent_account"]
    if sha256(account["latest_head_path"]) != account["latest_head_sha256"]:
        raise RuntimeError("PARENT_ACCOUNT_HEAD_MISMATCH")
    head = json.loads(Path(account["latest_head_path"]).read_text())
    if head.get("cf4_cumulative_used_seconds") != account["used_seconds"] or head.get("cf4_remaining_seconds") != account["remaining_seconds"]:
        raise RuntimeError("PARENT_ACCOUNT_VALUES_MISMATCH")
    if account["parent_cap_seconds"] != 600 or account["consumer_cap_seconds"] != 60 or account["independent_review_reserved_seconds"] != 20:
        raise RuntimeError("RESOURCE_CONTRACT_CHANGED")
    used, remaining = account["used_seconds"], account["remaining_seconds"]
    if remaining < 80 or used < 0 or abs(used + remaining - 600) > 1e-6:
        raise RuntimeError("INSUFFICIENT_OR_INCONSISTENT_ACCOUNT")
    input_sha = sha256(HERE / "INPUT.json")
    binding = json.loads((HERE / "DISPATCH_BINDING.json").read_text())
    if binding["schema"] != "htt.cf4_exact_factor_dispatch_binding/1" or binding["input_sha256"] != input_sha:
        raise RuntimeError("DISPATCH_INPUT_IDENTITY_MISMATCH")
    if binding["agent_id"] != "/root/r28_cf4_exact_factor_numeric":
        raise RuntimeError("DISPATCH_AGENT_ID_MISMATCH")
    for name in ("factor.py", "consume.py", "test_controls.py", "runner.py"):
        if binding["source_sha256"].get(name) != sha256(HERE / name):
            raise RuntimeError(f"DISPATCH_SOURCE_SHA_MISMATCH_{name}")
    docs = {}
    for role in ("packet", "ack", "go"):
        obj = binding[role]
        if sha256(obj["path"]) != obj["sha256"]:
            raise RuntimeError(f"{role.upper()}_SHA_MISMATCH")
        docs[role] = json.loads(Path(obj["path"]).read_text())
    packet, ack, go = (docs[role] for role in ("packet", "ack", "go"))
    if packet.get("input_identity") != "sha256:" + input_sha:
        raise RuntimeError("PACKET_FROZEN_INPUT_MISMATCH")
    if packet.get("task_id") != binding["task_id"] or packet.get("agent_id") != binding["agent_id"]:
        raise RuntimeError("PACKET_TASK_OR_AGENT_MISMATCH")
    if ack.get("status") != "GO" or ack.get("go") is not True or go.get("status") != "GO" or go.get("go") is not True:
        raise RuntimeError("NO_CONTROLLER_ACK_AND_GO")
    for doc in (ack, go):
        if doc.get("packet_id") != packet.get("packet_id") or doc.get("task_id") != binding["task_id"]:
            raise RuntimeError("ACK_GO_PACKET_MISMATCH")
        if doc.get("input_sha256") != input_sha:
            raise RuntimeError("ACK_GO_INPUT_IDENTITY_MISMATCH")
        for name, digest in binding["source_sha256"].items():
            if doc.get("source_sha256", {}).get(name) != digest:
                raise RuntimeError(f"ACK_GO_SOURCE_MISMATCH_{name}")
    if not PYTHON.is_file():
        raise RuntimeError("EXPECTED_INTERPRETER_MISSING")
    return inp


def main():
    actual = HERE / "actual_run"
    actual.mkdir(exist_ok=False)
    receipt = {
        "schema": "htt.cf4_exact_factor_whole_invocation/1",
        "status": "STARTED", "requested_runtime": "gpt-6-sol/high",
        "observed_runtime": "UNKNOWN", "all_started_commands": [],
        "whole_limit_seconds": LIMIT_SECONDS,
        "child_deadline_seconds": CHILD_DEADLINE_SECONDS,
        "rss_limit_bytes": RSS_LIMIT_BYTES,
        "source_sha256": {name: sha256(HERE / name) for name in
                          ("factor.py", "consume.py", "test_controls.py", "runner.py", "INPUT.json", "DISPATCH_BINDING.json")},
    }
    try:
        verify_input()
        env = dict(os.environ)
        for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
                     "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
            env[name] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for name in ("test_controls.py", "consume.py"):
            if elapsed() >= CHILD_DEADLINE_SECONDS:
                receipt["status"] = "TIME_LIMIT_BEFORE_CHILD"
                break
            argv = [str(PYTHON), "-B", str(HERE / name)]
            stem = name.removesuffix(".py")
            stdout, stderr = actual / f"{stem}.stdout", actual / f"{stem}.stderr"
            entry = {"argv": argv, "stdout": str(stdout), "stderr": str(stderr)}
            receipt["all_started_commands"].append(entry)
            start_ns = time.monotonic_ns()
            with stdout.open("xb") as out, stderr.open("xb") as err:
                child = subprocess.Popen(argv, cwd=HERE, env=env, stdout=out, stderr=err)
                peak = 0
                reason = None
                while child.poll() is None:
                    peak = max(peak, rss(child.pid))
                    if peak > RSS_LIMIT_BYTES:
                        reason = "RSS_LIMIT_EXCEEDED"
                    elif elapsed() >= CHILD_DEADLINE_SECONDS:
                        reason = "CHILD_TIME_LIMIT"
                    if reason:
                        child.kill()
                        break
                    time.sleep(0.05)
                code = child.wait()
                out.flush(); err.flush()
                os.fsync(out.fileno()); os.fsync(err.fileno())
            entry.update({"returncode": code, "reason": reason,
                          "observed_monotonic_seconds": (time.monotonic_ns() - start_ns) / 1e9,
                          "peak_polled_rss_bytes": peak})
            if code != 0 or reason:
                receipt["status"] = reason or "FIRST_CHILD_FAILURE"
                break
        else:
            receipt["status"] = "CHILDREN_EXITED_ZERO"
    except Exception as exc:
        receipt["status"] = "OUTER_OR_BINDING_FAILURE"
        receipt["exception"] = repr(exc)
    for path in actual.rglob("*"):
        if path.is_file():
            fsync_file(path)
    fd = os.open(actual, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    receipt["monotonic_through_products_fsync_seconds"] = elapsed()
    receipt["charge_rule"] = "max(controller whole API/host wall, external kernel elapsed, outer monotonic after receipt fsync); overlapping time charged once"
    receipt_path = actual / "WHOLE_COMMAND_RECEIPT.json"
    with receipt_path.open("x") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    final = elapsed()
    print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path),
                      "outer_monotonic_after_receipt_fsync_seconds": final}), flush=True)
    return 0 if receipt["status"] == "CHILDREN_EXITED_ZERO" and final <= LIMIT_SECONDS else 1


if __name__ == "__main__":
    sys.exit(main())
