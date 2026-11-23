"""Plan remaining R99 products. Executing an explicitly budgeted subset is opt-in."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
PLAN = (ROOT / "docs/research_program/observational_publication_20261015"
        / "R99_FIFTH_BLOCKER_RESOLUTION_20261123/ACQUISITION_PLAN.json")
R99_PLAN_SHA = "012ebc7a87a4c5ef8a6c37307232a4c8ad733411163944428aea1cf29df3cdb9"
# The other two R99 jobs were already completed in R100.
FILENAMES = {
    "commander_pr3_ffp10_noise_00000": "dx12_v3_commander_noise_mc_00000_raw.fits",
    "sdss_randoms_v1_1": "SDSS_randoms_public.dat",
    "sdss_mocks_v1_1": "mocks.tar.gz",
    "sixdf_reconstruction_mocks": "6dFGSRecon_Files.tar.gz",
    "lotss_aux_1078": "HP-misc-1078.tar",
    "lotss_aux_355": "HP-misc-355.tar",
}


def _require_fixed_identity_body(headers, expected):
    # HTTPMessage.items() preserves repeated header fields. Converting to a
    # dict first would silently lose a conflicting Content-Length.
    values = {}
    for key, value in headers.items():
        values.setdefault(key.lower(), []).append(str(value).strip())
    lengths = values.get("content-length", [])
    if (len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit()
            or int(lengths[0]) != expected):
        raise ValueError("expected one Content-Length matching the product size")
    if "transfer-encoding" in values:
        raise ValueError("Transfer-Encoding conflicts with fixed-length intake")
    if [x.lower() for x in values.get("content-encoding", [])] not in ([], ["identity"]):
        raise ValueError("the product must have identity Content-Encoding")


class _ProductBody:
    """Read the HTTP-framed science body, capping the read request itself."""

    def __init__(self, response, length):
        self._response = response
        self._remaining = length
        self.headers = response.headers
        self.status = response.status

    def read(self, size):
        if self._remaining == 0:
            return b""
        count = self._remaining if size < 0 else min(size, self._remaining)
        part = self._response.read(count)
        if len(part) > count:
            raise ValueError("response reader returned more than requested")
        self._remaining -= len(part)
        return part


def acquire_one(job, destination, budget, *, fetch, digests, validate_headers, opener=urlopen):
    """Reuse identifiable content or publish a validated download without clobbering."""
    pid = job["id"]
    filename = FILENAMES[pid]
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise ValueError(f"invalid product basename: {filename}")
    expected_bytes = job["expected_bytes"]
    if budget < expected_bytes:
        raise ValueError(f"insufficient remaining budget for {pid}")
    checksum = job.get("checksum")
    if checksum is not None and not checksum.startswith("md5:"):
        raise ValueError(f"unsupported source checksum for {pid}")
    expected_md5 = checksum.split(":", 1)[1] if checksum else None
    spec = dict(url=job["url"], filename=filename, expected_bytes=expected_bytes,
                expected_md5=expected_md5, release=job.get("release", pid))
    target = destination / filename
    common = dict(id=pid, path=str(target), url=spec["url"], release=spec["release"],
                  expected_bytes=expected_bytes, provider_checksum=checksum,
                  provider_checksum_available=checksum is not None)

    def inspect_existing():
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"nonregular existing path: {target}")
        digest = digests(target)
        if digest["bytes"] != expected_bytes or (expected_md5 and digest["md5"] != expected_md5):
            raise FileExistsError(f"preserved conflicting product: {target}")
        return dict(common, **digest, downloaded=False,
                    status="REUSED_PROVIDER_MD5_VERIFIED" if expected_md5 else "PRESENT_LOCAL_DIGEST_ONLY")

    if target.exists() or target.is_symlink():
        return inspect_existing()
    if pid.startswith("lotss_aux_"):
        # The R99 200/202 observations are historical. A current HEAD response
        # must describe an online science payload before the ordinary HTTPS GET.
        req = Request(job["url"], method="HEAD", headers={"Accept-Encoding": "identity"})
        with opener(req, timeout=60) as resp:
            if resp.status == 202:
                return dict(common, status="DEFERRED_HTTP_202", downloaded=False, bytes=0)
            validate_headers(resp.status, resp.headers, expected_bytes)
            _require_fixed_identity_body(resp.headers, expected_bytes)

    @contextmanager
    def open_bounded(request, **kwargs):
        with opener(request, **kwargs) as response:
            if response.status == 200:
                _require_fixed_identity_body(response.headers, expected_bytes)
            yield _ProductBody(response, expected_bytes)

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".r101-intake-", dir=destination) as work:
        rec = fetch(pid, spec, Path(work), max_bytes_remaining=budget, opener=open_bounded)
        if not rec["verified"]:
            raise RuntimeError(f"source intake verification failed for {pid}")
        try:
            os.link(Path(work) / filename, target)  # same filesystem, atomic no-replace
        except FileExistsError:
            existing = inspect_existing()
            if existing["sha256"] != rec["sha256"]:
                raise FileExistsError(f"concurrent differing product preserved: {target}") from None
            return dict(existing, transferred_bytes=rec["bytes"])
        return dict(common, status="FETCHED_PROVIDER_MD5_VERIFIED" if expected_md5 else
                    "FETCHED_EXACT_LENGTH_LOCAL_DIGEST", downloaded=True, bytes=rec["bytes"],
                    md5=rec["actual_md5"], sha256=rec["sha256"],
                    fetched_at_utc=rec["fetched_at_utc"], http_status=rec["http_status"],
                    headers=rec["headers"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ids", nargs="+", choices=list(FILENAMES))
    ap.add_argument("--max-bytes", type=int)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--destination", type=Path)
    args = ap.parse_args(argv)
    if args.execute and (not args.ids or args.max_bytes is None or args.destination is None):
        ap.error("--execute requires --ids, --max-bytes and --destination")
    if bool(args.ids) != (args.max_bytes is not None):
        ap.error("select jobs with both --ids and --max-bytes")
    raw = PLAN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != R99_PLAN_SHA:
        raise ValueError("R99 plan differs from the source used by R100 intake")
    plan = json.loads(raw)
    jobs = {j["id"]: j for j in plan["jobs"]}
    if not args.ids:
        print(json.dumps({"mode": "PLAN_ONLY", "jobs": [jobs[pid] for pid in FILENAMES]}, indent=2))
        return 0
    from scripts.r99.acquisition import select_jobs
    selection = select_jobs(plan, args.ids, args.max_bytes)
    if not args.execute:
        print(json.dumps(selection, indent=2))
        return 0

    from scripts.r100.source_intake import compute_digests, download_bounded_product
    from scripts.r99.acquisition import validate_product_response
    remaining = args.max_bytes
    for pid in args.ids:
        rec = acquire_one(jobs[pid], args.destination.resolve(), remaining,
                          fetch=download_bounded_product, digests=compute_digests,
                          validate_headers=validate_product_response)
        rec["transferred_bytes"] = rec.get("transferred_bytes", rec["bytes"] if rec["downloaded"] else 0)
        remaining -= rec["transferred_bytes"]
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        if rec["status"] == "DEFERRED_HTTP_202":
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
