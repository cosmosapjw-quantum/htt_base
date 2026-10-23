"""One separately allocated, finite suffix phase. Source-only; no science."""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

from acquire_sdss import BLOCK, MD5, RANGES, RESERVE, TOTAL, URL, acquire, digest, validate_response
from resume_acquisition import API, HERE, OVERLAP, durable_json, open_direct, prefix_digest, validate_metadata

ATTEMPT = "1792327821626160108"
PHASE = "suffix_phase1"
NS = ATTEMPT + "." + PHASE
SIZES = (2591793744, 2105540608, 2053284129)
FAILURE = "recovery." + ATTEMPT + ".metadata_phase1.execution.json"
FAILURE_SHA = "937817522ef9c2b2cdcd76ac0a55511448863bb76f48abd06ff589295ebe3f1a"
PART2_SHA = "43f62633765b085d50359bbd2a91589c99bec8e15f73048471b21629dc5cc1a5"
MAX_BODY = 268435456
NEW_BYTES = MAX_BODY - OVERLAP
BODY_CAP = 3893648816
REQUEST_CAP = 16
METADATA_CAP = 1024**2
PHASE_SECONDS = 7200
REQUEST_SECONDS = 1200
INACTIVITY_SECONDS = 120
OLD_PIDS = (999286, 1001635, 1001651, 1001653)


def part_path(root, index):
    a, b = RANGES[index]
    return root / f"mocks.{a}-{b}.part"


def chunks(index, retained):
    start, end = RANGES[index]
    length = end - start + 1
    if index not in (0, 1) or not OVERLAP <= retained < length:
        raise ValueError("Only the two unfinished frozen parts admit suffixes")
    result = []
    while retained < length:
        novel = min(NEW_BYTES, length - retained)
        result.append({"retained": retained, "start": start + retained - OVERLAP,
                       "end": start + retained + novel - 1, "novel": novel,
                       "body": novel + OVERLAP})
        retained += novel
    return result


@contextmanager
def deadline(seconds):
    def expired(signum, frame):
        raise TimeoutError("Full request/phase deadline expired; prefix preserved")
    if seconds <= 0:
        raise TimeoutError("Phase deadline exhausted")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def interrupted(signum, frame):
    raise InterruptedError(f"Controller signal {signum}; CANCELLED_PRESERVED")


def source_seals():
    names = ("chunked_suffix.py", "test_chunked_suffix.py", "acquire_sdss.py",
             "resume_acquisition.py", "inspect_archive.py", "root_launcher.py",
             "CONTRACT.md", "SUFFIX_PHASE_CONTRACT.md", "SCIENTIFIC_BUDGET.jsonl")
    return {name: digest(HERE / name) for name in names}


def history(root):
    if digest(root / FAILURE) != FAILURE_SHA:
        raise ValueError("Exact terminal failure identity mismatch")
    old = json.loads((root / FAILURE).read_text())
    if (old.get("status") != "FAILED_PRESERVED" or old.get("phase") != "metadata_phase1"
            or old.get("root_bulk_requests_launched_this_phase") != 3
            or [c["exit_code"] for c in old["child_exit_codes"]] != [1, 1, 0]):
        raise ValueError("Original phase is not the frozen closed 3/3 failure")
    if any(Path(f"/proc/{pid}").exists() for pid in OLD_PIDS):
        raise ValueError("Historical process PID exists; return for classification")
    paths = sorted(set(root.glob("recovery.*.json")) | set(root.glob("range.*.json")))
    return {p.name: digest(p) for p in paths if NS not in p.name}


def reuse_complete(root, expected, stream):
    a, b = RANGES[2]
    receipt = json.loads((root / f"range.{a}-{b}.json").read_text())
    if (receipt.get("status") != "VALIDATED" or receipt.get("url") != URL
            or receipt.get("start") != a or receipt.get("end") != b
            or receipt.get("archive_total") != TOTAL or receipt.get("sha256") != PART2_SHA
            or expected["sha256"] != PART2_SHA or expected["bytes"] != b-a+1
            or prefix_digest(stream, b-a+1) != PART2_SHA):
        raise ValueError("Completed part2/receipt identity mismatch")


