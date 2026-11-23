"""Bounded chunked-FITS intake for Planck PR3 FFP10 Commander noise (R102)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scripts.r98.acquisition_preflight import (
    COMMANDER_SIZE,
    PLA,
    archive_filename,
    archive_job,
    validate_payload,
)
from scripts.r100.source_intake import CHUNK_BYTES, compute_digests

ROOT = Path(__file__).resolve().parents[2]
R101_PLAN_ID = "commander_pr3_ffp10_noise_00000"
COMMANDER_NOISE_ID = "dx12_v3_commander_noise_mc_00000_raw.fits"
DEFAULT_DEST = Path("/home/cosmosapjw/Downloads/htt_r101")
DEFAULT_RECEIPT = (
    ROOT
    / "docs/research_program/observational_publication_20261015"
    / "R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123"
    / "ACQUISITION_RECEIPT.json"
)


def _validate_commander_headers(status: int, headers, filename: str, expected_bytes: int) -> tuple[bool, int | None]:
    """Validate HTTP 200 PLA Commander FITS headers, permitting verified chunked transfer."""
    if int(status) != 200:
        raise ValueError(f"expected HTTP 200 for full Commander product, got {status}")
    values: dict[str, list[str]] = {}
    for key, value in headers.items():
        values.setdefault(key.lower(), []).append(str(value).strip())

    ctype = ";".join(values.get("content-type", [])).lower()
    if "image/fits" not in ctype or any(bad in ctype for bad in ("html", "json", "xml")):
        raise ValueError(f"unexpected Content-Type for Commander FITS: {ctype!r}")

    c_enc = [x.lower() for x in values.get("content-encoding", [])]
    if c_enc not in ([], ["identity"]):
        raise ValueError(f"compressed Content-Encoding rejected: {c_enc!r}")

    disp_msg = {"Content-Disposition": values.get("content-disposition", [""])[0]}
    if archive_filename(disp_msg) != filename:
        raise ValueError(
            f"Content-Disposition filename mismatch: {archive_filename(disp_msg)!r} != {filename!r}"
        )

    te_vals = [x.lower() for x in values.get("transfer-encoding", [])]
    cl_vals = values.get("content-length", [])
    if cl_vals:
        if te_vals:
            raise ValueError("ambiguous response with both Content-Length and Transfer-Encoding")
        if len(cl_vals) != 1 or not cl_vals[0].isascii() or not cl_vals[0].isdigit():
            raise ValueError(f"invalid Content-Length header: {cl_vals!r}")
        cl = int(cl_vals[0])
        if cl != expected_bytes:
            raise ValueError(f"Content-Length {cl} != expected {expected_bytes}")
        return False, cl

    if te_vals != ["chunked"]:
        raise ValueError("expected either Content-Length or Transfer-Encoding: chunked")
    return True, None


def acquire_commander_noise(
    destination: Path = DEFAULT_DEST,
    *,
    max_bytes: int = COMMANDER_SIZE,
    timeout: float = 120.0,
    opener=urlopen,
    payload_validator=validate_payload,
) -> dict[str, object]:
    """Download/reuse dx12_v3_commander_noise_mc_00000_raw.fits safely with no-clobber link."""
    job = archive_job(COMMANDER_NOISE_ID)
    return _acquire(job, R101_PLAN_ID, destination, max_bytes, timeout, opener, payload_validator)


def ensemble_job(part: str, index: int) -> dict:
    """Fullmission matched PR3 products in the 300-realization noise range."""
    if part not in ("cmb", "noise") or type(index) is not int or not 0 <= index < 300:
        raise ValueError("expected cmb/noise and a realization in 0..299")
    name = f"dx12_v3_commander_{part}_mc_{index:05d}_raw.fits"
    return {"id": name, "url": PLA + name, "bytes": COMMANDER_SIZE}


def acquire_commander_product(part: str, index: int, destination: Path, *, max_bytes: int):
    job = ensemble_job(part, index)
    return _acquire(job, job["id"], destination, max_bytes, 120.0, urlopen, validate_payload)


def _acquire(job, product_id, destination, max_bytes, timeout, opener, payload_validator):
    filename = job["id"]
    expected_bytes = int(job["bytes"])
    if max_bytes < expected_bytes:
        raise ValueError(f"max_bytes={max_bytes} < required {expected_bytes}")
    url = str(job["url"])
    if urlparse(url).scheme != "https":
        raise ValueError(f"insecure scheme rejected: {url}")

    dest = Path(destination).resolve()
    if str(dest).startswith("/mnt/extdrive"):
        raise PermissionError(f"Refusing write under /mnt/extdrive: {dest}")
    target = dest / filename

    def _inspect_existing() -> dict[str, object]:
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"nonregular existing path: {target}")
        dig = compute_digests(target)
        if dig["bytes"] != expected_bytes:
            raise FileExistsError(f"preserved conflicting product at {target}: bytes={dig['bytes']}")
        fits_info = payload_validator(target, job)
        return {
            "id": product_id,
            "filename": filename,
            "path": str(target),
            "url": url,
            "release": "Planck PR3/FFP10 dx12_v3 Commander fullmission",
            "expected_bytes": expected_bytes,
            "downloaded": False,
            "transferred_bytes": 0,
            "status": "PRESENT_LOCAL_FITS_AND_DIGEST_VERIFIED",
            "bytes": dig["bytes"],
            "md5": dig["md5"],
            "sha256": fits_info["sha256"],
            "channels": fits_info.get("channels"),
            "provider_checksum": None,
            "provider_checksum_available": False,
            "commander_null_qualified": False,
        }

    if target.exists() or target.is_symlink():
        return _inspect_existing()

    dest.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.monotonic()
    req = Request(
        url,
        headers={
            "User-Agent": "htt-r102-commander-intake/1.0",
            "Accept-Encoding": "identity",
        },
    )

    with tempfile.TemporaryDirectory(prefix=".r102-cmd-intake-", dir=dest) as work:
        part = Path(work) / filename
        h_md5 = hashlib.md5()
        h_sha = hashlib.sha256()
        total = 0
        with opener(req, timeout=timeout) as resp:
            is_chunked, cl = _validate_commander_headers(
                resp.status, resp.headers, filename, expected_bytes
            )
            hdrs_norm = {k.lower(): str(v) for k, v in resp.headers.items()}
            with part.open("wb") as out:
                while True:
                    # Request at most 1 byte beyond expected_bytes to detect oversized bodies immediately.
                    cap = min(CHUNK_BYTES, expected_bytes + 1 - total)
                    if cap <= 0:
                        raise ValueError(f"stream exceeded expected_bytes={expected_bytes}")
                    block = resp.read(cap)
                    if not block:
                        break
                    if len(block) > cap:
                        raise ValueError("underlying reader returned more bytes than requested")
                    total += len(block)
                    if total > expected_bytes:
                        raise ValueError(
                            f"Commander response exceeded expected size: {total} > {expected_bytes}"
                        )
                    h_md5.update(block)
                    h_sha.update(block)
                    out.write(block)
                out.flush()
                os.fsync(out.fileno())
        if total != expected_bytes:
            raise ValueError(f"truncated Commander stream: {total} != {expected_bytes}")

        fits_info = payload_validator(part, job)
        actual_sha = h_sha.hexdigest()
        if fits_info["sha256"] != actual_sha:
            raise RuntimeError("streaming SHA-256 mismatch against FITS validation pass")
        try:
            os.link(part, target)
        except FileExistsError:
            existing = _inspect_existing()
            if existing["sha256"] != actual_sha:
                raise FileExistsError(f"concurrent differing product preserved: {target}") from None
            return dict(existing, transferred_bytes=total)

        return {
            "id": product_id,
            "filename": filename,
            "path": str(target),
            "url": url,
            "release": "Planck PR3/FFP10 dx12_v3 Commander fullmission",
            "expected_bytes": expected_bytes,
            "downloaded": True,
            "transferred_bytes": total,
            "status": "FETCHED_CHUNKED_FITS_VERIFIED_EXACT_BYTES"
            if is_chunked
            else "FETCHED_EXACT_LENGTH_FITS_VERIFIED",
            "transfer_encoding_chunked": is_chunked,
            "response_content_length": cl,
            "bytes": total,
            "md5": h_md5.hexdigest(),
            "sha256": actual_sha,
            "channels": fits_info.get("channels"),
            "fetched_at_utc": started,
            "elapsed_seconds": time.monotonic() - t0,
            "http_status": 200,
            "headers": {
                k: hdrs_norm[k]
                for k in (
                    "content-type",
                    "content-disposition",
                    "content-length",
                    "transfer-encoding",
                    "content-encoding",
                )
                if k in hdrs_norm
            },
            "provider_checksum": None,
            "provider_checksum_available": False,
            "commander_null_qualified": False,
        }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destination", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--max-bytes", type=int, default=COMMANDER_SIZE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    ap.add_argument("--sdss-receipt-json", type=str, default=None)
    args = ap.parse_args(argv)

    cmd_rec = acquire_commander_noise(destination=args.destination, max_bytes=args.max_bytes)
    payload = {
        "schema": "htt.r102.acquisition_receipt/1",
        "destination": str(args.destination.resolve()),
        "live_endpoint_finding": (
            "PLA endpoint https://pla.esac.esa.int/pla/aio/product-action responds HTTP 200 "
            "with Content-Type=image/fits, inline FITS SIMPLE=T, Transfer-Encoding=chunked, "
            "and no Content-Length (ignoring Range), which trips R101's strict fixed-Content-Length check "
            "(scripts/r101/acquire.py). R101/R99 contracts are preserved unchanged; R102 acquires "
            "dx12_v3_commander_noise_mc_00000_raw.fits via strict <=603,987,840 B bounded chunked stream + full FITS validation."
        ),
        "commander_pr3_ffp10_noise_00000": cmd_rec,
        "sdss_randoms_v1_1": json.loads(args.sdss_receipt_json) if args.sdss_receipt_json else None,
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps(cmd_rec, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
