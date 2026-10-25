#!/usr/bin/env python3
"""One create-only metadata repair call with receipt, reap and hard limits."""

import time
OUTER_START_NS = time.monotonic_ns()

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PYTHON = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python")
LIMIT_SECONDS = 10.0
CHILD_DEADLINE_SECONDS = 8.0
RSS_LIMIT_BYTES = 2 * 1024**3


def elapsed():
    return (time.monotonic_ns() - OUTER_START_NS) / 1e9


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
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


def verify():
    inp = json.loads((HERE / "INPUT.json").read_text())
    if inp["schema"] != "htt.cf4_exact_factor_metadata_repair_input/1" or inp["state"] != "FROZEN_REPAIR_SCIENCE_INPUT":
        raise RuntimeError("SCIENCE_INPUT_NOT_FROZEN")
    for role in ("original_task_input", "original_factor", "original_result", "failed_review", "repair_contract", "parent_account_head"):
        obj = inp[role]
        if sha256(obj["path"]) != obj["sha256"]:
            raise RuntimeError(f"{role.upper()}_SHA_MISMATCH")
    review = json.loads(Path(inp["failed_review"]["path"]).read_text())
    if review.get("issue", {}).get("code") != "NEW_ZERO_LEVERAGE_MASK_MISMATCH":
        raise RuntimeError("REPAIR_ISSUE_MISMATCH")
    if review.get("candidate_identity") != "sha256:" + inp["original_result"]["sha256"]:
        raise RuntimeError("REVIEWED_CANDIDATE_MISMATCH")
    account = json.loads(Path(inp["parent_account_head"]["path"]).read_text())
    if account.get("cf4_cumulative_used_seconds") != inp["account"]["used_seconds"]:
        raise RuntimeError("ACCOUNT_HEAD_USED_MISMATCH")
    if inp["account"]["parent_cap_seconds"] != 600 or inp["account"]["repair_cap_seconds"] != 10 or inp["account"]["review_reserved_seconds"] != 17:
        raise RuntimeError("REPAIR_RESOURCE_CONTRACT_CHANGED")
    if 600 - inp["account"]["used_seconds"] < 27:
        raise RuntimeError("INSUFFICIENT_PARENT_ACCOUNT")

    repair_input_sha = sha256(HERE / "INPUT.json")
    task_input_identity = "sha256:" + inp["original_task_input"]["sha256"]
    binding = json.loads((HERE / "DISPATCH_BINDING.json").read_text())
    if binding["schema"] != "htt.cf4_exact_factor_metadata_repair_dispatch/1" or binding["repair_input_sha256"] != repair_input_sha:
        raise RuntimeError("DISPATCH_INPUT_MISMATCH")
    if binding["task_input_identity"] != task_input_identity:
        raise RuntimeError("DISPATCH_TASK_INPUT_IDENTITY_MISMATCH")
    if binding["agent_id"] != "/root/r28_cf4_exact_factor_numeric":
        raise RuntimeError("DISPATCH_AGENT_MISMATCH")
    for name in ("repair_metadata.py", "runner.py"):
        if sha256(HERE / name) != binding["source_sha256"].get(name):
            raise RuntimeError(f"DISPATCH_SOURCE_MISMATCH_{name}")
    docs = {}
    for role in ("packet", "ack", "go"):
        obj = binding[role]
        if sha256(obj["path"]) != obj["sha256"]:
            raise RuntimeError(f"{role.upper()}_SHA_MISMATCH")
        docs[role] = json.loads(Path(obj["path"]).read_text())
    packet, ack, go = (docs[role] for role in ("packet", "ack", "go"))
    if packet.get("input_identity") != task_input_identity or packet.get("task_id") != binding["task_id"] or packet.get("agent_id") != binding["agent_id"]:
        raise RuntimeError("PACKET_INPUT_TASK_AGENT_MISMATCH")
    for doc in (ack, go):
        if doc.get("status") != "GO" or doc.get("go") is not True or doc.get("packet_id") != packet.get("packet_id"):
            raise RuntimeError("ACK_GO_MISMATCH")
        if doc.get("task_id") != binding["task_id"] or doc.get("input_sha256") != inp["original_task_input"]["sha256"]:
            raise RuntimeError("ACK_GO_INPUT_TASK_MISMATCH")
        if doc.get("repair_input_sha256") != repair_input_sha:
            raise RuntimeError("ACK_GO_REPAIR_INPUT_MISMATCH")
        if doc.get("source_sha256") != binding["source_sha256"]:
            raise RuntimeError("ACK_GO_SOURCE_MISMATCH")
    if not PYTHON.is_file():
        raise RuntimeError("EXPECTED_INTERPRETER_MISSING")
    return inp, binding, packet


