#!/usr/bin/env python3
"""BASS-Extended joint PV+CMB information forecast on the REAL CF4 catalogue.

Runs the honest, solver-free core of the proposed joint likelihood:
  1. a feasible correlated-covariance bulk-flow / tilt (Omega_tilt) GLS on the real CF4
     groups (`pv_covariance`, Woodbury low-rank shear modes -- never a dense N x N inversion);
  2. a JWST-anchored distance prior FORECAST: the CF4 groups cross-matched to published JWST
     distances (`jwst_cf4_crossmatch`) get their distance errors shrunk, tightening Omega_tilt;
  3. the coupled-Fisher degeneracy-break: the tighter Omega_tilt precision (via the rev-r141
     coupled Fisher) reduces the Sigma^2 covariance inflation, blocking observer-boost leakage;
  4. the theory-g CMB likelihood sector, FAIL-CLOSED (AWAITING_NATIVE_LOWELL_SOLVER).

Diagnostic-only: model-independent kinematics + a labelled forecast; the JWST prior is a
survey-design forecast (few nearby anchors -> a modest, honestly-reported gain), not a
measurement; Sigma^2 stays partial; no family/geometry/native-solver/MIO-as-odds claim.
Deterministic; --check. Graceful BLOCKED if CF4 absent. Outputs
docs/generated/bass_extended_joint_forecast.json.
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

from htt.obsstat.bulkflow_mle import velocity_error, fit_sigma_star  # noqa: E402
from htt.obsstat import pv_covariance as pv  # noqa: E402
from htt.obsstat import joint_pv_cmb_forecast as jf  # noqa: E402

CF4 = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
ANCHORS = REPO / "docs/generated/jwst_cf4_anchors.json"
OUT_JSON = REPO / "docs/generated/bass_extended_joint_forecast.json"
JWST_SHRINK = 1.0 / 3.0
RHO_REPORT = 0.5           # representative boost-tilt coupling for the inflation report
SIGMA_SHEAR = 0.3         # km/s/Mpc, subdominant coherent-field shear mode prior


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_cf4_with_index():
    d = np.load(CF4, allow_pickle=True)
    pos = np.c_[d["SGX"], d["SGY"], d["SGZ"]].astype(float)
    r = np.linalg.norm(pos, axis=1)
    vpec = np.asarray(d["Vpec"], float)
    v3k = np.asarray(d["V3k"], float)
    e_dm = np.asarray(d["e_DMzp"], float)
    sigma = velocity_error(e_dm, v3k)
    good = np.isfinite(vpec) & np.isfinite(sigma) & (sigma > 0) & (r > 1.0) & np.isfinite(v3k)
    full_idx = np.nonzero(good)[0]
    n_hat = pos[good] / r[good, None]
    return {"pos": pos[good], "n_hat": n_hat, "vpec": vpec[good], "sigma": sigma[good],
            "full_index": full_idx}


def _anchor_mask(full_index: np.ndarray) -> tuple:
    if not ANCHORS.is_file():
        return np.zeros(full_index.size, bool), 0, "anchors_file_absent"
    a = json.loads(ANCHORS.read_text())
    idx = {int(x["cf4_index"]) for x in a.get("anchors", [])}
    pos = {v: i for i, v in enumerate(full_index.tolist())}
    mask = np.zeros(full_index.size, bool)
    matched = 0
    for ci in idx:
        if ci in pos:
            mask[pos[ci]] = True
            matched += 1
    return mask, matched, a.get("status", "unknown")


def build_report() -> dict:
    if not CF4.is_file():
        return {"schema": "htt.bass_extended_joint_forecast.v1",
                "status": "BLOCKED_MISSING_CF4",
                "note": f"CF4 catalogue not at {CF4.relative_to(REPO)}"}
    cat = _load_cf4_with_index()
    n_hat, vpec, sigma = cat["n_hat"], cat["vpec"], cat["sigma"]
    sigma_star = fit_sigma_star(n_hat, vpec, sigma)        # intrinsic dispersion (K5-consistent)
    diag_sigma2 = sigma ** 2 + sigma_star ** 2
    modes = pv.velocity_field_modes(cat["pos"], sigma_shear_kms_per_mpc=SIGMA_SHEAR)
    U, Lam = modes["U"][:, 3:], modes["Lambda"][3:]        # coherent shear field as correlated cov

    fit_diag = pv.pv_tilt_gls(n_hat, vpec, diag_sigma2)
    fit_corr = pv.pv_tilt_gls(n_hat, vpec, diag_sigma2, U, Lam)

    mask, n_anchor, anchor_status = _anchor_mask(cat["full_index"])
    fc = jf.jwst_anchor_forecast(n_hat, vpec, diag_sigma2, mask,
                                 jwst_shrink=JWST_SHRINK, U=U, Lambda=Lam)
    jff = jf.joint_fisher_forecast(rho=RHO_REPORT,
                                   f_omega_tilt_data=fc["f_omega_tilt_data"],
                                   f_omega_tilt_jwst=fc["f_omega_tilt_jwst"])
    return {
        "schema": "htt.bass_extended_joint_forecast.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "family_identification": False,
        "native_solver_result": False,
        "pv_sector": {
            "status": "measured",
            "n_groups": int(n_hat.shape[0]),
            "sigma_star_kms": float(sigma_star),
            "tilt_diagonal": fit_diag.as_dict(),
            "tilt_correlated": fit_corr.as_dict(),
            "covariance": "diag(sigma_v^2) + U Lambda U^T (Woodbury; coherent shear modes)",
            "input_hash": _sha256(CF4),
        },
        "jwst_forecast": {
            "status": "forecast",
            "n_anchor_matched": n_anchor,
            "anchor_source": anchor_status,
            "jwst_shrink": JWST_SHRINK,
            "omega_tilt_precision_gain": fc["precision_gain"],
            "label": fc["label"],
        },
        "coupled_fisher_degeneracy_break": {
            "rho_report": RHO_REPORT,
            "sigma2_inflation_data": jff["inflation_data"],
            "sigma2_inflation_jwst": jff["inflation_jwst"],
            "degeneracy_break_factor": jff["degeneracy_break_factor"],
            "note": "tighter Omega_tilt precision reduces the Sigma^2 covariance inflation (boost leakage blocked)",
        },
        "cmb_theory_sector": {"status": "fail_closed", "blocker": jf.AWAITING_NATIVE_LOWELL_SOLVER,
                              "note": "g-conditioned C_{lm,l'm'}(g) needs the native solver; not fabricated"},
        "cmb_data_sector": {"status": "measured_partial",
                            "ref": "docs/generated/k1_biposh_smica.json (real SMICA BipoSH SI measurement)"},
        "caveats": [
            "correlated PV covariance is the leading bulk+shear Woodbury model; full xi_ij from a "
            "velocity power spectrum / WF ensemble is BLOCKED_MISSING_FIELD_REALIZATIONS",
            "JWST prior is a survey-design forecast on a few nearby anchors; the gain is reported, not inflated",
            "model-independent kinematics; Sigma^2 stays partial; no family/geometry/native-solver claim",
        ],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    payload = build_report()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print("stale bass_extended_joint_forecast.json; rerun scripts/bass_extended_joint_forecast.py")
            return 1
        print("bass_extended_joint_forecast.json up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON.relative_to(REPO)} (status={payload.get('status', 'measured')})")
    if "jwst_forecast" in payload:
        print(f"   n_anchor={payload['jwst_forecast']['n_anchor_matched']}, "
              f"Omega_tilt precision gain={payload['jwst_forecast']['omega_tilt_precision_gain']:.3f}, "
              f"Sigma^2 inflation {payload['coupled_fisher_degeneracy_break']['sigma2_inflation_data']:.4f}"
              f"->{payload['coupled_fisher_degeneracy_break']['sigma2_inflation_jwst']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
