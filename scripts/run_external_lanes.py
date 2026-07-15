#!/usr/bin/env python3
"""Run the EGS3 external-data lanes (DESI / ACT / JWST) and write the seal.

Deterministic (fixed mock seed + fixed on-disk data); --check byte-diffs the
regenerated seal against docs/generated/external_lanes_seal.json. The lanes
that need a missing companion product emit a registered blocker, never a
substitute estimate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
for p in (REPO, REPO / "htt", REPO / "htt/htt"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from htt.obsstat.egs3_external_lanes import external_lanes_seal  # noqa: E402

OUT = REPO / "docs/generated/external_lanes_seal.json"
_INPUT_PATHS = (
    "scripts/run_external_lanes.py",
    "htt/obsstat/egs3_external_lanes.py",
    "workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz",
    "workdir/raw/desi/BGS_ANY_SGC_clustering.dat.fits",
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/baseline/kappa_alm_data_act_dr6_lensing_v1_baseline.fits",
    "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/baseline/N_L_kk_act_dr6_lensing_v1_baseline.txt",
    "docs/generated/desi_dipole_card.json",
    "docs/generated/act_kappa_card.json",
    "docs/generated/jwst_cf4_anchors.json",
)
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
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _stable_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _input_hashes() -> list[str]:
    records: list[str] = []
    for relative in _INPUT_PATHS:
        path = REPO / relative
        records.append(
            f"{relative}:{_sha256(path)}" if path.is_file() else f"{relative}:missing"
        )
    return records


def _with_artifact_metadata(source: dict) -> dict:
    """Attach provenance without invoking any DESI/ACT/JWST lane."""
    payload = copy.deepcopy(source)
    inputs = _input_hashes()
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
        "sky_support_status": "mixed_release_sky_support_recorded_in_lane_payloads",
        "null_mock_status": "mixed_mock_verification_and_release_sim_calibration_as_recorded",
        "caveats": [
            "Diagnostic external-data lanes only; no anisotropy, geometry, family, or inference claim.",
            "DESI and ACT interpretation remains limited by each lane's recorded residual gates.",
            "JWST/CF4 is catalogue linkage only while N-DATA-CF4-DOWNSTREAM remains OPEN.",
            "No native low-ell solver output is represented.",
        ],
        "generating_command": "python scripts/run_external_lanes.py",
        "metadata_refresh_command": "python scripts/run_external_lanes.py --metadata-only",
        "git_commit": "content-addressed",
        "git_commit_or_worktree_state": "content-addressed",
        "worktree_state": "content-addressed",
    })
    return payload


def _render(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument(
        "--metadata-only",
        action="store_true",
        help="refresh/check metadata on the existing seal without running external-data lanes",
    )
    args = ap.parse_args(argv)
    if args.metadata_only:
        if not OUT.is_file():
            print("missing external_lanes_seal.json; metadata-only refresh cannot synthesize lanes")
            return 1
        payload = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        payload = external_lanes_seal()
    payload = _with_artifact_metadata(payload)
    rendered = _render(payload)
    if args.check:
        if not OUT.exists() or OUT.read_text() != rendered:
            print("STALE external_lanes_seal.json", file=sys.stderr)
            return 1
        print("external_lanes seal current")
        return 0
    OUT.write_text(rendered)
    print(f"wrote {OUT} status={payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