@contextmanager
def locked_sources(root):
    with ExitStack() as stack:
        controller = stack.enter_context((root / "recovery.controller.lock").open("a"))
        fcntl.flock(controller, fcntl.LOCK_EX | fcntl.LOCK_NB)
        streams = []
        for index in range(3):
            stream = stack.enter_context(part_path(root, index).open("r+b", buffering=0))
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            streams.append(stream)
        yield streams


def file_identity(stream):
    st = os.fstat(stream.fileno())
    return {"bytes": st.st_size, "inode": st.st_ino, "device": st.st_dev,
            "mtime_ns": st.st_mtime_ns}


def snapshot_sources(root, streams):
    values = []
    for index, stream in enumerate(streams):
        before = file_identity(stream)
        if before["bytes"] != SIZES[index]:
            raise ValueError("Frozen current prefix size drift")
        sha = prefix_digest(stream, before["bytes"])
        if before != file_identity(stream):
            raise ValueError("Source changed during SHA preseal")
        values.append(dict(before, sha256=sha, index=index, start=RANGES[index][0], end=RANGES[index][1]))
    reuse_complete(root, values[2], streams[2])
    return values


def seal(root, output):
    with locked_sources(root) as streams:
        old = history(root)
        result = {"status": "PRESEALED", "task": ATTEMPT, "phase": PHASE,
                  "root": str(root.resolve()), "ranges": snapshot_sources(root, streams),
                  "history_sha256": old, "source_sha256": source_seals(),
                  "previous_root_bulk_requests": 3, "new_bulk_request_cap": REQUEST_CAP,
                  "cumulative_observed_root_request_ceiling": 19,
                  "earlier_fixture_requests_and_bytes": "UNKNOWN",
                  "scientific_execution": "NOT_STARTED", "utc_epoch": time.time()}
        durable_json(output, result)
        return result


def evidence(root, suffix):
    return root / f"suffix.{NS}.{suffix}"


def reject_transfer_encoding(headers):
    # HTTPResponse gives chunked transfer framing precedence over Content-Length.
    # Any presence is outside this phase's exact identity-framed response contract.
    if headers.get("Transfer-Encoding") is not None:
        raise ValueError("Transfer-Encoding present; rejected before body read")


