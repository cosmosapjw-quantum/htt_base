"""R108 gaia lane: receipt lines for inputs that were not downloaded in R108 (RCPT-1 of the R108 review).

Purpose
    Every raw input of the gaia lane gets a line in ~/Downloads/htt_r108/gaia/RECEIPTS.jsonl. The R108 downloads (D08, D08G,
    D09, D10F) already have receipts; the R106-pinned inputs read through scripts/r108/gaia_estimator.py (Quaia x Gaia
    join, Quaia full join used by the CRF3 complement, Gaia-CRF3 FITS, R98 receipt and patch cache, R106 GAIA_OBSERVED.json)
    get 'pre-existing input' lines: {id, name, path, bytes, sha256, status, route, originating_round, origin, used_by,
    referenced_in, pinned_in_code, pinned_sha256_match, recorded_at_utc, recorded_by}. Each SHA-256 is computed now and must
    equal the pin of the owning R106/R103 module (fail closed otherwise). Lines are appended once (same id and SHA-256).
Inputs: the files above (paths and pins from scripts/r106/gaia_null_refit.py and scripts/r103/gaia_frame_curvature.py).
Units: bytes.
Usage (repo root): python3 -m scripts.r108.gaia_input_receipts [--dry-run]
No randomness.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as r106
from scripts.r108.radio_input_receipts import PRE, append_receipts, entry, sha256

GAIA_DL = Path.home() / "Downloads/htt_r108/gaia"
R106_OBSERVED = Path("docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124/GAIA/GAIA_OBSERVED.json")
USERS = ["scripts/r108/gaia_estimator.py (load_context)", "scripts/r108/gaia_scan_null.py", "scripts/r108/gaia_frame_leakage.py",
         "scripts/r108/gaia_agn_split.py"]


def pinned(e, pin):
    """Attach the pin comparison; fail closed if the file no longer has the pinned SHA-256."""
    if e["sha256"] != pin:
        raise ValueError(f"{e['id']}: SHA-256 {e['sha256']} differs from the pin {pin}")
    return dict(e, pinned_sha256_match=True)


def gaia_entries():
    meta = json.loads(Path(g.SOURCE).read_text())["joint_160d_patch_covariance"]
    return [
        pinned(entry("PRE:quaia_crf3_join", r106.JOIN, PRE, "A22 (2026-10-23) / pinned in R106",
                     "Quaia x Gaia-CRF3 qualified join (634,233 R106 rows); pinned by scripts/r106/gaia_null_refit.py JOIN_SHA",
                     USERS), r106.JOIN_SHA),
        pinned(entry("PRE:quaia_gaia_full_join", r106.FULL_JOIN, PRE, "A22 (2026-10-23) / pinned in R106",
                     "Quaia x Gaia full join (ids removed from the CRF3 complement); pinned by FULL_JOIN_SHA",
                     ["scripts/r108/gaia_scan_null.py (calibrate)", "scripts/r108/gaia_frame_leakage.py (part B)"]), r106.FULL_JOIN_SHA),
        pinned(entry("PRE:gaia_crf3_astrometry_full", r106.CRF3, PRE, "pre-R106 bundle / pinned in R106",
                     "Gaia DR3 gaia_crf3_xm x gaia_source astrometry FITS (1,614,173 rows); pinned by CRF3_SHA", USERS), r106.CRF3_SHA),
        pinned(entry("PRE:R98_GAIA_FULL_SHARED_PATCH", g.SOURCE, PRE, "R98",
                     "R98 shell x patch receipt (redshift medians, patch covariance metadata); pinned by R103 SOURCE_SHA",
                     ["scripts/r108/gaia_estimator.py (load_context)"]), g.SOURCE_SHA),
        pinned(entry("PRE:R98_patch_cache", meta["cache_path"], PRE, "R98",
                     "R98 per-shell per-patch normal-equation cache (F, s, n); pinned by the R98 receipt",
                     ["scripts/r108/gaia_estimator.py (load_context)"]), meta["sha256"]),
        entry("PRE:R106_GAIA_OBSERVED", R106_OBSERVED, PRE, "R106",
              "R106 observed Gaia/Quaia statistics (replay target and observed Q)",
              ["scripts/r108/gaia_estimator.py (r106_replay)", "scripts/r108/gaia_scan_null.py (summarize)"]),
    ]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipts", default=str(GAIA_DL / "RECEIPTS.jsonl"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    res = append_receipts(a.receipts, gaia_entries(), "scripts/r108/gaia_input_receipts.py (sha256 "
                          f"{sha256(Path(__file__))})", a.dry_run)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
