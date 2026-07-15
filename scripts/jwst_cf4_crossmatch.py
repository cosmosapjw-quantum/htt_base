#!/usr/bin/env python3
"""Cross-match JWST distance anchors to the CF4 group catalogue.

Reads the cited seed `dl_pipeline/data/jwst_distances_seed.csv` (or a downloaded table),
loads the real CF4 groups (`cf4_groups.npz`), matches by sky position (astropy SkyCoord,
default tolerance 0.25 deg to the CF4 GROUP centres), and writes a compact JSON with the
matched CF4 indices + PGC + the JWST e_DM. Raw catalogues stay under workdir/raw
(gitignored); only this compact, provenance-stamped result is committed.

Diagnostic-only catalogue linkage: matched identities and anchor-error metadata may be
retained, but the downstream global-tilt forecast is quarantined while
N-DATA-CF4-DOWNSTREAM remains OPEN. No family/geometry/native-solver claim. Graceful: if CF4 is absent, emits a
BLOCKED record; if only the seed is present, records `source=seed`.
"""
from __future__ import annotations

import argparse
import copy
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
_METADATA_KEYS = frozenset({
    "owner",
    "implementation_scope",
    "claim_tier",
    "transfer_source",
    "config_hash",
    "input_hashes",
    "sky_support_status",
    "null_mock_status",
    "caveats",
    "generating_command",
    "metadata_refresh_command",
    "git_commit",
    "git_commit_or_worktree_state",
    "worktree_state",
})


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _input_hashes(payload: dict) -> list[str]:
    script = Path(__file__).resolve()
    records = [f"scripts/jwst_cf4_crossmatch.py:{_sha256(script)}"]
    for path, key in ((CF4, "cf4_input_hash"), (SEED, "seed_input_hash")):
        if isinstance(payload.get(key), str):
            digest = payload[key]
        elif path.is_file():
            digest = _sha256(path)
        else:
            records.append(f"{path.relative_to(REPO)}:missing")
            continue
        records.append(f"{path.relative_to(REPO)}:{digest}")
    return records


def _with_artifact_metadata(source: dict) -> dict:
    """Attach provenance to an existing linkage record without rematching it."""
    payload = copy.deepcopy(source)
    inputs = _input_hashes(payload)
    scientific_payload = {
        key: value for key, value in payload.items() if key not in _METADATA_KEYS
    }
    payload.update({
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "config_hash": _stable_hash({
            "metadata_schema": "htt.minimum_artifact_metadata.v1",
            "scientific_payload_hash": _stable_hash(scientific_payload),
            "input_hashes": inputs,
        }),
        "input_hashes": inputs,
        "sky_support_status": "catalogue_coordinate_crossmatch_metadata_only",
        "null_mock_status": "not_statistical_catalogue_linkage_only",
        "caveats": [
            "Catalogue identities and anchor-error metadata only; not a global-tilt forecast.",
            "N-DATA-CF4-DOWNSTREAM remains OPEN and downstream public use is false.",
            "No detection, geometry, family-identification, or native-solver claim is authorized.",
        ],
        "generating_command": "python scripts/jwst_cf4_crossmatch.py",
        "metadata_refresh_command": "python scripts/jwst_cf4_crossmatch.py --metadata-only",
        "git_commit": "content-addressed",
        "git_commit_or_worktree_state": "content-addressed",
        "worktree_state": "content-addressed",
    })
    return payload


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
        "status": "matched_catalogue_linkage_only",
        "source": "seed",
        "match_tolerance_deg": tol_deg,
        "n_jwst": len(seed),
        "n_matched": len(matched),
        "anchors": matched,
        "cf4_input_hash": _sha256(CF4),
        "seed_input_hash": _sha256(SEED),
        "claim_tier": "diagnostic_only",
        "allowed_use": "catalogue_linkage_and_anchor_error_metadata_only",
        "finding_state": {
            "finding_id": "N-DATA-CF4-DOWNSTREAM",
            "scientific_status": "OPEN",
            "canonical_source": "docs/generated/cf4_p0_quarantine_block.json",
        },
        "downstream_global_tilt_forecast": {
            "status": "QUARANTINED_OPEN_FINDING",
            "value": None,
            "replacement_value": None,
            "public_use": False,
        },
        "note": ("compact JWST-to-CF4 catalogue linkage with anchor-error metadata only; "
                 "the downstream global-tilt forecast is quarantined while "
                 "N-DATA-CF4-DOWNSTREAM remains OPEN. Full authoritative tables are "
                 "fetched by dl_pipeline/scripts/download_jwst_anchors.py."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument(
        "--metadata-only",
        action="store_true",
        help="refresh/check metadata on the existing record without rerunning the cross-match",
    )
    ap.add_argument("--tol-deg", type=float, default=MATCH_TOL_DEG)
    args = ap.parse_args(argv)
    if args.metadata_only:
        if not OUT.is_file():
            print("missing jwst_cf4_anchors.json; metadata-only refresh cannot synthesize matches")
            return 1
        payload = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        payload = build_report(args.tol_deg)
    payload = _with_artifact_metadata(payload)
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
