"""R95 Step 3 (G03_GAIA / P6): Exact SO(3) / STF5 ICRS -> Galactic -> Ecliptic frame covariance & scan-law alignment.

Reuses source-verified R89/R91 Gaia-CRF3 (n=1,614,173; quality=1,203,489), Quaia G<20 (n=634,233),
scanning-law (n_rows=34,504,372), and VLBA (n=713) VSH reductions with SHA256 provenance checks.

Transforms full 16D VSH vectors (E1[3], B1[3], E2[5], B2[5]) and 10x10 (E2, B2) 48-patch jackknife
covariances analytically via J_16(R) = diag(R, R, M_5(R), M_5(R)) and checks ecliptic-pole alignment
of Gaia's scanning-law quadrupole. Preserves SQ-GAIA = DIAGNOSTIC_COMPLETED_SCOPED and
actual_normal_vorticity = None.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

ROOT = Path(__file__).resolve().parents[2]
G03_DIR = ROOT / "docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G03_GAIA"
R91_QUAIA = ROOT / "docs/research_program/observational_publication_20261015/R91_SOLVERFREE_SECOND_CYCLE_20261121/GAIA_QUAIA_FULL_SELECTION.json"
FIVEVIEW_PY = ROOT / "scripts/r68/fiveview_geometry.py"
GAIA_E2B2_PY = ROOT / "scripts/r69/gaia_e2_b2.py"
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_icrs_to_frame_rotation(target_frame: str) -> np.ndarray:
    """Exact 3x3 proper orthogonal matrix R mapping v_target = R @ v_icrs."""
    cols = []
    for axis in np.eye(3, dtype=np.float64):
        sc = SkyCoord(x=axis[0], y=axis[1], z=axis[2], representation_type="cartesian", frame="icrs")
        tf = getattr(sc, target_frame)
        tf_cart = tf.represent_as("cartesian")
        cols.append(np.array([float(tf_cart.x.value), float(tf_cart.y.value), float(tf_cart.z.value)], dtype=np.float64))
    R = np.column_stack(cols)
    ortho_err = float(np.max(np.abs(R.T @ R - np.eye(3))))
    det_err = abs(float(np.linalg.det(R)) - 1.0)
    if ortho_err > 1e-13 or det_err > 1e-13:
        raise RuntimeError(f"Non-SO(3) frame rotation for {target_frame}: ortho={ortho_err}, det={det_err}")
    return R


def _build_stf5_rotation(R: np.ndarray, E: np.ndarray) -> np.ndarray:
    """Exact 5x5 orthogonal matrix M5 such that S' = R S R^T <=> c' = M5 @ c in E basis."""
    M5 = np.einsum("aij,ik,bkl,jl->ab", E, R, E, R, optimize=True)
    ortho_err = float(np.max(np.abs(M5.T @ M5 - np.eye(5))))
    if ortho_err > 1e-13:
        raise RuntimeError(f"M5 orthogonality failed: {ortho_err}")
    return M5


def _build_j16(R: np.ndarray, E: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    M5 = _build_stf5_rotation(R, E)
    J16 = np.zeros((16, 16), dtype=np.float64)
    J16[0:3, 0:3] = R
    J16[3:6, 3:6] = R
    J16[6:11, 6:11] = M5
    J16[11:16, 11:16] = M5
    return J16, M5


def _verify_tangent_equivariance_oracle(R: np.ndarray, J16: np.ndarray, E: np.ndarray, gaia_e2b2) -> float:
    """Verify VSH 16D design vector transforms by J16(R) under n' = R n on random directions."""
    rng = np.random.default_rng(9503)
    ra = rng.uniform(0.0, 2.0 * np.pi, size=24)
    dec = np.arcsin(rng.uniform(-0.95, 0.95, size=24))
    beta = rng.normal(scale=5.0, size=16)

    n, B = gaia_e2b2.templates(ra, dec)
    mu = np.einsum("nai,i->na", B, beta)
    # Reconstruct 3D tangent vector field V = mu_ra * e_ra + mu_dec * e_dec
    cr, sr = np.cos(ra), np.sin(ra)
    cd, sd = np.cos(dec), np.sin(dec)
    era = np.column_stack((-sr, cr, np.zeros(len(ra))))
    edec = np.column_stack((-sd * cr, -sd * sr, cd))
    V = mu[:, 0:1] * era + mu[:, 1:2] * edec

    # Rotate points and tangent vectors directly by R
    n_p = n @ R.T
    V_p = V @ R.T
    ra_p = np.arctan2(n_p[:, 1], n_p[:, 0]) % (2.0 * np.pi)
    dec_p = np.arcsin(np.clip(n_p[:, 2], -1.0, 1.0))
    _, B_p = gaia_e2b2.templates(ra_p, dec_p)
    crp, srp = np.cos(ra_p), np.sin(ra_p)
    cdp, sdp = np.cos(dec_p), np.sin(dec_p)
    era_p = np.column_stack((-srp, crp, np.zeros(len(ra))))
    edec_p = np.column_stack((-sdp * crp, -sdp * srp, cdp))
    mu_p_direct = np.column_stack([np.sum(V_p * era_p, axis=1), np.sum(V_p * edec_p, axis=1)])
    mu_p_j16 = np.einsum("nai,i->na", B_p, J16 @ beta)
    err = float(np.max(np.abs(mu_p_direct - mu_p_j16)))
    if err > 1e-12:
        raise RuntimeError(f"16D VSH SO(3) tangent oracle failed: err={err}")
    return err