def main():
    actual = HERE / "actual_run"
    actual.mkdir(exist_ok=False)
    receipt = {"schema": "htt.cf4_exact_factor_metadata_repair_whole_invocation/1",
               "status": "STARTED", "agent_id": "/root/r28_cf4_exact_factor_numeric",
               "requested_runtime": "gpt-6-sol/high", "observed_runtime": "UNKNOWN",
               "whole_limit_seconds": LIMIT_SECONDS,
               "child_deadline_seconds": CHILD_DEADLINE_SECONDS,
               "rss_limit_bytes": RSS_LIMIT_BYTES,
               "all_started_commands": []}
    try:
        inp, binding, packet = verify()
        receipt["task_id"] = binding["task_id"]
        receipt["packet_id"] = packet["packet_id"]
        receipt["input_identity"] = binding["task_input_identity"]
        receipt["repair_input_sha256"] = binding["repair_input_sha256"]
        receipt["base_packet_id"] = "3910317d169e1b024a10a246ff415f2f1faf918ac9a13db01042cf764febdd41"
        receipt["base_candidate_identity"] = "sha256:ce46049e719e15749ee9adf8b5101f5cb4f439de6751a6285fa26eeeb6920e02"
        receipt["source_sha256"] = {name: sha256(HERE / name) for name in
                                     ("repair_metadata.py", "runner.py", "INPUT.json", "DISPATCH_BINDING.json")}
        env = dict(os.environ)
        for name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
                     "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
            env[name] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        argv = [str(PYTHON), "-B", str(HERE / "repair_metadata.py")]
        stdout, stderr = actual / "repair_metadata.stdout", actual / "repair_metadata.stderr"
        entry = {"argv": argv, "stdout": str(stdout), "stderr": str(stderr)}
        receipt["all_started_commands"].append(entry)
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
                time.sleep(0.02)
            code = child.wait()
            out.flush(); err.flush()
            os.fsync(out.fileno()); os.fsync(err.fileno())
        entry.update({"returncode": code, "reason": reason, "peak_polled_rss_bytes": peak})
        receipt["status"] = reason or ("CHILD_EXITED_ZERO" if code == 0 else "FIRST_CHILD_FAILURE")
    except Exception as exc:
        receipt["status"] = "OUTER_OR_BINDING_FAILURE"
        receipt["exception"] = repr(exc)
    receipt["outcome"] = "success" if receipt["status"] == "CHILD_EXITED_ZERO" else "blocker"
    product_dir = actual / "products"
    product_result = product_dir / "RESULT.json"
    product_valid = receipt["outcome"] == "success" and product_result.is_file()
    receipt["candidate_identity"] = "sha256:" + sha256(product_result) if product_valid else None
    canonical = {
        "schema": "htt.cf4_exact_factor_metadata_repair_return/1",
        "task_id": receipt.get("task_id"),
        "agent_id": receipt["agent_id"],
        "packet_id": receipt.get("packet_id"),
        "input_identity": receipt.get("input_identity"),
        "repair_input_sha256": receipt.get("repair_input_sha256"),
        "base_packet_id": receipt.get("base_packet_id"),
        "base_candidate_identity": receipt.get("base_candidate_identity"),
        "outcome": receipt["outcome"],
        "status": "METADATA_REPAIR_CANDIDATE_PENDING_FRESH_INDEPENDENT_REVIEW" if receipt["outcome"] == "success" else receipt["status"],
        "candidate_identity": receipt["candidate_identity"],
        "candidate_dir": str(product_dir) if product_valid else None,
        "raw_receipt": str(actual / "WHOLE_COMMAND_RECEIPT.json"),
        "products": [str(product_dir / name) for name in ("FACTOR.npz", "RESULT.json", "REPORT.md")] if product_valid else [],
        "qualified_products": [],
        "independent_review": "PENDING",
        "original_exact_values_and_response_reused": True if product_valid else "NOT_VERIFIED",
        "claim_ceiling": "exact only for fixed serialized-input support-simplex additive calibration; unrestricted nuisance and physical H02/H03/H04 remain UNKNOWN/HOLD",
    }
    with (HERE / "RESULT.json").open("x") as f:
        json.dump(canonical, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    for path in actual.rglob("*"):
        if path.is_file():
            with path.open("rb") as f:
                os.fsync(f.fileno())
    fd = os.open(actual, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    receipt["monotonic_through_products_fsync_seconds"] = elapsed()
    receipt["charge_rule"] = "maximum of overlapping parent whole API/host wall, external kernel elapsed, outer monotonic after receipt fsync; all starts count once"
    raw = actual / "WHOLE_COMMAND_RECEIPT.json"
    with raw.open("x") as f:
        json.dump(receipt, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    final = elapsed()
    print(json.dumps({"status": receipt["status"], "raw_receipt": str(raw),
                      "outer_monotonic_after_receipt_fsync_seconds": final}), flush=True)
    return 0 if receipt["status"] == "CHILD_EXITED_ZERO" and final <= LIMIT_SECONDS else 1


if __name__ == "__main__":
    sys.exit(main())
