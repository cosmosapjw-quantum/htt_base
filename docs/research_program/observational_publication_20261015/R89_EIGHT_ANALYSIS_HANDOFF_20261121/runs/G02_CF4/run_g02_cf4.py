"""R89 G02_CF4 bounded source diagnostic for SQ-CF4 / H01 / H03 (H02/H04-H06 blocked).

Reuses:
- htt.obsstat.cf4_p0b (R87 35,970-group method overlap & RA heldout)
- htt.obsstat.p2p3_fast (R83 4-window H03 4x9 / 36x36 GLS)
- htt.obsstat.p5p6_fast (R85 K02 4x12 / 32x32 method-profiled fit)
- htt.obsstat.pv_covariance (low-rank Woodbury PV covariance)
- docs/research_program/.../H03_20261016/src/h03_tomography.py
- scripts/r88/run_p0c.py (fail-closed SQ-CF4 dry-run contract)

Write scope: create-only under R89/.../runs/G02_CF4/.
No physical H(z,n), calibrated S_PV, J_cal Sigma_cal J_cal^T, C_selection, or Pi is claimed.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

H03_SRC = ROOT / "docs/research_program/observational_publication_20261015/H03_20261016/src"
if str(H03_SRC) not in sys.path:
    sys.path.insert(0, str(H03_SRC))

import h03_tomography as H03
from htt.obsstat import cf4_p0b, p2p3_fast, p5p6_fast
from htt.obsstat.pv_covariance import velocity_field_modes, woodbury_solve
from scripts.r88.run_p0c import build_packet as r88_build_packet

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"
PV_SCENARIOS = ((0.0, 1.5), (150.0, 0.0), (150.0, 1.5))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _serialize(obj):
    if isinstance(obj, np.ndarray):
        return _serialize(obj.tolist())
    if isinstance(obj, np.generic):
        return _serialize(obj.item())
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    if isinstance(obj, (bool, int, str)) or obj is None:
        return obj
    raise TypeError(f"Unsupported type: {type(obj)}")


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {OUT_JSON}")

    t0 = time.perf_counter()
    s = cf4_p0b.load_cf4_method_source()
    assert cf4_p0b.validate_source_identity(s)
    r87_info = cf4_p0b.profile_source_method_offsets(s)
    r87_held = cf4_p0b.spatial_group_heldout(s)

    # P0-C fail-closed dry-run verification
    p0c_packet = r88_build_packet("SQ-CF4")
    assert p0c_packet["status"] == "BLOCKED_INPUT"

    # H03 4-window GLS setup
    d = H03.proxy_distance(s.distance_modulus)
    sig = H03.working_sigma(d, s.distance_modulus_error)
    X9 = H03.velocity_design(d, s.direction)
    y = H03.C_KM_S * s.z_CMB
    W = np.column_stack([H03.window(s.z_CMB, sig, c) for c in H03.CENTERS])
    h03_gls = p2p3_fast.four_window_working_gls(X9, y, W, sig)
    h03_receipt = p2p3_fast.last_p2p3_receipt()

    # K02 4x12 -> 32D method-profiled setup
    k02_src = p5p6_fast.prepare_cf4_method_source(cf4_p0b.SELECT)
    assert np.array_equal(k02_src["group_id"], s.group_id)
    k02_res = p5p6_fast.k02_method_profiled(k02_src)
    k02_receipt = p5p6_fast.last_p5p6_receipt()

    # (A) Window-by-window method genealogy & overlap decomposition
    n_pres_raw = s.method_presence.sum(axis=1)
    n_use6 = np.isfinite(s.method_sigma).sum(axis=1)
    zero_ind_mask = n_pres_raw == 0
    assert int(zero_ind_mask.sum()) == 185
    assert int(np.sum(s.selected_family[zero_ind_mask] == "OTHER")) == 185

    window_genealogy = []
    for j, center in enumerate(H03.CENTERS):
        wj = W[:, j]
        w_sum = float(np.sum(wj))
        w_eff = float((w_sum ** 2) / np.dot(wj, wj))
        fam_share = {
            fam: {
                "group_count_nonzero_weight": int(np.sum((s.selected_family == fam) & (wj > 0))),
                "weight_fraction": float(np.sum(wj[s.selected_family == fam]) / w_sum),
            }
            for fam in H03.METHODS
        }
        raw7_share = {
            name: {
                "group_count_total": int(np.sum(s.method_presence[:, m_idx])),
                "weight_fraction": float(np.sum(wj[s.method_presence[:, m_idx]]) / w_sum),
            }
            for m_idx, name in enumerate(("CAL", "SNIA", "FP", "TF", "SBFO", "SBFI", "SNII"))
        }
        window_genealogy.append({
            "window_index": j,
            "z_center": float(center),
            "weight_sum": w_sum,
            "effective_sample_size": w_eff,
            "selected_family_breakdown": fam_share,
            "table3_raw7_indicator_weight_fraction": raw7_share,
            "usable_multimethod_922_weight_fraction": float(np.sum(wj[n_use6 >= 2]) / w_sum),
            "zero_indicator_OTHER_185_weight_fraction": float(np.sum(wj[zero_ind_mask]) / w_sum),
        })

    # (B) Empirical table4 DMzp vs table3 published per-method group moduli
    # Compare group-level table4 DMzp against inverse-variance combined table3
    # (already within-method/MCMC-processed; aligned via R87 delta_mag in SNIA=0 gauge + mean SNIA tie-in).
    live6 = np.isfinite(s.method_sigma)
    invvar6 = np.zeros_like(s.method_sigma)
    invvar6[live6] = s.method_sigma[live6] ** -2
    invvar_sum = invvar6.sum(axis=1)
    has_use6 = invvar_sum > 0
    mu_raw_filled = np.where(live6, s.method_modulus, 0.0)
    mu_comb_raw = np.divide(
        (invvar6 * mu_raw_filled).sum(axis=1),
        invvar_sum,
        out=np.full(len(s.group_id), np.nan),
        where=has_use6,
    )
    delta6 = r87_info["delta_mag"]
    mu_shifted_filled = np.where(live6, s.method_modulus - delta6[None, :], 0.0)
    mu_comb_delta_aligned = np.divide(
        (invvar6 * mu_shifted_filled).sum(axis=1),
        invvar_sum,
        out=np.full(len(s.group_id), np.nan),
        where=has_use6,
    )
    snia_mask = np.isfinite(s.method_sigma[:, 0])
    snia_mean_tie = float(np.mean(s.distance_modulus[snia_mask] - s.method_modulus[snia_mask, 0]))
    residual_dmzp_minus_aligned = s.distance_modulus[has_use6] - (
        mu_comb_delta_aligned[has_use6] + snia_mean_tie
    )
    table4_vs_table3 = {
        "usable_groups_count": int(has_use6.sum()),
        "snia_mean_dmzp_minus_table3_mag": snia_mean_tie,
        "per_method_raw_dmzp_minus_table3": {
            name: {
                "count": int(np.sum(live6[:, k])),
                "mean_mag": float(np.mean(s.distance_modulus[live6[:, k]] - s.method_modulus[live6[:, k], k])),
                "std_mag": float(np.std(s.distance_modulus[live6[:, k]] - s.method_modulus[live6[:, k], k])),
                "r87_negative_delta_mag": float(-delta6[k]),
            }
            for k, name in enumerate(s.method_names)
        },
        "residual_dmzp_minus_delta_aligned_summary": {
            "mean_mag": float(np.mean(residual_dmzp_minus_aligned)),
            "std_mag": float(np.std(residual_dmzp_minus_aligned)),
            "rms_mag": float(np.sqrt(np.mean(residual_dmzp_minus_aligned ** 2))),
            "max_abs_mag": float(np.max(np.abs(residual_dmzp_minus_aligned))),
        },
    }

    # Propagate per-group table4-vs-(delta-aligned table3) discrepancy as a
    # sensitivity test into H03 (4x9) & K02 (4x8) on the 35,783 groups with >=1 usable method.
    dm_perturbed = s.distance_modulus.copy()
    dm_perturbed[has_use6] = mu_comb_delta_aligned[has_use6] + snia_mean_tie
    d_pert = H03.proxy_distance(dm_perturbed)
    sig_pert = H03.working_sigma(d_pert, s.distance_modulus_error)
    X9_pert = H03.velocity_design(d_pert, s.direction)
    W_pert = np.column_stack([H03.window(s.z_CMB, sig_pert, c) for c in H03.CENTERS])
    h03_pert = p2p3_fast.four_window_working_gls(X9_pert, y, W_pert, sig_pert)

    # Same perturbation in K02 12D source space (without modifying original source file)
    X12_pert = k02_src["X"].copy()
    scale_d = d_pert / k02_src["distance_Mpc"]
    X12_pert *= scale_d[:, None]
    w_k02_pert = np.column_stack([
        np.exp(-0.5 * ((s.z_CMB - c) / 0.012) ** 2) / (sig_pert ** 2)
        for c in H03.CENTERS
    ])
    k02_pert_theta = []
    for j in range(4):
        Fj = 0.5 * (X12_pert.T @ (w_k02_pert[:, j, None] * X12_pert))
        Fj = Fj + Fj.T
        ev_k = np.linalg.eigvalsh(Fj)
        if ev_k[0] <= 0 or ev_k[-1] / ev_k[0] > 1e10:
            raise ValueError(f"Perturbed K02 window {j} ill-conditioned")
        bj = X12_pert.T @ (w_k02_pert[:, j] * y)
        k02_pert_theta.append(np.linalg.solve(Fj, bj))
    k02_pert_theta = np.asarray(k02_pert_theta)
    k02_delta_shape8 = k02_pert_theta[:, 4:] - k02_res["shape8"]
    h03_delta_theta = h03_pert["theta"] - h03_gls["theta"]

    # (C) 4-RA-quadrant out-of-sample H03 velocity prediction consistency (with R87 method-contrast folds)
    ra = np.arctan2(s.direction[:, 1], s.direction[:, 0]) % (2.0 * np.pi)
    skybin = np.minimum((ra / (np.pi / 2.0)).astype(np.int8), 3)
    ra_heldout_4x9 = []
    for fold in range(4):
        test = skybin == fold
        train = ~test
        assert not np.intersect1d(s.group_id[train], s.group_id[test]).size
        gls_train = p2p3_fast.four_window_working_gls(
            X9[train], y[train], W[train], sig[train], native_lib=None
        )
        fold_windows = []
        for j, center in enumerate(H03.CENTERS):
            th_tr = gls_train["theta"][j]
            th_full = h03_gls["theta"][j]
            res_test_tr = y[test] - X9[test] @ th_tr
            res_test_full = y[test] - X9[test] @ th_full
            wt = W[test, j]
            wsum = float(np.sum(wt))
            loss_tr = float(np.dot(wt, res_test_tr ** 2))
            loss_full = float(np.dot(wt, res_test_full ** 2))
            fold_windows.append({
                "window_index": j,
                "z_center": float(center),
                "theta_train_minus_full_maxabs": float(np.max(np.abs(th_tr - th_full))),
                "test_weighted_mse_from_train_kms2": float(loss_tr / wsum),
                "test_weighted_mse_in_sample_full_kms2": float(loss_full / wsum),
                "test_weighted_chi2_proxy": loss_tr,
            })
        ra_heldout_4x9.append({
            "fold": fold,
            "RA_sector_deg": [90 * fold, 90 * (fold + 1)],
            "train_groups": int(train.sum()),
            "test_groups": int(test.sum()),
            "windows": fold_windows,
        })

    # (D) Multi-window 36D coherent low-rank PV sensitivity (O(N K^2) Woodbury, no dense N x N)
    pos_mpc = d[:, None] * s.direction
    pv_4window = []
    # Base diagonal 36x36 inverse factors from h03_gls
    F_diag_invs = [np.linalg.inv(0.5 * (h03_gls["F"][j] + h03_gls["F"][j].T)) for j in range(4)]
    C36_diag = h03_gls["joint_cov"]

    for bulk_sig, shear_sig in PV_SCENARIOS:
        mode = velocity_field_modes(
            pos_mpc, sigma_bulk_kms=bulk_sig, sigma_shear_kms_per_mpc=shear_sig
        )
        valid_m = mode["Lambda"] > 0
        U = np.ascontiguousarray(mode["U"][:, valid_m])
        lam = np.ascontiguousarray(mode["Lambda"][valid_m])

        # 1) Exact 36x36 covariance inflation of the fixed H03 4-window estimator
        # Cov(theta_fixed) = C36_diag + J_U @ diag(lam) @ J_U.T where J_U[j] = F_j^-1 X^T W_j U
        JU = np.vstack([F_diag_invs[j] @ (X9.T @ (W[:, j : j + 1] * U)) for j in range(4)])
        C36_fixed_est_with_PV = C36_diag + (JU * lam[None, :]) @ JU.T
        C36_fixed_est_with_PV = 0.5 * (C36_fixed_est_with_PV + C36_fixed_est_with_PV.T)
        ev_fixed = np.linalg.eigvalsh(C36_fixed_est_with_PV)
        assert ev_fixed[0] > 0

        # 2) Window-by-window PV-weighted Woodbury GLS: C_j = diag(sigma^2 / g_j) + U Lambda U^T
        # Note: W[:, j] = g_j / sig^2, so diag_j = 1 / W[:, j] (all W[:, j] > 0 for z in (0, 0.2)).
        window_pv_rows = []
        for j, center in enumerate(H03.CENTERS):
            wj = W[:, j]
            if np.any(wj <= 0) or not np.all(np.isfinite(1.0 / wj)):
                raise ValueError(f"Window {j} has zero/underflow weights; cannot invert diagonal cleanly")
            diag_j = 1.0 / wj
            Cinv_X = woodbury_solve(diag_j, U, lam, X9)
            Cinv_y = woodbury_solve(diag_j, U, lam, y)
            Fj_pv = 0.5 * (X9.T @ Cinv_X + (X9.T @ Cinv_X).T)
            bj_pv = X9.T @ Cinv_y
            cf_pv = cho_factor(Fj_pv, lower=True, check_finite=False)
            th_pv = cho_solve(cf_pv, bj_pv, check_finite=False)
            inv_pv = cho_solve(cf_pv, np.eye(9), check_finite=False)

            # Weighted projection residual of U onto X9 in window j
            w_sqrt = np.sqrt(wj)
            Xw = w_sqrt[:, None] * X9
            Uw = w_sqrt[:, None] * U
            proj = np.linalg.lstsq(Xw, Uw, rcond=None)[0]
            rel_res = np.linalg.norm(Uw - Xw @ proj, axis=0) / np.linalg.norm(Uw, axis=0)

            window_pv_rows.append({
                "window_index": j,
                "z_center": float(center),
                "theta_pv_minus_diag_maxabs": float(np.max(np.abs(th_pv - h03_gls["theta"][j]))),
                "theta_pv_monopole_shift": float(th_pv[0] - h03_gls["theta"][j, 0]),
                "theta_pv_dipole_shift_norm": float(np.linalg.norm(th_pv[1:4] - h03_gls["theta"][j, 1:4])),
                "theta_pv_stf5_shift_norm": float(np.linalg.norm(th_pv[4:9] - h03_gls["theta"][j, 4:9])),
                "window_cov_trace_ratio_Cj_vs_diag": float(np.trace(inv_pv) / np.trace(F_diag_invs[j])),
                "U_weighted_relative_distance_to_X9_span": rel_res.tolist(),
            })

        pv_4window.append({
            "sigma_bulk_km_per_s": float(bulk_sig),
            "sigma_shear_km_per_s_per_Mpc": float(shear_sig),
            "velocity_modes_rank": int(U.shape[1]),
            "fixed_4x9_estimator_36x36_cov_trace_ratio": float(
                np.trace(C36_fixed_est_with_PV) / np.trace(C36_diag)
            ),
            "fixed_4x9_estimator_36x36_cov_min_eigen": float(ev_fixed[0]),
            "window_by_window_woodbury_gls": window_pv_rows,
            "physical_PV_field_qualified": False,
        })

    elapsed = time.perf_counter() - t0
    out = {
        "schema": "htt.r89.g02_cf4_bounded_source_diagnostic/1",
        "group_id": "G02_CF4",
        "node_ids": ["H01", "H03", "SQ-CF4", "H02", "H04", "H05", "H06"],
        "source_sha256": {
            **s.source_sha256,
            "R87_RESULT": _sha256(ROOT / "docs/research_program/observational_publication_20261015/R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/RESULT.json"),
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "h03_backend_receipt": h03_receipt,
            "k02_backend_receipt": k02_receipt,
        },
        "p0c_fail_closed_check": {
            "node_id": p0c_packet["node_id"],
            "status": p0c_packet["status"],
            "science_execution_authorized": p0c_packet["science_execution_authorized"],
        },
        "h01_h03_k02_baseline": {
            "selected_groups": 35970,
            "h03_theta_4x9": h03_gls["theta"],
            "h03_condition_normal": h03_gls["condition_normal"],
            "h03_joint_cov_36x36_min_eigen": float(np.linalg.eigvalsh(C36_diag)[0]),
            "k02_shape8_4x8": k02_res["shape8"],
            "k02_intercepts4_4x4": k02_res["intercepts4"],
            "k02_joint_cov_32x32_min_eigen": float(k02_res["source_eig_min"]),
        },
        "window_method_genealogy_4w": window_genealogy,
        "table4_vs_table3_empirical_offsets": table4_vs_table3,
        "table3_delta_aligned_propagation_sensitivity": {
            "h03_4x9_theta_shift": h03_delta_theta,
            "h03_4x9_max_abs_shift": float(np.max(np.abs(h03_delta_theta))),
            "k02_4x8_shape_shift": k02_delta_shape8,
            "k02_4x8_max_abs_shape_shift": float(np.max(np.abs(k02_delta_shape8))),
            "note": "Sensitivity to substituting table3 inverse-variance combined modulus aligned via R87 delta_mag + mean SNIA tie-in for table4 DMzp",
        },
        "ra_quadrant_4w_heldout_product_consistency": {
            "r87_method_contrast_folds": r87_held["folds"],
            "h03_4x9_velocity_folds": ra_heldout_4x9,
            "independent_upstream_heldout": False,
        },
        "multi_window_36d_pv_sensitivity": pv_4window,
        "physical_claim_gates": {
            "N_stat": "WORKING_DIAGONAL_ONLY",
            "S_PV": None,
            "J_cal_Sigma_cal_J_cal_T": None,
            "C_selection": None,
            "independent_upstream_heldout": None,
            "physical_H_z_n": None,
            "physical_Pi": None,
            "SQ_CF4_physical_status": "BLOCKED_INPUT",
            "H02_status": "BLOCKED_INPUT",
            "H04_H05_H06_status": "BLOCKED_DEPENDENCY",
        },
        "node_verdicts": {
            "H01": "REUSED_SCOPED",
            "H03": "REUSED_SCOPED",
            "SQ-CF4": "DIAGNOSTIC_COMPLETED_SCOPED",
            "H02": "BLOCKED_INPUT",
            "H04": "BLOCKED_DEPENDENCY",
            "H05": "BLOCKED_DEPENDENCY",
            "H06": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "pre-intercalibration zero-point posterior and J_cal Sigma_cal J_cal^T",
                "independently calibrated 35970-group S_PV ensemble",
                "survey selection/completeness C_selection",
                "upstream-independent calibration heldout/null",
            ],
            "next_action": "Obtain true CF4 upstream calibration/PV/selection/null inputs for SQ-CF4 -> H02; keep H04-H06 blocked and proceed independently to G03_GAIA (SQ-GAIA)",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(_serialize(out), indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G02_CF4",
        "elapsed_s": round(elapsed, 3),
        "maxrss_mib": round(out["runtime"]["maxrss_kib"] / 1024.0, 1),
        "h03_delta_max": out["table3_delta_aligned_propagation_sensitivity"]["h03_4x9_max_abs_shift"],
        "k02_delta_max": out["table3_delta_aligned_propagation_sensitivity"]["k02_4x8_max_abs_shape_shift"],
        "pv_36d_trace_ratios": [x["fixed_4x9_estimator_36x36_cov_trace_ratio"] for x in pv_4window],
        "p0c_status": p0c_packet["status"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
