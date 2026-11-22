"""R97 Unit A (SQ-CF4 / P3): Complete CF4 table2/table3 genealogy, R36-vs-R27 subspace reconciliation & sharp partial-ID bounds.

Connects:
  - Raw Cosmicflows-4 table2.dat (55,877 galaxies), table3.dat (38,053 groups),
    table4.dat, ReadMe (SHA-pinned)
  - 35,970 selected CF4 groups (selected_source_observables.npz)
  - R36 RESULT_MATRICES.npz (K4 in (km/s/Mpc) per method-offset, Sigma4, pv_total, conditional_R5)
  - R27 FACTOR.npz (7-channel selected_support_7)
  - R87 htt.obsstat.cf4_p0b + R95 sq_cf4_synthesis + R96 cf4_covariance_bridge

Scientifically establishes:
  1. Reconciles table3.dat blank-count-flag rows (+87 FP, +120 TFR, +2 SBFir) with R27
     selected_support_7 (0 mismatches across all 6 velocity channels) and identifies the
     exact CAL (11) vs DirectCal (2) definition split.
  2. Derives table3 DMzp == DMav - 0.147 mag identically across all 35,968 non-DirectCal-only
     groups, verifies table2 per-galaxy MCMC-registered scales vs table3 pre-offset scales,
     and builds the empirical inter-method overlap covariance Sigma_overlap (rank 5) plus
     unidentifiable common zero-point rank-1 nullspace u0 = 1/sqrt(7).
  3. Reconciles R36 K4 == A @ (d * I4) vs R27 J7 == A @ (d * dcz_dmu * S7) via canonical
     angles and weighted-metric variance decomposition; never sums non-equivalent models.
  4. Computes exact closed-form & GLS-verified sharp partial-identification bounds and
     radial-window Schur + Sky-NS / Galactic-hemisphere heldout checks.

Preserves SQ-CF4 = BLOCKED_INPUT, publication_ready = False, full_S_PV_and_calibration = None.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
import sys

import numpy as np
from astropy.coordinates import SkyCoord
from scipy.linalg import cho_factor, cho_solve, subspace_angles

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from htt.obsstat import cf4_p0b
from scripts.r95 import sq_cf4_synthesis as r95
from scripts.r96 import cf4_covariance_bridge as r96

RAW_CF4 = Path("/mnt/extdrive/workdir/raw/cf4_full")
R36_NPZ = Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual/RESULT_MATRICES.npz")
R27_NPZ = Path("/mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_numeric/actual_run/products/FACTOR.npz")
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R97_SCIENCE_EXECUTION_20261122/CF4_GENEALOGY_AND_PARTIAL_ID.json"

# Standard H0_fid = 70.0 km/s/Mpc linearization matching R95/R96 J7 definition (note: ~4% lower than H0_point ~ 72.9).
DCZ_DMU_FACTOR = -(math.log(10.0) / 5.0) * 70.0


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _parse_complete_table3_for_selected(group_ids: np.ndarray) -> dict:
    """Parse ALL numeric DM/e_DM fields in table3.dat (including rows where o_DM* count is blank)."""
    t3_path = RAW_CF4 / "table3.dat"
    t3_lines = {int(r[:7]): r for r in t3_path.read_text(encoding="ascii").splitlines() if r.strip()}
    # 0-based byte slices matching ReadMe 1-based positions:
    # DMzp(9-14)->[8:14], DMav(16-21)->[15:21], e_DMav(23-27)->[22:27]
    # CAL: o(88:90), DM(91:97)
    # SNIA: o(98:99), DM(100:106), e(107:112)
    # FP: o(113:116), DM(117:123), e(124:129)
    # TF: o(130:132), DM(133:139), e(140:145)
    # SBFO: o(146:149), DM(150:156), e(157:162)
    # SBFI: o(163:164), DM(165:171), e(172:177)
    # SNII: o=None, DM(178:184), e(185:190)
    col_specs = [
        ("CAL", (88, 90), (91, 97), None),
        ("SNIA", (98, 99), (100, 106), (107, 112)),
        ("FP", (113, 116), (117, 123), (124, 129)),
        ("TF", (130, 132), (133, 139), (140, 145)),
        ("SBFO", (146, 149), (150, 156), (157, 162)),
        ("SBFI", (163, 164), (165, 171), (172, 177)),
        ("SNII", None, (178, 184), (185, 190)),
    ]
    n = len(group_ids)
    dmzp = np.empty(n, dtype=np.float64)
    dmav = np.empty(n, dtype=np.float64)
    e_dmav = np.empty(n, dtype=np.float64)
    count_present = np.zeros((n, 7), dtype=bool)
    dm_present = np.zeros((n, 7), dtype=bool)
    dm_vals = np.full((n, 6), np.nan, dtype=np.float64)  # 6 velocity methods
    e_vals = np.full((n, 6), np.inf, dtype=np.float64)
    cal_vals = np.full(n, np.nan, dtype=np.float64)

    def _flt(s: str) -> float:
        st = s.strip()
        return float(st) if st else np.nan

    for row, gid in enumerate(group_ids):
        r = t3_lines[int(gid)]
        dmzp[row] = float(r[8:14])
        dmav[row] = float(r[15:21])
        e_dmav[row] = float(r[22:27])
        for j, (name, o_sp, dm_sp, e_sp) in enumerate(col_specs):
            v = _flt(r[dm_sp[0]:dm_sp[1]])
            has_num = np.isfinite(v) and v > 0.0
            if o_sp is not None:
                os = r[o_sp[0]:o_sp[1]].strip()
                has_o = (int(os) > 0) if os else False
            else:
                has_o = has_num
            count_present[row, j] = has_o
            dm_present[row, j] = has_num
            if j == 0:
                if has_num:
                    cal_vals[row] = v
            else:
                if has_num:
                    ev = _flt(r[e_sp[0]:e_sp[1]])
                    if not np.isfinite(ev) or ev <= 0.0:
                        raise RuntimeError(f"Non-positive e_DM for {name} in gid={gid}")
                    dm_vals[row, j - 1] = v
                    e_vals[row, j - 1] = ev

    # Verify exact global shift between DMzp and DMav for the 35,968 groups with DMav > 0
    has_av = dmav > 0.0
    zp_minus_av = dmzp[has_av] - dmav[has_av]
    return {
        "dmzp": dmzp,
        "dmav": dmav,
        "e_dmav": e_dmav,
        "count_present_7": count_present,
        "dm_present_7": dm_present,
        "dm_vals_6": dm_vals,
        "e_vals_6": e_vals,
        "cal_vals": cal_vals,
        "n_dmav_zero": int(np.sum(~has_av)),
        "dmav_zero_group_ids": group_ids[~has_av].tolist(),
        "dmzp_minus_dmav_min": float(np.min(zp_minus_av)),
        "dmzp_minus_dmav_max": float(np.max(zp_minus_av)),
    }


def _parse_table2_genealogy(group_ids: np.ndarray, t3_parsed: dict) -> dict:
    """Compare individual-galaxy table2.dat MCMC-registered moduli vs group table3.dat moduli."""
    t2_path = RAW_CF4 / "table2.dat"
    t2_lines = [r for r in t2_path.read_text(encoding="ascii").splitlines() if r.strip()]
    from collections import defaultdict
    t2_by_g: dict[int, list[str]] = defaultdict(list)
    n_selected_galaxies = 0
    sel_set = set(int(g) for g in group_ids.tolist())
    for r in t2_lines:
        g1 = int(r[8:15])
        t2_by_g[g1].append(r)
        if g1 in sel_set:
            n_selected_galaxies += 1

    spans2 = {"SNIA": (41, 47), "TF": (53, 59), "FP": (65, 71), "SBF": (77, 83), "SNII": (90, 96)}
    idx3_map = {"SNIA": 0, "FP": 1, "TF": 2, "SBFO": 3, "SBFI": 4, "SNII": 5}
    method_pairs = [("SNIA", "SNIA"), ("FP", "FP"), ("TF", "TF"), ("SBF", "SBFO"), ("SBF", "SBFI"), ("SNII", "SNII")]
    t3_minus_t2_stats = {}
    for m2, m3 in method_pairs:
        diffs = []
        j3 = idx3_map[m3]
        for row, gid in enumerate(group_ids):
            rows2 = t2_by_g.get(int(gid), [])
            if len(rows2) != 1:
                continue
            v3 = t3_parsed["dm_vals_6"][row, j3]
            if not np.isfinite(v3):
                continue
            s2 = rows2[0][spans2[m2][0]:spans2[m2][1]].strip()
            if s2:
                diffs.append(round(float(v3) - float(s2), 4))
        arr = np.asarray(diffs, dtype=np.float64)
        uniq = sorted(set(float(x) for x in arr.tolist()))
        t3_minus_t2_stats[f"{m3}_minus_table2_{m2}"] = {
            "n_single_member_groups": int(len(arr)),
            "unique_rounded_offsets": uniq[:12],
            "n_unique_offsets": len(uniq),
            "median_mag": float(np.median(arr)) if len(arr) else None,
        }

    return {
        "table2_sha256": _sha(t2_path),
        "table2_total_galaxies": len(t2_lines),
        "table2_galaxies_in_selected_35970_groups": n_selected_galaxies,
        "single_member_table3_minus_table2_mag": t3_minus_t2_stats,
        "genealogy_interpretation": (
            "table2 per-method columns are already MCMC-registered to DMzp; table3 retains raw arbitrary per-method scales "
            "before global -0.147 mag SNIa->calibrator tie (DMzp = DMav - 0.147 identically across 35,968 groups)."
        ),
    }


def _reconcile_subspaces(K4: np.ndarray, Sigma4: np.ndarray, J7: np.ndarray, C0: np.ndarray) -> dict:
    """Exact subspace angles & quadratic variance decomposition between R36 K4 (36x4) and R27 J7 (36x7)."""
    # Euclidean principal angles (rad -> deg)
    ang_euc = subspace_angles(K4, J7)
    # Precision-weighted C0^{-1/2} principal angles
    evals, evecs = np.linalg.eigh(0.5 * (C0 + C0.T))
    W_half = (evecs / np.sqrt(evals)[None, :]) @ evecs.T
    K4_w = W_half @ K4
    J7_w = W_half @ J7
    ang_w = subspace_angles(K4_w, J7_w)

    # Project K4 onto col(J7) in precision metric M = C0^{-1} and Euclidean metric
    P_J_euc = J7 @ np.linalg.pinv(J7)
    K4_proj_euc = P_J_euc @ K4
    rel_orth_euc = float(np.linalg.norm(K4 - K4_proj_euc) / np.linalg.norm(K4))

    Q_J, _ = np.linalg.qr(J7_w)
    K4_w_proj = Q_J @ (Q_J.T @ K4_w)
    C_K_w = K4_w @ Sigma4 @ K4_w.T
    C_K_in_J_w = K4_w_proj @ Sigma4 @ K4_w_proj.T
    K4_w_orth = K4_w - K4_w_proj
    C_K_orth_J_w = K4_w_orth @ Sigma4 @ K4_w_orth.T

    # Check exact R36 residual trace wrt C_R36 - C_PV - K4 Sigma4 K4^T vs (K4 orth J7)
    return {
        "K4_rank": int(np.linalg.matrix_rank(K4)),
        "J7_rank": int(np.linalg.matrix_rank(J7)),
        "euclidean_principal_angles_deg": np.rad2deg(ang_euc).tolist(),
        "metric_C0inv_principal_angles_deg": np.rad2deg(ang_w).tolist(),
        "K4_relative_residual_orth_to_J7_euclidean": rel_orth_euc,
        "whitened_trace_K4Sigma4K4T": float(np.trace(C_K_w)),
        "whitened_trace_inside_col_J7": float(np.trace(C_K_in_J_w)),
        "whitened_trace_orth_to_col_J7": float(np.trace(C_K_orth_J_w)),
        "fraction_whitened_variance_inside_col_J7": float(np.trace(C_K_in_J_w) / np.trace(C_K_w)),
        "units_distinction": "K4 = A@(d*I4) has dimensionless velocity-offset units [km/s/Mpc per km/s/Mpc offset]; J7 = A@(d*(-ln(10)/5*70)*S7) has mag units [(km/s/Mpc)/mag].",
    }


def _sharp_partial_id_bounds(C_base: np.ndarray, J_bound: np.ndarray, Sigma_bound: np.ndarray,
                             D: np.ndarray, y: np.ndarray, r2_chi2: float) -> dict:
    """Exact sharp partial-identification bounds over delta^T Sigma_bound^{-1} delta <= r2_chi2.

    Compares closed-form Cauchy-Schwarz bound c^T G Sigma_bound G^T c against direct brute-force
    GLS substitution theta' = y - J_bound @ delta_worst at +- the extreme delta!
    """
    beta_hat, cov_hat, chi2_hat = r96.woodbury_gls(C_base, np.zeros((36, 0)), D, y)
    cc = cho_factor(0.5 * (C_base + C_base.T), lower=True, check_finite=False)
    CiD = cho_solve(cc, D, check_finite=False)
    CiJ = cho_solve(cc, J_bound, check_finite=False)
    fisher_inv = np.linalg.inv(D.T @ CiD)
    # G = d(beta_hat)/d(-delta) = (D^T C^{-1} D)^{-1} D^T C^{-1} J_bound   (since mu_shift -> y - J delta)
    G = fisher_inv @ (D.T @ CiJ)
    r = math.sqrt(float(r2_chi2))

    # 1. Monopole H0 extremal delta
    e0 = np.zeros(9, dtype=np.float64)
    e0[0] = 1.0
    g0 = G.T @ e0
    halfwidth_H0 = r * math.sqrt(max(0.0, float(g0 @ Sigma_bound @ g0)))
    # Check extreme substitution delta_* = -(r / sqrt(g0^T Sig g0)) * Sig @ g0
    denom0 = math.sqrt(max(float(g0 @ Sigma_bound @ g0), 1e-30))
    delta_hi = -(r / denom0) * (Sigma_bound @ g0)
    beta_hi, _, _ = r96.woodbury_gls(C_base, np.zeros((36, 0)), D, y - J_bound @ delta_hi)
    sub_err = float(abs(beta_hi[0] - (beta_hat[0] + halfwidth_H0)))
    if sub_err > 1e-11:
        raise RuntimeError(f"Partial-ID substitution parity error: {sub_err}")

    # 2. Maximum L2 shift of dipole vector (beta[1:4]) over the ellipsoid:
    # max_{delta^T Sig^-1 delta <= r^2} || G_dip delta ||_2 = r * sqrt(lambda_max(G_dip Sigma_bound G_dip^T))
    G_dip = G[1:4, :]
    M_d = G_dip @ Sigma_bound @ G_dip.T
    evals_dip, evecs_dip = np.linalg.eigh(0.5 * (M_d + M_d.T))
    idx_d = int(np.argmax(evals_dip))
    max_dip_shift = r * math.sqrt(max(0.0, float(evals_dip[idx_d])))
    u_dip = evecs_dip[:, idx_d]
    gd_vec = G_dip.T @ u_dip
    denom_d = math.sqrt(max(float(gd_vec @ Sigma_bound @ gd_vec), 1e-30))
    delta_dip_hi = -(r / denom_d) * (Sigma_bound @ gd_vec)
    beta_dip_hi, _, _ = r96.woodbury_gls(C_base, np.zeros((36, 0)), D, y - J_bound @ delta_dip_hi)
    dip_sub_err = float(abs(np.linalg.norm(beta_dip_hi[1:4] - beta_hat[1:4]) - max_dip_shift))
    if dip_sub_err > 1e-11:
        raise RuntimeError(f"Dipole partial-ID substitution parity error: {dip_sub_err}")

    # 3. Maximum L2 shift of STF5 quadrupole (beta[4:9]) over the ellipsoid:
    G_q5 = G[4:9, :]
    M_q = G_q5 @ Sigma_bound @ G_q5.T
    evals_q, evecs_q = np.linalg.eigh(0.5 * (M_q + M_q.T))
    idx_q = int(np.argmax(evals_q))
    max_q5_shift = r * math.sqrt(max(0.0, float(evals_q[idx_q])))
    u_q = evecs_q[:, idx_q]
    gq_vec = G_q5.T @ u_q
    denom_q = math.sqrt(max(float(gq_vec @ Sigma_bound @ gq_vec), 1e-30))
    delta_q_hi = -(r / denom_q) * (Sigma_bound @ gq_vec)
    beta_q_hi, _, _ = r96.woodbury_gls(C_base, np.zeros((36, 0)), D, y - J_bound @ delta_q_hi)
    q_sub_err = float(abs(np.linalg.norm(beta_q_hi[4:9] - beta_hat[4:9]) - max_q5_shift))
    if q_sub_err > 1e-11:
        raise RuntimeError(f"Quadrupole partial-ID substitution parity error: {q_sub_err}")

    max_sub_err = max(sub_err, dip_sub_err, q_sub_err)

    return {
        "H0_point": float(beta_hat[0]),
        "H0_stat_sd": float(math.sqrt(cov_hat[0, 0])),
        "H0_partial_id_halfwidth": float(halfwidth_H0),
        "H0_partial_id_interval": [float(beta_hat[0] - halfwidth_H0), float(beta_hat[0] + halfwidth_H0)],
        "dipole_amp_point": float(np.linalg.norm(beta_hat[1:4])),
        "dipole_max_ellipsoid_shift": float(max_dip_shift),
        "quad_norm_point": float(np.linalg.norm(beta_hat[4:9])),
        "quad_max_ellipsoid_shift": float(max_q5_shift),
        "chi2_27dof": float(chi2_hat),
        "gls_substitution_parity_err": max_sub_err,
    }


def _evaluate_disjoint_partitions(H, inp, d, sig, X, y_raw, theta_full, PV_r5, C_r36, J7, S7) -> dict:
    """Evaluate disjoint sky (Galactic N/S) and radial-window (inner z<=0.04 vs outer z>0.04) consistency."""
    D = np.tile(np.eye(9, dtype=np.float64), (4, 1))
    # A. Radial window Schur cross-prediction under C_R36 vs C_R95(R5, cal=0.05)
    c_r95_005 = PV_r5 + r96.r95._load_h03().joint_covariance(
        np.vstack([H.fit(X, y_raw, H.window(inp.z, sig, zc), influence=True)["A"] for zc in H.CENTERS]),
        sig,
    )[0] + (0.05 ** 2) * (J7 @ J7.T)
    radial_checks = {}
    for model_name, C36 in (("C_R36_inherited", C_r36), ("C_R95_R5_cal005", c_r95_005)):
        # Blocks: train = windows 0,1 (indices 0:18), test = windows 2,3 (indices 18:36)
        C11 = C36[:18, :18]
        C21 = C36[18:, :18]
        C22 = C36[18:, 18:]
        D1 = D[:18, :]
        D2 = D[18:, :]
        y1 = theta_full[:18]
        y2 = theta_full[18:]
        cc11 = cho_factor(0.5 * (C11 + C11.T), lower=True, check_finite=False)
        C11_inv_D1 = cho_solve(cc11, D1, check_finite=False)
        F11 = D1.T @ C11_inv_D1
        cov_beta1 = np.linalg.inv(0.5 * (F11 + F11.T))
        beta1 = cov_beta1 @ (D1.T @ cho_solve(cc11, y1, check_finite=False))
        # Exact predictive residual y2 - y2_pred includes beta1 estimation uncertainty H @ Cov(beta1) @ H^T:
        # res2 = (y2 - D2 beta) - C21 C11^{-1}(y1 - D1 beta) - H(beta1 - beta), where H = D2 - C21 C11^{-1} D1
        C11_inv_C12 = cho_solve(cc11, C21.T, check_finite=False)
        H_schur = D2 - C21 @ C11_inv_D1
        y2_pred = D2 @ beta1 + C21 @ cho_solve(cc11, y1 - D1 @ beta1, check_finite=False)
        C22_cond = C22 - C21 @ C11_inv_C12
        C22_pred = C22_cond + H_schur @ cov_beta1 @ H_schur.T
        C22_pred = 0.5 * (C22_pred + C22_pred.T)
        res2 = y2 - y2_pred
        chi2_cond = float(res2 @ cho_solve(cho_factor(C22_pred, lower=True, check_finite=False), res2, check_finite=False))
        radial_checks[model_name] = {
            "inner_2w_H0": float(beta1[0]),
            "outer_2w_pred_chi2_18dof": chi2_cond,
            "outer_2w_pred_reduced_chi2": float(chi2_cond / 18.0),
            "outer_2w_H0_residual_z055_z070": [float(res2[0]), float(res2[9])],
        }

    # B. Galactic North (b>=0) vs South (b<0) 4-window refits
    sc = SkyCoord(x=inp.n[:, 0], y=inp.n[:, 1], z=inp.n[:, 2], representation_type="cartesian", frame="icrs").galactic
    gb = sc.b.deg
    hemi_out = {}
    for label, mask in (("Galactic_North", gb >= 0.0), ("Galactic_South", gb < 0.0)):
        Xm, ym, sigm, zm, S7m, dm = X[mask], y_raw[mask], sig[mask], inp.z[mask], S7[mask], d[mask]
        dcz_m = DCZ_DMU_FACTOR * dm
        A_m = []
        th_m = np.empty(36, dtype=np.float64)
        for j, zc in enumerate(H.CENTERS):
            fm = H.fit(Xm, ym, H.window(zm, sigm, zc), influence=True)
            A_m.append(fm["A"])
            th_m[j * 9 : (j + 1) * 9] = fm["theta"]
        Am_full = np.vstack(A_m)
        Cn_m, _ = H.joint_covariance(Am_full, sigm)
        J7_m = Am_full @ (S7m * dcz_m[:, None])
        beta_m, cov_m, chi_m = r96.woodbury_gls(Cn_m, J7_m * 0.05, D, th_m)
        hemi_out[label] = {
            "n_groups": int(np.sum(mask)),
            "H0_working_noise_plus_cal005": float(beta_m[0]),
            "H0_sd": float(math.sqrt(cov_m[0, 0])),
            "dipole_amp": float(np.linalg.norm(beta_m[1:4])),
            "chi2_27dof_no_PV": float(chi_m),
        }

    # Update outer residual keys cleanly (windows 2 and 3 have centers z = 0.06, 0.08)
    for m_row in radial_checks.values():
        res_vals = m_row.pop("outer_2w_H0_residual_z055_z070")
        m_row["outer_2w_H0_residual_z060_z080"] = res_vals

    win_masks = [H.window(inp.z, sig, zc) > 0.0 for zc in H.CENTERS]
    return {
        "window_centers_z": [float(c) for c in H.CENTERS],
        "window_positive_weight_counts": [int(np.count_nonzero(m)) for m in win_masks],
        "all_four_windows_shared_support_count": int(np.count_nonzero(np.logical_and.reduce(win_masks))),
        "radial_inner_to_outer_schur_18dof": radial_checks,
        "galactic_hemisphere_split_cal005_no_PV": hemi_out,
        "note": "Internal spatial/radial consistency on overlapping windows over the same 35,970 groups under working covariance models; does not supply independent selection/PV heldout.",
    }


def _evaluate_source_modulus_perturbation(
    H,
    inp,
    dist: np.ndarray,
    sig: np.ndarray,
    X: np.ndarray,
    y_raw: np.ndarray,
    weights_base: list[np.ndarray],
    theta_base: np.ndarray,
    W7: np.ndarray,
    J7_ivw: np.ndarray,
    C_pv5_noise: np.ndarray,
    PV_r5: np.ndarray,
    C_r36: np.ndarray,
    Sigma_pri_r95: np.ndarray,
    D: np.ndarray,
    chi2_7_95: float,
) -> dict:
    """Compare frozen-design velocity-residual approximation against actual source distance-modulus refits.

    Evaluates:
      1. Common zero-point shift delta = delta_0 * 1_7 (delta_0 in {-0.087, +0.087} mag):
         - Fixed window weights w_base -> exact scaling beta(delta_0) = 10^(-delta_0/5) * beta(0),
           non-zero dipole & STF5 shifts, and invariant q = ||STF5|| / H0.
         - Updated working weights w(z, sigma(k*d, e_mu)) under both fixed-C and updated C_noise(delta_0).
      2. Full 36x7 finite-difference source-response Jacobians J_source_fixed_w and J_source_updated_w
         vs frozen-design J7_ivw, plus resulting 7-channel ellipsoid sensitivity bounds.
    """
    beta_r95_0, _, _ = r96.woodbury_gls(C_pv5_noise, np.zeros((36, 0)), D, theta_base)
    beta_r36_0, _, _ = r96.woodbury_gls(C_r36, np.zeros((36, 0)), D, theta_base)
    q_r95_0 = float(np.linalg.norm(beta_r95_0[4:9]) / beta_r95_0[0])
    q_r36_0 = float(np.linalg.norm(beta_r36_0[4:9]) / beta_r36_0[0])

    cc_r95 = cho_factor(0.5 * (C_pv5_noise + C_pv5_noise.T), lower=True, check_finite=False)
    B_r95 = np.linalg.inv(D.T @ cho_solve(cc_r95, D, check_finite=False)) @ (D.T @ cho_solve(cc_r95, np.eye(36), check_finite=False))
    cc_r36 = cho_factor(0.5 * (C_r36 + C_r36.T), lower=True, check_finite=False)
    B_r36 = np.linalg.inv(D.T @ cho_solve(cc_r36, D, check_finite=False)) @ (D.T @ cho_solve(cc_r36, np.eye(36), check_finite=False))

    common_shifts = {}
    max_scaling_err = 0.0
    max_q_invariance_err = 0.0
    for delta_0 in (-0.087, 0.087):
        k = 10.0 ** (delta_0 / 5.0)
        d_k = k * dist
        X_k = k * X
        th_fix = np.concatenate([H.fit(X_k, y_raw, wb, influence=False)["theta"] for wb in weights_base])
        b95_fix = B_r95 @ th_fix
        b36_fix = B_r36 @ th_fix
        sc_err = max(
            float(np.max(np.abs(b95_fix - beta_r95_0 / k))),
            float(np.max(np.abs(b36_fix - beta_r36_0 / k))),
        )
        max_scaling_err = max(max_scaling_err, sc_err)
        q95_fix = float(np.linalg.norm(b95_fix[4:9]) / b95_fix[0])
        q36_fix = float(np.linalg.norm(b36_fix[4:9]) / b36_fix[0])
        q_inv_err = max(abs(q95_fix - q_r95_0), abs(q36_fix - q_r36_0))
        max_q_invariance_err = max(max_q_invariance_err, q_inv_err)

        # Updated working weights w(z, sigma(k*d, e_mu))
        sig_k = H.working_sigma(d_k, inp.e_mu)
        fits_upd = [H.fit(X_k, y_raw, H.window(inp.z, sig_k, zc), influence=True) for zc in H.CENTERS]
        th_upd = np.concatenate([f["theta"] for f in fits_upd])
        b95_upd_fixedC = B_r95 @ th_upd
        b36_upd_fixedC = B_r36 @ th_upd
        A_upd = np.vstack([f["A"] for f in fits_upd])
        Cn_upd, _ = H.joint_covariance(A_upd, sig_k)
        b95_upd_updC, _, _ = r96.woodbury_gls(PV_r5 + Cn_upd, np.zeros((36, 0)), D, th_upd)

        common_shifts[f"delta_{delta_0:+.3f}"] = {
            "delta_mag": delta_0,
            "distance_scale_k": k,
            "R95_fixed_weights": {
                "H0": float(b95_fix[0]),
                "dipole_shift_norm_kms_Mpc": float(np.linalg.norm(b95_fix[1:4] - beta_r95_0[1:4])),
                "quad_shift_norm_kms_Mpc": float(np.linalg.norm(b95_fix[4:9] - beta_r95_0[4:9])),
                "q_app_global": q95_fix,
                "scaling_law_max_abs_err": sc_err,
            },
            "R36_fixed_weights": {
                "H0": float(b36_fix[0]),
                "dipole_shift_norm_kms_Mpc": float(np.linalg.norm(b36_fix[1:4] - beta_r36_0[1:4])),
                "quad_shift_norm_kms_Mpc": float(np.linalg.norm(b36_fix[4:9] - beta_r36_0[4:9])),
                "q_app_global": q36_fix,
            },
            "R95_updated_weights_fixed_C": {
                "H0": float(b95_upd_fixedC[0]),
                "dipole_shift_norm_kms_Mpc": float(np.linalg.norm(b95_upd_fixedC[1:4] - beta_r95_0[1:4])),
                "quad_shift_norm_kms_Mpc": float(np.linalg.norm(b95_upd_fixedC[4:9] - beta_r95_0[4:9])),
            },
            "R36_updated_weights_fixed_C": {
                "H0": float(b36_upd_fixedC[0]),
                "dipole_shift_norm_kms_Mpc": float(np.linalg.norm(b36_upd_fixedC[1:4] - beta_r36_0[1:4])),
                "quad_shift_norm_kms_Mpc": float(np.linalg.norm(b36_upd_fixedC[4:9] - beta_r36_0[4:9])),
            },
            "R95_updated_weights_updated_Cnoise": {
                "H0": float(b95_upd_updC[0]),
                "dipole_shift_norm_kms_Mpc": float(np.linalg.norm(b95_upd_updC[1:4] - beta_r95_0[1:4])),
                "quad_shift_norm_kms_Mpc": float(np.linalg.norm(b95_upd_updC[4:9] - beta_r95_0[4:9])),
            },
        }

    # Central finite-difference 36x7 source Jacobians under fixed vs updated working weights
    eps = 1e-5
    J_src_fixed_w = np.zeros((36, 7), dtype=np.float64)
    J_src_updated_w = np.zeros((36, 7), dtype=np.float64)
    for c in range(7):
        th_f_pm = {}
        th_u_pm = {}
        for sgn in (+1.0, -1.0):
            k_i = np.power(10.0, (sgn * eps / 5.0) * W7[:, c])
            d_i = dist * k_i
            X_i = X * k_i[:, None]
            sig_i = H.working_sigma(d_i, inp.e_mu)
            th_f_pm[sgn] = np.concatenate([H.fit(X_i, y_raw, wb, influence=False)["theta"] for wb in weights_base])
            th_u_pm[sgn] = np.concatenate([H.fit(X_i, y_raw, H.window(inp.z, sig_i, zc), influence=False)["theta"] for zc in H.CENTERS])
        J_src_fixed_w[:, c] = (th_f_pm[+1.0] - th_f_pm[-1.0]) / (2.0 * eps)
        J_src_updated_w[:, c] = (th_u_pm[+1.0] - th_u_pm[-1.0]) / (2.0 * eps)

    u_com = np.ones(7, dtype=np.float64)
    exact_dth_dcom = -(math.log(10.0) / 5.0) * theta_base
    jac_common_scale_err = float(np.max(np.abs(J_src_fixed_w @ u_com - exact_dth_dcom)))
    # Note sign convention in _sharp_partial_id_bounds: y_shift = y - J_bound @ delta => pass -J_src!
    # Since _sharp_partial_id_bounds is symmetric in sign (+/-delta), sign does not change halfwidths/shifts,
    # while matching d(theta)/d(+delta) = J_src requires passing -J_src so y - (-J_src) delta = y + J_src delta.
    src_bounds = {
        "R95_source_fixed_w_0p087_1sigma": _sharp_partial_id_bounds(C_pv5_noise, -J_src_fixed_w, Sigma_pri_r95, D, theta_base, 1.0),
        "R95_source_fixed_w_0p087_95pct_ellipsoid": _sharp_partial_id_bounds(C_pv5_noise, -J_src_fixed_w, Sigma_pri_r95, D, theta_base, chi2_7_95),
        "R95_source_updated_w_0p087_1sigma": _sharp_partial_id_bounds(C_pv5_noise, -J_src_updated_w, Sigma_pri_r95, D, theta_base, 1.0),
        "R95_source_updated_w_0p087_95pct_ellipsoid": _sharp_partial_id_bounds(C_pv5_noise, -J_src_updated_w, Sigma_pri_r95, D, theta_base, chi2_7_95),
        "R36_source_fixed_w_common_0p087_1sigma": _sharp_partial_id_bounds(
            C_r36, -J_src_fixed_w, (0.087 ** 2) * np.outer(u_com, u_com) + 1e-10 * np.eye(7), D, theta_base, 1.0
        ),
    }

    return {
        "regime": "physical_source_modulus_perturbation",
        "common_scale_shifts_pm0p087mag": common_shifts,
        "fixed_w_R95_H0_interval_exact_refit": [
            common_shifts["delta_+0.087"]["R95_fixed_weights"]["H0"],
            common_shifts["delta_-0.087"]["R95_fixed_weights"]["H0"],
        ],
        "fixed_w_R36_H0_interval_exact_refit": [
            common_shifts["delta_+0.087"]["R36_fixed_weights"]["H0"],
            common_shifts["delta_-0.087"]["R36_fixed_weights"]["H0"],
        ],
        "updated_w_R95_fixedC_H0_interval_refit": [
            common_shifts["delta_+0.087"]["R95_updated_weights_fixed_C"]["H0"],
            common_shifts["delta_-0.087"]["R95_updated_weights_fixed_C"]["H0"],
        ],
        "updated_w_R36_fixedC_H0_interval_refit": [
            common_shifts["delta_+0.087"]["R36_updated_weights_fixed_C"]["H0"],
            common_shifts["delta_-0.087"]["R36_updated_weights_fixed_C"]["H0"],
        ],
        "fixed_w_scaling_law_max_abs_err": max_scaling_err,
        "fixed_w_q_invariance_max_abs_err": max_q_invariance_err,
        "jacobian_common_mode_vs_analytic_max_abs_err": jac_common_scale_err,
        "frozen_design_J7_common_dipole_quad_norm": float(np.linalg.norm((B_r95 @ J7_ivw @ u_com)[1:9])),
        "source_jacobian_common_dipole_quad_norm": float(np.linalg.norm((B_r95 @ J_src_fixed_w @ u_com)[1:9])),
        "source_jacobian_ellipsoid_sensitivity_bounds": src_bounds,
        "J_source_fixed_w_36x7": J_src_fixed_w.tolist(),
        "J_source_updated_w_36x7": J_src_updated_w.tolist(),
    }


def compute() -> dict:
    t0 = time.perf_counter()
    src = cf4_p0b.load_cf4_method_source()
    H = r95._load_h03()
    inp = H.source(r95.SELECT)
    dist = H.proxy_distance(inp.mu)
    sig = H.working_sigma(dist, inp.e_mu)
    X = H.velocity_design(dist, inp.n)
    y_raw = H.C_KM_S * inp.z

    theta = np.empty(36, dtype=np.float64)
    A_list = []
    for j, zc in enumerate(H.CENTERS):
        fj = H.fit(X, y_raw, H.window(inp.z, sig, zc), influence=True)
        A_list.append(fj["A"])
        theta[j * 9 : (j + 1) * 9] = fj["theta"]
    A = np.vstack(A_list)
    Cnoise, _ = H.joint_covariance(A, sig)

    with np.load(R27_NPZ, allow_pickle=False) as f27:
        if not np.array_equal(f27["group_id"], inp.ids):
            raise RuntimeError("R27 group_id mismatch")
        S7 = np.asarray(f27["selected_support_7"], dtype=np.float64)
        channels7 = [str(x) for x in f27["channel_names"].tolist()]
    with np.load(R36_NPZ, allow_pickle=False) as f36:
        PVall = np.asarray(f36["pv_total"], dtype=np.float64)
        C_r36 = np.asarray(f36["conditional_R5"], dtype=np.float64)
        theta_r36 = np.asarray(f36["theta"], dtype=np.float64)
        K4 = np.asarray(f36["method_K"], dtype=np.float64)
        Sigma4 = np.asarray(f36["method_Sigma"], dtype=np.float64)

    # Verify R36 K4 formula exactly
    K4_rebuilt = A @ (dist[:, None] * np.column_stack([(inp.method == fm).astype(float) for fm in ("FP", "OTHER", "SN", "TF")]))
    k4_formula_err = float(np.max(np.abs(K4 - K4_rebuilt)))
    if k4_formula_err > 1e-13:
        raise RuntimeError(f"R36 K4 identity drift: {k4_formula_err}")

    dcz_dmu = DCZ_DMU_FACTOR * dist
    J7 = A @ (S7 * dcz_dmu[:, None])

    # 1. Table3 complete genealogy & Table2 cross-check
    t3_full = _parse_complete_table3_for_selected(inp.ids)
    t2_gen = _parse_table2_genealogy(inp.ids, t3_full)

    # Compare count-flagged (cf4_p0b) vs numeric-DM table3 vs R27 S7
    dm_p_ord = t3_full["dm_present_7"][:, [1, 2, 3, 4, 5, 6, 0]]
    cnt_p_ord = t3_full["count_present_7"][:, [1, 2, 3, 4, 5, 6, 0]]
    diff_dm_vs_s7 = {channels7[j]: int(np.sum(dm_p_ord[:, j] != (S7[:, j] > 0.5))) for j in range(7)}
    diff_cnt_vs_s7 = {channels7[j]: int(np.sum(cnt_p_ord[:, j] != (S7[:, j] > 0.5))) for j in range(7)}

    # Overlap Fisher & internal covariance on COMPLETE 6 numeric velocity methods
    fit_p0b = cf4_p0b.profile_method_offsets(src.method_modulus, src.method_sigma)
    fit_complete = cf4_p0b.profile_method_offsets(t3_full["dm_vals_6"], t3_full["e_vals_6"])

    # Verify table3 DMav reconstruction using delta_6 on all DMav > 0 groups
    delta6 = fit_complete["delta_mag"]
    w6 = np.where(np.isfinite(t3_full["e_vals_6"]), t3_full["e_vals_6"] ** -2, 0.0)
    y6_shifted = np.where(np.isfinite(t3_full["dm_vals_6"]), t3_full["dm_vals_6"] - delta6[None, :], 0.0)
    wtot = w6.sum(axis=1)
    has_av = t3_full["dmav"] > 0.0
    dmav_rebuilt = np.divide((w6 * y6_shifted).sum(axis=1), wtot, out=np.zeros(len(inp.ids)), where=wtot > 0)
    dmav_diff = dmav_rebuilt[has_av] - t3_full["dmav"][has_av]

    # Build exact inverse-variance group-weighted 7-channel Jacobian W7 (row sums == 1.0 on all 35,970 groups!)
    # Avoids double/multi-counting uniform common zero-point shifts on the 944 multi-method overlap groups.
    W7 = np.zeros_like(S7)
    w_row_norm = np.divide(w6, wtot[:, None], out=np.zeros_like(w6), where=wtot[:, None] > 0)
    W7[:, :6] = w_row_norm
    W7[~has_av, 6] = 1.0  # DirectCal-only groups {20679, 59927} carry unit weight in channel 6
    if not np.allclose(W7.sum(axis=1), 1.0, atol=1e-12):
        raise RuntimeError("Inverse-variance 7-channel partition-of-unity failed")
    J7_ivw = A @ (W7 * dcz_dmu[:, None])

    # Build 7x7 empirical overlap covariance Sigma_overlap (rank 5) + unidentifiable common scale u0
    # In SNIA=0 gauge, cov6[1:,1:] has 5 methods (FP, TFR, SBFm, SBFir, SNII);
    # Embed into 7-channel ordering [SNIa(0), FP(1), TFR(2), SBFm(3), SBFir(4), SNII(5), DirectCal(6)]
    Sigma7_overlap = np.zeros((7, 7), dtype=np.float64)
    Sigma7_overlap[1:6, 1:6] = fit_complete["cov_working_mag2"][1:6, 1:6]
    u_common = np.ones(7, dtype=np.float64)

    # 2. Subspace reconciliation K4 vs J7 (report both binary S7 and IVW W7)
    sub_bin = _reconcile_subspaces(K4, Sigma4, J7, PVall[:36, :36] + Cnoise)
    sub_ivw = _reconcile_subspaces(K4, Sigma4, J7_ivw, PVall[:36, :36] + Cnoise)
    subspace_rec = dict(sub_bin)
    subspace_rec["binary_S7"] = sub_bin
    subspace_rec["ivw_W7"] = sub_ivw
    subspace_rec["interpretation_note"] = "High whitened trace inclusion measures subspace overlap only and does not equate covariance models or recover a physical calibration posterior."

    # 3. Sharp partial-identification bounds under frozen-design linear residual approximation
    D = np.tile(np.eye(9, dtype=np.float64), (4, 1))
    from scipy.stats import chi2 as sp_chi2
    chi2_6_95 = float(sp_chi2.ppf(0.95, df=6))
    chi2_7_95 = float(sp_chi2.ppf(0.95, df=7))
    chi2_1_95 = float(sp_chi2.ppf(0.95, df=1))

    bounds_grid = {}
    C_pv5_noise = PVall[:36, :36] + Cnoise
    for label, sig_com in (("overlap_only_plus_0p02cal", 0.02),
                           ("overlap_plus_0p05cal", 0.05),
                           ("overlap_plus_0p087_tully23sys", 0.087)):
        Sig_pri = Sigma7_overlap + (sig_com ** 2) * np.outer(u_common, u_common) + 1e-8 * np.eye(7)
        b_1s = _sharp_partial_id_bounds(C_pv5_noise, J7_ivw, Sig_pri, D, theta, 1.0)
        b_1s["regime"] = "frozen_design_velocity_residual_approx"
        b_1s["radius_definition"] = "mahalanobis_r1"
        b_95 = _sharp_partial_id_bounds(C_pv5_noise, J7_ivw, Sig_pri, D, theta, chi2_7_95)
        b_95["regime"] = "frozen_design_velocity_residual_approx"
        b_95["radius_definition"] = "chi2_df7_0p95_with_1e8_ridge"
        b_95["rank6_unregularized_chi2_df6_H0_halfwidth"] = _sharp_partial_id_bounds(
            C_pv5_noise, J7_ivw, Sig_pri, D, theta, chi2_6_95
        )["H0_partial_id_halfwidth"]
        bounds_grid[f"R95_R5_ivw_{label}_1sigma"] = b_1s
        bounds_grid[f"R95_R5_ivw_{label}_95pct_ellipsoid"] = b_95

    b_iso = _sharp_partial_id_bounds(C_pv5_noise, J7_ivw, (0.05 ** 2) * np.eye(7), D, theta, 1.0)
    b_iso["regime"] = "frozen_design_velocity_residual_approx"
    bounds_grid["R95_R5_ivw_isotropic_0p05_1sigma"] = b_iso

    b_bin = _sharp_partial_id_bounds(
        C_pv5_noise, J7, Sigma7_overlap + (0.087 ** 2) * np.outer(u_common, u_common) + 1e-8 * np.eye(7), D, theta, 1.0
    )
    b_bin["regime"] = "frozen_design_velocity_residual_approx"
    bounds_grid["R95_R5_binaryS7_overlap_plus_0p087_tully23sys_1sigma"] = b_bin

    # Family B: Inherited R36 conditional_R5 base with rank-1 common zero-point magnitude uncertainty (exact partition-of-unity J7_ivw)
    for label, sig_com in (("common_0p05mag_1sigma", 0.05), ("common_0p087_tully23sys_1sigma", 0.087)):
        Sig_com = (sig_com ** 2) * np.outer(u_common, u_common) + 1e-10 * np.eye(7)
        b_r36 = _sharp_partial_id_bounds(C_r36, J7_ivw, Sig_com, D, theta, 1.0)
        b_r36["regime"] = "frozen_design_velocity_residual_approx"
        b_r36["radius_definition"] = "mahalanobis_r1"
        bounds_grid[f"R36_inherited_ivw_{label}"] = b_r36
    b_r36_95 = _sharp_partial_id_bounds(
        C_r36, J7_ivw, (0.087 ** 2) * np.outer(u_common, u_common) + 1e-10 * np.eye(7), D, theta, chi2_1_95
    )
    b_r36_95["regime"] = "frozen_design_velocity_residual_approx"
    bounds_grid["R36_inherited_ivw_common_0p087_95pct_1d"] = b_r36_95

    # 3b. DirectCal / nuisance dimension 5/6/7 audit
    F7_zero = np.zeros((7, 7), dtype=np.float64)
    F7_zero[:6, :6] = fit_complete["F"]
    Sig_087_unreg = Sigma7_overlap + (0.087 ** 2) * np.outer(u_common, u_common)
    Sig_087_reg = Sig_087_unreg + 1e-8 * np.eye(7)
    v_sn_minus_cal = np.zeros(7, dtype=np.float64)
    v_sn_minus_cal[0] = 1.0
    v_sn_minus_cal[6] = -1.0
    r95_087_1s = bounds_grid["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]
    r95_087_95 = bounds_grid["R95_R5_ivw_overlap_plus_0p087_tully23sys_95pct_ellipsoid"]
    nuisance_audit = {
        "rank_F_overlap_7x7": int(np.linalg.matrix_rank(F7_zero)),
        "rank_Sigma7_overlap": int(np.linalg.matrix_rank(Sigma7_overlap)),
        "rank_Sigma7_plus_common0087_unregularized": int(np.linalg.matrix_rank(Sig_087_unreg)),
        "rank_Sigma7_plus_common0087_with_ridge_1e8": int(np.linalg.matrix_rank(Sig_087_reg)),
        "unestimated_contrast_vector": "e_SNIa - e_DirectCal",
        "unregularized_contrast_variance": float(v_sn_minus_cal @ Sig_087_unreg @ v_sn_minus_cal),
        "ridge_1e8_induced_contrast_sd_mag": float(math.sqrt(max(0.0, float(v_sn_minus_cal @ Sig_087_reg @ v_sn_minus_cal)))),
        "R95_0p087_95pct_H0_halfwidth_rank6_chi2": float(r95_087_1s["H0_partial_id_halfwidth"] * math.sqrt(chi2_6_95)),
        "R95_0p087_95pct_H0_halfwidth_rank7_chi2": float(r95_087_95["H0_partial_id_halfwidth"]),
        "R36_0p087_95pct_H0_halfwidth_rank6_chi2": float(bounds_grid["R36_inherited_ivw_common_0p087_tully23sys_1sigma"]["H0_partial_id_halfwidth"] * math.sqrt(chi2_6_95)),
        "R36_0p087_95pct_H0_halfwidth_rank7_chi2": float(bounds_grid["R36_inherited_ivw_common_0p087_tully23sys_1sigma"]["H0_partial_id_halfwidth"] * math.sqrt(chi2_7_95)),
        "directcal_sensitivity_note": (
            "The 6-method velocity overlap table leaves SNIa - DirectCal unconstrained (zero unregularized contrast variance; "
            "the ~1.414e-4 mag contrast SD arises purely from the 1e-8*I_7 numerical stabilization ridge, NOT data constraints on groups {20679, 59927}). "
            "Likewise, 0.087 mag is a sensitivity scale (~3 km/s/Mpc systematic scale in Tully+23, where 0.087 mag also appears as TRGB-CPLR RMS), not a 7-channel Gaussian posterior."
        ),
    }

    # 3c. Actual physical source-modulus perturbation (d -> 10^(delta/5)*d, X -> 10^(delta/5)*X) vs frozen-design approx
    weights_base = [H.window(inp.z, sig, zc) for zc in H.CENTERS]
    source_pert = _evaluate_source_modulus_perturbation(
        H, inp, dist, sig, X, y_raw, weights_base, theta, W7, J7_ivw, C_pv5_noise, PVall[:36, :36], C_r36, Sig_087_reg, D, chi2_7_95
    )

    # 4. Disjoint radial & sky partitions
    partitions = _evaluate_disjoint_partitions(H, inp, dist, sig, X, y_raw, theta, PVall[:36, :36], C_r36, J7, S7)

    out = {
        "schema": "htt.r97.cf4_genealogy_subspace_and_partial_id/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "sources_sha256": {
            "selected_35970": _sha(r95.SELECT),
            "table3_dat": _sha(RAW_CF4 / "table3.dat"),
            "table4_dat": _sha(RAW_CF4 / "table4.dat"),
            "ReadMe": _sha(RAW_CF4 / "ReadMe"),
            "r36_matrices_npz": _sha(R36_NPZ),
            "r27_factor_npz": _sha(R27_NPZ),
        },
        "r36_K4_exact_formula_max_abs_diff": k4_formula_err,
        "r36_theta_parity_max_abs_diff": float(np.max(np.abs(theta - theta_r36))),
        "cf4_genealogy": {
            "N_selected_groups": int(len(inp.ids)),
            "count_flag_vs_R27_S7_mismatches": diff_cnt_vs_s7,
            "numeric_DM_vs_R27_S7_mismatches": diff_dm_vs_s7,
            "DirectCal_definition_split_note": "9 of 11 table3 CAL-bearing groups also have velocity indicators so R27 sets DirectCal=1 only on the 2 pure-calibrator groups (DMav==0: {20679, 59927}).",
            "p0b_usable_multimethod_groups": int(fit_p0b["n_distinct_supported_groups"]),
            "complete_numeric_multimethod_groups": int(fit_complete["n_distinct_supported_groups"]),
            "complete_delta_SNIa_gauge_mag": fit_complete["delta_mag"].tolist(),
            "complete_overlap_sigma_mag": [None if not np.isfinite(x) else float(x) for x in np.sqrt(np.diag(fit_complete["cov_working_mag2"]))],
            "table3_DMav_reconstruction_median_abs_diff_mag": float(np.median(np.abs(dmav_diff))),
            "table3_DMav_reconstruction_p95_abs_diff_mag": float(np.quantile(np.abs(dmav_diff), 0.95)),
            "table3_DMzp_minus_DMav_min_max": [t3_full["dmzp_minus_dmav_min"], t3_full["dmzp_minus_dmav_max"]],
            "n_CAL_only_groups_with_DMav_zero": t3_full["n_dmav_zero"],
            "CAL_only_group_ids": t3_full["dmav_zero_group_ids"],
            "table2_comparison": t2_gen,
        },
        "subspace_reconciliation_K4_vs_J7": subspace_rec,
        "nuisance_dimension_and_directcal_audit": nuisance_audit,
        "sharp_partial_identification_bounds": bounds_grid,
        "source_modulus_perturbation": source_pert,
        "disjoint_partition_consistency": partitions,
        "physics_gates": {
            "sq_cf4_status": "BLOCKED_INPUT",
            "publication_ready": False,
            "full_S_PV_and_calibration": None,
            "independent_raw_zeropoint_posterior": False,
            "exact_blocker": "Published CF4 table2/table3 are post-MCMC registered with unquantified ~0.087 mag (~3 km/s/Mpc) systematic global tie and missing C_selection + full nonlinear S_PV.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    return out


if __name__ == "__main__":
    res = compute()
    print(json.dumps({
        "k4_err": res["r36_K4_exact_formula_max_abs_diff"],
        "numeric_S7_diff": res["cf4_genealogy"]["numeric_DM_vs_R27_S7_mismatches"],
        "dmzp_minus_dmav": res["cf4_genealogy"]["table3_DMzp_minus_DMav_min_max"],
        "subspace_frac_in_J7": res["subspace_reconciliation_K4_vs_J7"]["fraction_whitened_variance_inside_col_J7"],
        "bound_R95_ivw_0087_1s": res["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]["H0_partial_id_interval"],
        "bound_R36_ivw_0087_1s": res["sharp_partial_identification_bounds"]["R36_inherited_ivw_common_0p087_tully23sys_1sigma"]["H0_partial_id_interval"],
        "schur_red_chi2_R36_vs_R95": [
            res["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]["C_R36_inherited"]["outer_2w_pred_reduced_chi2"],
            res["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]["C_R95_R5_cal005"]["outer_2w_pred_reduced_chi2"],
        ],
        "elapsed_s": res["elapsed_seconds"],
    }))
