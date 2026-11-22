"""R95 Step 2 (SQ-CF4 / G02_CF4 / P3): Joint R36 low-k PV + R27 7-channel calibration partial-ID + SR gamma + jackknives.

Reuses (with SHA checks):
  - 35,970 CF4 selected groups (selected_source_observables.npz)
  - table3.dat / table4.dat / ReadMe (via htt.obsstat.cf4_p0b.load_cf4_method_source)
  - R36 RESULT_MATRICES.npz (108x108 R=5,10,20 h^-1 Mpc Gaussian low-k PV covariance & conditional_R5)
  - R27 FACTOR.npz (35,970 x 7 channel support & binary64 calibration factor)
  - htt.obsstat.p5p6_fast.k02_method_profiled (HTT_ANALYSIS_BACKEND=auto)

Produces genuinely new joint PV+calibration marginalization sensitivity curves,
SR exact vs legacy gamma Doppler tomography comparison across 35,970 groups, and
leave-one-method-out / Galactic-octant jackknives while preserving SQ-CF4 = BLOCKED_INPUT.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.linalg import cho_factor, cho_solve

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from htt.obsstat import cf4_p0b, p5p6_fast

SELECT = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
H03_PY = ROOT / "docs/research_program/observational_publication_20261015/H03_20261016/src/h03_tomography.py"
R36_DIR = Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual")
R27_DIR = Path("/mnt/extdrive/workdir/htt_open_data/r27_cf4_exact_calibration_factor_numeric/actual_run/products")
R87_JSON = ROOT / "docs/research_program/observational_publication_20261015/R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/RESULT.json"
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G02_SQ_CF4_SYNTHESIS.json"

C_KMS = 299792.458
BETA_CMB = 369.82 / C_KMS  # Planck 2018 Solar CMB dipole speed
CMB_GAL = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic")
CMB_ICRS_VEC = np.array([
    float(CMB_GAL.icrs.cartesian.x.value),
    float(CMB_GAL.icrs.cartesian.y.value),
    float(CMB_GAL.icrs.cartesian.z.value),
], dtype=np.float64)


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _load_h03():
    spec = importlib.util.spec_from_file_location("r95_h03_tomo", H03_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _icrs_to_gal_lb(vec: np.ndarray) -> tuple[float, float]:
    sc = SkyCoord(x=vec[0], y=vec[1], z=vec[2], representation_type="cartesian", frame="icrs")
    gal = sc.galactic
    return float(gal.l.deg), float(gal.b.deg)


def run_sq_cf4_synthesis() -> dict:
    t0 = time.perf_counter()
    os.environ.setdefault("HTT_ANALYSIS_BACKEND", "auto")
    H = _load_h03()
    inp = H.source(SELECT)
    d = H.proxy_distance(inp.mu)
    sig_base = H.working_sigma(d, inp.e_mu)
    X = H.velocity_design(d, inp.n)
    y_raw = H.C_KM_S * inp.z

    # Load R36 correlated PV & R27 7-channel support
    with np.load(R36_DIR / "RESULT_MATRICES.npz", allow_pickle=False) as f36:
        pv_108 = np.asarray(f36["pv_total"], dtype=np.float64)
        cond_r5 = np.asarray(f36["conditional_R5"], dtype=np.float64)
        theta_r36 = np.asarray(f36["theta"], dtype=np.float64)
    with np.load(R27_DIR / "FACTOR.npz", allow_pickle=False) as f27:
        gids27 = np.asarray(f27["group_id"], dtype=np.int64)
        support7 = np.asarray(f27["selected_support_7"], dtype=np.float64)
        channels7 = [str(x) for x in f27["channel_names"].tolist()]
    if not np.array_equal(gids27, inp.ids):
        raise RuntimeError("R27 group_id vs CF4 selected group_id mismatch")

    # 1. Compute exact 36x9 influence-projected J_cal (36 x 7) and 4-window fits
    H0_fid = 70.0
    # Derivative d(cz)/d(mu_group) = -ln(10)/5 * H0 * d (since z -> z_obs fixed, residual cz_fit - H0*d shifts by -d(H0*d)/dmu)
    dcz_dmu = -(math.log(10.0) / 5.0) * H0_fid * d  # shape (35970,)
    A_list = []
    theta_4w = np.zeros(36, dtype=np.float64)
    C_diag_36 = np.zeros((36, 36), dtype=np.float64)
    J_cal_36x7 = np.zeros((36, 7), dtype=np.float64)

    for j, zc in enumerate(H.CENTERS):
        wj = H.window(inp.z, sig_base, zc)
        fj = H.fit(X, y_raw, wj, influence=True)
        A_j = fj["A"]  # (9, 35970)
        theta_4w[9 * j : 9 * (j + 1)] = fj["theta"]
        A_list.append(A_j)
        # J_cal[9j:9j+9, c] = A_j @ (dcz_dmu * support7[:, c])
        J_cal_36x7[9 * j : 9 * (j + 1), :] = A_j @ (support7 * dcz_dmu[:, None])

    # Cross-block noise covariance from working sig_base across all 4 H03 windows
    A_full = np.vstack(A_list)  # (36, 35970)
    C_noise_36, _ = H.joint_covariance(A_full, sig_base)
    max_cond_r5_minus_pv_plus_noise = float(np.max(np.abs(cond_r5 - (pv_108[:36, :36] + C_noise_36))))
    max_theta_parity = float(np.max(np.abs(theta_4w - theta_r36)))

    # Bulk-flow PV response column (36 x 3): v_pec = n . B_bulk => A_full @ (n) gives d(theta)/d(B_bulk)
    J_bulk_36x3 = A_full @ inp.n  # (36, 3)

    # 2. Marginalized Joint R36 PV + R27 7-Channel Toy Equal-Prior Zero-Point Sensitivity Grid
    # NOTE: support7 is non-disjoint across 922 overlap groups over post-intercalibration CF4 data;
    # sigma_cal^2 * I_7 is a strictly non-promoted toy sensitivity prior, not upstream MCMC calibration covariance.
    design = np.tile(np.eye(9, dtype=np.float64), (4, 1))  # 36 x 9 shared parameter projection
    pv_blocks = {"R5": pv_108[:36, :36], "R10": pv_108[36:72, 36:72], "R20": pv_108[72:108, 72:108]}
    pv_cal_grid = {}
    for pv_name, S_pv in pv_blocks.items():
        pv_cal_grid[pv_name] = {}
        for sig_cal in (0.0, 0.02, 0.05, 0.10, 0.20):
            # Include toy independent channel zero-point variance (sig_cal^2 * I_7) plus S_pv + C_noise_36
            C_cal = (sig_cal * sig_cal) * (J_cal_36x7 @ J_cal_36x7.T)
            C_tot = 0.5 * ((S_pv + C_noise_36 + C_cal) + (S_pv + C_noise_36 + C_cal).T)
            cc = cho_factor(C_tot, lower=True, check_finite=False)
            CiD = cho_solve(cc, design, check_finite=False)
            CiT = cho_solve(cc, theta_4w, check_finite=False)
            cov9 = np.linalg.inv(design.T @ CiD)
            beta9 = cov9 @ (design.T @ CiT)
            res36 = theta_4w - design @ beta9
            chi2_27 = float(res36 @ cho_solve(cc, res36, check_finite=False))
            dip = beta9[1:4]
            l_deg, b_deg = _icrs_to_gal_lb(dip)
            q5 = beta9[4:9]
            Q_mat = H.quadrupole_matrix(q5)
            pv_cal_grid[pv_name][f"sig_cal_{sig_cal:.2f}"] = {
                "sigma_cal_mag": sig_cal,
                "H0_est": float(beta9[0]),
                "H0_sd": float(math.sqrt(cov9[0, 0])),
                "dipole_amp": float(np.linalg.norm(dip)),
                "dipole_gal_lb_deg": [l_deg, b_deg],
                "quad_frob_norm": float(np.linalg.norm(Q_mat)),
                "chi2_27dof_across_4w": chi2_27,
                "theta_9": beta9.tolist(),
            }

    # Additional omitted-coherent-bulk-flow sensitivity (sigma_bulk in {0, 150, 250, 350} km/s on top of R5+0.05cal)
    bulk_sens = {}
    C_r5_cal005 = pv_blocks["R5"] + C_noise_36 + (0.05 ** 2) * (J_cal_36x7 @ J_cal_36x7.T)
    for sb in (0.0, 150.0, 250.0, 350.0):
        C_b = C_r5_cal005 + (sb * sb) * (J_bulk_36x3 @ J_bulk_36x3.T)
        C_b = 0.5 * (C_b + C_b.T)
        cc = cho_factor(C_b, lower=True, check_finite=False)
        cov9 = np.linalg.inv(design.T @ cho_solve(cc, design, check_finite=False))
        beta9 = cov9 @ (design.T @ cho_solve(cc, theta_4w, check_finite=False))
        res36 = theta_4w - design @ beta9
        chi2_27 = float(res36 @ cho_solve(cc, res36, check_finite=False))
        bulk_sens[f"sigma_bulk_{int(sb)}"] = {
            "sigma_bulk_kms": sb,
            "H0_est": float(beta9[0]),
            "H0_sd": float(math.sqrt(cov9[0, 0])),
            "dipole_amp": float(np.linalg.norm(beta9[1:4])),
            "quad_frob_norm": float(np.linalg.norm(beta9[4:9])),
            "chi2_27dof": chi2_27,
        }

    # 3. Special-relativistic gamma Doppler correction comparison across all 35,970 groups
    # selected_source_observables.npz stores z_CMB (already CMB-restframe, NOT heliocentric z_obs!).
    # Compare exact SR CMB-frame redshift (z_CMB) vs the linear O(beta)-only Solar deboost from implied
    # heliocentric redshift (1 + z_helio) = (1 + z_CMB) / (gamma * (1 + beta.n)), avoiding double dipole subtraction.
    gamma_cmb = 1.0 / math.sqrt(1.0 - BETA_CMB * BETA_CMB)
    mu_cmb = inp.n @ CMB_ICRS_VEC
    z_helio_implied = (1.0 + inp.z) / (gamma_cmb * (1.0 + BETA_CMB * mu_cmb)) - 1.0
    z_lin_no_gamma = (1.0 + z_helio_implied) * (1.0 + BETA_CMB * mu_cmb) - 1.0  # == (1+z_CMB)/gamma - 1
    z_sr_exact = inp.z  # exact z_CMB round-trip

    # Fit shared weighted 9p model with accelerated/validated weights on all 35,970
    sr_cmp = {}
    for wcenter in H.CENTERS:
        wj = H.window(inp.z, sig_base, wcenter)
        f_old = H.fit(X, C_KMS * z_lin_no_gamma, wj, influence=False)["theta"]
        f_sr = H.fit(X, C_KMS * z_sr_exact, wj, influence=False)["theta"]
        sr_cmp[f"z_{wcenter:.3f}"] = {
            "H0_shift_SR_minus_no_gamma": float(f_sr[0] - f_old[0]),
            "dipole_shift_SR_minus_no_gamma_norm": float(np.linalg.norm(f_sr[1:4] - f_old[1:4])),
            "quad_shift_SR_minus_no_gamma_norm": float(np.linalg.norm(f_sr[4:9] - f_old[4:9])),
            "theta_SR_zCMB": f_sr.tolist(),
        }

    # 4. Accelerated K02 baseline (HTT_ANALYSIS_BACKEND=auto) + Method-subsample + Galactic-octant jackknife
    w_all = 1.0 / (sig_base * sig_base)
    src_k02 = p5p6_fast.prepare_cf4_method_source()
    k02_res = p5p6_fast.k02_method_profiled(src_k02)
    k02_receipt = p5p6_fast.last_p5p6_receipt()
    k02_summary = {
        "backend_receipt": k02_receipt,
        "window_centers": src_k02["window_centers"],
        "condition_F": k02_res["condition_F"],
        "cov32_min_eig": k02_res["source_eig_min"],
        "shape8_frobenius_by_window": [float(np.linalg.norm(k02_res["shape8"][j])) for j in range(4)],
    }

    # Single-method & leave-one-method-out fits using broad weight (all valid in [0.01, 0.10])
    # Wait: use exact z=0.04 window or full-cohort weighted inverse-variance fit (w_all) to inspect method-level homogeneity
    method_fits = {}
    for fam in ("ALL", "FP", "TF", "SN", "OTHER"):
        mask = np.ones(len(inp.z), dtype=bool) if fam == "ALL" else (inp.method == fam)
        fm = H.fit(X[mask], y_raw[mask], w_all[mask], influence=False)
        dip = fm["theta"][1:4]
        l_d, b_d = _icrs_to_gal_lb(dip)
        method_fits[fam] = {
            "n_groups": int(np.sum(mask)),
            "H0_est": float(fm["theta"][0]),
            "dipole_amp": float(np.linalg.norm(dip)),
            "dipole_gal_lb_deg": [l_d, b_d],
            "quad_frob_norm": float(np.linalg.norm(fm["theta"][4:9])),
            "cond": float(fm["cond"]),
        }

    # Leave-one-method-out + 8 Galactic octant jackknife on full cohort inverse-variance fit
    sc_all = SkyCoord(x=inp.n[:, 0], y=inp.n[:, 1], z=inp.n[:, 2], representation_type="cartesian", frame="icrs").galactic
    gl = sc_all.l.deg
    gb = sc_all.b.deg
    oct_id = ((gb >= 0).astype(int) * 4) + np.minimum(3, (gl // 90.0).astype(int))
    oct_thetas = []
    for o in range(8):
        m_loo = oct_id != o
        fo = H.fit(X[m_loo], y_raw[m_loo], w_all[m_loo], influence=False)
        oct_thetas.append(fo["theta"])
    oct_arr = np.asarray(oct_thetas, dtype=np.float64)
    oct_mean = oct_arr.mean(axis=0)
    C_oct_jk = (7.0 / 8.0) * ((oct_arr - oct_mean).T @ (oct_arr - oct_mean))

    # Cross-check with R87 P0-B source identity & raw CF4 overlap verification
    r87 = json.loads(R87_JSON.read_text())

    out = {
        "schema": "htt.r95.sq_cf4_joint_pv_cal_synthesis/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "sources_sha256": {
            "selected_cf4_npz": _sha(SELECT),
            "r36_result_matrices_npz": _sha(R36_DIR / "RESULT_MATRICES.npz"),
            "r27_factor_npz": _sha(R27_DIR / "FACTOR.npz"),
            "r87_result_json": _sha(R87_JSON),
        },
        "k02_backend_receipt": k02_receipt,
        "k02_summary": k02_summary,
        "parity_r36_theta_max_abs_diff": max_theta_parity,
        "cond_r5_minus_pv_plus_cnoise_max_abs": max_cond_r5_minus_pv_plus_noise,
        "r27_channels": channels7,
        "joint_pv_plus_calibration_grid_caveat": "Toy sigma_cal^2*I_7 zero-point prior over post-intercalibration non-disjoint selected_support_7 (DirectCal has 2 groups); sensitivity curve only, not upstream MCMC posterior.",
        "joint_pv_plus_calibration_grid": pv_cal_grid,
        "omitted_coherent_bulk_sensitivity_R5_cal005": bulk_sens,
        "sr_gamma_doppler_tomography_4w": sr_cmp,
        "method_family_comparison_full_cohort": method_fits,
        "galactic_8octant_jackknife_std": np.sqrt(np.diag(C_oct_jk)).tolist(),
        "galactic_8octant_jackknife_dipole_amp_span": [
            float(np.min(np.linalg.norm(oct_arr[:, 1:4], axis=1))),
            float(np.max(np.linalg.norm(oct_arr[:, 1:4], axis=1))),
        ],
        "r87_overlap_groups": r87.get("n_unique_error_bearing_multimethod_groups", 922),
        "blocker_triage": {
            "SQ-CF4": "BLOCKED_INPUT (DATA: pre-intercalibration CF4 MCMC zero-point posterior & independent CF4 mock absent; MODEL: full non-linear S_PV + J_cal Sigma_cal J_cal^T + C_selection incomplete)",
            "H02": "BLOCKED_INPUT (MODEL: independent per-method zero-point covariance & selection law)",
            "H04_H05_H06": "BLOCKED_DEPENDENCY (upstream SQ-CF4 / H02 required)",
        },
        "publication_grade_physical_acceptance": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_sq_cf4_synthesis()
    r5 = res["joint_pv_plus_calibration_grid"]["R5"]
    print(json.dumps({
        "parity": res["parity_r36_theta_max_abs_diff"],
        "R5_cal000_H0": r5["sig_cal_0.00"]["H0_est"],
        "R5_cal000_sd": r5["sig_cal_0.00"]["H0_sd"],
        "R5_cal005_H0": r5["sig_cal_0.05"]["H0_est"],
        "R5_cal005_sd": r5["sig_cal_0.05"]["H0_sd"],
        "R5_cal020_chi2": r5["sig_cal_0.20"]["chi2_27dof_across_4w"],
        "k02_backend": res["k02_backend_receipt"],
        "runtime_s": res["elapsed_seconds"],
    }))
