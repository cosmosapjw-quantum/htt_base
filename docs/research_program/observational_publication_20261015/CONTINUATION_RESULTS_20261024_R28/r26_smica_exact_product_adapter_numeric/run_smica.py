#!/usr/bin/env python3
"""One-use bounded controller for the prospective exact-product SMICA component.

Root owns the canonical campaign state and supplies the actual sealed packet.
This process owns only an additive private attempt, costs, and raw receipts.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import traceback
import uuid

import project_smica as child_source  # stdlib-only at module import


HERE = Path(__file__).resolve().parent
RUN = HERE / "run"
ALL = child_source.ACCOUNTS
CAP = 900.0
CONTROL_CAP = 20.0
POST_CAP = 20.0
CONTROL_RSS = 2 * 1024 ** 3
NATIVE_RSS = 6 * 1024 ** 3
LAUNCH_MEM = 10 * 1024 ** 3
RUNTIME_MEM = 4 * 1024 ** 3
PYTHON = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/.venv/bin/python")


def write(path, obj):
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w") as stream:
        json.dump(obj, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def persist(ledger):
    write(RUN / "RAW_RECEIPT.json", ledger)


def debit(ledger, seconds, keys, label, attempt_id=None):
    if not math.isfinite(seconds) or seconds < 0:
        raise RuntimeError("INVALID_ELAPSED_CHARGE")
    if attempt_id and any(c.get("attempt_id") == attempt_id for c in ledger["charges"]):
        raise RuntimeError("DUPLICATE_ATTEMPT_DEBIT")
    for key in keys:
        ledger["delta_charged_seconds"][key] += seconds / len(keys)
        ledger["cumulative_charged_seconds"][key] += seconds / len(keys)
        if ledger["cumulative_charged_seconds"][key] > CAP:
            ledger.setdefault("account_cap_exceeded", []).append(key)
    charge = {"label": label, "elapsed_seconds": seconds, "allocated_products": list(keys)}
    if attempt_id:
        charge["attempt_id"] = attempt_id
    ledger["charges"].append(charge)
    persist(ledger)


def settle_native(ledger, marker):
    if marker["status"] not in ("FINISHED", "FAILED", "FAILED_NOT_LAUNCHED",
                                "OUTCOME_UNKNOWN"):
        raise RuntimeError("NATIVE_ATTEMPT_NOT_TERMINAL")
    seconds = (marker["native_bound_seconds"] if marker["status"] == "OUTCOME_UNKNOWN"
               else marker["elapsed_seconds"])
    debit(ledger, seconds, ("SMICA",), "EXACT_SMICA_NATIVE_ONE_USE",
          marker["attempt_id"])


def mem_available():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("MEMAVAILABLE_UNOBSERVED")


def proc_status(pid):
    try:
        values = {}
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(("VmRSS:", "VmHWM:", "Threads:")):
                key, raw = line.split(":", 1)
                number = int(raw.split()[0])
                values[key] = number if key == "Threads" else number * 1024
        return values
    except (OSError, ValueError):
        return {}


def process_start_ticks(pid):
    value = Path(f"/proc/{pid}/stat").read_text()
    return int(value[value.rfind(")") + 2:].split()[19])


def group_rss(pgid):
    total = 0
    for item in Path("/proc").iterdir():
        if item.name.isdigit():
            try:
                if os.getpgid(int(item.name)) == pgid:
                    total += proc_status(int(item.name)).get("VmRSS", 0)
            except (OSError, ProcessLookupError):
                pass
    return total


def preexec():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_PDEATHSIG")


class Interrupted(BaseException):
    pass


def on_signal(signum, _frame):
    raise Interrupted(f"signal {signum}")


def bounded_child(command, marker, ledger, cap_seconds, rss_cap, *, native=False):
    """One owned child, wait4 high-water, sampled group RSS, host floor."""
    began = time.monotonic()
    proc = None
    status = usage = None
    reaped = False
    trigger = failure = cleanup_failure = None
    max_parent = max_child = max_group = max_threads = 0
    min_available = None
    read_fd = write_fd = None
    old_term = signal.getsignal(signal.SIGTERM)
    old_int = signal.getsignal(signal.SIGINT)
    marker.update(status="STARTED", command=list(command),
                  start_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    persist(ledger)
    try:
        signal.signal(signal.SIGTERM, on_signal)
        signal.signal(signal.SIGINT, on_signal)
        if native:
            read_fd, write_fd = os.pipe()
            command = command + ["--internal-fd", str(read_fd),
                                 "--attempt-id", marker["attempt_id"]]
            marker["command"] = list(command)
        env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
               "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
               "VECLIB_MAXIMUM_THREADS": "1", "BLIS_NUM_THREADS": "1"}
        env["PYTHONPATH"] = os.pathsep.join((str(HERE), str(child_source.OPERATOR.parent),
                                             str(child_source.DECODER.parents[2])))
        with open(marker["stdout"], "xb") as out, open(marker["stderr"], "xb") as err:
            proc = subprocess.Popen(command, cwd=HERE, stdout=out, stderr=err,
                                    start_new_session=True, preexec_fn=preexec,
                                    pass_fds=(() if read_fd is None else (read_fd,)), env=env)
            marker.update(pid=proc.pid, parent_pid=os.getpid(),
                          child_start_ticks=process_start_ticks(proc.pid))
            persist(ledger)
            if native:
                os.close(read_fd)
                read_fd = None
                os.write(write_fd, marker["attempt_id"].encode())
                os.close(write_fd)
                write_fd = None
            while True:
                pid, polled_status, polled_usage = os.wait4(proc.pid, os.WNOHANG)
                if pid == proc.pid:
                    status, usage, reaped = polled_status, polled_usage, True
                    break
                own = proc_status(os.getpid())
                child = proc_status(proc.pid)
                max_parent = max(max_parent, own.get("VmHWM", 0))
                max_child = max(max_child, child.get("VmHWM", 0))
                max_group = max(max_group, own.get("VmRSS", 0) + group_rss(proc.pid))
                max_threads = max(max_threads, child.get("Threads", 0))
                if native:
                    available = mem_available()
                    min_available = available if min_available is None else min(min_available, available)
                elapsed = time.monotonic() - began
                if max(max_parent, max_child, max_group) > rss_cap:
                    trigger = "RSS_CAP"
                elif max_threads > 1:
                    trigger = "THREAD_CAP"
                elif native and min_available < RUNTIME_MEM:
                    trigger = "HOST_MEMAVAILABLE_FLOOR"
                elif elapsed >= cap_seconds - 2:
                    trigger = "TIME_CAP_TERM"
                if trigger:
                    try:
                        os.killpg(proc.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    deadline = time.monotonic() + 1.5
                    while time.monotonic() < deadline:
                        pid, polled_status, polled_usage = os.wait4(proc.pid, os.WNOHANG)
                        if pid == proc.pid:
                            status, usage, reaped = polled_status, polled_usage, True
                            break
                        time.sleep(.05)
                    if not reaped:
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        _, status, usage = os.wait4(proc.pid, 0)
                        reaped = True
                    break
                time.sleep(.05)
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "repr": repr(exc),
                   "traceback": traceback.format_exc()}
        trigger = trigger or "LAUNCH_OR_MONITOR_EXCEPTION"
    finally:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            for fd in (read_fd, write_fd):
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError as exc:
                        cleanup_failure = repr(exc)
            if proc is not None and not reaped:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError as exc:
                    cleanup_failure = repr(exc)
                try:
                    _, status, usage = os.wait4(proc.pid, 0)
                    reaped = True
                except BaseException as exc:
                    cleanup_failure = repr(exc)
            elapsed = time.monotonic() - began
            hwm = int(usage.ru_maxrss * 1024) if reaped and usage else None
            parent_lifetime_hwm = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
            exit_code = os.waitstatus_to_exitcode(status) if reaped and status is not None else None
            marker.update(elapsed_seconds=elapsed, wait_status=status if reaped else None,
                          exit_code=exit_code, wait4_ru_maxrss_bytes=hwm,
                          parent_vm_hwm_bytes=max_parent, child_vm_hwm_bytes=max_child,
                          parent_lifetime_ru_maxrss_bytes=parent_lifetime_hwm,
                          owned_group_sampled_rss_peak_bytes=max_group,
                          max_observed_child_threads=max_threads,
                          minimum_host_mem_available_bytes=min_available,
                          trigger=trigger, child_reaped=reaped, exception=failure,
                          cleanup_exception=cleanup_failure)
            if proc is None:
                marker["status"] = "FAILED_NOT_LAUNCHED"
            elif not reaped:
                marker["status"] = "OUTCOME_UNKNOWN"
            elif (failure or cleanup_failure or trigger or exit_code != 0 or hwm is None
                  or max(max_parent, parent_lifetime_hwm, max_child, max_group, hwm) > rss_cap
                  or max_threads > 1):
                marker["status"] = "FAILED"
            else:
                marker["status"] = "FINISHED"
            persist(ledger)
        finally:
            signal.signal(signal.SIGTERM, old_term)
            signal.signal(signal.SIGINT, old_int)
    return marker


def run(args):
    entered = time.monotonic()
    if RUN.exists() and (RUN / "RAW_RECEIPT.json").exists():
        raise RuntimeError("ONE_USE_RAW_RECEIPT_EXISTS_NO_RELAUNCH")
    cfg, contract, head_ref, packet_id = child_source.validate_go(args)
    ack = json.loads(child_source.sealed_ref(
        json.loads(Path(args.packet).read_text())["controller_ack"]).read_text())
    if (ack.get("compute_slot_granted") is not True
            or ack.get("one_use_attempt_id") is None
            or cfg["latest_account_head"]["minimum_ancestor"] != contract["accounting"]["old_terminal_snapshot"]):
        raise RuntimeError("COMPUTE_SLOT_OR_OLD_FAILURE_BINDING_REQUIRED")
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError("WRONG_EXISTING_INTERPRETER")
    RUN.mkdir(exist_ok=True)
    ledger = {"schema": "htt.smica_exact_product_additive_ledger/1",
              "component_id": child_source.COMPONENT, "packet_id": packet_id,
              "input_sha256": args.input_sha, "packet_sha256": args.packet_sha,
              "latest_account_head": head_ref,
              "old_terminal_snapshot": contract["accounting"]["old_terminal_snapshot"],
              "old_failed_one_use_preserved": True,
              "baseline_charged_seconds": dict(head_ref["cumulative_charged_seconds"]),
              "delta_charged_seconds": {k: 0.0 for k in ALL},
              "cumulative_charged_seconds": dict(head_ref["cumulative_charged_seconds"]),
              "charges": [], "first_failures": [], "control": {}, "native": {},
              "stage": "PREPARING", "scientific_admission": "HOLD",
              "accounting_status": "PROPOSED_UNTIL_ROOT_INGEST",
              "requested_runtime": contract["resources"]["requested_worker"],
              "observed_runtime": "UNKNOWN"}
    persist(ledger)
    phase_start = entered
    try:
        # Exact production header and qualified stat; no FITS body read.
        import smica_implicit_reader as reader
        with reader._open_rows(cfg["source_product"]) as (_, _, _, header_sha):
            pass
        ledger["map_header_sha256"] = header_sha
        if time.monotonic() - entered >= CONTROL_CAP - 2:
            raise RuntimeError("FORMAT_CONTROL_BUDGET_EXHAUSTED_BEFORE_TESTS")
        marker = {"status": "STARTED", "one_use": True,
                  "stdout": str(RUN / "FORMAT.stdout"),
                  "stderr": str(RUN / "FORMAT.stderr")}
        ledger["control"] = marker
        ledger["stage"] = "FORMAT_CONTROL_STARTED"
        persist(ledger)
        command = [str(PYTHON), "-B", "-m", "unittest", "-v", "test_format_controls"]
        bounded_child(command, marker, ledger,
                      CONTROL_CAP - (time.monotonic() - entered), CONTROL_RSS)
        control_elapsed = time.monotonic() - phase_start
        debit(ledger, control_elapsed, ALL, "COMMON_PREPARATION_AND_FORMAT_CONTROL")
        phase_start = time.monotonic()
        if marker["status"] != "FINISHED" or control_elapsed > CONTROL_CAP:
            raise RuntimeError("FORMAT_CONTROL_FIRST_FAILURE_OR_CAP")
        lines = Path(marker["stderr"]).read_text().splitlines()
        outcomes = [line.strip() for line in lines if line.startswith("test_")]
        if (len(outcomes) != 5 or any(not line.endswith(" ... ok") for line in outcomes)):
            raise RuntimeError("FORMAT_TEST_OUTCOME_PARSE_OR_COUNT")
        source_hashes = cfg["implementation_source_seals"]["sha256"]
        format_receipt = {"schema": "htt.smica_exact_format_control/1",
                          "status": "PASS", "component_id": child_source.COMPONENT,
                          "source_profile_id": contract["source_profile_id"],
                          "source_sha256": source_hashes,
                          "map_header_sha256": header_sha,
                          "observed_test_outcomes": outcomes,
                          "control": marker, "elapsed_shared_seconds": control_elapsed,
                          "stdout_sha256": child_source.sha(marker["stdout"]),
                          "stderr_sha256": child_source.sha(marker["stderr"]),
                          "scientific_admission": "HOLD"}
        receipt_file = RUN / "FORMAT_CONTROL_RECEIPT.json"
        if receipt_file.exists():
            raise RuntimeError("FORMAT_RECEIPT_ALREADY_EXISTS")
        write(receipt_file, format_receipt)
        ledger["stage"] = "FORMAT_PASS_NATIVE_PRELAUNCH"
        persist(ledger)
        if mem_available() < LAUNCH_MEM:
            raise RuntimeError("HOLD_PRELAUNCH_HOST_CAPACITY")
        # Charge common wrapper before computing the exact residual native bound.
        debit(ledger, time.monotonic() - phase_start, ALL, "COMMON_NATIVE_PRELAUNCH")
        phase_start = time.monotonic()
        for key in ALL:
            if CAP - ledger["cumulative_charged_seconds"][key] < POST_CAP / 8:
                raise RuntimeError("POSTPROCESS_RESERVE_UNAVAILABLE " + key)
        remaining = CAP - ledger["cumulative_charged_seconds"]["SMICA"]
        native_cap = min(300.0, remaining - POST_CAP / 8)
        if native_cap <= 2:
            raise RuntimeError("NATIVE_CAP_EXHAUSTED")
        marker = {"status": "STARTED", "attempt_id": ack["one_use_attempt_id"],
                  "stdout": str(RUN / "SMICA.stdout"),
                  "stderr": str(RUN / "SMICA.stderr"),
                  "native_bound_seconds": native_cap,
                  "prelaunch_mem_available_bytes": mem_available()}
        if marker["prelaunch_mem_available_bytes"] < LAUNCH_MEM:
            raise RuntimeError("HOLD_PRELAUNCH_HOST_CAPACITY")
        ledger["native"] = marker
        ledger["stage"] = "NATIVE_STARTED"
        persist(ledger)  # One-use marker precedes spawn.
        command = [str(PYTHON), "-B", str(HERE / "project_smica.py"),
                   "--input", args.input, "--input-sha", args.input_sha,
                   "--packet", args.packet, "--packet-sha", args.packet_sha,
                   "--control-receipt", str(receipt_file),
                   "--control-receipt-sha", child_source.sha(receipt_file)]
        bounded_child(command, marker, ledger, native_cap, NATIVE_RSS, native=True)
        settle_native(ledger, marker)
        phase_start = time.monotonic()
        if marker["status"] != "FINISHED":
            raise RuntimeError("SMICA_NATIVE_FIRST_FAILURE_NO_RETRY")
        for name in ("CARRIER_SMICA_EXACT_IMPLICIT.npz", "CONTROL_SMICA_EXACT_IMPLICIT.json",
                     "SMICA_SIGNED24.png", "RESULT.json"):
            if not (RUN / name).is_file():
                raise RuntimeError("MISSING_CANDIDATE_ARTIFACT " + name)
        ledger["stage"] = "CANDIDATE_REVIEW_REQUIRED"
        ledger["native"]["status"] = "FINISHED_REVIEW_REQUIRED"
    except BaseException as exc:
        ledger["stage"] = "HOLD_FIRST_FAILURE"
        if (ledger["control"].get("status") == "STARTED"
                and not any(c["label"] == "COMMON_PREPARATION_AND_FORMAT_CONTROL"
                            for c in ledger["charges"])):
            ledger["control"]["status"] = "OUTCOME_UNKNOWN"
            debit(ledger, CONTROL_CAP, ALL, "OUTCOME_UNKNOWN_FORMAT_ENVELOPE")
            phase_start = time.monotonic()
        if (ledger["native"].get("attempt_id")
                and not any(c.get("attempt_id") == ledger["native"]["attempt_id"]
                            for c in ledger["charges"])):
            if ledger["native"].get("status") == "STARTED":
                ledger["native"]["status"] = "OUTCOME_UNKNOWN"
            settle_native(ledger, ledger["native"])
            phase_start = time.monotonic()
        ledger["first_failures"].append({"type": type(exc).__name__,
                                         "message": str(exc),
                                         "traceback": traceback.format_exc(),
                                         "control": ledger["control"].copy(),
                                         "native": ledger["native"].copy()})
    finally:
        # Any uncharged wrapper interval is common, including failure handling.
        elapsed = time.monotonic() - phase_start
        if elapsed > POST_CAP and ledger["control"].get("status") == "FINISHED":
            ledger["stage"] = "HOLD_POSTPROCESS_CAP"
        debit(ledger, elapsed, ALL, "COMMON_FINALIZATION_OR_FAILURE")
        ledger["postprocess_shared_seconds"] = elapsed
        if ledger.get("account_cap_exceeded"):
            ledger["stage"] = "HOLD_CUMULATIVE_ACCOUNT_CAP_EXCEEDED"
        persist(ledger)
        write(RUN / "LEDGER.json", ledger)
    return 0 if ledger["stage"] == "CANDIDATE_REVIEW_REQUIRED" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--input-sha", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--packet-sha", required=True)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
