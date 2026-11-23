"""R100 Step B: Finite-redshift Bianchi position drift, T_C(z) and T_G(z) response kernels."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
from scipy.spatial.transform import Rotation

from bass.transport.finite_redshift_optics import OpticalHistory
from bass.transport.position_drift_optics import (
    C_LIGHT_KMS,
    RATE_S_TO_UASYR,
    finite_redshift_position_drift,
)
from docs.research_program.observational_publication_20261015.H03_20261016.src.h03_tomography import stf_features
from scripts.r69.gaia_e2_b2 import templates as vsh_templates
from scripts.r97 import bianchi_coupled_m_transport as r97
from scripts.r98 import bianchi_history as r98

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research_program/observational_publication_20261015/R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123"
REDSHIFTS = np.array([
    0.01, 0.025, 0.04, 0.045, 0.06, 0.065, 0.08, 0.085, 0.10,
    0.50, 0.596, 1.00, 1.171, 1.761, 2.00, 2.461,
], dtype=float)
CF4_WINDOW_CENTERS = np.array([0.025, 0.045, 0.065, 0.085], dtype=float)
QUAIA_SHELL_MEDIANS = np.array([0.596, 1.171, 1.761, 2.461], dtype=float)
N_MIN = -math.log(4.0)  # covers z up to 3.0 including Quaia shell median 2.461


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_history(family: str, samples: int = 641, emitter_beta=None) -> OpticalHistory:
    _, t = r98.background(family, samples=samples)
    href = float(r98.optics()[0].H_of_z(r98.Z_INITIAL))
    eb = None if emitter_beta is None else np.broadcast_to(np.asarray(emitter_beta, float), (len(t.N_grid), 3)).copy()
    return OpticalHistory(
        t.N_grid, t.H_grid, t.sigma_ab_grid, t.a_grid, t.n_grid,
        h_reference_si=href, emitter_beta=eb,
    )


def sphere_projectors(n_theta: int = 10):
    """Build exact GL spherical quadrature projectors onto H03 9D STF and R69 16D VSH."""
    th, ph, nh, w = r97.gl_sphere_grid(n_theta)
    w4 = (w / (4.0 * math.pi)).ravel()
    dirs = nh.reshape(-1, 3)
    ra = ph.ravel()
    dec = math.pi / 2.0 - th.ravel()

    X9 = np.column_stack((np.ones(len(dirs)), dirs, stf_features(dirs)))  # (N, 9)
    G9 = (X9.T * w4) @ X9
    P9 = np.linalg.solve(G9, X9.T * w4)  # (9, N)

    _, B16 = vsh_templates(ra, dec)  # (N, 2, 16)
    B_flat = B16.reshape(len(dirs) * 2, 16)
    w_vsh = np.repeat(w4, 2)
    G16 = (B_flat.T * w_vsh) @ B_flat
    P16 = np.linalg.solve(G16, B_flat.T * w_vsh)  # (16, 2N)
    return dirs, w4, P9, P16, G9, G16


def project_responses(beams, P9: np.ndarray, P16: np.ndarray, flrw_DL: np.ndarray):
    """Project finite-z ln(D_L / D_L_FLRW) and proper motion into T_C (nz, 9) and T_G (nz, 16)."""
    ln_ratio = np.log(beams.luminosity_distance_mpc / flrw_DL)  # (nr, nz)
    TC = (P9 @ ln_ratio).T  # (nz, 9)
    pm_obs = beams.pm_observed_uasyr.transpose(1, 0, 2).reshape(beams.redshift.shape[1], -1)  # (nz, 2*nr)
    TG = (P16 @ pm_obs.T).T  # (nz, 16)
    local_pm = np.empty((len(beams.observed_sky), 2))
    from bass.transport.position_drift_optics import screen_basis_for_directions
    era, edec = screen_basis_for_directions(beams.observed_sky)
    local_pm[:, 0] = np.einsum("ni,ni->n", era, beams.local_kinematic_limit_3d_uasyr)
    local_pm[:, 1] = np.einsum("ni,ni->n", edec, beams.local_kinematic_limit_3d_uasyr)
    TG_local = P16 @ local_pm.ravel()
    return TC, TG, TG_local


def compute() -> dict[str, object]:
    t0 = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    dirs, w4, P9, P16, G9, G16 = sphere_projectors(8)
    dirs_fine, _, P9_f, P16_f, _, _ = sphere_projectors(12)

    coarse_opt = dict(rtol=2e-10, atol=2e-13, max_step=0.04)
    fine_opt = dict(rtol=2e-12, atol=2e-15, max_step=0.02)

    histories = {fam: make_history(fam, 641) for fam in r98.FAMILIES}
    beams_by_fam = {}
    beams_by_fam["FLRW"] = finite_redshift_position_drift(
        histories["FLRW"], dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **coarse_opt
    )
    flrw_DL = beams_by_fam["FLRW"].luminosity_distance_mpc
    for fam in r98.FAMILIES:
        if fam != "FLRW":
            beams_by_fam[fam] = finite_redshift_position_drift(
                histories[fam], dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **coarse_opt
            )

    fam_summary = {}
    TC_fam, TG_fam, TG_loc_fam = {}, {}, {}
    for fam in r98.FAMILIES:
        bm = beams_by_fam[fam]
        tc, tg, tg_loc = project_responses(bm, P9, P16, flrw_DL)
        TC_fam[fam] = tc
        TG_fam[fam] = tg
        TG_loc_fam[fam] = tg_loc

        pm_rms_by_z = np.sqrt(np.einsum("n,nzk->zk", w4, bm.pm_observed_uasyr ** 2).sum(axis=1))
        rem_rms_by_z = np.sqrt(np.einsum("n,nz->z", w4, np.sum(bm.finite_z_remainder_3d_uasyr ** 2, axis=2)))
        loc_rms = float(np.sqrt(np.sum(w4 * np.sum(bm.local_kinematic_limit_3d_uasyr ** 2, axis=1))))

        fam_summary[fam] = {
            "max_redshift_residual": float(np.max(np.abs(bm.redshift - REDSHIFTS))),
            "max_null_error": bm.max_null_error,
            "max_longitudinal_invariant_error": bm.max_longitudinal_invariant_error,
            "max_direction_tangency": bm.max_direction_tangency,
            "max_connector_tangency": bm.max_normalized_connector_tangency,
            "local_z0_shear_pm_rms_uasyr": loc_rms,
            "pm_rms_by_z_uasyr": pm_rms_by_z.tolist(),
            "finite_z_remainder_rms_by_z_uasyr": rem_rms_by_z.tolist(),
            "finite_z_remainder_fraction_of_local_by_z": (
                (rem_rms_by_z / loc_rms).tolist() if loc_rms > 0 else [0.0] * len(REDSHIFTS)
            ),
            "TC_lnDL_9d_by_z": tc.tolist(),
            "TG_vsh_16d_by_z_microasyr": tg.tolist(),
            "TG_local_z0_16d_microasyr": tg_loc.tolist(),
            "TG_sectors_at_quaia_z_norms": {
                f"z={REDSHIFTS[zi]:.3f}": {
                    "glide_E1": float(np.linalg.norm(tg[zi, 0:3])),
                    "spin_B1": float(np.linalg.norm(tg[zi, 3:6])),
                    "E2": float(np.linalg.norm(tg[zi, 6:11])),
                    "B2": float(np.linalg.norm(tg[zi, 11:16])),
                    "finite_z_B2_ratio_to_E2": float(np.linalg.norm(tg[zi, 11:16]) / max(np.linalg.norm(tg[zi, 6:11]), 1e-300)),
                }
                for zi in [10, 12, 13, 15]
            },
        }

    # Convergence checks on VII_h and VI_h (ODE tolerance + grid refinement + angular sphere refinement)
    convergence = {}
    flrw_fine_DL = finite_redshift_position_drift(
        histories["FLRW"], dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **fine_opt
    ).luminosity_distance_mpc
    flrw_ang_DL = finite_redshift_position_drift(
        histories["FLRW"], dirs_fine, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **coarse_opt
    ).luminosity_distance_mpc
    for fam in ("VII_h", "VI_h"):
        b_coarse = beams_by_fam[fam]
        b_fine = finite_redshift_position_drift(
            histories[fam], dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **fine_opt
        )
        h_1281 = make_history(fam, 1281)
        b_dense = finite_redshift_position_drift(
            h_1281, dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **fine_opt
        )
        b_ang = finite_redshift_position_drift(
            histories[fam], dirs_fine, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **coarse_opt
        )
        _, tg_c, _ = project_responses(b_coarse, P9, P16, flrw_DL)
        _, tg_f, _ = project_responses(b_fine, P9, P16, flrw_fine_DL)
        _, tg_d, _ = project_responses(b_dense, P9, P16, flrw_fine_DL)
        _, tg_a, _ = project_responses(b_ang, P9_f, P16_f, flrw_ang_DL)
        convergence[fam] = {
            "ode_coarse_vs_fine_max_abs_pm_uasyr": float(np.max(np.abs(b_coarse.pm_observed_uasyr - b_fine.pm_observed_uasyr))),
            "ode_coarse_vs_fine_rel_TG": float(np.linalg.norm(tg_c - tg_f) / max(np.linalg.norm(tg_f), 1e-300)),
            "bg_641_vs_1281_max_abs_pm_uasyr": float(np.max(np.abs(b_fine.pm_observed_uasyr - b_dense.pm_observed_uasyr))),
            "bg_641_vs_1281_rel_TG": float(np.linalg.norm(tg_f - tg_d) / max(np.linalg.norm(tg_d), 1e-300)),
            "ang_gl10_vs_gl14_rel_TG": float(np.linalg.norm(tg_c - tg_a) / max(np.linalg.norm(tg_a), 1e-300)),
        }

    # Finite-difference Jacobians wrt observer boost beta_o, global source tilt beta_e (in units of 10^-3 c)
    # on FLRW and VI_h!
    eps_beta = 1.0e-4  # dimensionless v/c; normalize derivatives per 10^-3 c (approx 300 km/s)!
    scale_per_1e3 = 1.0e-3
    jac_results = {}
    cf4_idx = [np.argmin(np.abs(REDSHIFTS - zc)) for zc in CF4_WINDOW_CENTERS]
    quaia_idx = [np.argmin(np.abs(REDSHIFTS - zq)) for zq in QUAIA_SHELL_MEDIANS]
    templates_npz = {
        "redshifts": REDSHIFTS,
        "cf4_window_centers": CF4_WINDOW_CENTERS,
        "quaia_shell_medians": QUAIA_SHELL_MEDIANS,
        "directions": dirs,
        "weights_4pi": w4,
    }
    for fam in r98.FAMILIES:
        templates_npz[f"TC_geo_{fam}"] = TC_fam[fam]
        templates_npz[f"TG_geo_{fam}"] = TG_fam[fam]

    for fam in ("FLRW", "VI_h"):
        h_base = histories[fam]
        ref_DL = flrw_DL if fam == "FLRW" else beams_by_fam[fam].luminosity_distance_mpc
        J_C_bo = np.empty((len(REDSHIFTS), 9, 3))
        J_G_bo = np.empty((len(REDSHIFTS), 16, 3))
        J_C_be = np.empty((len(REDSHIFTS), 9, 3))
        J_G_be = np.empty((len(REDSHIFTS), 16, 3))
        for axis in range(3):
            ev = np.zeros(3); ev[axis] = eps_beta
            bp_o = finite_redshift_position_drift(h_base, dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", observer_beta=ev, **coarse_opt)
            bm_o = finite_redshift_position_drift(h_base, dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", observer_beta=-ev, **coarse_opt)
            tc_p, tg_p, _ = project_responses(bp_o, P9, P16, ref_DL)
            tc_m, tg_m, _ = project_responses(bm_o, P9, P16, ref_DL)
            J_C_bo[:, :, axis] = (tc_p - tc_m) / (2.0 * eps_beta) * scale_per_1e3
            J_G_bo[:, :, axis] = (tg_p - tg_m) / (2.0 * eps_beta) * scale_per_1e3

            hp_e = make_history(fam, 641, emitter_beta=ev)
            hm_e = make_history(fam, 641, emitter_beta=-ev)
            bp_e = finite_redshift_position_drift(hp_e, dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **coarse_opt)
            bm_e = finite_redshift_position_drift(hm_e, dirs, REDSHIFTS, n_min=N_MIN, sky_frame="observed", **coarse_opt)
            tc_pe, tg_pe, _ = project_responses(bp_e, P9, P16, ref_DL)
            tc_me, tg_me, _ = project_responses(bm_e, P9, P16, ref_DL)
            J_C_be[:, :, axis] = (tc_pe - tc_me) / (2.0 * eps_beta) * scale_per_1e3
            J_G_be[:, :, axis] = (tg_pe - tg_me) / (2.0 * eps_beta) * scale_per_1e3

        templates_npz[f"TC_beta_o_per_1e3c_{fam}"] = J_C_bo
        templates_npz[f"TG_beta_o_per_1e3c_{fam}"] = J_G_bo
        templates_npz[f"TC_beta_e_per_1e3c_{fam}"] = J_C_be
        templates_npz[f"TG_beta_e_per_1e3c_{fam}"] = J_G_be

        # Joint 6-parameter [beta_o (3), beta_e (3)] transfer matrices on CF4 4 windows (36x6) and Quaia 4 shells (64x6)
        M_CF4 = np.hstack([
            J_C_bo[cf4_idx].reshape(-1, 3),
            J_C_be[cf4_idx].reshape(-1, 3),
        ])  # (36, 6) in dimensionless log-distance response units (per 10^-3 c)
        M_Gaia = np.hstack([
            J_G_bo[quaia_idx].reshape(-1, 3),
            J_G_be[quaia_idx].reshape(-1, 3),
        ])  # (64, 6) in uas/yr (per 10^-3 c)
        # Evaluate raw (scale-explicit!) and covariance-weighted joint rank using fiducial noise scales:
        # sigma_C_fid ~ 0.003 (typical R100 CF4 window log-dist error), sigma_G_fid ~ 1.0 uas/yr
        M_joint_scaled = np.vstack([M_CF4 / 0.003, M_Gaia / 1.0])
        sv_cf4 = np.linalg.svd(M_CF4, compute_uv=False)
        sv_gaia = np.linalg.svd(M_Gaia, compute_uv=False)
        sv_joint = np.linalg.svd(M_joint_scaled, compute_uv=False)

        # Measure cosine similarity between beta_o and beta_e x-columns at CF4 z=0.045 vs Quaia z=0.596..2.461
        cos_cf4 = float(np.dot(M_CF4[:, 0], M_CF4[:, 3]) / (np.linalg.norm(M_CF4[:, 0]) * np.linalg.norm(M_CF4[:, 3])))
        cos_gaia = float(np.dot(M_Gaia[:, 0], M_Gaia[:, 3]) / (np.linalg.norm(M_Gaia[:, 0]) * np.linalg.norm(M_Gaia[:, 3])))
        jac_results[fam] = {
            "units": "CF4: Delta ln D_L per 10^-3 c (log-distance shift = -Delta ln D_L); Gaia: uas/yr per 10^-3 c",
            "CF4_z_centers": CF4_WINDOW_CENTERS.tolist(),
            "CF4_TC_beta_o_dipole_amplitude_by_z": np.linalg.norm(J_C_bo[cf4_idx, 1:4, 0], axis=1).tolist(),
            "CF4_TC_beta_e_dipole_amplitude_by_z": np.linalg.norm(J_C_be[cf4_idx, 1:4, 0], axis=1).tolist(),
            "CF4_36x6_singular_values": sv_cf4.tolist(),
            "CF4_36x6_condition": float(sv_cf4[0] / sv_cf4[-1]),
            "Gaia_quaia_z_medians": QUAIA_SHELL_MEDIANS.tolist(),
            "Gaia_TG_beta_o_glide_by_z_uasyr_per_1e3c": np.linalg.norm(J_G_bo[quaia_idx, 0:3, 0], axis=1).tolist(),
            "Gaia_TG_beta_e_glide_by_z_uasyr_per_1e3c": np.linalg.norm(J_G_be[quaia_idx, 0:3, 0], axis=1).tolist(),
            "Gaia_64x6_singular_values_uasyr": sv_gaia.tolist(),
            "Gaia_64x6_condition": float(sv_gaia[0] / sv_gaia[-1]),
            "joint_CF4_Gaia_fiducial_normalized_singular_values": sv_joint.tolist(),
            "joint_condition": float(sv_joint[0] / sv_joint[-1]),
            "cosine_beta_o_vs_beta_e_CF4_36D": cos_cf4,
            "cosine_beta_o_vs_beta_e_Gaia_64D": cos_gaia,
            "arbitrary_column_rescaling_does_not_recover_rank_note": True,
        }

    # Exact SO(3) rotational equivariance test on Class B VI_h
    R_rot = Rotation.from_rotvec([0.27, -0.41, 0.19]).as_matrix()
    h_vi = histories["VI_h"]
    sig_r = np.einsum("ij,tjk,lk->til", R_rot, h_vi.ratios(h_vi.ratios.x)[:, :9].reshape(-1, 3, 3), R_rot)
    _, tr_vi = r98.background("VI_h", samples=641)
    h_vi_rot = OpticalHistory(
        tr_vi.N_grid, tr_vi.H_grid,
        np.einsum("ij,tjk,lk->til", R_rot, tr_vi.sigma_ab_grid, R_rot),
        np.einsum("ij,tj->ti", R_rot, tr_vi.a_grid),
        np.einsum("ij,tjk,lk->til", R_rot, tr_vi.n_grid, R_rot),
        h_reference_si=h_vi.h_reference_si,
    )
    test_dirs = dirs[:24]
    rot_dirs = test_dirs @ R_rot.T
    b_orig = finite_redshift_position_drift(h_vi, test_dirs, [0.05, 1.0], n_min=N_MIN, sky_frame="observed", **coarse_opt)
    b_rot = finite_redshift_position_drift(h_vi_rot, rot_dirs, [0.05, 1.0], n_min=N_MIN, sky_frame="observed", **coarse_opt)
    eq_err = float(np.max(np.abs(np.einsum("ij,nzj->nzi", R_rot, b_orig.drift_observed_3d_uasyr) - b_rot.drift_observed_3d_uasyr)))

    # Secular aberration amplitude check: standard Galactocentric ~ 5.05 uas/yr (~7.3e-19 s^-1 = a ~ 2.2e-10 m/s^2)
    a_gal_s_inv = np.array([-0.14e-18, -0.68e-18, -0.34e-18])
    b_sec = finite_redshift_position_drift(
        histories["FLRW"], dirs, [1.0], n_min=N_MIN, sky_frame="observed",
        observer_accel_s_inv=a_gal_s_inv, **coarse_opt
    )
    _, tg_sec, _ = project_responses(b_sec, P9, P16, flrw_DL[[11]])
    sec_glide = tg_sec[0, 0:3]
    expected_glide = a_gal_s_inv * RATE_S_TO_UASYR

    npz_path = OUT / "OPTICAL_DRIFT_TEMPLATES.npz"
    np.savez_compressed(npz_path, **templates_npz)

    source_paths = [
        Path(__file__),
        ROOT / "htt/bass/transport/position_drift_optics.py",
        ROOT / "htt/bass/transport/finite_redshift_optics.py",
        ROOT / "scripts/r98/bianchi_history.py",
        ROOT / "scripts/r69/gaia_e2_b2.py",
    ]
    payload = {
        "schema": "htt.r100.optical_position_drift/1",
        "owner": "bass_py_presolver",
        "status": "MODEL_CONDITIONAL_NUMERICALLY_CHECKED",
        "transfer_source": "R49_homogeneous_bianchi_IVP_pre_solver_optics",
        "redshifts": REDSHIFTS.tolist(),
        "cf4_window_centers": CF4_WINDOW_CENTERS.tolist(),
        "quaia_shell_medians": QUAIA_SHELL_MEDIANS.tolist(),
        "n_sphere_directions": int(len(dirs)),
        "gl_gram_error_stf9": float(np.max(np.abs(G9 - np.diag([1.0] + [1.0 / 3.0] * 3 + [2.0 / 15.0] * 5)))),
        "gl_gram_error_vsh16": float(np.max(np.abs(G16 - np.diag([2.0 / 3.0] * 6 + [1.0 / 5.0] * 10)))),
        "families": fam_summary,
        "convergence": convergence,
        "jacobians_TC_TG": jac_results,
        "so3_rotational_equivariance_VIh_max_abs_uasyr": eq_err,
        "secular_aberration_check": {
            "input_accel_s_inv": a_gal_s_inv.tolist(),
            "projected_glide_uasyr": sec_glide.tolist(),
            "exact_expected_glide_uasyr": expected_glide.tolist(),
            "max_abs_err_uasyr": float(np.max(np.abs(sec_glide - expected_glide))),
            "residual_non_glide_norm_uasyr": float(np.linalg.norm(tg_sec[0, 3:])),
        },
        "templates_npz": {"path": str(npz_path), "sha256": sha256(npz_path)},
        "inputs_sha256": {os.path.relpath(p, ROOT): sha256(p) for p in source_paths},
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "threads": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        },
        "physical_Pi": None,
        "physical_GF": None,
        "runtime_seconds": time.monotonic() - t0,
    }
    out_path = OUT / "OPTICAL_DRIFT_RESULTS.json"
    out_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    res = compute()
    print(json.dumps({
        "status": res["status"],
        "VI_h_z2_rem_frac": res["families"]["VI_h"]["finite_z_remainder_fraction_of_local_by_z"][-2],
        "VII_h_rel_ode_conv": res["convergence"]["VII_h"]["ode_coarse_vs_fine_rel_TG"],
        "so3_equivariance_err": res["so3_rotational_equivariance_VIh_max_abs_uasyr"],
        "FLRW_cos_bo_be_CF4": res["jacobians_TC_TG"]["FLRW"]["cosine_beta_o_vs_beta_e_CF4_36D"],
        "FLRW_cos_bo_be_Gaia": res["jacobians_TC_TG"]["FLRW"]["cosine_beta_o_vs_beta_e_Gaia_64D"],
        "runtime_s": res["runtime_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
