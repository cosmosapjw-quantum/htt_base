#!/usr/bin/env python3
"""Extract the three CF4 group peculiar-velocity estimators (REV-R196).

The frozen `cf4_groups.npz` (hashed by the rev-r195 card) carries only the
`Vpec` RAMP peculiar velocity. The raw VizieR table4 (J/ApJ/944/94) also
provides two more estimators for the SAME 38053 groups:

  Vpds  (cols 52-57)  Davis & Scrimgeour 2014, Eq. 9   -- DIRECT (least model-dependent)
  Vpwf  (cols 59-63)  Watkins & Feldman 2015           -- pure Wiener-filter
  Vpec  (cols 65-69)  ramp Eq. 11                      -- WF-ramp blend (frozen npz)

These three are genuinely different reconstruction/estimator variants: the
reconstruction-method-dependence lane runs the same bulk-flow estimator on each,
and the reconstruction-INDEPENDENT statistics attach to the DIRECT `Vpds`.

This never rewrites `cf4_groups.npz`; it writes a NEW keyed-by-PGC variants npz.
Acquisition/extraction only (no analysis). Idempotent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TABLE4 = REPO / "workdir/raw/cf4_full/table4.dat"
OUT = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_pv_variants.npz"

# 1-indexed byte ranges from the VizieR ReadMe (confirmed on disk)
COLS = {"PGC": (1, 7), "Vpds": (52, 57), "Vpwf": (59, 63), "Vpec": (65, 69)}


def _parse(path: Path) -> dict[str, np.ndarray]:
    cols: dict[str, list] = {k: [] for k in COLS}
    with path.open(encoding="latin-1") as fh:
        for line in fh:
            if not line.strip():
                continue
            for name, (a, b) in COLS.items():
                tok = line[a - 1:b].strip()
                try:
                    cols[name].append(float(tok) if tok not in ("", "-") else np.nan)
                except ValueError:
                    cols[name].append(np.nan)
    return {k: np.asarray(v, dtype=float) for k, v in cols.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the on-disk npz matches a fresh extraction")
    args = ap.parse_args(argv)
    if not TABLE4.is_file():
        print(f"BLOCKED_MISSING_CF4_TABLE4: {TABLE4} not present")
        return 1
    parsed = _parse(TABLE4)
    n = len(parsed["PGC"])

    if args.check:
        if not OUT.is_file():
            print("STALE cf4_pv_variants.npz (missing)")
            return 1
        cur = np.load(OUT)
        ok = all(np.array_equal(np.nan_to_num(cur[k]), np.nan_to_num(parsed[k]))
                 for k in COLS)
        print("cf4 pv variants current" if ok else "STALE cf4_pv_variants.npz")
        return 0 if ok else 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, **parsed)
    manifest = {
        "release": "Cosmicflows-4 (Tully+ 2023), VizieR J/ApJ/944/94 table4",
        "n_groups": n,
        "table4_sha256": hashlib.sha256(TABLE4.read_bytes()).hexdigest(),
        "columns": {"Vpds": "Davis-Scrimgeour 2014 direct (Eq.9)",
                    "Vpwf": "Watkins-Feldman 2015 Wiener-filter",
                    "Vpec": "ramp Eq.11 (WF blend; == frozen cf4_groups.npz)"},
        "out_npz": OUT.name,
    }
    (OUT.parent / "cf4_pv_variants_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    finite = {k: int(np.isfinite(parsed[k]).sum()) for k in COLS}
    print(f"wrote {OUT}  n={n}  finite={finite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
