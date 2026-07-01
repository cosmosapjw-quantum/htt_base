#!/usr/bin/env python3
"""K1-BipoSH: off-diagonal <a_lm a*_l'm'> statistical-isotropy measurement on the REAL
Planck SMICA / Commander low-ell maps, null-calibrated against an isotropic GRF ensemble.

This extracts the DATA-side off-diagonal structure the "extract C_{lm,l'm'} from SMICA"
request asks for -- as the rotationally-invariant Bipolar-Spherical-Harmonic power
D^L_{l1 l2} (`biposh_smica`). L=1 is the observer-boost / aberration l<->l+1 coupling; L=2
is the quadrupolar SI violation a global tilt or shear would source. The observed powers are
ranked against synfast realizations of the observed C_ell (the matched isotropic null) via the
shared `calibrate_max_scan`, giving a look-elsewhere-corrected global p-value. Real single-sky
observable; GRF null now, the FFP10/NPIPE E2E null is the pending upgrade
(BLOCKED_MISSING_PR4_E2E_ACCESS). The THEORY prediction A^{LM}_{l1l2}(g) for a Bianchi g needs
the native solver and stays fail-closed (`joint_pv_cmb_forecast.anisotropic_cmb_covariance`).

Diagnostic-only: model-independent SI descriptor; no Bianchi family, geometry, frame-violation,
or native-solver claim. Deterministic; --check. Outputs docs/generated/k1_biposh_smica.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt/htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

import make_lowell_morphology_real_map as rm  # noqa: E402
from htt.obsstat.biposh_smica import compute_biposh_from_alm, biposh_power_vector  # noqa: E402
from htt.obsstat.lowell_global_calibration import calibrate_max_scan  # noqa: E402

OUT_JSON = REPO / "docs/generated/k1_biposh_smica.json"
L_VALUES = (1, 2)
N_NULL = 500
SEED = 20260702


def _sha256_map(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _measure(path: Path, n_null: int, seed: int) -> dict:
    import healpy as hp
    temp = rm._load_real_map(path)
    alm = hp.map2alm(temp, lmax=rm.LMAX, iter=3)
    obs = compute_biposh_from_alm(alm, rm.LMAX, L_values=L_VALUES, ell_min=rm.ELL_MIN)
    keys = sorted(obs.power_by_L_l1_l2)
    obs_vec, _ = biposh_power_vector(obs, keys)
    cl = hp.alm2cl(alm, lmax=rm.LMAX)                       # matched isotropic null spectrum
    rng = np.random.default_rng(seed)
    sims = np.empty((n_null, len(keys)))
    for i in range(n_null):
        np.random.seed(int(rng.integers(0, 2**31 - 1)))
        null_map = hp.synfast(cl, nside=rm.NSIDE, lmax=rm.LMAX, pixwin=False)
        null_alm = hp.map2alm(null_map, lmax=rm.LMAX, iter=3)
        meas = compute_biposh_from_alm(null_alm, rm.LMAX, L_values=L_VALUES, ell_min=rm.ELL_MIN)
        v, _ = biposh_power_vector(meas, keys)
        sims[i] = v
    directions = ["high"] * len(keys)                      # excess bipolar power = SI violation
    cal = calibrate_max_scan(obs_vec, sims, directions)
    return {
        "map_sha256": _sha256_map(path),
        "lmax": rm.LMAX, "ell_min": rm.ELL_MIN, "nside": rm.NSIDE, "L_values": list(L_VALUES),
        "observed_power_by_L": obs.power_by_L,
        "scan_keys": [list(k) for k in keys],
        "global_p": cal.global_p,
        "n_scan_statistics": len(keys),
        "n_null": n_null,
    }


def build_report(n_null: int = N_NULL, seed: int = SEED) -> dict:
    maps = {"smica": rm.SMICA_MAP, "commander": rm.COMMANDER_MAP}
    present = {k: p for k, p in maps.items() if p.is_file()}
    if not present:
        return {"schema": "htt.k1_biposh_smica.v1", "status": "BLOCKED_MISSING_REAL_MAP"}
    results = {k: _measure(p, n_null, seed) for k, p in present.items()}
    return {
        "schema": "htt.k1_biposh_smica.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "family_identification": False,
        "native_solver_result": False,
        "statistic": "rotationally-invariant BipoSH power D^L_{l1 l2}",
        "null": "isotropic GRF synfast of the observed C_ell (matched-power isotropic null)",
        "results": results,
        "config": {"n_null": n_null, "seed": seed},
        "theory_side_status": {"status": "fail_closed", "blocker": "AWAITING_NATIVE_LOWELL_SOLVER",
                               "note": "A^{LM}_{l1l2}(g) prediction needs the native low-ell solver"},
        "pending_upgrade": "BLOCKED_MISSING_PR4_E2E_ACCESS (FFP10/NPIPE E2E null replaces the GRF null)",
        "caveats": [
            "real single-sky SI descriptor; GRF null is matched-power isotropic, not E2E systematics",
            "look-elsewhere corrected over the (L,l1,l2) scan family via calibrate_max_scan",
            "model-independent; no Bianchi family, geometry, frame-violation, or native-solver claim",
        ],
        "claim_boundary": "OBSSTAT off-diagonal SI measurement; no anisotropy evidence or family identification",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--n-null", type=int, default=N_NULL)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args(argv)
    payload = build_report(args.n_null, args.seed)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print("stale k1_biposh_smica.json; rerun scripts/k1_biposh_smica.py")
            return 1
        print("k1_biposh_smica.json up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON.relative_to(REPO)} (status={payload.get('status', 'measured')})")
    for k, r in payload.get("results", {}).items():
        print(f"   {k}: BipoSH global p = {r['global_p']:.3f} "
              f"(L1={r['observed_power_by_L'].get(1, 0):.3g}, L2={r['observed_power_by_L'].get(2, 0):.3g})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
