"""Parent-owned, finite three-request recovery; stop before actual science."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from acquire_sdss import RANGES, RESERVE, TOTAL, acquire, digest
from resume_acquisition import API, HERE, INITIAL_SIZES, durable_json, validate_metadata, verify_metadata

ORIGINAL_ATTEMPT = "1792327821626160108"
PRIOR_FAILURE_SHA256 = "4e04ea37c91dfaec3f65939597b14c39e3d5b4be2e1f897bb27ad456b75f3b32"
SAVED_METADATA_SHA256 = "d88f31e90aab9a782c59ceac46a1891c0fda628b1f642f731201b6a4a9daf818"
ORIGINAL_MARKER_SHA256 = "c3acabb9b0584ebefc3fbd78b1fc0a26b3b66dfdb5cec760c350a855150c2fbf"
ORIGINAL_PRESEAL_SHA256 = "adb19757269d2c7ac9956bbed7ab04a92ac9d98929022b3dfdb6b5f63a15bc7b"
PHASE = "metadata_phase1"
NAMESPACE = ORIGINAL_ATTEMPT + "." + PHASE
VERSION_ERROR = "ValueError('Official record/version identity mismatch')"


def launch_guards(root, preseal, approval, approval_sha256):
    if digest(approval) != approval_sha256:
        raise ValueError("Approval artifact SHA mismatch")
    snapshot = json.loads(preseal.read_text())
    if snapshot["status"] != "PRESEALED" or len(snapshot["ranges"]) != 3:
        raise ValueError("Missing frozen preseal")
    for filename, sha in snapshot["source_sha256"].items():
        if digest(HERE / filename) != sha:
            raise ValueError(f"Source drift after preseal: {filename}")
    if digest(HERE / "CONTRACT.md") != snapshot["contract_sha256"]:
        raise ValueError("Original contract drift")
    if digest(HERE / "SCIENTIFIC_BUDGET.jsonl") != snapshot["scientific_budget_sha256"]:
        raise ValueError("Scientific accounting drift")
    for expected, (start, end), retained in zip(snapshot["ranges"], RANGES, INITIAL_SIZES):
        part = root / f"mocks.{start}-{end}.part"
        stat = part.stat()
        if ((expected["start"], expected["end"], expected["bytes"]) != (start, end, retained)
                or stat.st_size != retained or stat.st_ino != expected["inode"]
                or stat.st_mtime_ns != expected["mtime_ns"] or digest(part) != expected["sha256"]):
            raise ValueError("Retained prefix drift; return to controller")
        if digest(Path(expected["original_response"])) != expected["original_response_sha256"]:
            raise ValueError("Original response evidence drift")
    remaining = TOTAL - sum(INITIAL_SIZES)
    if remaining != 7690428705 or shutil.disk_usage(root).free < remaining + RESERVE:
        raise ValueError("Aggregate remaining bytes plus 2 GiB reserve unavailable")
    return snapshot, remaining


def validate_continuation(root, preseal, snapshot, prior_failure, prior_failure_sha256,
                          saved_metadata, saved_metadata_sha256):
    """Only the exact observed zero-bulk metadata failure admits this one phase."""
    marker = root / f"recovery.{NAMESPACE}.started.json"
    if marker.exists():
        raise ValueError("Metadata continuation phase already consumed; no second continuation")
    expected_failure = root / f"recovery.{ORIGINAL_ATTEMPT}.execution.json"
    expected_metadata = root / f"recovery.{ORIGINAL_ATTEMPT}.metadata.json"
    if (prior_failure.resolve() != expected_failure.resolve()
            or prior_failure_sha256 != PRIOR_FAILURE_SHA256
            or digest(prior_failure) != PRIOR_FAILURE_SHA256):
        raise ValueError("Only the exact original metadata failure is authorized")
    if (saved_metadata.resolve() != expected_metadata.resolve()
            or saved_metadata_sha256 != SAVED_METADATA_SHA256
            or digest(saved_metadata) != SAVED_METADATA_SHA256):
        raise ValueError("Saved official metadata identity mismatch")
    old_marker = root / "recovery.single_attempt.started.json"
    if digest(old_marker) != ORIGINAL_MARKER_SHA256:
        raise ValueError("Original attempt marker identity mismatch")
    previous = json.loads(prior_failure.read_text())
    original = json.loads(old_marker.read_text())
    if (previous.get("attempt") != ORIGINAL_ATTEMPT or previous.get("status") != "FAILED_PRESERVED"
            or previous.get("error") != VERSION_ERROR or previous.get("children") != []
            or previous.get("child_exit_codes") != [] or previous.get("maximum_requests") != 3
            or previous.get("scientific_execution") != "NOT_STARTED"
            or original.get("status") != "STARTED"
            or any(previous.get(k) != v for k, v in original.items() if k != "status")):
        raise ValueError("Nonempty or non-metadata execution history; continuation forbidden")
    if Path(f"/proc/{previous['pid']}").exists():
        raise ValueError("Prior controller PID exists; continuation forbidden")
    # No alternate execution, range worker, response or completion can be hidden.
    if (set(root.glob("recovery.*.execution.json")) != {expected_failure}
            or any(root.glob("recovery.*.range*"))
            or any((root / f"range.{a}-{b}.json").exists() for a, b in RANGES)
            or any(root.glob(f"recovery.{NAMESPACE}.*"))):
        raise ValueError("Range/alternate-phase history exists; continuation forbidden")
    metadata = json.loads(saved_metadata.read_text())
    if (metadata.get("url") != API or metadata.get("final_url") != API
            or metadata.get("http_status") != 200 or metadata.get("status") != "STARTED"):
        raise ValueError("Original metadata response is not direct official HTTP200")
    validate_metadata(json.loads(metadata["raw_body_utf8"]))
    metadata_failure = json.loads((root / f"recovery.{ORIGINAL_ATTEMPT}.metadata.failure.json").read_text())
    expected_metadata_failure = dict(metadata, status="FAILED_PRESERVED", error=VERSION_ERROR)
    if metadata_failure != expected_metadata_failure:
        raise ValueError("Original metadata failure binding mismatch")
    response = json.loads((root / f"recovery.{ORIGINAL_ATTEMPT}.metadata.response.json").read_text())
    if response != {k: v for k, v in metadata.items() if k != "raw_body_utf8"}:
        raise ValueError("Original metadata response binding mismatch")
    prior_preseal = preseal.with_name(preseal.name + ".pre_metadata_phase")
    if (digest(prior_preseal) != ORIGINAL_PRESEAL_SHA256
            or previous["preseal_sha256"] != ORIGINAL_PRESEAL_SHA256):
        raise ValueError("Original preseal binding mismatch")
    prior_snapshot = json.loads(prior_preseal.read_text())
    if ({k: v for k, v in snapshot.items() if k != "source_sha256"}
            != {k: v for k, v in prior_snapshot.items() if k != "source_sha256"}):
        raise ValueError("Prefix/contract/accounting seals changed; continuation forbidden")
    return marker


def launch(root, preseal, approval, approval_sha256, prior_failure, prior_failure_sha256,
           saved_metadata, saved_metadata_sha256):
    snapshot, remaining = launch_guards(root, preseal, approval, approval_sha256)
    marker = validate_continuation(root, preseal, snapshot, prior_failure, prior_failure_sha256,
                                   saved_metadata, saved_metadata_sha256)
    attempt = ORIGINAL_ATTEMPT
    record = {"status": "STARTED", "attempt": attempt, "phase": PHASE,
              "artifact_namespace": NAMESPACE, "pid": os.getpid(),
              "prior_failure": str(prior_failure), "prior_failure_sha256": prior_failure_sha256,
              "saved_official_metadata": str(saved_metadata), "saved_official_metadata_sha256": saved_metadata_sha256,
              "root_bulk_requests_previously_launched": 0, "root_bulk_request_ceiling": 3,
              "root_bulk_requests_launched_this_phase": 0,
              "earlier_faulty_fixture_external_get_count": "UNKNOWN",
              "controller_command": [sys.executable, *sys.argv], "cwd": os.getcwd(),
              "observed_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "preseal": str(preseal), "preseal_sha256": digest(preseal),
              "approval": str(approval), "approval_sha256": approval_sha256,
              "executor_role": "parent controller launching a Python source-only data job",
              "controller_requested_model_effort": "NOT_SPECIFIED",
              "controller_observed_model_effort": "UNKNOWN",
              "python_job_model_effort": "NOT_APPLICABLE",
              "actual_source_sha256": snapshot["source_sha256"],
              "remaining_new_bytes": remaining, "maximum_requests": 3,
              "scientific_execution": "NOT_STARTED", "children": [], "utc_epoch": time.time()}
    # Under the controller lock: consume ONE phase of the existing attempt before
    # any network. Original marker and failure remain untouched; no retry hook.
    durable_json(marker, record)
    children = []
    started = time.monotonic()
    try:
        metadata = verify_metadata(root, NAMESPACE)
        record["official_metadata"] = str(metadata)
        for index in range(3):
            command = [sys.executable, "-u", str(HERE / "resume_acquisition.py"), str(root),
                       "--preseal", str(preseal), "--range-index", str(index), "--attempt", NAMESPACE]
            log_path = root / f"recovery.{NAMESPACE}.range{index}.log"
            with log_path.open("x") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            children.append(process)
            record["root_bulk_requests_launched_this_phase"] = len(children)
            binding = {"index": index, "pid": process.pid, "command": command, "log": str(log_path)}
            record["children"].append(binding)
            durable_json(root / f"recovery.{NAMESPACE}.range{index}.launch.json", binding)
        while any(process.poll() is None for process in children):
            if any(process.poll() not in (None, 0) for process in children):
                raise RuntimeError("A range worker failed; stopping this attempt without retry")
            print(json.dumps({"status": "RECOVERY_MONITOR", "attempt": attempt,
                              "children": [{"pid": p.pid, "exit_code": p.poll()} for p in children],
                              "part_bytes": [(root / f"mocks.{a}-{b}.part").stat().st_size for a, b in RANGES]}), flush=True)
            time.sleep(30)
        if any(process.returncode != 0 for process in children):
            raise RuntimeError("Range failure; no assembly")
        # Existing acquisition code can only reuse all three now-validated ranges.
        for start, end in RANGES:
            if not (root / f"range.{start}-{end}.json").exists():
                raise ValueError("Completion receipt missing; no assembly")
        if shutil.disk_usage(root).free < TOTAL + RESERVE:
            raise RuntimeError("Insufficient assembly capacity plus 2 GiB reserve")
        acquire(root)
        command = [sys.executable, "-u", str(HERE / "inspect_archive.py"), str(root), str(HERE)]
        header_log = root / f"recovery.{NAMESPACE}.index_header.log"
        record.update(header_command=command, header_log=str(header_log))
        with header_log.open("x") as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
            finally:
                log.flush()
                os.fsync(log.fileno())
        record.update(status="STAGE1_RETURN_TO_ASTRA", header_exit_code=result.returncode)
    except BaseException as error:
        for process in children:
            if process.poll() is None:
                process.terminate()
        for process in children:
            process.wait()
        record.update(status="FAILED_PRESERVED", error=repr(error))
        raise
    finally:
        for binding in record["children"]:
            with Path(binding["log"]).open("rb") as log:
                os.fsync(log.fileno())
        record.update(elapsed_s=time.monotonic()-started,
                      child_exit_codes=[{"pid": p.pid, "exit_code": p.poll()} for p in children])
        durable_json(root / f"recovery.{NAMESPACE}.execution.json", record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--preseal", required=True, type=Path)
    parser.add_argument("--approval", required=True, type=Path)
    parser.add_argument("--approval-sha256", required=True)
    parser.add_argument("--continue-prior-failure", required=True, type=Path)
    parser.add_argument("--prior-failure-sha256", required=True)
    parser.add_argument("--saved-metadata", required=True, type=Path)
    parser.add_argument("--saved-metadata-sha256", required=True)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise InterruptedError(f"Controller signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    class Tee:
        def __init__(self, original, log):
            self.original, self.log = original, log
        def write(self, text):
            self.original.write(text)
            return self.log.write(text)
        def flush(self):
            self.original.flush()
            self.log.flush()
            os.fsync(self.log.fileno())
    # One controller; workers take independent exclusive locks on their parts.
    log_path = args.root / f"recovery.controller.{time.time_ns()}.log"
    with (args.root / "recovery.controller.lock").open("a") as lock, log_path.open("x") as log:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            try:
                launch(args.root, args.preseal, args.approval, args.approval_sha256,
                       args.continue_prior_failure, args.prior_failure_sha256,
                       args.saved_metadata, args.saved_metadata_sha256)
            except BaseException:
                import traceback
                traceback.print_exc()
                sys.stderr.flush()
                raise SystemExit(1)
            finally:
                sys.stdout.flush()