def _vector_gal_ecl_angles(v_icrs: np.ndarray, R_gal: np.ndarray, R_ecl: np.ndarray) -> dict:
    v_gal = R_gal @ v_icrs
    v_ecl = R_ecl @ v_icrs
    n_icrs = float(np.linalg.norm(v_icrs))
    l_deg = float(np.rad2deg(np.arctan2(v_gal[1], v_gal[0])) % 360.0)
    b_deg = float(np.rad2deg(np.arcsin(np.clip(v_gal[2] / max(n_icrs, 1e-30), -1.0, 1.0))))
    ecl_pole_frac = float((v_ecl[2] ** 2) / max(n_icrs * n_icrs, 1e-30))
    return {
        "norm_uasyr": n_icrs,
        "vec_icrs": v_icrs.tolist(),
        "vec_gal": v_gal.tolist(),
        "vec_ecl": v_ecl.tolist(),
        "gal_lb_deg": [l_deg, b_deg],
        "ecl_z_axis_energy_fraction": ecl_pole_frac,
    }


def _quad_summary(q_icrs: np.ndarray, M5_gal: np.ndarray, M5_ecl: np.ndarray, stf_shape_fn, stf_matrix_fn) -> dict:
    q_gal = M5_gal @ q_icrs
    q_ecl = M5_ecl @ q_icrs
    norm2 = float(np.dot(q_icrs, q_icrs))
    sh = stf_shape_fn(stf_matrix_fn(q_icrs))
    # Component index 1 in E basis is diag(1, 1, -2)/sqrt(6), exact z-axisymmetric Y_{20} mode!
    return {
        "norm_uasyr": float(np.sqrt(norm2)),
        "vec_icrs": q_icrs.tolist(),
        "vec_gal": q_gal.tolist(),
        "vec_ecl": q_ecl.tolist(),
        "signed_chi": float(sh["signed_chi"]),
        "ecliptic_m0_axisymmetric_fraction": float((q_ecl[1] ** 2) / max(norm2, 1e-30)),
        "galactic_m0_axisymmetric_fraction": float((q_gal[1] ** 2) / max(norm2, 1e-30)),
    }


