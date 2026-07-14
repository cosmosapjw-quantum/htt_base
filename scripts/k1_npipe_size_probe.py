#!/usr/bin/env python3
"""Measure the PR4/NPIPE E2E download volume and decide whether it fits the NVMe.

The NVMe cannot hold PR3 (FFP10, ~1 TB) and PR4 (NPIPE) simultaneously, so the exact
NPIPE volume decides the acquisition path: coexist (never), swap-after-PR3-delete, a
subset stream, or blocked. The PLA/NERSC listings are behind an interactive
portal / authentication, so this probe works two ways:

  * `--head-list <file>`: a text file of direct map URLs (one per line, e.g. exported
    from the authenticated NERSC listing). The probe HTTP-HEAD each URL, sums
    Content-Length -> exact total bytes. No credentials are stored; if a URL needs a
    session cookie, pass it via `--header "Cookie: ..."`.
  * `--du-listing <file>`: paste of a `du -ab`/`ls -l` style listing from an
    authenticated shell (NERSC). The probe parses the byte column and sums.

Given the total and the disk state it prints one of:
  FITS_ALONGSIDE_PR3 / FITS_AFTER_PR3_DELETE / NEEDS_SUBSET_STREAM / BLOCKED_TOO_LARGE.

With no listing it prints the documented estimate (below) + the exact command to run
once authenticated. Estimates are grounded in the NPIPE release facts (600 full-frequency
+ detector-set MC realizations; FFP10 = 300 residual MC per frequency); the K1-USABLE
product is NOT the full frequency ensemble but a component-separated CMB sim set or a
single cleaned channel.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs/generated"
NVME = "/mnt/sn850x2t"

# Documented estimates (grounded in the PLA wiki + K1_E2E_DOWNLOAD_GUIDE; exact bytes
# require an authenticated listing). Sizes are for the K1 low-ell morphology use case.
ESTIMATES = {
    "ffp10_smica_k1": {
        "what": "FFP10 component-separated SMICA CMB MC (999 usable) + noise MC (300) at Nside=2048 IQU",
        "approx_tb": 1.0,
        "note": "the PR3 product actually used for K1; ~1 TB (guide: 'Full IQU Nside=2048 is ~1 TB')",
    },
    "npipe_full_frequency": {
        "what": "NPIPE 600 full-frequency + detector-set E2E MC (9 freq x A/B), Nside=2048 IQU",
        "approx_tb": 5.0,      # 600 x ~9 freq x ~0.5-1 GB, x A/B; multi-TB, order 5+ TB
        "note": "the FULL frequency ensemble; DOES NOT FIT the 1.8 TB NVMe even after deleting PR3 -- do NOT download whole",
    },
    "npipe_k1_usable": {
        "what": "NPIPE K1-usable subset: component-separated CMB sims (~600) OR one cleaned channel, Nside=2048 IQU",
        "approx_tb": 0.6,      # ~600 x ~0.5-1 GB single product; ~0.3-1 TB
        "note": "the ONLY NPIPE product needed for K1; ~0.3-1 TB -> fits AFTER deleting PR3, not alongside it. Measure exactly before deleting.",
    },
}


def _disk_free_bytes(path: str) -> int | None:
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return None


def _reclaimable_bytes(pr3_dir: str | None) -> tuple[int | None, str]:
    """Bytes freed by deleting the PR3 raw ensemble. Only meaningful when --pr3-dir
    names the ACTUAL directory that would be deleted; otherwise return None (never
    assume deleting PR3 frees the whole shared e2e tree, which also holds ACT sims,
    reconstructions, and the K1 reduced cache)."""
    if pr3_dir is None:
        return None, "no --pr3-dir given; reclaimable-after-delete not estimated"
    root = Path(pr3_dir)
    if not root.is_dir():
        return None, f"--pr3-dir {pr3_dir} not found"
    try:
        out = subprocess.run(["du", "-sb", str(root)], capture_output=True, text=True,
                             timeout=180)
        if out.returncode == 0:
            return int(out.stdout.split()[0]), f"du -sb {pr3_dir}"
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return None, f"du failed: {e}"
    return None, "du returned nonzero"


def _sum_head(url_list: Path, headers: list[str]) -> tuple[int, int, list[str]]:
    import urllib.request
    total = 0
    n = 0
    misses: list[str] = []
    for line in url_list.read_text().splitlines():
        u = line.strip()
        if not u or u.startswith("#"):
            continue
        req = urllib.request.Request(u, method="HEAD")
        for h in headers:
            k, _, v = h.partition(":")
            req.add_header(k.strip(), v.strip())
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                cl = r.headers.get("Content-Length")
                if cl is None:
                    misses.append(u)
                    continue
                total += int(cl)
                n += 1
        except Exception as e:  # noqa: BLE001 -- report, never fabricate a size
            misses.append(f"{u}  [{e}]")
    return total, n, misses


def _sum_du(listing: Path) -> tuple[int, int]:
    """Sum the leading byte column of a `du -ab` / `ls -l` style listing."""
    total = 0
    n = 0
    for line in listing.read_text().splitlines():
        m = re.match(r"\s*(\d{4,})\s", line)          # a byte count (>= 1 KB) at line start
        if m:
            total += int(m.group(1))
            n += 1
    return total, n


def _decision(npipe_bytes: int, free: int | None, reclaim: int | None) -> dict:
    tb = npipe_bytes / 1e12
    free_after_delete = None
    if free is not None and reclaim is not None:
        free_after_delete = free + reclaim     # deleting the named PR3 dir returns its bytes
    verdict = "UNKNOWN (no disk numbers)"
    if free is not None:
        if npipe_bytes <= free:
            verdict = "FITS_ALONGSIDE_PR3"
        elif free_after_delete is not None and npipe_bytes <= free_after_delete:
            verdict = "FITS_AFTER_PR3_DELETE (swap: reduce+gate PR3 -> delete raw -> download NPIPE)"
        else:
            verdict = ("NEEDS_SUBSET_STREAM or BLOCKED_TOO_LARGE: even after deleting PR3 the "
                       "NVMe cannot hold NPIPE -> download a K1-usable subset (component-separated "
                       "CMB sims / one cleaned channel), or stream+reduce in chunks, or use external storage")
    return {"npipe_total_bytes": npipe_bytes, "npipe_total_tb": round(tb, 3),
            "nvme_free_bytes": free, "reclaimable_by_pr3_delete_bytes": reclaim,
            "free_after_pr3_delete_bytes": free_after_delete, "verdict": verdict}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--head-list", type=Path, default=None,
                    help="text file of direct NPIPE map URLs (HTTP HEAD each -> exact bytes)")
    ap.add_argument("--header", action="append", default=[],
                    help="HTTP header for --head-list (e.g. --header 'Cookie: ...'); repeatable")
    ap.add_argument("--du-listing", type=Path, default=None,
                    help="paste of a du -ab / ls -l listing from an authenticated NERSC shell")
    ap.add_argument("--nvme", default=NVME)
    ap.add_argument("--pr3-dir", default=None,
                    help="the ACTUAL PR3 raw dir that would be deleted (du'd for the "
                         "reclaimable-after-delete figure); omit to leave it unestimated")
    ap.add_argument("--out", type=Path, default=GEN / "k1_npipe_size_probe.json")
    args = ap.parse_args(argv)

    free = _disk_free_bytes(args.nvme)
    reclaim, reclaim_src = _reclaimable_bytes(args.pr3_dir)
    payload: dict = {"schema": "htt.k1.npipe_size_probe.v1", "owner": "OBSSTAT",
                     "claim_tier": "diagnostic_only", "nvme": args.nvme,
                     "estimates": ESTIMATES,
                     "note": "NPIPE full-frequency ensemble is multi-TB and will NOT fit; "
                             "download only the K1-usable component-separated / single-channel subset"}

    if args.head_list:
        total, n, misses = _sum_head(args.head_list, args.header)
        payload["measured"] = {"method": "http_head", "n_files": n,
                               "unresolved": misses[:50], "n_unresolved": len(misses)}
        payload.update(_decision(total, free, reclaim))
    elif args.du_listing:
        total, n = _sum_du(args.du_listing)
        payload["measured"] = {"method": "du_listing", "n_files": n}
        payload.update(_decision(total, free, reclaim))
    else:
        payload["measured"] = None
        payload["how_to_measure"] = [
            "On an authenticated NERSC shell, list the NPIPE K1-usable sim product and run "
            "`du -ab <dir> > npipe_listing.txt`, then: "
            "venv/bin/python scripts/k1_npipe_size_probe.py --du-listing npipe_listing.txt",
            "Or export the direct map URLs to urls.txt and run: "
            "venv/bin/python scripts/k1_npipe_size_probe.py --head-list urls.txt --header 'Cookie: <session>'",
        ]
        # still emit the disk state + estimate-based decision for the K1-usable subset
        est = int(ESTIMATES["npipe_k1_usable"]["approx_tb"] * 1e12)
        payload["reclaim_source"] = reclaim_src
        payload["estimate_based_decision"] = _decision(est, free, reclaim)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.out.relative_to(REPO_ROOT)}")
    if free is not None:
        print(f"   NVMe free = {free/1e12:.3f} TB"
              + (f"; reclaimable by PR3 delete = {reclaim/1e12:.3f} TB; free after = "
                 f"{(free+reclaim)/1e12:.3f} TB" if reclaim else "; (--pr3-dir unset)"))
    dec = payload.get("estimate_based_decision") or payload
    if "verdict" in dec:
        print(f"   verdict = {dec['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