def account(root, event):
    """Single fsynced append ledger, locked across both workers; never reset."""
    path = evidence(root, "accounting.jsonl")
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        prior = [json.loads(line) for line in stream]
        starts = [v for v in prior if v["event"] == "REQUEST_STARTED"]
        body = sum(v.get("bytes", 0) for v in prior if v["event"] == "BODY_READ")
        metadata = [v for v in prior if v["event"] == "METADATA_STARTED"]
        if event["event"] == "REQUEST_STARTED":
            if (len(starts) >= REQUEST_CAP or any(v["request_id"] == event["request_id"] for v in starts)
                    or sum(v["body_bound"] for v in starts) + event["body_bound"] > BODY_CAP
                    or not 0 < event["body_bound"] <= MAX_BODY):
                raise ValueError("Consumed request or bulk allocation exceeded")
        if event["event"] == "METADATA_STARTED" and metadata:
            raise ValueError("One official metadata request already consumed")
        if event["event"] == "BODY_READ" and body + event["bytes"] > BODY_CAP:
            raise ValueError("Bulk response-body cap exceeded")
        event = dict(event, pid=os.getpid(), utc_epoch=time.time(),
                     previous_root_requests=3, historical_fixture_usage="UNKNOWN")
        stream.seek(0, 2)
        stream.write(json.dumps(event, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def metadata(root, end_time):
    prefix = "metadata"
    account(root, {"event": "METADATA_STARTED", "url": API, "byte_cap": METADATA_CAP})
    record = {"url": API, "status": "STARTED", "body_bytes": 0}
    durable_json(evidence(root, prefix + ".started.json"), record)
    try:
        with deadline(min(REQUEST_SECONDS, end_time-time.monotonic())):
            request = urllib.request.Request(API, headers={"Accept": "application/json", "Accept-Encoding": "identity"})
            with open_direct(request, timeout=INACTIVITY_SECONDS) as response:
                record.update(final_url=response.url, http_status=response.status, headers=dict(response.headers.items()))
                durable_json(evidence(root, prefix + ".response.json"), record)
                reject_transfer_encoding(response.headers)
                length = int(response.headers.get("Content-Length", "-1"))
                if (response.url != API or response.status != 200 or not 0 < length <= METADATA_CAP
                        or response.headers.get("Content-Encoding", "identity") not in ("", "identity")):
                    raise ValueError("Official metadata status/URL/length/encoding rejected before body")
                raw = bytearray()
                while len(raw) < length:
                    block = response.read(length-len(raw))
                    if not block:
                        raise EOFError("Short metadata body")
                    raw.extend(block)
                    record["body_bytes"] += len(block)
                validate_metadata(json.loads(raw))
                record.update(raw_body_utf8=raw.decode("utf-8"), status="VALIDATED")
        durable_json(evidence(root, prefix + ".complete.json"), record)
    except BaseException as error:
        record.update(status="FAILED_PRESERVED", error=repr(error))
        durable_json(evidence(root, prefix + ".failure.json"), record)
        raise


def append_chunk(stream, response, chunk, on_read):
    retained = chunk["retained"]
    if os.fstat(stream.fileno()).st_size != retained:
        raise ValueError("Part drift before chunk")
    stream.seek(retained-OVERLAP)
    tail = stream.read(OVERLAP)
    received = 0
    def read_bounded(size):
        nonlocal received
        block = response.read(size)
        if len(block) > size:
            raise ValueError("Reader exceeded bounded read")
        received += len(block)
        if block:
            on_read(len(block))
        if not block:
            raise EOFError(f"SHORT_RESPONSE_BODY at {received}/{chunk['body']}")
        return block
    overlap = bytearray()
    while len(overlap) < OVERLAP:
        overlap.extend(read_bounded(OVERLAP-len(overlap)))
    if len(tail) != OVERLAP or overlap != tail:
        raise ValueError("Overlap mismatch; no append")
    appended = 0
    try:
        while appended < chunk["novel"]:
            block = read_bounded(min(BLOCK, chunk["novel"]-appended))
            if os.fstat(stream.fileno()).st_size != retained+appended:
                raise ValueError("Concurrent part mutation")
            stream.seek(0, 2)
            view = memoryview(block)
            while view:
                written = stream.write(view)
                if not written:
                    raise OSError("Short filesystem write")
                appended += written
                view = view[written:]
        # HTTPResponse frames the body by the exact validated Content-Length.
        # Never read a probe byte beyond the frozen global response-body cap.
        if received != chunk["body"]:
            raise ValueError("Chunk response-body length mismatch")
    finally:
        os.fsync(stream.fileno())
    return appended


def worker(root, preseal, index, fd, end_time):
    snapshot = json.loads(preseal.read_text())
    expected = snapshot["ranges"][index]
    with os.fdopen(os.dup(fd), "r+b", buffering=0) as stream:
        if any(file_identity(stream)[key] != expected[key] for key in ("bytes", "inode", "device", "mtime_ns") if key in expected):
            raise ValueError("Inherited locked source descriptor identity drift")
        fcntl.fcntl(stream, fcntl.F_SETFL, fcntl.fcntl(stream, fcntl.F_GETFL) | os.O_APPEND)
        for number, chunk in enumerate(chunks(index, expected["bytes"])):
            request_id = f"part{index}.chunk{number:02}"
            record = dict(chunk, request_id=request_id, status="STARTED", url=URL,
                          source_version="v1.1.0", archive_total=TOTAL, body_bytes=0,
                          retained_prefix_sha256=expected["sha256"], pid=os.getpid())
            durable_json(evidence(root, request_id + ".started.json"), record)
            try:
                with deadline(min(REQUEST_SECONDS, end_time-time.monotonic())):
                    account(root, {"event": "REQUEST_STARTED", "request_id": request_id,
                                   "body_bound": chunk["body"], "start": chunk["start"], "end": chunk["end"]})
                    request = urllib.request.Request(URL, headers={"Range": f"bytes={chunk['start']}-{chunk['end']}",
                                                                   "Accept-Encoding": "identity"})
                    with open_direct(request, timeout=INACTIVITY_SECONDS) as response:
                        record.update(http_status=response.status, final_url=response.url,
                                      headers=dict(response.headers.items()), etag=response.headers.get("ETag", "UNAVAILABLE"))
                        durable_json(evidence(root, request_id + ".response.json"), record)
                        reject_transfer_encoding(response.headers)
                        if response.url != URL:
                            raise ValueError("Response final URL differs from frozen direct endpoint")
                        validate_response(response.status, response.headers, chunk["start"], chunk["end"])
                        def on_read(count):
                            record["body_bytes"] += count
                            account(root, {"event": "BODY_READ", "request_id": request_id, "bytes": count})
                        record["appended_bytes"] = append_chunk(stream, response, chunk, on_read)
                    record.update(status="VALIDATED", part_bytes=os.fstat(stream.fileno()).st_size)
                    durable_json(evidence(root, request_id + ".complete.json"), record)
            except BaseException as error:
                record.update(status="CANCELLED_PRESERVED" if isinstance(error, InterruptedError) else "FAILED_PRESERVED",
                              error=repr(error), part_bytes=os.fstat(stream.fileno()).st_size)
                durable_json(evidence(root, request_id + ".failure.json"), record)
                raise
        if prefix_digest(stream, expected["bytes"]) != expected["sha256"]:
            raise ValueError("Presealed prefix changed")
        a, b = RANGES[index]
        if os.fstat(stream.fileno()).st_size != b-a+1:
            raise ValueError("Whole part size mismatch")
        durable_json(root / f"range.{a}-{b}.json", {
            "status": "VALIDATED", "url": URL, "source_version": "v1.1.0", "start": a, "end": b,
            "archive_total": TOTAL, "bytes": b-a+1, "sha256": prefix_digest(stream, b-a+1),
            "retained_prefix_sha256_after": expected["sha256"], "phase": PHASE,
            "preseal_sha256": digest(preseal), "whole_archive_md5": "PENDING"})


def launch_guards(root, preseal, approval, approval_sha, streams):
    if evidence(root, "started.json").exists():
        raise ValueError("Suffix phase already consumed; no second phase")
    snapshot = json.loads(preseal.read_text())
    if (snapshot.get("status") != "PRESEALED" or snapshot.get("task") != ATTEMPT
            or snapshot.get("phase") != PHASE or snapshot.get("root") != str(root.resolve())
            or digest(approval) != approval_sha):
        raise ValueError("Frozen preseal/approval binding mismatch")
    if snapshot["source_sha256"] != source_seals() or snapshot["history_sha256"] != history(root):
        raise ValueError("Code/contract/science accounting/historical evidence drift")
    if snapshot["ranges"] != snapshot_sources(root, streams):
        raise ValueError("Source prefix identity drift before launch")
    plans = [chunks(i, SIZES[i]) for i in (0, 1)]
    if ([len(v) for v in plans] != [7, 9] or sum(c["body"] for v in plans for c in v) != BODY_CAP
            or shutil.disk_usage(root).free < TOTAL-sum(SIZES)+RESERVE):
        raise ValueError("Frozen chunk plan/storage bound failed")
    return snapshot


def stop_children(children):
    for process in children:
        if process.poll() is None:
            process.terminate()
    for process in children:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def usage(root):
    path = evidence(root, "accounting.jsonl")
    events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    requests = sum(v["event"] == "REQUEST_STARTED" for v in events)
    return {"new_bulk_attempts": requests, "cumulative_observed_root_bulk_attempts": 3+requests,
            "new_bulk_body_bytes_read": sum(v.get("bytes", 0) for v in events if v["event"] == "BODY_READ"),
            "new_bulk_bytes_reserved": sum(v.get("body_bound", 0) for v in events if v["event"] == "REQUEST_STARTED"),
            "new_metadata_attempts": sum(v["event"] == "METADATA_STARTED" for v in events),
            "historical_fixture_requests_and_bytes": "UNKNOWN"}


def launch(root, preseal, approval, approval_sha):
    with locked_sources(root) as streams:
        snapshot = launch_guards(root, preseal, approval, approval_sha, streams)
        record = {"status": "STARTED", "task": ATTEMPT, "phase": PHASE, "pid": os.getpid(),
                  "preseal_sha256": digest(preseal), "approval": str(approval), "approval_sha256": approval_sha,
                  "source_sha256": snapshot["source_sha256"], "scientific_execution": "NOT_STARTED",
                  "previous_root_bulk_requests": 3, "new_request_cap": REQUEST_CAP,
                  "cumulative_observed_root_request_ceiling": 19, "historical_fixture_usage": "UNKNOWN",
                  "controller_command": [sys.executable, *sys.argv], "children": [], "utc_epoch": time.time()}
        durable_json(evidence(root, "started.json"), record)
        started = time.monotonic()
        end_time = started+PHASE_SECONDS
        children = []
        try:
            metadata(root, end_time)
            for index in (0, 1):
                fd = streams[index].fileno()
                command = [sys.executable, "-u", str(HERE / "chunked_suffix.py"), str(root),
                           "--preseal", str(preseal.resolve()), "--worker", str(index),
                           "--fd", str(fd), "--end-time", str(end_time)]
                log_path = evidence(root, f"part{index}.log")
                with log_path.open("x") as log:
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, pass_fds=(fd,))
                children.append(process)
                binding = {"pid": process.pid, "command": command, "log": str(log_path)}
                record["children"].append(binding)
                durable_json(evidence(root, f"part{index}.launch.json"), binding)
            while any(p.poll() is None for p in children):
                if time.monotonic() >= end_time:
                    raise TimeoutError("7200s suffix phase cap")
                if any(p.poll() not in (None, 0) for p in children):
                    raise RuntimeError("Suffix worker failed; sibling cancelled; no retry")
                time.sleep(0.2)
            if any(p.returncode for p in children):
                raise RuntimeError("Suffix worker failure; no assembly")
            if shutil.disk_usage(root).free < TOTAL+RESERVE:
                raise ValueError("Assembly requires TOTAL plus 2 GiB free")
            with deadline(end_time-time.monotonic()):
                acquire(root)  # All three validated receipts must already exist.
                command = [sys.executable, "-u", str(HERE / "inspect_archive.py"), str(root), str(HERE)]
                log_path = evidence(root, "index_header.log")
                with log_path.open("x") as log:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                            timeout=max(0.001, end_time-time.monotonic()), check=True)
                record.update(header_command=command, header_exit_code=result.returncode)
            record["status"] = "STAGE1_RETURN_TO_ASTRA"
        except BaseException as error:
            stop_children(children)
            record.update(status="FAILED_PRESERVED", error=repr(error))
            raise
        finally:
            record.update(elapsed_s=time.monotonic()-started,
                          usage=usage(root),
                          child_exit_codes=[{"pid": p.pid, "exit_code": p.poll()} for p in children])
            durable_json(evidence(root, "execution.json"), record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--seal", type=Path)
    parser.add_argument("--preseal", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--approval-sha256")
    parser.add_argument("--worker", type=int, choices=(0, 1))
    parser.add_argument("--fd", type=int)
    parser.add_argument("--end-time", type=float)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    if args.seal:
        seal(args.root, args.seal)
    elif args.worker is not None and args.preseal and args.fd is not None and args.end_time:
        # Workers need a live inherited locked descriptor and the consumed phase.
        marker = json.loads(evidence(args.root, "started.json").read_text())
        if marker["pid"] != os.getppid() or digest(args.preseal) != marker["preseal_sha256"]:
            raise ValueError("Worker lacks active controller/preseal binding")
        worker(args.root, args.preseal, args.worker, args.fd, args.end_time)
    elif args.preseal and args.approval and args.approval_sha256:
        launch(args.root, args.preseal, args.approval, args.approval_sha256)
    else:
        parser.error("Use --seal or parent launch --preseal --approval --approval-sha256")
