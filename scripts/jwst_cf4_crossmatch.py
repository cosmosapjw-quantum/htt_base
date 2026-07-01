#!/usr/bin/env python3
"""Cross-match JWST distance anchors to the CF4 group catalogue and emit the compact
anchor set (matched CF4 group indices + the JWST distance-modulus precision) that the
Omega_tilt precision FORECAST consumes.

Reads the cited seed `dl_pipeline/data/jwst_distances_seed.csv` (or a downloaded table),
loads the real CF4 groups (`cf4_groups.npz`), matches by sky position (astropy SkyCoord,
default tolerance 0.25 deg to the CF4 GROUP centres), and writes a compact JSON with the
matched CF4 indices + PGC + the JWST e_DM. Raw catalogues stay under workdir/raw
(gitignored); only this compact, provenance-stamped result is committed.

Diagnostic-only: the anchors feed a labelled Omega_tilt FORECAST (survey-design), not a
measurement. No family/geometry/native-solver claim. Graceful: if CF4 is absent, emits a
BLOCKED record; if only the seed is present, records `source=seed`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt/htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

CF4 = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
SEED = REPO / "dl_pipeline/data/jwst_distances_seed.csv"
OUT = REPO / "docs/generated/jwst_cf4_anchors.json"
MATCH_TOL_DEG = 0.25


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_seed(path: Path):
    rows = []
    with path.open() as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("name,"):
                continue
            r = next(csv.reader([line]))
            if len(r) < 5:
                continue
            rows.append({"name": r[0], "ra": float(r[1]), "dec": float(r[2]),
                         "e_dm": float(r[3]), "method": r[4]})
    return rows


def _angular_sep_deg(ra1, dec1, ra2, dec2):
    r1, d1, r2, d2 = map(np.radians, (ra1, dec1, ra2, dec2))
    cos = np.sin(d1) * np.sin(d2) + np.cos(d1) * np.cos(d2) * np.cos(r1 - r2)
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))


def build_report(tol_deg: float = MATCH_TOL_DEG) -> dict:
    if not SEED.is_file():
        return {"schema": "htt.jwst_cf4_anchors.v1", "status": "BLOCKED_MISSING_JWST_SEED"}
    seed = _load_seed(SEED)
    if not CF4.is_file():
        return {"schema": "htt.jwst_cf4_anchors.v1", "status": "BLOCKED_MISSING_CF4",
                "note": f"CF4 catalogue not at {CF4.relative_to(REPO)}", "n_jwst": len(seed)}
    d = np.load(CF4, allow_pickle=True)
    ra, dec = np.asarray(d["RAdeg"], float), np.asarray(d["DEdeg"], float)
    pgc = np.asarray(d["PGC"], float)
    matched = []
    for s in seed:
        sep = _angular_sep_deg(s["ra"], s["dec"], ra, dec)
        j = int(np.argmin(sep))
        if sep[j] <= tol_deg:
            matched.append({"name": s["name"], "cf4_index": j, "pgc": float(pgc[j]),
                            "sep_deg": float(sep[j]), "jwst_e_dm_mag": s["e_dm"],
                            "cf4_e_dm_mag": float(d["e_DMzp"][j]) if "e_DMzp" in d else None,
                            "method": s["method"]})
    return {
        "schema": "htt.jwst_cf4_anchors.v1",
        "status": "matched",
        "source": "seed",
        "match_tolerance_deg": tol_deg,
        "n_jwst": len(seed),
        "n_matched": len(matched),
        "anchors": matched,
        "cf4_input_hash": _sha256(CF4),
        "seed_input_hash": _sha256(SEED),
        "claim_tier": "diagnostic_only",
        "note": ("compact JWST->CF4 anchor set; feeds a labelled Omega_tilt precision FORECAST "
                 "(survey-design), not a measurement. Full authoritative tables fetched by "
                 "dl_pipeline/scripts/download_jwst_anchors.py."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tol-deg", type=float, default=MATCH_TOL_DEG)
    args = ap.parse_args(argv)
    payload = build_report(args.tol_deg)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text() != text:
            print("stale jwst_cf4_anchors.json; rerun scripts/jwst_cf4_crossmatch.py")
            return 1
        print("jwst_cf4_anchors.json up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO)} (status={payload['status']}, "
          f"n_matched={payload.get('n_matched', 0)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
