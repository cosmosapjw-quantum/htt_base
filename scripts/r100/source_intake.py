"""R100 Step A1: Bounded validated intake of SDSS PV v1.1.0 and 6dFGSv table1.txt.

Downloads strictly to /home/cosmosapjw/Downloads/htt_r100/source_intake/ within
the explicit <= 22,000,000-byte budget, validates HTTP status/headers/byte
count/checksums, rejects HTTP 202 deferred JSON, parses exact identifiers safely,
and persists SOURCE_INTAKE_RECEIPT.json under R100 outputs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scripts.r99.acquisition import (
    DeferredProduct,
    exact_identifier,
    sha as sha256_file,
    validate_product_response,
    write_json,
)

ROOT = Path(__file__).resolve().parents[2]
R99_DIR = ROOT / "docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123"
R100_DIR = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
INTAKE_DIR = Path("/home/cosmosapjw/Downloads/htt_r100/source_intake")
MAX_TOTAL_BYTES = 22_000_000
CHUNK_BYTES = 262_144

PRODUCTS = {
    "sdss_pv_v1_1": {
        "url": "https://zenodo.org/api/records/6824749/files/SDSS_PV_public.dat/content",
        "filename": "SDSS_PV_public.dat",
        "expected_bytes": 20_231_640,
        "expected_md5": "b5b6e31caf7ea469c2ac2cb775fa8d14",
        "release": "Howlett et al. 2022, Zenodo 10.5281/zenodo.6824749 v1.1.0",
    },
    "sixdf_pv_table1": {
        "url": "https://www.mso.anu.edu.au/6dfgs/vfield/table1.txt",
        "filename": "table1.txt",
        "expected_bytes": 696_070,
        "expected_md5": None,
        "release": "Springob et al. 2014, 6dFGSv table1.txt",
    },
}


def compute_digests(path: Path) -> dict[str, object]:
    """Compute size, MD5, and SHA-256 in a single streaming pass."""
    h_md5 = hashlib.md5()
    h_sha = hashlib.sha256()
    nbytes = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_BYTES)
            if not chunk:
                break
            nbytes += len(chunk)
            h_md5.update(chunk)
            h_sha.update(chunk)
    return {
        "bytes": nbytes,
        "md5": h_md5.hexdigest(),
        "sha256": h_sha.hexdigest(),
    }


def download_bounded_product(
    product_id: str,
    spec: dict[str, object],
    dest_dir: Path = INTAKE_DIR,
    *,
    max_bytes_remaining: int = MAX_TOTAL_BYTES,
    timeout: float = 60.0,
    opener=urlopen,
) -> dict[str, object]:
    """Download one product atomically with strict header, byte-cap, and MD5 guards."""
    url = str(spec["url"])
    filename = str(spec["filename"])
    expected_bytes = int(spec["expected_bytes"])
    expected_md5 = spec.get("expected_md5")
    if urlparse(url).scheme != "https":
        raise ValueError(f"{product_id}: insecure scheme rejected")
    if expected_bytes > max_bytes_remaining:
        raise ValueError(
            f"{product_id}: expected {expected_bytes} B exceeds remaining budget {max_bytes_remaining} B"
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    # Never write inside /mnt/extdrive
    resolved = dest_dir.resolve()
    if str(resolved).startswith("/mnt/extdrive"):
        raise PermissionError(f"Refusing write under /mnt/extdrive: {resolved}")

    target = resolved / filename
    if target.exists():
        dig = compute_digests(target)
        md5_ok = (expected_md5 is None) or (dig["md5"] == expected_md5)
        if dig["bytes"] == expected_bytes and md5_ok:
            return {
                "product_id": product_id,
                "url": url,
                "local_path": str(target),
                "release": spec["release"],
                "download_performed": False,
                "reused_verified_local": True,
                "expected_bytes": expected_bytes,
                "bytes": dig["bytes"],
                "expected_md5": expected_md5,
                "actual_md5": dig["md5"],
                "sha256": dig["sha256"],
                "verified": True,
            }

    part = resolved / f".{filename}.part.{os.getpid()}"
    req = Request(url, headers={"User-Agent": "htt-r100-intake/1.0", "Accept-Encoding": "identity"})
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    t0 = time.monotonic()
    h_md5 = hashlib.md5()
    h_sha = hashlib.sha256()
    total_read = 0
    try:
        with opener(req, timeout=timeout) as resp:
            status = int(resp.status)
            headers = {k.lower(): str(v) for k, v in resp.headers.items()}
            validate_product_response(status, headers, expected_bytes)
            with part.open("wb") as out:
                while True:
                    chunk = resp.read(CHUNK_BYTES)
                    if not chunk:
                        break
                    total_read += len(chunk)
                    if total_read > expected_bytes or total_read > max_bytes_remaining:
                        raise ValueError(
                            f"{product_id}: stream exceeded cap ({total_read} > min({expected_bytes}, {max_bytes_remaining}))"
                        )
                    h_md5.update(chunk)
                    h_sha.update(chunk)
                    out.write(chunk)
        if total_read != expected_bytes:
            raise ValueError(f"{product_id}: truncated stream {total_read} != {expected_bytes}")
        actual_md5 = h_md5.hexdigest()
        actual_sha = h_sha.hexdigest()
        if expected_md5 is not None and actual_md5 != expected_md5:
            raise ValueError(f"{product_id}: MD5 mismatch {actual_md5} != {expected_md5}")
        part.replace(target)
    except Exception:
        if part.exists():
            part.unlink()
        raise

    return {
        "product_id": product_id,
        "url": url,
        "local_path": str(target),
        "release": spec["release"],
        "download_performed": True,
        "reused_verified_local": False,
        "fetched_at_utc": started,
        "elapsed_seconds": time.monotonic() - t0,
        "http_status": status,
        "headers": {
            k: headers[k]
            for k in ("content-type", "content-length", "content-range", "etag", "last-modified", "accept-ranges")
            if k in headers
        },
        "expected_bytes": expected_bytes,
        "bytes": total_read,
        "expected_md5": expected_md5,
        "actual_md5": actual_md5,
        "sha256": actual_sha,
        "verified": True,
    }


def _tabular_sanity_check(sdss_path: Path, sixdf_path: Path) -> dict[str, object]:
    """Verify row counts and exact ID/sentinel parsing constraints on downloaded catalogs."""
    sdss_rows = 0
    sdss_pgcs = set()
    sdss_groups = set()
    sdss_objids_exact = 0
    sdss_specobj_tokens = 0
    with sdss_path.open("r", encoding="ascii") as f:
        header = f.readline().lstrip("#").split()
        idx = {name: i for i, name in enumerate(header)}
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) != len(header):
                raise ValueError(f"SDSS row column count mismatch: {len(parts)} != {len(header)}")
            sdss_pgcs.add(exact_identifier(parts[idx["PGC"]]))
            sdss_groups.add(exact_identifier(parts[idx["IDgroupT17"]]))
            # objid is a full decimal 64-bit integer; specObjID is serialized in E18 scientific notation.
            _ = exact_identifier(parts[idx["objid"]])
            sdss_objids_exact += 1
            if parts[idx["specObjID"]]:
                sdss_specobj_tokens += 1
            _ = exact_identifier(parts[idx["in_mask"]])
            sdss_rows += 1

    sixdf_rows = 0
    sixdf_ungrouped_sentinel = 0
    sixdf_grouped = 0
    with sixdf_path.open("r", encoding="ascii") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) != 9:
                raise ValueError(f"6dFGSv row column count mismatch: {len(parts)} != 9")
            cz_group = int(parts[4])
            grp_id = int(parts[5])
            if cz_group == -1 or grp_id == -1:
                sixdf_ungrouped_sentinel += 1
            else:
                sixdf_grouped += 1
            sixdf_rows += 1

    return {
        "sdss_pv_v1_1": {
            "header_columns": len(header),
            "data_rows": sdss_rows,
            "unique_pgc": len(sdss_pgcs),
            "unique_idgroupt17_incl_0": len(sdss_groups),
            "exact_integer_objids_parsed": sdss_objids_exact,
            "specobjid_raw_tokens_retained": sdss_specobj_tokens,
            "specobjid_format_note": "Scientific notation (e.g. 1.95125...E18) retained as verbatim string; objid retained as exact int64.",
        },
        "sixdf_pv_table1": {
            "data_rows": sixdf_rows,
            "ungrouped_sentinel_minus1_rows": sixdf_ungrouped_sentinel,
            "grouped_rows": sixdf_grouped,
        },
    }


def run_intake(max_total_bytes: int = MAX_TOTAL_BYTES, dest_dir: Path = INTAKE_DIR) -> dict[str, object]:
    """Download/verify both upstream catalogs within budget and emit receipt JSON."""
    if max_total_bytes > MAX_TOTAL_BYTES:
        raise ValueError(f"max_total_bytes={max_total_bytes} exceeds campaign cap {MAX_TOTAL_BYTES}")
    expected_sum = sum(int(s["expected_bytes"]) for s in PRODUCTS.values())
    if expected_sum > max_total_bytes:
        raise ValueError(f"Combined expected bytes {expected_sum} exceeds budget {max_total_bytes}")

    r99_plan = json.loads((R99_DIR / "ACQUISITION_PLAN.json").read_text())
    r99_lookup = {j["id"]: j for j in r99_plan["jobs"]}
    for pid, spec in PRODUCTS.items():
        if r99_lookup[pid]["url"] != spec["url"] or r99_lookup[pid]["expected_bytes"] != spec["expected_bytes"]:
            raise ValueError(f"R99 plan contract drift for {pid}")

    remaining = max_total_bytes
    products_receipt = {}
    total_actual = 0
    for pid, spec in PRODUCTS.items():
        rec = download_bounded_product(pid, spec, dest_dir=dest_dir, max_bytes_remaining=remaining)
        remaining -= int(rec["bytes"])
        total_actual += int(rec["bytes"])
        products_receipt[pid] = rec

    sanity = _tabular_sanity_check(
        Path(products_receipt["sdss_pv_v1_1"]["local_path"]),
        Path(products_receipt["sixdf_pv_table1"]["local_path"]),
    )

    receipt = {
        "schema": "htt.r100.source_intake_receipt/1",
        "owner": "obsstat",
        "status": "SOURCE_QUALIFIED_UPSTREAM_CATALOG_INTAKE",
        "budget_cap_bytes": max_total_bytes,
        "total_verified_bytes": total_actual,
        "remaining_budget_bytes": remaining,
        "storage_root": str(dest_dir.resolve()),
        "r99_acquisition_plan_sha256": sha256_file(R99_DIR / "ACQUISITION_PLAN.json"),
        "products": products_receipt,
        "tabular_sanity": sanity,
        "producer_path": str(Path(__file__).resolve()),
        "producer_sha256": sha256_file(__file__),
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    write_json(R100_DIR / "SOURCE_INTAKE_RECEIPT.json", receipt)
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-bytes", type=int, default=MAX_TOTAL_BYTES)
    args = ap.parse_args(argv)
    rec = run_intake(max_total_bytes=args.max_bytes)
    print(json.dumps({
        "status": rec["status"],
        "total_verified_bytes": rec["total_verified_bytes"],
        "sdss_rows": rec["tabular_sanity"]["sdss_pv_v1_1"]["data_rows"],
        "sixdf_rows": rec["tabular_sanity"]["sixdf_pv_table1"]["data_rows"],
        "receipt": str(R100_DIR / "SOURCE_INTAKE_RECEIPT.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
