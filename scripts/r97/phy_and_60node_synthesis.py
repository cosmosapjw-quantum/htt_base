"""R97 Unit D (P1, P4, P6, PHY-01..07 & 60-Node R97 Master Ledger).

Integrates new R97 outputs (Units A, B, C) with R95/R91/R89 P1/P4/P6 source-conditioned products:
  - P1: couples 2,048 4-window draws with R97 CF4 partial-ID quadrupole calibration bounds
    while strictly enforcing physical_Pi = None and physical_GF = None.
  - P4: synthesizes 5-survey Ellis-Baldwin dipole/quadrupole/clustering ladder across NVSS,
    RACS-DR1, SPICE-RACS, SUMSS, LoTSS (preserving joint_five_survey_covariance_qualified = False).
  - P6: projects R97 non-axisymmetric coupled-m Bianchi L=2 shear/curl templates onto
    Quaia 10x10 jackknife (E2, B2) VSH covariance vs Gaia ecliptic scanning-law quadrupole
    (preserving actual_normal_vorticity = None and k04..k06 = BLOCKED_DEPENDENCY).
  - PHY-01..07 & 60-Node R97 Master Ledger: preserves immutable R78 INTEGRATED_DAG.json
    (SHA256 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11, 60 nodes, 129 edges,
    NEXT_ID = SQ-CF4) and separates code/conditional execution from publication approval.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
import sys

import numpy as np
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from htt.obsstat import p1_fast
from scripts.r95 import gaia_p6_analysis as r95_gaia
from scripts.r97 import cf4_genealogy_and_partial_id as r97_cf4

R78_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R94_MAP = ROOT / "docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/R94_PROGRAM_EXECUTION_MAP.json"
R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
R97_DIR = ROOT / "docs/research_program/observational_publication_20261015/R97_SCIENCE_EXECUTION_20261122"
P1_NPZ = ROOT / "docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results/paired_functional_arrays.npz"
R91_QUAIA = ROOT / "docs/research_program/observational_publication_20261015/R91_SOLVERFREE_SECOND_CYCLE_20261121/GAIA_QUAIA_FULL_SELECTION.json"
EXPECTED_R78_SHA = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _load_r97_and_r95_inputs() -> tuple[dict, dict]:
    req = {
        "R97_A": R97_DIR / "CF4_GENEALOGY_AND_PARTIAL_ID.json",
        "R97_B": R97_DIR / "CMB_INJECTION_AND_EB_LEAKAGE.json",
        "R97_C": R97_DIR / "BIANCHI_COUPLED_M_TRANSPORT.json",
        "R95_G03": R95_DIR / "G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json",
        "R95_G04": R95_DIR / "G04_RADIO_P4_KINEMATIC_VS_SELECTION.json",
        "R95_G06": R95_DIR / "G06_P1_FIVE_VIEW_TYPED_LEDGER.json",
        "R95_G07_BG": R95_DIR / "G07_BIANCHI_BACKGROUND_AUDIT.json",
        "R95_G07_OPT": R95_DIR / "G07_BIANCHI_REC_REI_OPTICS.json",
        "R95_G08": R95_DIR / "G08_CROSS_PHY_01_TO_07.json",
    }
    missing = [k for k, p in req.items() if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required upstream inputs for R97 Unit D: {missing}")
    return {k: json.loads(p.read_text()) for k, p in req.items()}, {k: _sha(p) for k, p in req.items()}


def _p6_quaia_bianchi_alignment(d: dict) -> dict:
    """Compare R95 Quaia E2/B2 & scanning-law quadrupole vs R95 geodesic templates and summarize R97 L=60 coupled-m E/B transport."""
    quaia = json.loads(R91_QUAIA.read_text())
    inv = quaia["fits"]["inverse_noise"]
    beta16 = np.array(inv["coefs_microasyr"], dtype=np.float64)
    C10 = np.array(inv["jackknife_E2_B2_cov"], dtype=np.float64)
    e2b2_obs = beta16[6:16]
    e2_obs = beta16[6:11]
    b2_obs = beta16[11:16]
    scan_q = np.array(d["R95_G03"]["scanning_law_quadrupole_frame_check"]["vec_icrs"], dtype=np.float64)

    # Rotate scanning law to Galactic and evaluate alignment with canonical-triad R95 geodesic STF5 quadrupoles
    fiveview = r95_gaia._load_mod("r97_fiveview_geom", r95_gaia.FIVEVIEW_PY)
    R_gal = r95_gaia._build_icrs_to_frame_rotation("galactic")
    _, M5_gal = r95_gaia._build_j16(R_gal, fiveview.E)
    e2_gal = M5_gal @ e2_obs
    scan_gal = M5_gal @ scan_q

    # Test canonical-triad R95_G07_BG geodesic Q2_stf5 templates (with B2=0 exploratory E2-only axis projection)
    traj_cmp = {}
    for key in ("VI_-1/9_exception__tilted", "VII_h__tilted", "IX__tilted"):
        q_tmpl = np.array(d["R95_G07_BG"]["trajectories"][key]["geodesic_cosmo_Q2_stf5"], dtype=np.float64)
        q_tmpl_n = q_tmpl / max(np.linalg.norm(q_tmpl), 1e-30)
        q_icrs_unit = M5_gal.T @ q_tmpl_n
        cos_e2 = float(np.dot(e2_obs, q_icrs_unit) / (np.linalg.norm(e2_obs) * np.linalg.norm(q_icrs_unit)))
        cos_scan = float(np.dot(scan_q, q_icrs_unit) / (np.linalg.norm(scan_q) * np.linalg.norm(q_icrs_unit)))
        t10 = np.concatenate([q_icrs_unit, np.zeros(5, dtype=np.float64)])
        Cinv_t = np.linalg.solve(C10, t10)
        amp_hat = float((t10 @ np.linalg.solve(C10, e2b2_obs)) / (t10 @ Cinv_t))
        chi2_obs = float(e2b2_obs @ np.linalg.solve(C10, e2b2_obs))
        res = e2b2_obs - amp_hat * t10
        chi2_res = float(res @ np.linalg.solve(C10, res))
        traj_cmp[key] = {
            "cos_alignment_with_quaia_inv_E2": cos_e2,
            "cos_alignment_with_gaia_scanlaw_Q": cos_scan,
            "fitted_pure_E2_template_uasyr": amp_hat,
            "wald10_null": chi2_obs,
            "wald10_residual_after_1dof_fit": chi2_res,
            "delta_chi2_1dof": chi2_obs - chi2_res,
        }

    r97c = d["R97_C"]
    l60 = r97c["coupled_m5_by_L"]["60"]
    coupled_m_l60_summary = {
        fname: {
            "B_over_E_norm_ratio": float(l60[fname]["B_over_E_norm_ratio"]),
            "cross_m_coupling_fraction": float(l60[fname]["cross_m_coupling_fraction"]),
            "m_nonzero_over_total_T_power": float(l60[fname]["m_nonzero_over_total_T_power"]),
        }
        for fname in ("I_rotated", "V", "VI_-1/9", "VII_0", "VII_h", "IX")
    }

    return {
        "quaia_inv_E2_norm_uasyr": float(np.linalg.norm(e2_obs)),
        "quaia_inv_B2_norm_uasyr": float(np.linalg.norm(b2_obs)),
        "quaia_inv_E2_gal": e2_gal.tolist(),
        "scanlaw_gal": scan_gal.tolist(),
        "template_10x10_overlap": traj_cmp,
        "r97c_coupled_m_L60_cmb_summary": coupled_m_l60_summary,
        "frame_projection_note": "template_10x10_overlap projects canonical-triad R95_G07_BG scalar geodesic Q2_stf5 with B2=0 into ICRS via M5_gal.T as an exploratory canonical-axis alignment check, alongside R97 Unit C coupled-m L=60 CMB E/B summary metrics.",
        "actual_normal_vorticity": None,
        "k04_k05_k06_status": "BLOCKED_DEPENDENCY",
    }


def _p1_cf4_coupling_summary(d: dict) -> dict:
    """Propagate shared 7-channel CF4 nuisance across all 4 windows' signed 9-vectors on P1's 2,048 draws.

    Replaces uniform additive q-width sensitivity with exact signed 9-vector propagation q = ||Q||_2 / H:
      1. Preserves & asserts the F4 finite interior counterexample (1972/2048 > 1971/2048 at w=2).
      2. Establishes guaranteed conservative triangle-inequality outer bounds on numerator and denominator.
      3. Computes per-draw sharp min/max fractional-programming bounds over the 95% (and 1-sigma) ellipsoid
         with an analytical global optimality certificate, plus best common-nuisance witness bounds.
      4. Verifies exact physical distance-scaling invariance under uniform d -> 10^(-delta/5)*d (fixed weights).
    """
    with np.load(P1_NPZ, allow_pickle=False) as z:
        draws = np.asarray(z["draws"], dtype=np.float64)
        q_app = np.asarray(z["q_app"], dtype=np.float64)
        w = np.asarray(z["weights"], dtype=np.float64)
    ratio_parity_err = float(np.max(np.abs(q_app - np.linalg.norm(draws[:, :, 4:9], axis=2) / draws[:, :, 0])))
    if ratio_parity_err > 1e-14:
        raise RuntimeError(f"P1 draws vs q_app ratio parity error: {ratio_parity_err}")

    thr = np.array([0.03, 0.05])
    res_nom = p1_fast.joint_tail_bounds(q_app, w, thr)
    if res_nom["physical_Pi"] is not None:
        raise RuntimeError("P1 physical_Pi guard violated")

    # Reconstruct 36x7 IVW Jacobian J7_ivw and 7x7 C7 covariance matching CF4 Unit A
    H = r97_cf4.r95._load_h03()
    inp = H.source(r97_cf4.r95.SELECT)
    dist = H.proxy_distance(inp.mu)
    sig = H.working_sigma(dist, inp.e_mu)
    X = H.velocity_design(dist, inp.n)
    y_raw = H.C_KM_S * inp.z
    A = np.vstack([H.fit(X, y_raw, H.window(inp.z, sig, zc), influence=True)["A"] for zc in H.CENTERS])
    t3 = r97_cf4._parse_complete_table3_for_selected(inp.ids)
    F_ov = r97_cf4.cf4_p0b.profile_method_offsets(t3["dm_vals_6"], t3["e_vals_6"])
    e6 = t3["e_vals_6"]
    w6 = np.where(np.isfinite(e6), e6 ** -2, 0.0)
    wt = w6.sum(axis=1)
    W7 = np.zeros((len(inp.z), 7), dtype=np.float64)
    np.divide(w6, wt[:, None], where=wt[:, None] > 0, out=W7[:, :6])
    W7[wt == 0, 6] = 1.0
    J7_ivw = A @ (W7 * (r97_cf4.DCZ_DMU_FACTOR * dist[:, None]))
    T_frozen = J7_ivw.reshape(4, 9, 7)

    Sigma7_overlap = np.zeros((7, 7), dtype=np.float64)
    Sigma7_overlap[1:6, 1:6] = F_ov["cov_working_mag2"][1:6, 1:6]
    C7 = Sigma7_overlap + (0.087 ** 2) * np.ones((7, 7), dtype=np.float64) + 1e-8 * np.eye(7, dtype=np.float64)
    r2_7_95 = float(chi2.ppf(0.95, 7))
    r2_6_95 = float(chi2.ppf(0.95, 6))

    # Preserved uniform-width sensitivity comparison from original R97
    bnd_r95_1s = d["R97_A"]["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]
    bnd_r95_95 = d["R97_A"]["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_95pct_ellipsoid"]
    bnd_r36 = d["R97_A"]["sharp_partial_identification_bounds"]["R36_inherited_ivw_common_0p087_tully23sys_1sigma"]
    q_frac_shift_r95_1s = float(bnd_r95_1s["quad_max_ellipsoid_shift"] / bnd_r95_1s["H0_point"])
    q_frac_shift_r95_95 = float(bnd_r95_95["quad_max_ellipsoid_shift"] / bnd_r95_95["H0_point"])
    q_frac_shift_r36 = float(bnd_r36["quad_max_ellipsoid_shift"] / bnd_r36["H0_point"])
    w_mean_q = [float(np.dot(w, q_app[:, j])) for j in range(4)]

    # 1. Preserved F4 interior counterexample regression check (must give 1972/2048 > 1971/2048 at w=2)
    delta_ce = np.array([
        0.315481238721, 0.301087828206, 0.304561550799, 0.305795937348,
        0.308176649253, 0.321630403743, 0.315480198825,
    ], dtype=np.float64)
    mahal2_ce = float(delta_ce @ np.linalg.solve(C7, delta_ce))
    if not mahal2_ce < r2_7_95:
        raise RuntimeError(f"F4 counterexample fell outside ellipsoid: {mahal2_ce} >= {r2_7_95}")
    x_ce = draws + np.einsum("wij,j->wi", T_frozen, delta_ce)[None, :, :]
    q_ce = np.linalg.norm(x_ce[:, :, 4:9], axis=2) / x_ce[:, :, 0]
    ce_w3_count = int(np.count_nonzero(q_ce[:, 2] > 0.05))
    old_unif_w3_count = int(np.count_nonzero(q_app[:, 2] + q_frac_shift_r95_95 > 0.05))
    min_pos_margin_ce = float(np.min((q_ce[:, 2] - 0.05)[q_ce[:, 2] > 0.05]))
    if ce_w3_count != 1972 or old_unif_w3_count != 1971:
        raise RuntimeError(f"F4 counterexample count mismatch: ce={ce_w3_count}, old_unif={old_unif_w3_count}")
    res_ce = p1_fast.joint_tail_bounds(q_ce, w, thr)

    # Helper to compute BOTH guaranteed triangle-inequality outer bounds AND certified sharp per-draw bounds
    evals_c, evecs_c = np.linalg.eigh(0.5 * (C7 + C7.T))
    L7 = evecs_c * np.sqrt(np.maximum(evals_c, 0.0))[None, :]

    def _trs_quadratic_extremum(P: np.ndarray, B: np.ndarray, C_const: np.ndarray, maximize: bool) -> tuple[np.ndarray, np.ndarray]:
        """Exact global max or min of u^T P u + 2 b^T u + c over ||u||_2 <= 1 via the S-lemma dual.

        Strong duality holds unconditionally (Slater condition at u=0):
          max_{||u||<=1} (u^T P u + 2 b^T u + c) = inf_{lam > max(0, lam_max(P))} [ c + lam + sum_k b_k^2 / (lam - e_k) ].
        Minimizing M(u) is identical to maximizing (-M)(u) and negating the result.
        Returns (exact_extremum_values, primal_feasible_u_witnesses).
        """
        P_s = P if maximize else -P
        B_s = B if maximize else -B
        C_s = C_const if maximize else -C_const
        eig_p, V_p = np.linalg.eigh(0.5 * (P_s + P_s.T))
        lam0 = max(0.0, float(eig_p[-1]))
        B_rot = B_s @ V_p
        B2 = B_rot * B_rot
        top_mask = eig_p >= lam0 - 1e-12
        sub_mask = ~top_mask
        n_d = len(C_s)

        lo = np.full(n_d, lam0 + 1e-12, dtype=np.float64)
        hi = lam0 + np.maximum(1.0, np.linalg.norm(B_s, axis=1)) + 16.0
        for _ in range(40):
            s_hi = np.sum(B2 / (hi[:, None] - eig_p[None, :]) ** 2, axis=1)
            need = s_hi > 1.0
            if not np.any(need):
                break
            hi[need] = lam0 + 2.0 * (hi[need] - lam0)
        for _ in range(72):
            mid = 0.5 * (lo + hi)
            s_mid = np.sum(B2 / (mid[:, None] - eig_p[None, :]) ** 2, axis=1)
            mask = s_mid > 1.0
            lo[mask] = mid[mask]
            hi[~mask] = mid[~mask]
        vals = C_s + hi + np.sum(B2 / (hi[:, None] - eig_p[None, :]), axis=1)
        u_rot = B_rot / (hi[:, None] - eig_p[None, :])

        if lam0 > 0.0 and np.any(top_mask):
            zero_top = np.sum(B2[:, top_mask], axis=1) < 1e-24
            deg_norm = np.sum(B2[:, sub_mask] / np.maximum(lam0 - eig_p[None, sub_mask], 1e-30) ** 2, axis=1) if np.any(sub_mask) else np.zeros(n_d)
            hard = zero_top & (deg_norm <= 1.0)
            if np.any(hard):
                lam_h = lam0 + 1e-13
                vals[hard] = C_s[hard] + lam_h + np.sum(B2[hard][:, sub_mask] / (lam_h - eig_p[None, sub_mask]), axis=1)
                u_rot[hard] = 0.0
                if np.any(sub_mask):
                    u_rot[np.ix_(hard, sub_mask)] = B_rot[np.ix_(hard, sub_mask)] / (lam_h - eig_p[None, sub_mask])
                u_rot[hard, -1] = np.sqrt(np.maximum(0.0, 1.0 - deg_norm[hard]))

        u_opt = u_rot @ V_p.T
        u_norm = np.linalg.norm(u_opt, axis=1, keepdims=True)
        u_opt = np.where(u_norm > 1.0, u_opt / np.maximum(u_norm, 1e-30), u_opt)
        return (vals if maximize else -vals), u_opt

    def _compute_ellipsoid_bounds(T_resp: np.ndarray, r2_val: float, tag: str) -> dict:
        rad = math.sqrt(float(r2_val))
        Q_norm = np.linalg.norm(draws[:, :, 4:9], axis=2)
        H_vals = draws[:, :, 0]

        bH = np.array([rad * math.sqrt(max(0.0, float(T_resp[j, 0, :] @ C7 @ T_resp[j, 0, :]))) for j in range(4)])
        bQ = np.array([rad * math.sqrt(max(0.0, float(np.linalg.eigvalsh(T_resp[j, 4:9, :] @ C7 @ T_resp[j, 4:9, :].T)[-1]))) for j in range(4)])
        if np.any(H_vals <= bH[None, :]):
            raise RuntimeError(f"Denominator H <= bH encountered in outer bound for {tag}")

        q_out_lo = np.maximum(0.0, Q_norm - bQ[None, :]) / (H_vals + bH[None, :])
        q_out_hi = (Q_norm + bQ[None, :]) / (H_vals - bH[None, :])
        r_out_lo = p1_fast.joint_tail_bounds(q_out_lo, w, thr)
        r_out_hi = p1_fast.joint_tail_bounds(q_out_hi, w, thr)

        q_sh_lo = np.zeros_like(q_app)
        q_sh_hi = np.zeros_like(q_app)
        cw_lo_tails = []
        cw_hi_tails = []
        cw_lo_counts = []
        cw_hi_counts = []
        trs_max_disagree = 0
        trs_min_disagree = 0
        trs_min_abs_margin = float("inf")
        min_amb_curv_gap = float("inf")

        for j in range(4):
            Aw = rad * (T_resp[j, 4:9, :] @ L7)  # (5, 7)
            aw = rad * (L7.T @ T_resp[j, 0, :])  # (7,)
            Qj = draws[:, j, 4:9]
            Hj = draws[:, j, 0]

            # Solve exact ratio max via fixed-point iteration
            v = Qj / np.linalg.norm(Qj, axis=1, keepdims=True)
            q_cur = q_app[:, j].copy()
            for _ in range(35):
                g = (v @ Aw) - q_cur[:, None] * aw[None, :]
                g_n = np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-30)
                u_hi = g / g_n
                Qu = Qj + u_hi @ Aw.T
                Hu = Hj + u_hi @ aw
                q_cur = np.linalg.norm(Qu, axis=1) / Hu
                v = Qu / np.linalg.norm(Qu, axis=1, keepdims=True)
            q_sh_hi[:, j] = q_cur

            # Ambiguity-filtered primal curvature check for f_i(u) = ||Q + Aw u|| - 0.05*(H + aw^T u)
            v_f = Qj / np.linalg.norm(Qj, axis=1, keepdims=True)
            for _ in range(30):
                g_f = (v_f @ Aw) - 0.05 * aw[None, :]
                gn_f = np.maximum(np.linalg.norm(g_f, axis=1, keepdims=True), 1e-30)
                u_f = g_f / gn_f
                Xf = Qj + u_f @ Aw.T
                v_f = Xf / np.linalg.norm(Xf, axis=1, keepdims=True)
            s_perp = np.empty(len(Qj), dtype=np.float64)
            for i_d in range(len(Qj)):
                P_perp = np.eye(5) - np.outer(v_f[i_d], v_f[i_d])
                s_perp[i_d] = float(np.linalg.svd(P_perp @ Aw, compute_uv=False)[0])
            min_proj = np.linalg.norm(Qj, axis=1) - float(np.linalg.norm(Aw, ord=2))
            kappa = np.where(min_proj > 0.0, (s_perp ** 2) / np.maximum(min_proj, 1e-12), float("inf"))
            amb_hi = (q_out_lo[:, j] <= 0.05) & (q_out_hi[:, j] >= 0.05)
            if np.any(amb_hi):
                min_amb_curv_gap = min(min_amb_curv_gap, float(np.min(gn_f[amb_hi, 0] - kappa[amb_hi])))

            # Per-draw min over ||u|| <= 1
            v_l = Qj / np.linalg.norm(Qj, axis=1, keepdims=True)
            q_l = q_app[:, j].copy()
            for _ in range(35):
                gl = -(v_l @ Aw) + q_l[:, None] * aw[None, :]
                gl_n = np.maximum(np.linalg.norm(gl, axis=1, keepdims=True), 1e-30)
                u_lo = gl / gl_n
                Qu_l = Qj + u_lo @ Aw.T
                Hu_l = Hj + u_lo @ aw
                q_l = np.linalg.norm(Qu_l, axis=1) / Hu_l
                v_l = Qu_l / np.linalg.norm(Qu_l, axis=1, keepdims=True)
            q_sh_lo[:, j] = q_l

            # Unconditional exact S-lemma / TRS global optimality certificate + exact primal witness refinement
            P_q = Aw.T @ Aw - (0.05 ** 2) * np.outer(aw, aw)
            B_q = (Qj @ Aw) - (0.05 ** 2) * Hj[:, None] * aw[None, :]
            C_q = np.sum(Qj ** 2, axis=1) - (0.05 ** 2) * (Hj ** 2)
            trs_hi, u_trs_hi = _trs_quadratic_extremum(P_q, B_q, C_q, maximize=True)
            trs_lo, u_trs_lo = _trs_quadratic_extremum(P_q, B_q, C_q, maximize=False)
            q_trs_hi = np.linalg.norm(Qj + u_trs_hi @ Aw.T, axis=1) / (Hj + u_trs_hi @ aw)
            q_trs_lo = np.linalg.norm(Qj + u_trs_lo @ Aw.T, axis=1) / (Hj + u_trs_lo @ aw)
            better_hi = q_trs_hi > q_sh_hi[:, j]
            if np.any(better_hi):
                q_sh_hi[better_hi, j] = q_trs_hi[better_hi]
                u_hi[better_hi] = u_trs_hi[better_hi]
            better_lo = q_trs_lo < q_sh_lo[:, j]
            if np.any(better_lo):
                q_sh_lo[better_lo, j] = q_trs_lo[better_lo]
                u_lo[better_lo] = u_trs_lo[better_lo]
            trs_max_disagree += int(np.sum((q_sh_hi[:, j] > 0.05) != (trs_hi > 0.0)))
            trs_min_disagree += int(np.sum((q_sh_lo[:, j] > 0.05) != (trs_lo > 0.0)))
            trs_min_abs_margin = min(trs_min_abs_margin, float(np.min(np.abs(trs_hi))), float(np.min(np.abs(trs_lo))))

            # Common-nuisance witness across all candidate extreme directions
            u_cand_hi = np.vstack([u_hi, u_f, u_trs_hi])
            Q_c_hi = Qj[None, :, :] + np.einsum("cj,kj->ck", u_cand_hi, Aw)[:, None, :]
            H_c_hi = Hj[None, :] + (u_cand_hi @ aw)[:, None]
            q_c_hi = np.linalg.norm(Q_c_hi, axis=2) / H_c_hi
            cnt_hi = np.sum(q_c_hi > 0.05, axis=1)
            wt_hi = (q_c_hi > 0.05) @ w
            best_hi = int(np.argmax(wt_hi))
            cw_hi_counts.append(int(cnt_hi[best_hi]))
            cw_hi_tails.append(float(wt_hi[best_hi]))

            u_cand_lo = np.vstack([u_lo, u_trs_lo])
            Q_c_lo = Qj[None, :, :] + np.einsum("cj,kj->ck", u_cand_lo, Aw)[:, None, :]
            H_c_lo = Hj[None, :] + (u_cand_lo @ aw)[:, None]
            q_c_lo = np.linalg.norm(Q_c_lo, axis=2) / H_c_lo
            cnt_lo = np.sum(q_c_lo > 0.05, axis=1)
            wt_lo = (q_c_lo > 0.05) @ w
            best_lo = int(np.argmin(wt_lo))
            cw_lo_counts.append(int(cnt_lo[best_lo]))
            cw_lo_tails.append(float(wt_lo[best_lo]))

        if trs_max_disagree > 0 or trs_min_disagree > 0 or trs_min_abs_margin <= 0.0:
            raise RuntimeError(
                f"Per-draw S-lemma global optimality certificate failed for {tag}: "
                f"max_dis={trs_max_disagree}, min_dis={trs_min_disagree}, margin={trs_min_abs_margin}"
            )

        r_sh_lo = p1_fast.joint_tail_bounds(q_sh_lo, w, thr)
        r_sh_hi = p1_fast.joint_tail_bounds(q_sh_hi, w, thr)
        if any(r["physical_Pi"] is not None for r in (r_out_lo, r_out_hi, r_sh_lo, r_sh_hi)):
            raise RuntimeError("P1 physical_Pi guard violated")

        return {
            "bH_denominator_bound": bH.tolist(),
            "bQ_numerator_bound": bQ.tolist(),
            "lower_outer": r_out_lo["lower"][1, :4].tolist(),
            "upper_outer": r_out_hi["upper"][1, :4].tolist(),
            "outer_any_all_lower": r_out_lo["lower"][1, 4:6].tolist(),
            "outer_any_all_upper": r_out_hi["upper"][1, 4:6].tolist(),
            "per_draw_sharp_lower": r_sh_lo["lower"][1, :4].tolist(),
            "per_draw_sharp_upper": r_sh_hi["upper"][1, :4].tolist(),
            "per_draw_sharp_any_all_lower": r_sh_lo["lower"][1, 4:6].tolist(),
            "per_draw_sharp_any_all_upper": r_sh_hi["upper"][1, 4:6].tolist(),
            "per_draw_sharp_lower_counts": [int(np.sum(q_sh_lo[:, j] > 0.05)) for j in range(4)],
            "per_draw_sharp_upper_counts": [int(np.sum(q_sh_hi[:, j] > 0.05)) for j in range(4)],
            "common_witness_lower": cw_lo_tails,
            "common_witness_upper": cw_hi_tails,
            "common_witness_lower_counts": cw_lo_counts,
            "common_witness_upper_counts": cw_hi_counts,
            "trs_slemma_max_disagreements": int(trs_max_disagree),
            "trs_slemma_min_disagreements": int(trs_min_disagree),
            "trs_slemma_min_abs_margin": float(trs_min_abs_margin),
            "ambiguity_set_curvature_min_gap": (None if min_amb_curv_gap == float("inf") else float(min_amb_curv_gap)),
            "min_global_optimality_cert_gap": float(min_amb_curv_gap if min_amb_curv_gap > 0.0 and min_amb_curv_gap != float("inf") else trs_min_abs_margin),
        }

    b_frozen_95 = _compute_ellipsoid_bounds(T_frozen, r2_7_95, "frozen_rank7_95pct")
    b_frozen_rank6_95 = _compute_ellipsoid_bounds(T_frozen, r2_6_95, "frozen_rank6_95pct")
    b_frozen_1s = _compute_ellipsoid_bounds(T_frozen, 1.0, "frozen_1sigma_r1")
    J_src_fixed = np.array(d["R97_A"]["source_modulus_perturbation"]["J_source_fixed_w_36x7"], dtype=np.float64)
    T_src = J_src_fixed.reshape(4, 9, 7)
    b_source_95 = _compute_ellipsoid_bounds(T_src, r2_7_95, "source_fixed_w_95pct")

    # Physical uniform scale invariance check on P1 draws (draws -> 10^(-delta_0/5)*draws preserves q identically)
    q_inv_err = 0.0
    for delta_0 in (-0.087, 0.087):
        draws_s = (10.0 ** (-delta_0 / 5.0)) * draws
        q_s = np.linalg.norm(draws_s[:, :, 4:9], axis=2) / draws_s[:, :, 0]
        q_inv_err = max(q_inv_err, float(np.max(np.abs(q_s - q_app))))

    # Legacy uniform-width sensitivity comparison (for explicit baseline contrast)
    r_unif_lo_95 = p1_fast.joint_tail_bounds(np.maximum(0.0, q_app - q_frac_shift_r95_95), w, thr)
    r_unif_hi_95 = p1_fast.joint_tail_bounds(q_app + q_frac_shift_r95_95, w, thr)

    return {
        "N_coupled_draws": int(len(q_app)),
        "draws_q_ratio_parity_err": ratio_parity_err,
        "physical_uniform_scale_q_invariance_err": q_inv_err,
        "weighted_mean_q_app_4w": w_mean_q,
        "r97_CF4_1sigma_quad_fractional_sys_R95": q_frac_shift_r95_1s,
        "r97_CF4_95pct_quad_fractional_sys_R95": q_frac_shift_r95_95,
        "r97_CF4_1sigma_quad_fractional_sys_R36": q_frac_shift_r36,
        "tail_bounds_at_0p05_4w": {
            "lower": res_nom["lower"][1, :4].tolist(),
            "upper": res_nom["upper"][1, :4].tolist(),
        },
        "f4_counterexample_regression": {
            "delta_mag": delta_ce.tolist(),
            "mahalanobis2": mahal2_ce,
            "chi2_7_0p95_cutoff": r2_7_95,
            "window_index": 2,
            "actual_w3_count": ce_w3_count,
            "uniform_width_reported_w3_count": old_unif_w3_count,
            "actual_w3_weighted_tail": float(res_ce["lower"][1, 2]),
            "uniform_width_w3_weighted_tail": float(r_unif_hi_95["upper"][1, 2]),
            "min_positive_margin": min_pos_margin_ce,
        },
        "conservative_outer_tail_bounds_at_0p05_4w": {
            "lower_outer": b_frozen_95["lower_outer"],
            "upper_outer": b_frozen_95["upper_outer"],
            "bH_denominator_bound": b_frozen_95["bH_denominator_bound"],
            "bQ_numerator_bound": b_frozen_95["bQ_numerator_bound"],
            "outer_any_all_lower": b_frozen_95["outer_any_all_lower"],
            "outer_any_all_upper": b_frozen_95["outer_any_all_upper"],
            "1sigma_lower_outer": b_frozen_1s["lower_outer"],
            "1sigma_upper_outer": b_frozen_1s["upper_outer"],
        },
        "certified_sharp_tail_bounds_at_0p05_4w": b_frozen_95,
        "certified_sharp_tail_bounds_rank6_chi2_df6": b_frozen_rank6_95,
        "certified_sharp_tail_bounds_1sigma_r1": b_frozen_1s,
        "source_modulus_jacobian_bounds_95pct": b_source_95,
        "legacy_uniform_q_sensitivity_NOT_A_BOUND": {
            "lower_sens": r_unif_lo_95["lower"][1, :4].tolist(),
            "upper_sens": r_unif_hi_95["upper"][1, :4].tolist(),
            "warning": "Uniform additive ||delta_q5||/H0 width is NOT a valid bound over the 7D ellipsoid (violated by f4_counterexample_regression 1972 > 1971).",
        },
        "physical_Pi": None,
        "physical_GF": None,
    }


def _p4_radio_summary(d: dict) -> dict:
    """Summarize all 5 radio catalogs (NVSS, RACS-DR1, SPICE-RACS, SUMSS, LoTSS) and selection bounds."""
    g4 = d["R95_G04"]
    lad = g4["five_survey_ladder_analysis"]
    by_survey = {}
    for sname, sblk in lad.items():
        thrs = sblk["thresholds"]
        amps = [v["dipole_4p_amp"] for v in thrs.values()]
        ratios = [v["excess_ratio_d_obs_over_d_eb"] for v in thrs.values()]
        seps = [v["dipole_4p_sep_cmb_deg"] for v in thrs.values()]
        jks = [v["jackknife_over_poisson_ratio"] for v in thrs.values()]
        by_survey[sname] = {
            "n_thresholds": len(thrs),
            "dipole_amp_range": [float(min(amps)), float(max(amps))],
            "d_obs_over_d_eb_range": [float(min(ratios)), float(max(ratios))],
            "sep_cmb_deg_range": [float(min(seps)), float(max(seps))],
            "jk_over_poisson_range": [float(min(jks)), float(max(jks))],
        }
    return {
        "surveys": by_survey,
        "racs_rms_selection_bias_factor": g4["selection_and_flux_artifacts"]["racs_selection_bias_amp_inflation_factor"],
        "joint_five_survey_covariance_qualified": False,
        "physical_Pi": None,
        "physical_GF": None,
    }


def build_synthesis_and_ledger() -> dict:
    t0 = time.perf_counter()
    actual_r78_sha = _sha(R78_DAG)
    if actual_r78_sha != EXPECTED_R78_SHA:
        raise RuntimeError(f"R78 DAG SHA mismatch: {actual_r78_sha}")
    r78 = json.loads(R78_DAG.read_text())
    rmap = json.loads(R94_MAP.read_text())
    if len(r78["nodes"]) != 60 or len(r78["edges"]) != 129 or r78["next_action_id"] != "SQ-CF4":
        raise RuntimeError("R78 DAG invariants violated")

    d, shas = _load_r97_and_r95_inputs()
    p1_syn = _p1_cf4_coupling_summary(d)
    p4_syn = _p4_radio_summary(d)
    p6_syn = _p6_quaia_bianchi_alignment(d)

    # Synthesize PHY-01..PHY-07 integrating R97 Units A, B, C
    r97a, r97b, r97c = d["R97_A"], d["R97_B"], d["R97_C"]
    l60_vi = r97c["coupled_m5_by_L"]["60"]["VI_-1/9"]
    l60_7h = r97c["coupled_m5_by_L"]["60"]["VII_h"]
    phy_routes = {
        "PHY-01": {
            "r97_upgrade": "Exact NSIDE=2048 Mask-Pol analytic Master M^{EE->BB} vs matched-estimand N=512 MC + train-only Gaunt/OLS 150/150 debiasing",
            "master_analytic_eb_ratio": r97b["master_spin2_mask_coupling"]["analytic_master_mean_clBB_over_clEE_2_48"],
            "mc8_matched_eb_ratio": r97b["master_spin2_mask_coupling"]["nside2048_mc8_ratio_of_mean_clBB_over_clEE_2_48"],
            "mc512_matched_eb_ratio": r97b["master_spin2_mask_coupling"]["bandlimited_mc512_ratio_of_mean_clBB_over_clEE_2_48"],
            "mc512_batch16_se": r97b["master_spin2_mask_coupling"]["bandlimited_mc512_batch16_se"],
            "master_vs_mc512_rel_diff": r97b["master_spin2_mask_coupling"]["analytic_vs_mc512_matched_estimand_rel_diff"],
            "te_to_b_heldout_variance_ratio": r97b["cross_split_60D_eb_leakage_debiasing"]["paired_TE_to_B_heldout_variance_ratio"],
            "te_to_b_heldout_variance_ratio_bootstrap_95pct_ci": r97b["cross_split_60D_eb_leakage_debiasing"]["paired_TE_to_B_heldout_variance_ratio_bootstrap_95pct_ci"],
            "debiased_150_150_rank_p": r97b["cross_split_60D_eb_leakage_debiasing"]["debiased_B_60D_150_150_rank_p"],
            "blocker_bucket": "NATIVE_TRANSFER + DATA",
        },
        "PHY-02": {
            "r97_upgrade": "Coupled-m (m=-2..2 to L=60 + all-m to L=8,12) exact Gamma4 transport + corrected +sqrt(6)/10 Thomson sign + expm time integrator + admissible VII_h 4D ray oracle",
            "skew_hermitian_err_oracle": r97c["oracle_verification"]["skew_hermitian_err"],
            "thomson_signed_angular_projection_max_err": r97c["oracle_verification"]["thomson_signed_angular_projection_max_err"],
            "twist_vs_2d_gl_err": r97c["oracle_verification"]["twist_operator_vs_2d_gl_grid_max_abs_err"],
            "r49_4d_geodesic_oracle_rel_errs": {
                "T": r97c["oracle_verification"]["r49_4d_geodesic_oracle_rel_err_T"],
                "E": r97c["oracle_verification"]["r49_4d_geodesic_oracle_rel_err_E"],
                "B": r97c["oracle_verification"]["r49_4d_geodesic_oracle_rel_err_B"],
            },
            "admissible_oracle_jacobi_na_norm": r97c["oracle_verification"]["jacobi_na_norm"],
            "k0_allm_L12_parity_err": r97c["controls"]["k0_allm_L12_reality_conjugate_parity_err"],
            "L60_VI_minus_1_9_B_over_E": l60_vi["B_over_E_norm_ratio"],
            "time_refinement_r1_to_r4_L60_BE_rel_diff": r97c["convergence_diagnostics"]["time_refinement_with_coeff_reeval"]["L60"]["r1_vs_r4_B_over_E_rel_diff"],
            "allm_vs_m5_L8_power_leak_gt2": r97c["full_all_m_vs_m5_L8_VI_minus_1_9"]["power_fraction_leaking_to_abs_m_gt_2"],
            "allm_vs_m5_L12_power_leak_gt2": r97c["full_all_m_vs_m5_L12_VI_minus_1_9"]["power_fraction_leaking_to_abs_m_gt_2"],
            "blocker_bucket": "NATIVE_TRANSFER + MODEL",
        },
        "PHY-03": {
            "r97_upgrade": "CF4 SR-gamma tomography paired with 5-survey radio Ellis-Baldwin ladder, frozen-design sensitivity, & physical source-modulus refit intervals",
            "radio_surveys_d_obs_over_d_eb_envelope": d["R95_G04"]["cross_ladder_summary"]["d_obs_over_d_eb_minmax"],
            "cf4_R95_0087sys_H0_1s_interval_frozen_design": r97a["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]["H0_partial_id_interval"],
            "cf4_R95_pm0087mag_H0_interval_source_fixed_w": r97a["source_modulus_perturbation"]["fixed_w_R95_H0_interval_exact_refit"],
            "cf4_R95_pm0087mag_H0_interval_source_updated_w": r97a["source_modulus_perturbation"]["updated_w_R95_fixedC_H0_interval_refit"],
            "blocker_bucket": "DATA",
        },
        "PHY-04": {
            "r97_upgrade": "Quaia 10x10 jackknife E2+B2 VSH covariance projected against canonical-triad R95 Bianchi Q2_stf5 + R97 coupled-m L=60 E/B metrics",
            "quaia_inv_E2_norm_uasyr": p6_syn["quaia_inv_E2_norm_uasyr"],
            "quaia_inv_B2_norm_uasyr": p6_syn["quaia_inv_B2_norm_uasyr"],
            "VIIh_cos_E2": p6_syn["template_10x10_overlap"]["VII_h__tilted"]["cos_alignment_with_quaia_inv_E2"],
            "r97c_L60_VI_B_over_E": l60_vi["B_over_E_norm_ratio"],
            "r97c_L60_VIIh_B_over_E": l60_7h["B_over_E_norm_ratio"],
            "actual_normal_vorticity": None,
            "blocker_bucket": "DATA + MODEL",
        },
        "PHY-05": {
            "r97_upgrade": "Exceptional Class-B VI_{-1/9} rotationally-invariant Casimir h=-1/9 verified across R49 evolution + m0 -> m!=0 geodesic scattering at L=8..60 (expm)",
            "h_casimir_preserved": r97c["controls"]["m0_seed_scattering_VI_minus_1_9"]["h_parameter_preserved"],
            "m0_to_m_nonzero_scatter_ratio": r97c["controls"]["m0_seed_scattering_VI_minus_1_9"]["m_nonzero_over_total_T_power"],
            "L60_VI_cross_m_frac": l60_vi["cross_m_coupling_fraction"],
            "blocker_bucket": "MODEL + NATIVE_TRANSFER",
        },
        "PHY-06": {
            "r97_upgrade": "Chiral VII_h parity flip on coupled-m TB/EB & Planck NSIDE=2048 150-heldout L=2 single-sign vs antithetic +-sqrt(A) injection recovery",
            "VIIh_TB_flip_residual_rel": r97c["chirality_VIIh_L16"]["TB_flip_residual_rel"],
            "VIIh_EB_flip_residual_rel": r97c["chirality_VIIh_L16"]["EB_flip_residual_rel"],
            "inj_recovery_single_sign_slope": r97b["anisotropy_injection_recovery"]["recovered_amplitude_linear_fit"]["slope"],
            "inj_recovery_antithetic_pair_slope": r97b["anisotropy_injection_recovery"]["antithetic_pair_amplitude_linear_fit"]["slope"],
            "L60_VIIh_B_over_E": l60_7h["B_over_E_norm_ratio"],
            "blocker_bucket": "NATIVE_TRANSFER + MODEL",
        },
        "PHY-07": {
            "r97_upgrade": "CF4 K4-vs-J7 subspace overlap + physical source-modulus refit + P1 shared-nuisance 9-vector outer & certified sharp tail bounds",
            "K4_in_J7_whitened_frac_binary": r97a["subspace_reconciliation_K4_vs_J7"]["binary_S7"]["fraction_whitened_variance_inside_col_J7"],
            "K4_in_J7_whitened_frac_ivw": r97a["subspace_reconciliation_K4_vs_J7"]["ivw_W7"]["fraction_whitened_variance_inside_col_J7"],
            "radial_schur_red_chi2_R36_vs_R95": [
                r97a["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]["C_R36_inherited"]["outer_2w_pred_reduced_chi2"],
                r97a["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]["C_R95_R5_cal005"]["outer_2w_pred_reduced_chi2"],
            ],
            "p1_w3_conservative_outer_tail": [
                p1_syn["conservative_outer_tail_bounds_at_0p05_4w"]["lower_outer"][2],
                p1_syn["conservative_outer_tail_bounds_at_0p05_4w"]["upper_outer"][2],
            ],
            "p1_w3_certified_sharp_tail": [
                p1_syn["certified_sharp_tail_bounds_at_0p05_4w"]["per_draw_sharp_lower"][2],
                p1_syn["certified_sharp_tail_bounds_at_0p05_4w"]["per_draw_sharp_upper"][2],
            ],
            "blocker_bucket": "DATA + MODEL",
        },
    }

    syn_out = {
        "schema": "htt.r97.phy_and_p1_p4_p6_synthesis/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "upstream_sha256": shas,
        "P1_five_view_with_r97_cf4_bounds": p1_syn,
        "P4_radio_five_survey_summary": p4_syn,
        "P6_gaia_quaia_bianchi_overlap": p6_syn,
        "PHY_routes": phy_routes,
        "physics_gates": {
            "cross_probe_joint_likelihood_qualified": False,
            "physical_Pi": None,
            "physical_GF": None,
            "actual_normal_vorticity": None,
            "commander_null_qualified": False,
            "Bianchi_family_attribution": None,
            "r78_historical_states_changed": False,
        },
    }
    syn_path = R97_DIR / "PHY_AND_P1_P4_P6_SYNTHESIS.json"
    syn_path.write_text(json.dumps(syn_out, indent=2) + "\n")
    syn_sha = _sha(syn_path)

    # Assemble 60-node R97 Master Ledger reusing exact R78 nodes & topological order + R95 baseline statuses
    r95_ledger = json.loads((R95_DIR / "R95_60_NODE_EVIDENCE.json").read_text())
    r95_by_id = {n["id"]: n for n in r95_ledger["nodes"]}
    r78_by_id = {n["id"]: n for n in r78["nodes"]}
    rmap_by_id = {r["id"]: r for r in rmap["rows"]}

    unit_file_for_paper = {
        "P3": ("CF4_GENEALOGY_AND_PARTIAL_ID.json", shas["R97_A"]),
        "P2": ("CMB_INJECTION_AND_EB_LEAKAGE.json", shas["R97_B"]),
        "P5": ("BIANCHI_COUPLED_M_TRANSPORT.json", shas["R97_C"]),
    }

    ledger_nodes = []
    for nid in r78["topological_order"]:
        n78 = r78_by_id[nid]
        n95 = r95_by_id[nid]
        pap = n78["paper"]
        if pap in unit_file_for_paper:
            art_name, art_sha = unit_file_for_paper[pap]
            r97_stage = "R97_EXECUTED_CONDITIONAL_SCIENCE"
        elif nid.startswith("PHY-") or pap in ("P1", "P4", "P6"):
            art_name, art_sha = ("PHY_AND_P1_P4_P6_SYNTHESIS.json", syn_sha)
            r97_stage = "R97_SYNTHESIS_UPDATED"
        else:
            art_name, art_sha = (n95["r95_primary_artifact"], n95["r95_artifact_sha256"])
            r97_stage = "R95_REUSED_PROVENANCE_LOCKED"

        ledger_nodes.append({
            "id": nid,
            "paper": pap,
            "work_group": rmap_by_id[nid]["work_group"],
            "r78_science_state_preserved": n78["state"],
            "r95_execution_status": n95["r95_execution_status"],
            "r97_campaign_layer": r97_stage,
            "r97_primary_artifact": art_name,
            "r97_artifact_sha256": art_sha,
            "publication_science_accepted": (n78["state"] == "completed_scoped"),
            "blocker_bucket": n95["blocker_bucket"],
            "specific_next_unit": n95["specific_next_unit"],
        })

    if len(ledger_nodes) != 60 or len({x["id"] for x in ledger_nodes}) != 60:
        raise RuntimeError("60-node ledger cardinality failed")

    master = {
        "schema": "htt.r97.60_node_science_execution_ledger/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "r78_integrated_dag_sha256": actual_r78_sha,
        "r78_total_nodes": 60,
        "r78_hard_edges": 129,
        "r78_next_action_id": "SQ-CF4",
        "original_science_status_changed": False,
        "actual_r97_physical_science_acceptance": False,
        "r97_unit_artifact_shas": {
            "CF4_GENEALOGY_AND_PARTIAL_ID.json": shas["R97_A"],
            "CMB_INJECTION_AND_EB_LEAKAGE.json": shas["R97_B"],
            "BIANCHI_COUPLED_M_TRANSPORT.json": shas["R97_C"],
            "PHY_AND_P1_P4_P6_SYNTHESIS.json": syn_sha,
        },
        "nodes": ledger_nodes,
    }
    (R97_DIR / "R97_60_NODE_EXECUTION_LEDGER.json").write_text(json.dumps(master, indent=2) + "\n")

    # Write concise Korean summary R97_REPORT_KO.md strictly from regenerated runtime artifacts
    eb_m = r97b["master_spin2_mask_coupling"]
    deb = r97b["cross_split_60D_eb_leakage_debiasing"]
    inj_f = r97b["anisotropy_injection_recovery"]["recovered_amplitude_linear_fit"]
    anti_f = r97b["anisotropy_injection_recovery"]["antithetic_pair_amplitude_linear_fit"]
    sub = r97a["subspace_reconciliation_K4_vs_J7"]
    b_r95 = r97a["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]
    src_p = r97a["source_modulus_perturbation"]
    ov = r97c["oracle_verification"]
    c_out = p1_syn["conservative_outer_tail_bounds_at_0p05_4w"]
    c_sh = p1_syn["certified_sharp_tail_bounds_at_0p05_4w"]
    f4_ce = p1_syn["f4_counterexample_regression"]
    report_lines = [
        "# HTT R97 Scientific Execution Report (F1-F8 Remediated)",
        "",
        f"- R78 정본 SHA256: `{actual_r78_sha}` (60 nodes, 129 edges, `NEXT_ID={r78['next_action_id']}`)",
        "- `original_science_status_changed = false`, `actual_r97_physical_science_acceptance = false`",
        "",
        "## 핵심 교정 결과 (Units A-D, F1-F8 반영)",
        f"- **Unit A / SQ-CF4 (P3, F3/F7)**: `K4 in col(J7)` 백색화 분산 포함률 binary `S7` `{100.0*sub['binary_S7']['fraction_whitened_variance_inside_col_J7']:.2f}%` / IVW `W7` `{100.0*sub['ivw_W7']['fraction_whitened_variance_inside_col_J7']:.2f}%` (모델 동일성 미주장). "
        f"고정 설계 잔차 근사 0.087 mag 1-sigma `H0` `[ {b_r95['H0_partial_id_interval'][0]:.2f}, {b_r95['H0_partial_id_interval'][1]:.2f} ]` vs 실제 원천 modulus 재적합 `delta=+-0.087 mag` "
        f"(고정 가중치 R95 `[{src_p['fixed_w_R95_H0_interval_exact_refit'][0]:.4f}, {src_p['fixed_w_R95_H0_interval_exact_refit'][1]:.4f}]`, `q` 불변 오차 `{src_p['fixed_w_q_invariance_max_abs_err']:.2e}`, 가중치 갱신 `[{src_p['updated_w_R95_fixedC_H0_interval_refit'][0]:.4f}, {src_p['updated_w_R95_fixedC_H0_interval_refit'][1]:.4f}]`). "
        f"DirectCal 대비(`e_SNIa - e_DirectCal`) 무정규화 분산=0, rank6/rank7 95% 반폭 구분 (`SQ-CF4 = BLOCKED_INPUT`).",
        f"- **Unit B / Planck SMICA (P2, F5/F6)**: MASTER 동일 추정대상 `ratio_of_means`: 이론 `{eb_m['analytic_master_mean_clBB_over_clEE_2_48']:.5f}` vs `N=512` band-limited MC `{eb_m['bandlimited_mc512_ratio_of_mean_clBB_over_clEE_2_48']:.5f}` (SE `{eb_m['bandlimited_mc512_batch16_se']:.5f}`, 상대차 `{eb_m['analytic_vs_mc512_matched_estimand_rel_diff']:.4f}`). "
        f"ID 우선 분할 + train-only 가중치 + 2048 OLS 일치 후 SMICA heldout rank p: raw `{deb['raw_60D_150_150_rank_p']:.4f}` ({deb['raw_60D_150_150_exceed_count']}/150 초과), ridge `{deb['debiased_B_60D_150_150_rank_p']:.4f}` ({deb['debiased_B_60D_150_150_exceed_count']}/150 초과), heldout B 분산비 `{deb['paired_TE_to_B_heldout_variance_ratio']:.4f}` (95% bootstrap CI `{deb['paired_TE_to_B_heldout_variance_ratio_bootstrap_95pct_ci']}`). "
        f"L=2 주입-복원: 단일부호 `{inj_f['slope']:.4f}` (이차 `[1,sqrt(A),A]` 교차항 반영), 대칭쌍 `+-sqrt(A)` `{anti_f['slope']:.4f}` (`commander_null_qualified = false`).",
        f"- **Unit C / Bianchi Coupled-m Spin-2 (P5, F1/F2/F8)**: Thomson $T_2-E_2$ 부호를 `+sqrt(6)/10`으로 교정(m=-2..2 signed 각도구적 최대오차 `{ov['thomson_signed_angular_projection_max_err']:.2e}`), "
        f"sparse augmented `expm_multiply` 시간전파 도입(`L=60` `VI_-1/9` `B/E = {l60_vi['B_over_E_norm_ratio']:.6f}`, 재평가 r=1->r=4 `B/E` 상대차 `{r97c['convergence_diagnostics']['time_refinement_with_coeff_reeval']['L60']['r1_vs_r4_B_over_E_rel_diff']:.2e}`), "
        f"admissible `VII_h` oracle (`|n@a|={ov['jacobi_na_norm']:.1e}`, T/E/B=`{ov['r49_4d_geodesic_oracle_rel_err_T']:.2e}/{ov['r49_4d_geodesic_oracle_rel_err_E']:.2e}/{ov['r49_4d_geodesic_oracle_rel_err_B']:.2e}`) (`SQ-NATIVE`, `B02-B05` 미승격).",
        f"- **Unit D / P1, P4, P6, PHY-01..07 (F4)**: P1 4창 signed 9-vector 전파(반례 재현 `{f4_ce['actual_w3_count']}/2048 > {f4_ce['uniform_width_reported_w3_count']}/2048`), "
        f"보수적 삼각부등식 outer bound w3 `[{c_out['lower_outer'][2]:.4f}, {c_out['upper_outer'][2]:.4f}]`, "
        f"전역 최적성 인증(min gap `{c_sh['min_global_optimality_cert_gap']:.4f}`) per-draw sharp bound w3 `[{c_sh['per_draw_sharp_lower'][2]:.4f}, {c_sh['per_draw_sharp_upper'][2]:.4f}]`, common witness `[{c_sh['common_witness_lower'][2]:.4f}, {c_sh['common_witness_upper'][2]:.4f}]` (`physical_Pi=None, physical_GF=None, actual_normal_vorticity=None`).",
    ]
    (R97_DIR / "R97_REPORT_KO.md").write_text("\n".join(report_lines) + "\n")
    return {"master": master, "synthesis": syn_out}


if __name__ == "__main__":
    res = build_synthesis_and_ledger()
    print(json.dumps({
        "n_nodes": len(res["master"]["nodes"]),
        "r78_sha_ok": res["master"]["r78_integrated_dag_sha256"] == EXPECTED_R78_SHA,
        "p6_VIIh_cos_E2": res["synthesis"]["P6_gaia_quaia_bianchi_overlap"]["template_10x10_overlap"]["VII_h__tilted"]["cos_alignment_with_quaia_inv_E2"],
        "p1_w3_outer": res["synthesis"]["P1_five_view_with_r97_cf4_bounds"]["conservative_outer_tail_bounds_at_0p05_4w"]["upper_outer"][2],
        "p1_w3_sharp": res["synthesis"]["P1_five_view_with_r97_cf4_bounds"]["certified_sharp_tail_bounds_at_0p05_4w"]["per_draw_sharp_upper"][2],
        "p1_f4_ce_count": res["synthesis"]["P1_five_view_with_r97_cf4_bounds"]["f4_counterexample_regression"]["actual_w3_count"],
        "elapsed_s": res["master"]["elapsed_seconds"] + res["synthesis"]["elapsed_seconds"],
    }))