def run_gaia_p6_analysis() -> dict:
    t0 = time.perf_counter()
    fiveview = _load_mod("r95_fiveview_geom", FIVEVIEW_PY)
    gaia_e2b2 = _load_mod("r95_gaia_e2b2", GAIA_E2B2_PY)
    E = fiveview.E

    R_gal = _build_icrs_to_frame_rotation("galactic")
    R_ecl = _build_icrs_to_frame_rotation("barycentrictrueecliptic")
    J16_gal, M5_gal = _build_j16(R_gal, E)
    J16_ecl, M5_ecl = _build_j16(R_ecl, E)
    oracle_gal = _verify_tangent_equivariance_oracle(R_gal, J16_gal, E, gaia_e2b2)
    oracle_ecl = _verify_tangent_equivariance_oracle(R_ecl, J16_ecl, E, gaia_e2b2)

    p_res = G03_DIR / "RESULT.json"
    p_deep = G03_DIR / "DEEP_SCANLAW_VLBA_RESULT.json"
    p_sf = G03_DIR / "SOLVER_FREE_RESEARCH_RESULT.json"
    p_quaia = R91_QUAIA
    d_res = json.loads(p_res.read_text())
    d_deep = json.loads(p_deep.read_text())
    d_sf = json.loads(p_sf.read_text())
    d_quaia = json.loads(p_quaia.read_text())

    # 1. Scanning-law quadrupole rotation to Ecliptic frame (should collapse to axisymmetric Y_20 mode!)
    scan_q_icrs = np.array(d_deep["gaia_scanning_law"]["delta_n_quad_stf5"], dtype=np.float64)
    scan_q_ecl = M5_ecl @ scan_q_icrs
    scan_q_gal = M5_gal @ scan_q_icrs
    scan_norm2 = float(np.dot(scan_q_icrs, scan_q_icrs))
    scan_ecl_m0_frac = float((scan_q_ecl[1] ** 2) / scan_norm2)

    # 2. Quaia 4 weighting models full frame & covariance transform
    quaia_models = {}
    M10_ecl = np.block([[M5_ecl, np.zeros((5, 5))], [np.zeros((5, 5)), M5_ecl]])
    M10_gal = np.block([[M5_gal, np.zeros((5, 5))], [np.zeros((5, 5)), M5_gal]])
    for wname, rec in d_quaia["fits"].items():
        beta = np.array(rec["coefs_microasyr"], dtype=np.float64)
        C10 = np.array(rec["jackknife_E2_B2_cov"], dtype=np.float64)
        eigs_C10 = np.linalg.eigvalsh(C10)
        C10_ecl = M10_ecl @ C10 @ M10_ecl.T
        C10_gal = M10_gal @ C10 @ M10_gal.T
        e2b2_icrs = beta[6:16]
        wald10_jk = float(e2b2_icrs @ np.linalg.solve(C10, e2b2_icrs))
        # Alignment cosine between E2 observed quadrupole and scanning-law density quadrupole
        e2_icrs = beta[6:11]
        cos_scan = float(np.dot(e2_icrs, scan_q_icrs) / (np.linalg.norm(e2_icrs) * np.linalg.norm(scan_q_icrs)))
        quaia_models[wname] = {
            "E1": _vector_gal_ecl_angles(beta[0:3], R_gal, R_ecl),
            "B1": _vector_gal_ecl_angles(beta[3:6], R_gal, R_ecl),
            "E2": _quad_summary(e2_icrs, M5_gal, M5_ecl, fiveview.stf_shape, fiveview.stf_matrix),
            "B2": _quad_summary(beta[11:16], M5_gal, M5_ecl, fiveview.stf_shape, fiveview.stf_matrix),
            "jk_10x10_E2B2_wald10": wald10_jk,
            "jk_10x10_min_eig": float(eigs_C10[0]),
            "ecliptic_jk_std_E2": np.sqrt(np.diag(C10_ecl)[:5]).tolist(),
            "galactic_jk_std_E2": np.sqrt(np.diag(C10_gal)[:5]).tolist(),
            "E2_cosine_with_scanlaw_density_quad": cos_scan,
        }

    # 3. Gaia-CRF3 subsets (all, quality, scanlaw-deprojected, and VLBA clean)
    named_subsets = {}
    subset_sources = {
        "gaia_all_1p61M": d_res["full_and_hemisphere_fits"]["all"]["coefs_microasyr"],
        "gaia_quality_1p20M": d_sf["part_a_joint_scanlaw_deprojection"]["vsh_16_without_scanlaw_uasyr"],
        "gaia_quality_scanlaw_deproj_1p20M": d_sf["part_a_joint_scanlaw_deprojection"]["vsh_16_with_scanlaw_deproj_uasyr"],
        "vlba_clean_651": d_sf["part_c_robust_covariance_and_vlba"]["vlba_and_normal_frame_projection"]["vlba_clean_5sigma"]["coefs_microasyr"],
    }
    for sname, vec in subset_sources.items():
        b = np.array(vec, dtype=np.float64)
        e2 = b[6:11]
        named_subsets[sname] = {
            "E1": _vector_gal_ecl_angles(b[0:3], R_gal, R_ecl),
            "B1": _vector_gal_ecl_angles(b[3:6], R_gal, R_ecl),
            "E2": _quad_summary(e2, M5_gal, M5_ecl, fiveview.stf_shape, fiveview.stf_matrix),
            "B2": _quad_summary(b[11:16], M5_gal, M5_ecl, fiveview.stf_shape, fiveview.stf_matrix),
            "E2_cosine_with_scanlaw_density_quad": float(np.dot(e2, scan_q_icrs) / (np.linalg.norm(e2) * np.linalg.norm(scan_q_icrs))),
        }

    # Note: Quaia z-tomography delta between z < 0.8 and z >= 2.1
    z_bins = d_sf["part_b_population_and_quaia_tomography"]["quaia_4bin_z_tomography"]
    vlba_vs_gaia = d_sf["part_c_robust_covariance_and_vlba"]["vlba_and_normal_frame_projection"]["gaia_jk_vs_vlba_chi2dof_scaled_cov"]

    out = {
        "schema": "htt.r95.gaia_p6_systematics_and_frame/1",
        "sources_sha256": {
            "G03_RESULT": _sha(p_res),
            "G03_DEEP_SCANLAW_VLBA": _sha(p_deep),
            "G03_SOLVER_FREE": _sha(p_sf),
            "R91_QUAIA_FULL_SELECTION": _sha(p_quaia),
        },
        "elapsed_seconds": time.perf_counter() - t0,
        "so3_tangent_equivariance_max_abs_err": {
            "galactic": oracle_gal,
            "ecliptic": oracle_ecl,
        },
        "scanning_law_quadrupole_frame_check": {
            "vec_icrs": scan_q_icrs.tolist(),
            "vec_ecl": scan_q_ecl.tolist(),
            "vec_gal": scan_q_gal.tolist(),
            "ecliptic_m0_axisymmetric_energy_fraction": scan_ecl_m0_frac,
        },
        "quaia_weighting_models_transformed": quaia_models,
        "gaia_and_vlba_subsets_transformed": named_subsets,
        "vlba_vs_gaia_jk_scaled_wald": vlba_vs_gaia,
        "quaia_redshift_contrast_summary": z_bins["z_lt_0p8_vs_ge_2p1_disjoint_contrast"],
        "physics_gates": {
            "sq_gaia_status": "DIAGNOSTIC_COMPLETED_SCOPED",
            "actual_normal_vorticity": None,
            "physical_Pi": None,
            "physical_GF": None,
            "cosmological_shear_or_vorticity_detection_claimed": False,
            "k04_k05_k06_status": "BLOCKED_DEPENDENCY",
            "exact_blocker": "No radial velocity or external-optical AGN selection null / true Gaia DR3 systematic covariance beyond 48-patch jackknife; B1 = Omega_frame - omega_cosmic spin-vorticity degeneracy.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_gaia_p6_analysis()
    print(json.dumps({
        "scan_ecl_m0_frac": res["scanning_law_quadrupole_frame_check"]["ecliptic_m0_axisymmetric_energy_fraction"],
        "oracle_gal": res["so3_tangent_equivariance_max_abs_err"]["galactic"],
        "quaia_inv_wald10_jk": res["quaia_weighting_models_transformed"]["inverse_noise"]["jk_10x10_E2B2_wald10"],
        "quaia_inv_E2_ecl_m0_frac": res["quaia_weighting_models_transformed"]["inverse_noise"]["E2"]["ecliptic_m0_axisymmetric_fraction"],
        "elapsed_s": res["elapsed_seconds"],
    }))
