"""R108 A7 SQ-LIE-FLUX: frame velocities with covariance (CMB, CF4), the R65 radio proxy, and the Codazzi flux map.

Purpose
    1. Frame measurements with covariance, in Galactic and ICRS Cartesian components:
       CMB  - Planck 2018 solar dipole (barycentre in CMB frame; registry key planck2018_solar_dipole);
       CF4  - coherent bulk velocity of the 0.01<z<0.1 CF4 groups (frame_cf4_joint.py), converted to the
              Planck 2018 CMB frame with registry keys only (cf4_t4_helio_to_cmb, planck2018_solar_dipole,
              both applied to data of release CF4_groups_J_ApJ_944_94_table4).
       The only candidate normal-frame flux direction is the CF4 matter-frame velocity relative to the CMB
       frame. Its comparison with zero and with the CMB dipole direction is a measured frame difference;
       no homogeneous-tilt interpretation is made (V03/V04).
    2. Radio: the R65 NVSS provider-peak common transverse count dipole (ICRS x,y only; the axial z component
       is unidentified by the ring-conditioned estimator) and the R65 shared peak-response proxy at
       alpha 0.5/0.75/1.0, with the R65 Poisson covariance and the R105 NSIDE-4 delete-one jackknife
       covariance. R65 labels the proxy 'provider peak-selected unresolved-source proxy; not a physical
       speed measurement'. It is reported only as a proxy compared with the CMB kinematic dipole
       (radio_proxy_comparisons). No radio frame velocity, radio flux candidate, radio-CF4 flux difference
       or radio flux-scale row is produced: that entry is BLOCKED (review-2 FRAME-1).
    3. The momentum (Codazzi) constraint map from STF-5 shear to normal flux in the PRODUCTION sign
       convention: kappa q = M s5 with M = -D, D s5 = D_j sigma^j_i = exact_momentum_divergence(sigma, a, n),
       i.e. D_j sigma^j_i + kappa q_i = 0 with q^i = T^{0i} (convention_bridge.exact_momentum_divergence;
       tilted_bianchi_state.evaluate_tilted_constraints and MomentumConstraintMap 'matrix @ shear = -kappa q').
       The R107 flux route, the tensor-state constraint evaluator, and the projected
       initial conditions are checked against this convention. Rank, singular values
       and every left-null (blind) flux direction are reported for
       the solver family atlas, including VI_-1/9 (PHY-05, TF5); rank < 2 maps report the whole blind subspace.
    4. The rank-aware Codazzi residual with the measured q needs an independently sourced shear with
       covariance, the structure constants and the orientation of the group frame; none is available,
       so that evaluation is reported as BLOCKED with the exact missing inputs.

Inputs (SHA-256 recorded in the output)
    R108 FRAME/CATALOGUE_FRAME_REGISTRY.json and FRAME/CF4_BULK_HDIPOLE_JOINT.json (this lane)
    R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json (R65 radio estimator output)
    R105_RESEARCH_20261124/RADIO_MATCHED_REFITS.json (NSIDE-4 jackknife covariance)
    R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json (PHY-05 recorded map), R105 CROSS_RESULTS.json
    htt/bass/background/{codazzi_tilt_rhs,constraints,convention_bridge,tilted_bianchi_state,initial_conditions}.py
        (code identity and located sign statements)

Units
    beta dimensionless (units of c); velocities km/s; structure constants and shear in the solver's
    geometric units (the map is linear in (a, n), singular values are quoted per unit structure scale).

Usage
    PYTHONPATH=.:htt:htt/src .venv/bin/python -m scripts.r108.frame_lie_flux \
        --output docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME/LIE_FLUX_FRAMES_V3.json
    Random shears for the sign-convention checks use numpy default_rng(20261124).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from obsstat.catalogue_frame_registry import C_KM_S, FrameRegistry
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

PUB = REPO / "docs/research_program/observational_publication_20261015"
REGISTRY_JSON = OUT_DIR / "FRAME/CATALOGUE_FRAME_REGISTRY.json"
CF4_JSON = OUT_DIR / "FRAME/CF4_BULK_HDIPOLE_JOINT.json"
CF4_RELEASE_ID = "CF4_groups_J_ApJ_944_94_table4"  # registry release whose bulk velocity is transformed
R65_JSON = PUB / "R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json"
R105_RADIO = PUB / "R105_RESEARCH_20261124/RADIO_MATCHED_REFITS.json"
DAG_JSON = PUB / "R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R105_CROSS = PUB / "R105_RESEARCH_20261124/CROSS_RESULTS.json"
CODE = ["htt/bass/background/codazzi_tilt_rhs.py", "htt/bass/background/constraints.py",
        "htt/bass/background/convention_bridge.py", "htt/bass/background/tilted_bianchi_state.py",
        "htt/bass/background/initial_conditions.py",
        "htt/bass/background/geometry.py", "htt/bass/transport/coupled_einstein_boltzmann.py",
        "htt/obsstat/catalogue_frame_registry.py", "htt/obsstat/publication_frame_kinematics.py",
        "scripts/r108/frame_lie_flux.py", "scripts/r108/frame_cf4_joint.py", "scripts/r108/frame_registry_build.py",
        "scripts/r108/common.py"]
OUTFILE = OUT_DIR / "FRAME/LIE_FLUX_FRAMES_V3.json"
CURV = 3e-4  # solver atlas structure scale (CoupledSolverConfig.curvature default)
CONVENTION_USED = ("production: kappa q_i = (M s5)_i with M = -D, where D s5 = D_j sigma^j_i = "
                   "exact_momentum_divergence(sigma, a, n, a_sign=+1) on the orthonormal STF-5 basis; equivalently "
                   "D_j sigma^j_i + kappa q_i = 0 with q^i = T^{0i} in the synchronous (-,+,+,+) tetrad")

# Located sign statements: (file, needle, meaning). Line numbers are found at run time.
PRODUCTION_SIGN_SOURCES = [
    ("htt/bass/background/convention_bridge.py", "D_j sigma^j_i + kappa q_i = 0",
     "exact_momentum_divergence docstring: q_i = T^{0i}, D_j sigma^j_i + kappa q_i = 0"),
    ("htt/bass/background/tilted_bianchi_state.py", "matrix @ shear_stf5 = -kappa*q_total",
     "MomentumConstraintMap convention"),
    ("htt/bass/background/tilted_bianchi_state.py", "G^{0i} = -D_j sigma^j_i == kappa T^{0i}",
     "evaluate_tilted_constraints derivation"),
    ("htt/bass/background/tilted_bianchi_state.py", "cod_vec = div_sig + kq",
     "evaluate_tilted_constraints executable residual div sigma + kappa q"),
    ("htt/bass/background/constraints.py", "return div_pstf2(sigma, geometry.Gamma) + kappa * matter.q",
     "normal-frame tensor residual div sigma + kappa q"),
    ("htt/bass/background/initial_conditions.py", "target = -kappa * q",
     "projected shear has div sigma = -kappa q"),
    ("htt/bass/background/codazzi_tilt_rhs.py", "+ κ q^A`` is evaluated",
     "per-axis momentum constraint described by the reduced module; its scalar gate measures Friedmann slack"),
]


def locate(rel: str, needle: str, meaning: str) -> dict:
    p = REPO / rel
    hits = [i for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1) if needle in ln]
    return {"file": rel, "lines": hits, "needle": needle, "meaning": meaning, "file_sha256": sha256_file(p)}


def icrs_to_gal_matrix() -> np.ndarray:
    from astropy.coordinates import SkyCoord
    cols = [SkyCoord(x=e[0], y=e[1], z=e[2], representation_type="cartesian", frame="icrs").galactic.cartesian.xyz.value
            for e in np.eye(3)]
    return np.array(cols).T


def lb(v) -> dict:
    v = np.asarray(v, float)
    r = float(np.linalg.norm(v))
    return {"norm": r, "l_deg": math.degrees(math.atan2(v[1], v[0])) % 360.0,
            "b_deg": math.degrees(math.asin(v[2] / r)) if r > 0 else float("nan")}


def wald(d, C) -> float:
    d = np.asarray(d, float)
    return float(d @ np.linalg.solve(np.asarray(C, float), d))


def angle2d(u, v) -> float:
    u, v = np.asarray(u, float), np.asarray(v, float)
    return float(np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))


def sign_fixed(v) -> np.ndarray:
    """Unit vector with its largest-magnitude component positive (a sign convention for null vectors)."""
    v = np.asarray(v, float)
    return v * np.sign(v[np.argmax(abs(v))])


# ---------------------------------------------------------------------------------------
# Codazzi map
# ---------------------------------------------------------------------------------------
def codazzi_div_map(a, n) -> np.ndarray:
    """3x5 matrix D with D s5 = div sigma = D_j sigma^j_i (exact_momentum_divergence) on the orthonormal STF-5 basis.

    D equals tilted_bianchi_state.momentum_constraint_map(alg).matrix, whose convention is
    ``matrix @ s5 = -kappa q`` (production). The flux map is :func:`codazzi_flux_map` = -D.
    """
    from bass.background.convention_bridge import exact_momentum_divergence
    from common.stf_metric_bridge import orthonormal_to_stf_matrix
    return np.column_stack([exact_momentum_divergence(orthonormal_to_stf_matrix(e, convention="kinematic_response"),
                                                      np.asarray(a, float), np.asarray(n, float), a_sign=1)
                            for e in np.eye(5)])


def codazzi_flux_map(a, n) -> np.ndarray:
    """3x5 matrix M with kappa q = M s5 in the production convention (D_j sigma^j_i + kappa q_i = 0): M = -D."""
    return -codazzi_div_map(a, n)


def map_spectrum(M, rtol=1e-12) -> dict:
    U, s, Vt = np.linalg.svd(M)
    scale = max(float(s[0]), 1e-300)
    rank = int(np.sum(s > rtol * scale))
    left_null = U[:, rank:].T  # rows: orthonormal basis of the flux directions no shear can produce
    return {"singular_values": s.tolist(), "rank": rank, "relative_threshold": rtol,
            "left_null_directions": left_null.tolist(), "left_null_dimension": int(left_null.shape[0]),
            "right_null_dimension": int(5 - rank),
            "sigma_min_over_sigma_max_in_range": float(s[rank - 1] / s[0]) if rank > 0 else None}


def blind_flux_report(M, alg_a, alg_n, spec: dict) -> dict:
    """All left-null (blind) flux directions with their count (review-2 FRAME-4)."""
    null = [sign_fixed(v) for v in spec["left_null_directions"]]
    dim = len(null)
    out = {"blind_flux_dimension": dim, "blind_flux_basis": [v.tolist() for v in null]}
    if dim == 0:
        out["blind_flux_note"] = "full rank: no blind flux direction"
    elif dim == 1:
        ell = null[0]
        evals, evecs = np.linalg.eigh(alg_n)
        ahat = alg_a / np.linalg.norm(alg_a) if np.linalg.norm(alg_a) > 0 else np.zeros(3)
        out.update({"blind_flux_direction": ell.tolist(), "blind_dot_a_hat": float(ell @ ahat),
                    "blind_in_n_eigenbasis": {"n_eigenvalues": evals.tolist(), "components": (evecs.T @ ell).tolist()},
                    "blind_residual_norm_ellT_M": float(np.linalg.norm(ell @ M)),
                    "blind_flux_note": "one blind direction (unique up to sign; largest component taken positive)"})
    else:
        out["blind_residual_norm_basisT_M"] = float(np.linalg.norm(np.asarray(null) @ M))
        out["blind_flux_note"] = ("map identically zero: every flux direction is blind; the basis is arbitrary"
                                  if dim == 3 else f"{dim}-dimensional blind subspace; the basis is not unique")
    return out


def family_algebras(curv: float = CURV) -> dict:
    """Solver-atlas algebras (coupled_einstein_boltzmann.build_early_family_state construction)."""
    from bass.background.bianchi_types import BianchiAlgebra, build_bianchi_algebra, build_structure_tensor
    out = {"FLRW": build_bianchi_algebra("I"), "I": build_bianchi_algebra("I"),
           "V": build_bianchi_algebra("V", a_twist=curv)}
    base = build_bianchi_algebra("VII_h", a_twist=0.5 * curv, n1=curv, n3=curv)
    out["VII_h(+1)"] = base
    out["VII_h(-1)"] = BianchiAlgebra(type_name="VII_h", a=base.a.copy(), n=-base.n,
                                      C=build_structure_tensor(base.a, -base.n), h_parameter=base.h_parameter,
                                      class_label="B", h_convention=base.h_convention,
                                      axis_permutation=base.axis_permutation, branch_policy=base.branch_policy)
    out["VI_h"] = build_bianchi_algebra("VI_h", a_twist=0.5 * curv, n1=curv, n3=-2.0 * curv)
    out["VI_-1/9"] = build_bianchi_algebra("VI_h", a_twist=(2.0 / 3.0) * curv, n1=curv, n3=-4.0 * curv)
    ix = build_bianchi_algebra("IX", n=curv)
    n_ix = np.diag([1.0 * curv, 1.15 * curv, 0.85 * curv])
    out["IX"] = BianchiAlgebra(type_name="IX", a=ix.a.copy(), n=n_ix, C=build_structure_tensor(ix.a, n_ix),
                               h_parameter=None, class_label="A", h_convention=ix.h_convention,
                               axis_permutation=ix.axis_permutation, branch_policy=ix.branch_policy)
    return out


def sign_convention_audit(rng) -> dict:
    """Numerical check of the repository statements of the momentum constraint (production sign confirmed)."""
    from bass.background.bianchi_types import build_bianchi_algebra
    from bass.background.constraints import MatterNormalFrameState, codazzi_constraint_residual
    from bass.background.convention_bridge import LEVI_CIVITA_3D, exact_momentum_divergence
    from bass.background.geometry import build_geometry, div_pstf2, pstf_rank2
    from bass.background.initial_conditions import project_shear_to_codazzi

    alg = build_bianchi_algebra("VI_h", a_twist=(2.0 / 3.0) * CURV, n1=CURV, n3=-4.0 * CURV)
    geom = build_geometry(alg)
    worst_div = worst_we = 0.0
    for _ in range(20):
        s = rng.normal(size=(3, 3)); s = pstf_rank2(s + s.T) * CURV
        d_exact = exact_momentum_divergence(s, alg.a, alg.n, a_sign=1)
        d_geom = div_pstf2(s, geom.Gamma)
        q_we = 3.0 * s @ alg.a - np.einsum("ijk,jd,kd->i", LEVI_CIVITA_3D, s, alg.n)  # R107 GAP route / WE 1997
        scale = max(np.linalg.norm(d_exact), 1e-300)
        worst_div = max(worst_div, float(np.linalg.norm(d_exact - d_geom) / scale))
        worst_we = max(worst_we, float(np.linalg.norm(q_we + d_exact) / scale))
    # an admissible production state: its total q satisfies div sigma + kappa q = 0
    from bass.transport.coupled_einstein_boltzmann import build_early_family_state
    state, _, _ = build_early_family_state("VI_-1/9", epsilon=1e-5)
    div = exact_momentum_divergence(state.sigma_ab, state.algebra.a, state.algebra.n, a_sign=1)
    kq = state.kappa * state.total_matter.q
    res_constraints = codazzi_constraint_residual(state.sigma_ab, MatterNormalFrameState(
        rho=state.total_matter.rho, p=state.total_matter.p, q=state.total_matter.q), state.geometry, kappa=state.kappa)
    sc = max(float(np.linalg.norm(div)), 1e-300)
    # initial_conditions.project_shear_to_codazzi on a full-rank VI_h algebra: which sign does it target?
    alg_ic = build_bianchi_algebra("VI_h", a_twist=0.5 * CURV, n1=CURV, n3=-2.0 * CURV)
    q_ic = rng.normal(size=3) * 1e-6
    sig_ic, meta_ic = project_shear_to_codazzi(sigma_ab=np.zeros((3, 3)), geometry=build_geometry(alg_ic),
                                               target_q=q_ic, kappa=1.0)
    div_ic = exact_momentum_divergence(sig_ic, alg_ic.a, alg_ic.n, a_sign=1)
    nq = float(np.linalg.norm(q_ic))
    return {
        "div_pstf2_vs_exact_momentum_divergence_max_rel": worst_div,
        "R107_route_q_equals_minus_div_sigma_max_rel": worst_we,
        "production_state_VI_-1/9_eps1e-5": {
            "norm_div_sigma": float(np.linalg.norm(div)), "norm_kappa_q": float(np.linalg.norm(kq)),
            "production_residual_div_plus_kappa_q_rel": float(np.linalg.norm(div + kq) / sc),
            "constraints_helper_residual_rel": float(np.linalg.norm(res_constraints) / sc),
            "state_constraint_report_codazzi_norm": float(state.constraints.codazzi_residual_norm)},
        "initial_conditions_projection_VI_h_full_rank": {
            "kappa": 1.0, "norm_target_q": nq, "projection_rank": int(meta_ic.rank),
            "div_sigma_minus_kappa_q_rel": float(np.linalg.norm(div_ic - q_ic) / nq),
            "production_residual_div_plus_kappa_q_rel": float(np.linalg.norm(div_ic + q_ic) / nq),
            "reading": "target_q is physical normal flux; compare both signed residuals"},
        "statement": {
            "convention_bridge.exact_momentum_divergence docstring / tilted_bianchi_state.evaluate_tilted_constraints "
            "/ MomentumConstraintMap": "div sigma + kappa q = 0  =>  kappa q = -div sigma (production solver states)",
            "R107 GAP_REGISTER SQ-LIE-FLUX route (WE97/HBW01 form)": "q = 3 sigma a - eps sigma n = -div sigma",
            "constraints.py codazzi_constraint_residual": "div sigma + kappa q",
            "initial_conditions.project_shear_to_codazzi": "div sigma = -kappa q",
            "codazzi_tilt_rhs": "the reduced six-variable diagnostic measures negative Friedmann slack",
        },
        "consequence": "Map polarity fixes the physical shear or flux direction. Singular values and blind subspaces are sign invariant.",
    }


# ---------------------------------------------------------------------------------------
def run(output: Path) -> dict:
    t0 = time.perf_counter()
    rng = np.random.default_rng(20261124)
    Mg = icrs_to_gal_matrix()
    reg = FrameRegistry.from_json(REGISTRY_JSON)

    # ---- CMB frame ----
    pl = reg.references["planck2018_solar_dipole"]
    b_cmb_g = pl.beta
    C_cmb_g = np.asarray(pl.covariance_galactic)
    b_cmb_i = Mg.T @ b_cmb_g
    C_cmb_i = Mg.T @ C_cmb_g @ Mg

    # ---- radio count-dipole proxy (R65 provider peak): a proxy, never a frame velocity ----
    r65 = json.loads(R65_JSON.read_text())
    mod = r65["models"]["provider_peak_dipole"]
    d_xy = np.asarray(mod["common_transverse_fit"]["estimate"])
    Cd_p = np.asarray(mod["common_transverse_fit"]["covariance"])
    r105 = json.loads(R105_RADIO.read_text())
    Cjk4 = np.asarray(r105["spatial_deletions"]["4"]["dipole"]["joint_covariance_peak_xy_integrated_xy"])[:2, :2]
    Cjk8 = np.asarray(r105["spatial_deletions"]["8"]["dipole"]["joint_covariance_peak_xy_integrated_xy"])[:2, :2]
    meanings = sorted({d["meaning"] for d in mod["conditional_peak_response_diagnostics"].values()})
    radio = {"estimator": "R65 ring-conditioned multinomial, provider peak flux bins 20-40/40-80/>=80 mJy, "
                          "common transverse dipole (ICRS x,y); axial z unidentified",
             "status": "PROXY: R65 count-dipole response proxy; not a frame velocity",
             "r65_meaning": meanings,
             "r65_meaning_locator": ("R65_DIPOLE_ANOMALY_20261117/RESULTS/PROVIDER_NVSS_RESULT.json "
                                     "models.provider_peak_dipole.conditional_peak_response_diagnostics[alpha].meaning"),
             "log_intensity_dipole_xy": d_xy.tolist(),
             "covariance_poisson_R65": Cd_p.tolist(),
             "covariance_jackknife_nside4_R105": Cjk4.tolist(),
             "covariance_jackknife_nside8_R105": Cjk8.tolist(),
             "jackknife4_over_poisson_trace": float(np.trace(Cjk4) / np.trace(Cd_p)),
             "shared_peak_proxy_beta_by_alpha": {}}
    proxy_cmp = {}
    for alpha, diag in sorted(mod["conditional_peak_response_diagnostics"].items()):
        fit = diag["shared_peak_proxy_beta_fit"]
        bxy = np.asarray(fit["estimate"]); Cb = np.asarray(fit["covariance"])
        k = float(np.trace(Cb) / np.trace(Cd_p))
        Cb_jk = k * Cjk4
        radio["shared_peak_proxy_beta_by_alpha"][alpha] = {
            "proxy_beta_xy_icrs": bxy.tolist(), "covariance_poisson": Cb.tolist(),
            "covariance_jackknife4_scaled": Cb_jk.tolist(), "jackknife_scaling": "trace(C_beta,P)/trace(C_d,P) x C_d,jk4",
            "per_bin_response": diag["response"], "proxy_beta_xy_norm": float(np.linalg.norm(bxy)),
            "meaning": diag["meaning"]}
        # proxy compared with the CMB kinematic dipole (transverse ICRS x,y); not a speed difference
        dlt = bxy - b_cmb_i[:2]
        Cc = C_cmb_i[:2, :2]
        proxy_cmp[f"radio_count_dipole_proxy_minus_cmb_xy_alpha_{alpha}"] = {
            "delta_proxy_beta_xy_icrs": dlt.tolist(),
            "wald_poisson_2dof": wald(dlt, Cb + Cc), "wald_jackknife4_2dof": wald(dlt, Cb_jk + Cc),
            "proxy_over_cmb_transverse_beta_ratio": float(np.linalg.norm(bxy) / np.linalg.norm(b_cmb_i[:2])),
            "angle_xy_deg": angle2d(bxy, b_cmb_i[:2]),
            "meaning": (f"R65: '{diag['meaning']}'. Proxy amplitude compared with the CMB kinematic dipole under the "
                        "R65 response law; not a speed and not a frame-velocity difference")}
    ratios = [v["proxy_over_cmb_transverse_beta_ratio"] for v in proxy_cmp.values()]

    # ---- CF4 frame ----
    cf4 = json.loads(CF4_JSON.read_text())
    cf4_frames = {}
    for cname in ("working", "working_plus_calibration"):
        for mname in ("MB_bulk", "MBH_bulk_plus_expansion_dipole"):
            e = cf4["results"][cname][mname]["bulk_kms"]
            B_g = np.asarray(e["galactic"]); C_g = np.asarray(e["galactic_cov"])
            # release CMB frame -> barycentre -> Planck 2018 CMB frame, registry keys on CF4-release data only
            b_sun = reg.velocity_to_moving("cf4_t4_helio_to_cmb", B_g / C_KM_S, release_id=CF4_RELEASE_ID)
            b_pl = reg.velocity_to_rest("planck2018_solar_dipole", b_sun, release_id=CF4_RELEASE_ID)
            cf4_frames[f"{mname}|{cname}"] = {
                "B_release_cmb_frame_galactic_kms": B_g.tolist(), "B_cov_galactic_kms2": C_g.tolist(),
                "B_planck2018_frame_galactic_kms": (b_pl * C_KM_S).tolist(),
                "planck_minus_release_kms": ((b_pl * C_KM_S) - B_g).tolist(),
                "direction_planck_frame": lb(b_pl * C_KM_S),
                "amplitude_sd_linear_kms": e["amplitude_sd_linear"]}
    fsys = cf4["frame_convention_systematic"]["variants"]["exact_relativistic_planck2018_beta"]["MB_bulk"]["bulk_kms"]
    cf4_frames["MB_bulk|working|exact_relativistic_planck2018_redshifts"] = {
        "B_planck2018_frame_galactic_kms": fsys["galactic"], "direction_planck_frame": lb(fsys["galactic"]),
        "note": "bulk re-fitted after converting every heliocentric Vh exactly with the Planck 2018 beta (registry)"}

    # ---- candidate q direction (CF4 only) and measured differences ----
    cand = {}
    main = cf4_frames["MB_bulk|working"]
    q_cf4 = np.asarray(main["B_planck2018_frame_galactic_kms"]) / C_KM_S
    Cq_cf4 = np.asarray(main["B_cov_galactic_kms2"]) / C_KM_S ** 2
    cand["cf4_matter_in_cmb_frame"] = {"beta_galactic": q_cf4.tolist(), "cov_galactic": Cq_cf4.tolist(),
                                       "direction": lb(q_cf4), "speed_kms": float(np.linalg.norm(q_cf4) * C_KM_S),
                                       "source": "MB_bulk|working (CF4 0.01<z<0.1 groups), Planck 2018 frame"}
    diffs = {}
    dq3 = q_cf4  # CF4 bulk relative to the CMB frame itself
    diffs["cf4_q_vs_zero_3dof"] = {"wald": wald(dq3, Cq_cf4), "speed_kms": float(np.linalg.norm(dq3) * C_KM_S)}
    diffs["cf4_q_vs_cmb_dipole_direction_deg"] = float(np.degrees(np.arccos(np.clip(q_cf4 @ b_cmb_g / np.linalg.norm(q_cf4) / np.linalg.norm(b_cmb_g), -1, 1))))

    # ---- Codazzi map (production sign), ranks, blind directions ----
    from bass.background.tilted_bianchi_state import momentum_constraint_map
    algs = family_algebras()
    fam = {}
    for name, alg in algs.items():
        M = codazzi_flux_map(alg.a, alg.n)
        prod = momentum_constraint_map(alg)
        scale = max(float(np.linalg.norm(alg.a)), float(np.linalg.norm(alg.n)), 1e-300)
        spec = map_spectrum(M)
        entry = {"a": alg.a.tolist(), "n": alg.n.tolist(), "structure_scale": scale,
                 "M_sigma_to_kappa_q_production": M.tolist(),
                 "max_abs_M_plus_production_divergence_matrix": float(np.max(abs(M + prod.matrix))),
                 "production_rank": int(prod.rank), **spec,
                 "singular_values_per_unit_structure_scale": (np.asarray(spec["singular_values"]) / scale).tolist()}
        entry.update(blind_flux_report(M, alg.a, alg.n, spec))
        fam[name] = entry
    # VI_-1/9 cross-checks: R75/R49 example algebra and the R78 PHY-05 recorded matrix
    a75 = np.array([0.005, 0.0, 0.0]); n75 = np.diag([0.0, 0.01, -0.0225])
    M75 = codazzi_flux_map(a75, n75)
    sp75 = map_spectrum(M75)
    dag = json.loads(DAG_JSON.read_text())
    phy05 = next(n for n in dag["nodes"] if n.get("id") == "PHY-05")["observable_evidence"]
    M78 = np.asarray(phy05["exceptional_M_signed_STF5_to_u"], float)
    sp78 = map_spectrum(M78)
    ell78 = np.asarray(phy05["exceptional_left_normal_flux_constraint"], float); ell78 /= np.linalg.norm(ell78)
    vi = fam["VI_-1/9"]
    vi19 = {
        "solver_atlas_algebra": {"a": vi["a"], "n": vi["n"], "rank": vi["rank"], "singular_values": vi["singular_values"],
                                 "blind_flux_dimension": vi["blind_flux_dimension"],
                                 "blind_flux_direction": vi.get("blind_flux_direction")},
        "R75_R49_example_algebra": {"a": a75.tolist(), "n_diag": [0.0, 0.01, -0.0225], "rank": sp75["rank"],
                                    "singular_values": sp75["singular_values"],
                                    "blind_flux_dimension": sp75["left_null_dimension"],
                                    "blind_flux_direction": (sign_fixed(sp75["left_null_directions"][0]).tolist()
                                                             if sp75["left_null_dimension"] == 1 else None)},
        "R78_PHY05_recorded_matrix": {"rank": sp78["rank"], "singular_values": sp78["singular_values"],
                                      "left_null_recorded_normalised": ell78.tolist(),
                                      "left_null_recomputed": (sign_fixed(sp78["left_null_directions"][0]).tolist()
                                                               if sp78["left_null_dimension"] == 1 else None),
                                      "recorded_residual_norm": float(np.linalg.norm(ell78 @ M78)),
                                      "note": "rank, singular values and left-null space are independent of the sign "
                                              "convention of the recorded matrix"},
        "frame_note": ("each blind direction is expressed in its own algebra (group-invariant) frame; mapping it to Galactic "
                       "axes needs the orientation of that frame, which no registry entry measures"),
    }

    audit = sign_convention_audit(rng)

    # conditional scale of the flux test: |kappa q|/(3 H^2) = Omega_m gamma^2 |beta| for dust (CF4 bulk only)
    planck_omega_m = 0.3153  # Planck 2018 VI Table 2 (TT,TE,EE+lowE+lensing); also htt/workspace/data/obs_defaults.json
    scale_rows = {}
    q = float(np.linalg.norm(q_cf4))
    scale_rows["cf4"] = {"beta": q, "kappa_q_over_3H2": planck_omega_m * q / (1 - q * q),
                         "min_shear_over_H_per_unit_structure_over_H_by_family": {
                             f: (3.0 * planck_omega_m * q / (1 - q * q) / max(e["singular_values_per_unit_structure_scale"][0], 1e-300)
                                 if e["rank"] > 0 else None) for f, e in fam.items()}}

    payload = {
        "schema": "htt.r108.frame.lie_flux_frames/3",
        "node": "SQ-LIE-FLUX (handoff A7); PHY-05 blind direction",
        "labels": {"frames_and_differences": "CONDITIONAL (CMB published dipole; CF4 working covariance)",
                   "radio_proxy_comparisons": ("CONDITIONAL (R65 proxy response law; Poisson or jackknife covariance; "
                                               "ICRS z unidentified); a proxy, not a speed"),
                   "radio_frame_velocity": "BLOCKED",
                   "codazzi_map_ranks_blind_directions": "NUMERICAL",
                   "codazzi_residual_with_measured_q": "BLOCKED",
                   "flux_scale_table": "CONDITIONAL (CF4 bulk only; Omega_m and unmeasured structure scale / orientation)"},
        "git": git_state(), "command": " ".join(sys.argv),
        "inputs": {p.name: {"path": str(p.relative_to(REPO)), "sha256": sha256_file(p)}
                   for p in (REGISTRY_JSON, CF4_JSON, R65_JSON, R105_RADIO, DAG_JSON, R105_CROSS)},
        "code_sha256": {c: sha256_file(REPO / c) for c in CODE},
        "frames": {
            "cmb": {"key": "planck2018_solar_dipole", "beta_galactic": b_cmb_g.tolist(), "cov_galactic": C_cmb_g.tolist(),
                    "beta_icrs": b_cmb_i.tolist(), "cov_icrs": C_cmb_i.tolist(), "direction": lb(b_cmb_g),
                    "speed_kms": float(np.linalg.norm(b_cmb_g) * C_KM_S), "locator": pl.locator},
            "cf4": cf4_frames,
            "registry_release_for_cf4_transforms": CF4_RELEASE_ID},
        "radio_count_dipole_proxy": radio,
        "radio_proxy_comparisons": proxy_cmp,
        "candidate_flux_directions": cand,
        "measured_differences": diffs,
        "interpretation_boundary": ("a q difference between frames is a measured frame difference; it is not a detection of a "
                                    "homogeneous tilt (V03/V04) and carries no Bianchi family attribution; the radio proxy "
                                    "is not a frame velocity"),
        "codazzi": {"convention_used": CONVENTION_USED,
                    "production_sign_sources": [locate(*x) for x in PRODUCTION_SIGN_SOURCES],
                    "sign_convention_audit": audit, "families": fam, "VI_-1/9": vi19,
                    "flux_scale_table": {"omega_m": planck_omega_m,
                                         "omega_m_locator": "Planck 2018 VI (A&A 641, A6) Table 2; htt/workspace/data/obs_defaults.json",
                                         "rows": scale_rows,
                                         "meaning": "minimum |sigma|/H (largest singular direction) needed to source the measured |q| if the "
                                                    "structure scale |a|,|n| were H; scale linearly by H/structure scale; blind directions need "
                                                    "infinite shear; sign invariant (largest singular value)"}},
        "blocked": {
            "codazzi_residual_with_measured_q": [
                "independently sourced normal-frame shear sigma_ab/H with covariance (no data product in the repository)",
                "structure constants (a, n)/H of the candidate family (not measured)",
                "orientation of the group-invariant frame relative to Galactic axes (not in the frame registry)",
                "identification of the normal frame among the CMB and CF4 frames",
                "Hamiltonian-constraint consistency inputs (Omega_k, Sigma^2 of the same state)"],
            "radio_frame_velocity": {
                "status": "BLOCKED",
                "reason": (f"no physical radio-source frame velocity exists in the repository: the R65 shared peak-response "
                           f"fit is labelled {meanings!r} by R65, and its transverse amplitude is "
                           f"{min(ratios):.2f}-{max(ratios):.2f} times the CMB kinematic value (radio_proxy_comparisons)"),
                "not_produced": ["radio candidate flux direction", "radio minus CF4 flux difference",
                                 "radio rows of the Codazzi flux-scale table"],
                "needed": ["a radio estimator whose output is a calibrated frame velocity with covariance (source-count "
                           "slope and spectral-index calibration of the response, clustering dipole separated)",
                           "the axial ICRS z component (unidentified by the R65 ring-conditioned estimator)"]},
            "radio_axial_component": "R65 ring-conditioned estimator leaves the ICRS z dipole unidentified",
        },
        "runtime_s": time.perf_counter() - t0,
    }
    write_json(output, payload)
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", type=Path, default=OUTFILE)
    a = ap.parse_args(argv)
    p = run(a.output)
    fam = {k: {"rank": v["rank"], "sv_unit": [round(x, 6) for x in v["singular_values_per_unit_structure_scale"]],
               "blind_dim": v["blind_flux_dimension"], "blind": v.get("blind_flux_direction"),
               "dM": v["max_abs_M_plus_production_divergence_matrix"]}
           for k, v in p["codazzi"]["families"].items()}
    print(json.dumps({"families": fam, "VI_-1/9": p["codazzi"]["VI_-1/9"], "audit": p["codazzi"]["sign_convention_audit"],
                      "differences": p["measured_differences"], "radio_proxy": p["radio_proxy_comparisons"],
                      "cf4": {k: v.get("direction_planck_frame") for k, v in p["frames"]["cf4"].items()},
                      "candidates": {k: v.get("direction") for k, v in p["candidate_flux_directions"].items()}},
                     indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
