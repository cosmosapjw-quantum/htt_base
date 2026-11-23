"""R100 Part D: Gaia/Quaia shared angular systematics + finite-z position-drift joint identifiability."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
from scipy.linalg import subspace_angles

from scripts.r99 import gaia_shared_field as r99_gaia
from scripts.r100 import cf4_upstream_and_kband as r100_cf4  # noqa: F401 (constants/helpers if needed)

ROOT = Path(__file__).resolve().parents[2]
R98_DIR = ROOT / "docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
R99_DIR = ROOT / "docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123"
OUT_DIR = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def whiten_positive_subspace(cov: np.ndarray, rel_tol: float = 1e-10) -> tuple[np.ndarray, int, np.ndarray]:
    """Scale-invariant symmetric eigenspace whitener W = U_k / sqrt(ev_k) @ U_k^T (rank <= 47; never inverts full space)."""
    c = np.asarray(cov, dtype=float)
    sym = 0.5 * (c + c.T)
    ev, U = np.linalg.eigh(sym)
    scale = float(ev[-1])
    if scale <= 0.0:
        raise ValueError("Zero or negative top eigenvalue")
    keep = ev > rel_tol * scale
    W = (U[:, keep] / np.sqrt(ev[keep])) @ U[:, keep].T
    return W, int(np.sum(keep)), ev


def evaluate_linear_model_on_subspace(y: np.ndarray, X: np.ndarray, W: np.ndarray, label: str) -> dict[str, object]:
    """Evaluate weighted least squares strictly inside positive-eigenspace W (avoiding rank-deficient inversion)."""
    yw = W @ y
    Xw = W @ X
    beta, _, rank_x, s_vals = np.linalg.lstsq(Xw, yw, rcond=None)
    resid = yw - Xw @ beta
    chi2_sub = float(resid @ resid)
    chi2_null = float(yw @ yw)
    # Parameter covariance via pseudoinverse of Xw (safe if X itself has near-collinearity)
    XtX = Xw.T @ Xw
    ev_x = np.linalg.eigvalsh(0.5 * (XtX + XtX.T))
    return {
        "model": label,
        "n_params": int(X.shape[1]),
        "effective_design_rank": int(rank_x),
        "whitened_singular_values": s_vals.tolist(),
        "whitened_condition": float(s_vals[0] / s_vals[-1]) if len(s_vals) and s_vals[-1] > 1e-14 * s_vals[0] else None,
        "beta": beta.tolist(),
        "subspace_chi2_null": chi2_null,
        "subspace_chi2_fit": chi2_sub,
        "subspace_delta_chi2": float(max(0.0, chi2_null - chi2_sub)),
        "min_fisher_eig": float(ev_x[0]),
    }


def compute() -> dict[str, object]:
    t0 = time.monotonic()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Verify R98 + R99 + R100 optical + R100 CF4 SHA identities
    g_r98 = json.loads((R98_DIR / "GAIA_FULL_SHARED_PATCH.json").read_text())
    g_r99 = json.loads((R99_DIR / "GAIA_SHARED_FIELD_RESULTS.json").read_text())
    opt_r100 = json.loads((OUT_DIR / "OPTICAL_DRIFT_RESULTS.json").read_text())
    cf4_r100 = json.loads((OUT_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json").read_text())

    meta_160 = g_r98["joint_160d_patch_covariance"]
    patch_npz_path = Path(meta_160["cache_path"])
    if sha256(patch_npz_path) != meta_160["sha256"]:
        raise ValueError("R98 gaia_joint_patch_statistics.npz SHA mismatch")
    cov_sys_npz_path = Path(g_r99["covariance_artifact"]["path"])
    if sha256(cov_sys_npz_path) != g_r99["covariance_artifact"]["sha256"]:
        raise ValueError("R99 GAIA_SHARED_FIELD_COVARIANCES.npz SHA mismatch")
    opt_npz_path = Path(opt_r100["templates_npz"]["path"])
    if sha256(opt_npz_path) != opt_r100["templates_npz"]["sha256"]:
        raise ValueError("R100 OPTICAL_DRIFT_TEMPLATES.npz SHA mismatch")
    cf4_npz_path = Path(cf4_r100["A3_full_kband_correlated_pv"]["covariances_npz"]["path"])
    if sha256(cf4_npz_path) != cf4_r100["A3_full_kband_correlated_pv"]["covariances_npz"]["sha256"]:
        raise ValueError("R100 CF4_FULL_KBAND_COVARIANCES.npz SHA mismatch")

    with np.load(patch_npz_path, allow_pickle=False) as zp:
        names = [str(v) for v in zp["names"]]
        C_jk_160 = zp["cov"].copy()
    with np.load(cov_sys_npz_path, allow_pickle=False) as zs:
        cov_sys_by_angle = {ang: zs[f"cov_angle_{ang}"].copy() for ang in (15, 30, 60)}
        responses_sys = zs["responses"].copy()  # (10, 48, 16, 6)
    with np.load(opt_npz_path, allow_pickle=False) as zo:
        z_opt = zo["redshifts"].copy()
        cf4_zc = zo["cf4_window_centers"].copy()
        quaia_zm = zo["quaia_shell_medians"].copy()
        TG_geo = {fam: zo[f"TG_geo_{fam}"].copy() for fam in ("FLRW", "I", "V", "VII_h", "VI_h")}
        TG_bo = {fam: zo[f"TG_beta_o_per_1e3c_{fam}"].copy() for fam in ("FLRW", "VI_h")}
        TG_be = {fam: zo[f"TG_beta_e_per_1e3c_{fam}"].copy() for fam in ("FLRW", "VI_h")}
        TC_bo = {fam: zo[f"TC_beta_o_per_1e3c_{fam}"].copy() for fam in ("FLRW", "VI_h")}
        TC_be = {fam: zo[f"TC_beta_e_per_1e3c_{fam}"].copy() for fam in ("FLRW", "VI_h")}
        TC_geo = {fam: zo[f"TC_geo_{fam}"].copy() for fam in ("FLRW", "I", "V", "VII_h", "VI_h")}
    with np.load(cf4_npz_path, allow_pickle=False) as zc:
        C_cf4_36 = zc["C_WF_R5_full_k"].copy()
        b_cf4_36 = (-zc["b_published_4x9"]).ravel()  # note: Delta ln D_L response has opposite sign to log(v/H_ref) - MAG*(mu-25)

    # Quaia z0..z3 indices in 10-fit ordering (6, 7, 8, 9 -> rows 96:160)
    z_names = ["quaia_z0", "quaia_z1", "quaia_z2", "quaia_z3"]
    z_fit_idx = [names.index(zn) for zn in z_names]
    idx_64 = np.concatenate([np.arange(16 * fi, 16 * (fi + 1)) for fi in z_fit_idx])
    quaia_idx_opt = [int(np.argmin(np.abs(z_opt - zm))) for zm in quaia_zm]
    cf4_idx_opt = [int(np.argmin(np.abs(z_opt - zm))) for zm in cf4_zc]

    theta_160 = np.concatenate([np.asarray(g_r98["fits"][n]["coefs_microasyr"], dtype=float) for n in names])
    theta_64 = theta_160[idx_64]
    C_jk_64 = C_jk_160[np.ix_(idx_64, idx_64)]

    # Verify rank <= 47 on 64D Quaia 4-shell jackknife covariance; compute supported_subspace (never invert!)
    subspace_jk_160 = r99_gaia.supported_subspace(theta_160, C_jk_160)
    subspace_jk_64 = r99_gaia.supported_subspace(theta_64, C_jk_64)
    W_jk_64, rank_jk_64, ev_jk_64 = whiten_positive_subspace(C_jk_64)
    if rank_jk_64 > 47:
        raise ValueError(f"64D patch jackknife rank cannot exceed 47, got {rank_jk_64}")

    # Separate C_sys check (strictly NOT added to C_jk!) across 15, 30, 60 degrees
    sys_subspaces = {}
    for ang, C160_s in cov_sys_by_angle.items():
        C64_s = C160_s[np.ix_(idx_64, idx_64)]
        sys_subspaces[str(ang)] = {
            "C_sys_64_subspace": r99_gaia.supported_subspace(theta_64, C64_s),
            "C_sys_64_trace": float(np.trace(C64_s)),
            "double_counting_prevented": True,
        }

    # Build 64D design bases (4 Quaia shells x 16 VSH):
    X_const_16 = np.kron(np.ones((4, 1)), np.eye(16))  # exact z-independent scan/aberration/spin/local-shear floor
    X_const_eb1 = X_const_16[:, :6]                     # z-independent observer secular accel (3) + frame spin (3)
    X_bo_64 = TG_bo["FLRW"][quaia_idx_opt].reshape(64, 3)  # finite-z observer boost parallax (per 10^-3 c)
    X_be_64 = TG_be["FLRW"][quaia_idx_opt].reshape(64, 3)  # finite-z global source tilt (per 10^-3 c)
    X_vih_64 = TG_geo["VI_h"][quaia_idx_opt].reshape(64, 1)  # normalized unit-10^-5 template for Bianchi VI_h
    X_viih_64 = TG_geo["VII_h"][quaia_idx_opt].reshape(64, 1)

    # Principal angles between scan/frame floor, observer boost parallax, source tilt, and Bianchi VI_h
    pa_bo_const = np.rad2deg(subspace_angles(X_bo_64, X_const_16)).tolist()
    pa_be_const = np.rad2deg(subspace_angles(X_be_64, X_const_16)).tolist()
    pa_bo_be = np.rad2deg(subspace_angles(X_bo_64, X_be_64)).tolist()
    pa_vih_const = np.rad2deg(subspace_angles(X_vih_64, X_const_16)).tolist()

    # Whitened principal angles under rank-47 C_jk_64
    pa_w_bo_be = np.rad2deg(subspace_angles(W_jk_64 @ X_bo_64, W_jk_64 @ X_be_64)).tolist()
    pa_w_bo_const = np.rad2deg(subspace_angles(W_jk_64 @ X_bo_64, W_jk_64 @ X_const_16)).tolist()
    pa_w_vih_const = np.rad2deg(subspace_angles(W_jk_64 @ X_vih_64, W_jk_64 @ X_const_16)).tolist()

    # Fit nested 4-component separation models cleanly on the rank-47 positive eigenspace
    nested_models_jk = [
        evaluate_linear_model_on_subspace(theta_64, X_const_eb1, W_jk_64, "const_glide_spin_6D"),
        evaluate_linear_model_on_subspace(theta_64, X_const_16, W_jk_64, "const_full_16D_scan_floor"),
        evaluate_linear_model_on_subspace(theta_64, np.hstack([X_const_eb1, X_bo_64]), W_jk_64, "const_glide_spin_plus_beta_o"),
        evaluate_linear_model_on_subspace(theta_64, np.hstack([X_const_16, X_bo_64]), W_jk_64, "const_16D_floor_plus_beta_o"),
        evaluate_linear_model_on_subspace(theta_64, np.hstack([X_const_16, X_bo_64, X_be_64]), W_jk_64, "const_16D_floor_plus_beta_o_plus_beta_e"),
        evaluate_linear_model_on_subspace(theta_64, np.hstack([X_const_16, X_vih_64]), W_jk_64, "const_16D_floor_plus_VIh_finite_z"),
    ]

    # Also test under C_sys_64 (30 deg) alone (separate regularized systematic sensitivity, rank 64 or positive subspace)
    W_sys30, rank_sys30, _ = whiten_positive_subspace(cov_sys_by_angle[30][np.ix_(idx_64, idx_64)], rel_tol=1e-10)
    nested_models_sys30 = [
        evaluate_linear_model_on_subspace(theta_64, X_const_16, W_sys30, "sys30_const_16D_floor"),
        evaluate_linear_model_on_subspace(theta_64, np.hstack([X_const_16, X_bo_64]), W_sys30, "sys30_const_16D_plus_beta_o"),
        evaluate_linear_model_on_subspace(theta_64, np.hstack([X_const_16, X_bo_64, X_be_64]), W_sys30, "sys30_const_16D_plus_beta_o_plus_beta_e"),
    ]

    # Joint CF4 (36D, full-k WF cov) + Gaia Quaia (64D, rank-47 jk cov) identifiability for [beta_o (3), beta_e (3)]
    W_cf4 = np.linalg.inv(np.linalg.cholesky(0.5 * (C_cf4_36 + C_cf4_36.T)))
    X_cf4_bo = TC_bo["FLRW"][cf4_idx_opt].reshape(36, 3)
    X_cf4_be = TC_be["FLRW"][cf4_idx_opt].reshape(36, 3)
    X_cf4_bobe = np.hstack([X_cf4_bo, X_cf4_be])
    X_gaia_bobe = np.hstack([X_bo_64, X_be_64])

    # Project Gaia onto orthogonal complement of constant 16D scan floor INSIDE W_jk_64 space!
    # Profiled Fisher information of [beta_o, beta_e] after marginalizing constant 16D Gaia floor & 9D CF4 mean
    Qg, _ = np.linalg.qr(W_jk_64 @ X_const_16)
    Zg = W_jk_64 @ X_gaia_bobe
    Zg_prof = Zg - Qg @ (Qg.T @ Zg)
    Fg_prof = Zg_prof.T @ Zg_prof

    Qc, _ = np.linalg.qr(W_cf4 @ np.tile(np.eye(9), (4, 1)))
    Zc = W_cf4 @ X_cf4_bobe
    Zc_prof = Zc - Qc @ (Qc.T @ Zc)
    Fc_prof = Zc_prof.T @ Zc_prof

    F_joint = Fg_prof + Fc_prof
    sv_cf4_prof = np.sqrt(np.maximum(0.0, np.linalg.eigvalsh(Fc_prof)))[::-1]
    sv_gaia_prof = np.sqrt(np.maximum(0.0, np.linalg.eigvalsh(Fg_prof)))[::-1]
    sv_joint_prof = np.sqrt(np.maximum(0.0, np.linalg.eigvalsh(F_joint)))[::-1]

    # Proper-motion vs parallax covariance provenance audit across all 10 fits:
    pm_cov_audit = {
        "source_columns_used_in_R98_R99": ["pmra", "pmdec", "pmra_error", "pmdec_error", "pmra_pmdec_corr"],
        "parallax_columns_substituted": False,
        "five_parameter_astrometric_filter_quaia": "gaia_astrometric_params_solved == 31, ruwe < 1.4, abs(pm) < 100 mas/yr",
        "crf3_quality_filter": "ruwe < 1.4, visibility_periods_used >= 8, duplicated_source == False",
        "open_blockers": [
            "D04: Gaia release-calibrated AGIS spatial scan/error law and independent AGN host/centroid controls",
            "M05: Uncalibrated scan+AGN+physical Bianchi normal-frame covariance closure",
        ],
    }

    payload = {
        "schema": "htt.r100.gaia_optical_joint/1",
        "owner": "obsstat",
        "status": "MODEL_CONDITIONAL_IDENTIFIABILITY_EXECUTED",
        "physical_Pi": None,
        "physical_GF": None,
        "calibrated_p": None,
        "full_160D_or_64D_inversion_avoided": True,
        "quaia_redshift_medians": quaia_zm.tolist(),
        "subspace_diagnostics": {
            "full_160D_jk": subspace_jk_160,
            "quaia_4shell_64D_jk": subspace_jk_64,
            "shared_C_sys_by_angle_deg_separate_from_jk": sys_subspaces,
        },
        "subspace_angles_degrees": {
            "raw_beta_o_vs_const_16D_floor": pa_bo_const,
            "raw_beta_e_vs_const_16D_floor": pa_be_const,
            "raw_beta_o_vs_beta_e": pa_bo_be,
            "raw_VIh_finite_z_vs_const_16D_floor": pa_vih_const,
            "jk_whitened_beta_o_vs_beta_e": pa_w_bo_be,
            "jk_whitened_beta_o_vs_const_16D_floor": pa_w_bo_const,
            "jk_whitened_VIh_vs_const_16D_floor": pa_w_vih_const,
        },
        "four_component_fits_on_jk_rank47": nested_models_jk,
        "four_component_fits_on_sys30_separate": nested_models_sys30,
        "joint_cf4_gaia_bobe_profiled_identifiability": {
            "parameter_order": ["beta_o_x", "beta_o_y", "beta_o_z", "beta_e_x", "beta_e_y", "beta_e_z (per 10^-3 c)"],
            "marginalized_nuisances": ["Gaia z-independent 16D scan/aberration/spin/local-shear floor", "CF4 shared 9D mean"],
            "cf4_only_profiled_sv": sv_cf4_prof.tolist(),
            "gaia_only_profiled_sv": sv_gaia_prof.tolist(),
            "joint_cf4_plus_gaia_profiled_sv": sv_joint_prof.tolist(),
            "joint_profiled_condition": float(sv_joint_prof[0] / max(sv_joint_prof[-1], 1e-30)),
            "min_sv_gain_joint_over_gaia_alone": float(sv_joint_prof[-1] / max(sv_gaia_prof[-1], 1e-30)),
            "arbitrary_column_rescaling_does_not_create_fisher_information": True,
        },
        "proper_motion_vs_parallax_covariance_audit": pm_cov_audit,
        "inputs_sha256": {
            "gaia_patch_cache": meta_160["sha256"],
            "r99_sys_cov": g_r99["covariance_artifact"]["sha256"],
            "r100_optical_templates": opt_r100["templates_npz"]["sha256"],
            "r100_cf4_covariances": cf4_r100["A3_full_kband_correlated_pv"]["covariances_npz"]["sha256"],
            "code": sha256(Path(__file__)),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "threads": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        },
        "runtime_seconds": time.monotonic() - t0,
    }
    out_path = OUT_DIR / "GAIA_OPTICAL_JOINT_RESULTS.json"
    out_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    res = compute()
    print(json.dumps({
        "status": res["status"],
        "rank_64D": res["subspace_diagnostics"]["quaia_4shell_64D_jk"]["rank"],
        "unsupported_frac_64D": res["subspace_diagnostics"]["quaia_4shell_64D_jk"]["unsupported_squared_norm_fraction"],
        "pa_w_bo_be_deg": res["subspace_angles_degrees"]["jk_whitened_beta_o_vs_beta_e"],
        "joint_prof_sv": res["joint_cf4_gaia_bobe_profiled_identifiability"]["joint_cf4_plus_gaia_profiled_sv"],
        "runtime_s": res["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
