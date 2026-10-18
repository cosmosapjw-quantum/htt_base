"""Frozen source-only SDSS mock acquisition; never imports upstream code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import time
import urllib.request

URL = "https://zenodo.org/api/records/6824749/files/mocks.tar.gz/content"
TOTAL = 10643218721
MD5 = "9ba3e8876f6f08a2af00d30cbf1c6cd9"
RANGES = ((0, 4294967295), (4294967296, 8589934591), (8589934592, 10643218720))
RESERVE = 2 * 1024**3
BLOCK = 8 * 1024**2


def validate_response(status, headers, start, end, total=TOTAL):
    """Reject ignored or altered ranges before reading any response body."""
    expected = f"bytes {start}-{end}/{total}"
    if status != 206:
        raise ValueError(f"Expected HTTP 206, received {status}; body not read")
    if headers.get("Content-Range") != expected:
        raise ValueError(f"Content-Range mismatch: {headers.get('Content-Range')!r}")
    if int(headers.get("Content-Length", "-1")) != end - start + 1:
        raise ValueError("Content-Length mismatch")
    if headers.get("Content-Encoding", "identity") not in ("", "identity"):
        raise ValueError("Encoded response cannot preserve archive byte ranges")


def safe_member(name, is_regular, size, limit=2 * 1024**3):
    """No absolute/traversing names, links, devices, or unbounded extraction."""
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise ValueError(f"Unsafe archive name {name!r}")
    if not is_regular or size < 0 or size > limit:
        raise ValueError(f"Unsupported archive member {name!r}")
    return p


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BLOCK), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    # These are execution outputs, rather than repository source edits.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def acquire(root, range_index=None):
    root.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    for start, end in (RANGES if range_index is None else (RANGES[range_index],)):
        length = end - start + 1
        part = root / f"mocks.{start}-{end}.part"
        receipt_path = root / f"range.{start}-{end}.json"
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if (receipt["status"] != "VALIDATED" or receipt["url"] != URL
                    or receipt["start"] != start or receipt["end"] != end
                    or receipt["archive_total"] != TOTAL or not part.exists()
                    or part.stat().st_size != length
                    or digest(part) != receipt["sha256"]):
                raise ValueError(f"Completed range receipt failed identity checks: {receipt_path}")
            print(f"REUSE validated range {start}-{end}", flush=True)
            continue
        if part.exists():
            raise ValueError(f"Unvalidated partial retained; explicit recovery required: {part}")
        if shutil.disk_usage(root).free < length + RESERVE:
            raise RuntimeError("Insufficient storage for range plus 2 GiB reserve")
        request = urllib.request.Request(URL, headers={
            "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity",
            "User-Agent": "htt_base-source-acquisition/20261018"})
        receipt = {"url": URL, "source_version": "v1.1.0", "start": start,
                   "end": end, "archive_total": TOTAL, "status": "STARTED"}
        attempt_start = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                headers = dict(response.headers.items())
                receipt.update(http_status=response.status, headers=headers,
                               final_url=response.url,
                               etag=response.headers.get("ETag", "UNAVAILABLE"))
                # Preserve raw response metadata even if validation rejects it.
                save_json(root / f"range.{start}-{end}.response.json", receipt)
                if not response.url.startswith("https://"):
                    raise ValueError("Non-HTTPS redirect")
                validate_response(response.status, response.headers, start, end)
                received = 0
                sha = hashlib.sha256()
                last_progress = time.monotonic()
                with part.open("xb") as out:
                    while received < length:
                        block = response.read(min(BLOCK, length - received))
                        if not block:
                            raise EOFError(f"Short range: {received} of {length}")
                        out.write(block)
                        sha.update(block)
                        received += len(block)
                        now = time.monotonic()
                        if now - last_progress >= 10:
                            rate = received / (now - attempt_start) / 1024**2
                            print(f"RANGE {start}-{end}: {received}/{length} bytes; {rate:.2f} MiB/s", flush=True)
                            last_progress = now
                    if response.read(1):
                        raise ValueError("Range body exceeds declared size")
                receipt.update(status="VALIDATED", bytes=received, sha256=sha.hexdigest(),
                               elapsed_s=time.monotonic() - attempt_start)
                save_json(receipt_path, receipt)
                print(f"VALIDATED {start}-{end}: {received} bytes", flush=True)
        except Exception as error:
            receipt.update(status="FAILED_PRESERVED", error=repr(error),
                           partial_bytes=part.stat().st_size if part.exists() else 0,
                           elapsed_s=time.monotonic() - attempt_start)
            save_json(root / f"range.{start}-{end}.failure.{time.time_ns()}.json", receipt)
            raise

    if range_index is not None:
        return
    archive = root / "mocks.tar.gz"
    receipt_path = root / "archive_identity.json"
    if archive.exists():
        if not receipt_path.exists():
            raise ValueError("Unvalidated assembled archive retained; explicit recovery required")
        identity = json.loads(receipt_path.read_text())
        if archive.stat().st_size != TOTAL or digest(archive, "md5") != MD5:
            raise ValueError("Existing archive identity mismatch")
        print("REUSE complete archive verified by size and MD5", flush=True)
        return
    if shutil.disk_usage(root).free < TOTAL + RESERVE:
        raise RuntimeError("Insufficient storage for assembly plus 2 GiB reserve")
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    count = 0
    with archive.open("xb") as out:
        for start, end in RANGES:
            with (root / f"mocks.{start}-{end}.part").open("rb") as source:
                for block in iter(lambda: source.read(BLOCK), b""):
                    out.write(block)
                    md5.update(block)
                    sha.update(block)
                    count += len(block)
    identity = {"url": URL, "source_version": "v1.1.0", "bytes": count,
                "md5": md5.hexdigest(), "sha256": sha.hexdigest(),
                "expected_md5": MD5, "expected_bytes": TOTAL,
                "elapsed_network_and_assembly_s": time.monotonic() - started,
                "status": "VALIDATED" if count == TOTAL and md5.hexdigest() == MD5 else "FAILED"}
    save_json(receipt_path, identity)
    if identity["status"] != "VALIDATED":
        raise ValueError("Full archive identity mismatch; extraction prohibited")
    print(json.dumps(identity), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--range-index", type=int, choices=range(3), default=None,
                        help="Acquire only one disjoint interval; do not assemble")
    args = parser.parse_args()
    acquire(args.root, args.range_index)
