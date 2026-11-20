"""R89 G04_RADIO_FRAME bounded source diagnostics for SQ-FRAME and SQ-RADIO.

Reuses:
- htt.obsstat.publication_frame_kinematics (Lorentz/Fermi frame identities, radial_operator)
- htt.obsstat.p4_bianchi_fast (source_conditional_local_global_rank, prepare_ring_source, batch_ring_occ)
- htt.obsstat.phy_fast.shared_beta_radio_photon (kinematic radio-photon second-order algebraic identity)

Write scope: create-only under R89/.../runs/G04_RADIO_FRAME/.
Does NOT fit cosmic beta_MO/shear/tilt or claim V04-V06 acceptance or qualified physical Pi.
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

from astropy import units as u
from astropy.coordinates import SkyCoord
import numpy as np

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p4_bianchi_fast as p4
from htt.obsstat import phy_fast
from htt.obsstat import publication_frame_kinematics as pfk
from scripts.r84.bench_baseline import axes as fib_axes

PROG = ROOT / "docs/research_program/observational_publication_20261015"
R63_DIR = PROG / "R63_LOCAL_BOOST_GLOBAL_TILT_20261117/RESULTS"
R65_DIR = PROG / "R65_DIPOLE_ANOMALY_20261117/RESULTS"
R74_RES = PROG / "R74_P4_SOURCE_SCORE_FIVEVIEW_20261119/RESULTS.json"

R63_FRAME_NPZ = R63_DIR / "OBSERVED/FRAME_HISTORY_CARRIERS.npz"
R63_INTERP = R63_DIR / "INTERPRETATION_SUMMARY.json"
R65_CARRIER = R65_DIR / "NVSS_CONDITIONAL_CARRIERS.npz"
R65_ORIG = R65_DIR / "NVSS_OBSERVED_RESULT.json"
R65_SUMMARY = R65_DIR / "INTERPRETATION_SUMMARY.json"
R65_PROV_CARRIER = R65_DIR / "PROVIDER_NVSS_CARRIERS.npz"
R65_PROV_RES = R65_DIR / "PROVIDER_NVSS_RESULT.json"

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"

C_KM_S = 299792.458
CMB_SPEED_KM_S = 369.82
THREADS = 12


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _cmb_axis_icrs() -> np.ndarray:
    cmb = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic").icrs
    vec = np.array(
        [
            np.cos(cmb.dec.rad) * np.cos(cmb.ra.rad),
            np.cos(cmb.dec.rad) * np.sin(cmb.ra.rad),
            np.sin(cmb.dec.rad),
        ],
        dtype=float,
    )
    return vec / np.linalg.norm(vec)


def _sq_frame_diagnostics() -> dict:
    """SQ-FRAME: proper Lorentz/Fermi identities + R63 local-vs-history carrier ranks."""
    cmb_axis = _cmb_axis_icrs()
    beta_ro = (CMB_SPEED_KM_S / C_KM_S) * cmb_axis
    # Illustrative oblique velocity probe (not an observed matter detection) to test Wigner non-collinearity.
    ortho_dir = np.cross(cmb_axis, np.array([0.0, 0.0, 1.0]))
    ortho_dir /= np.linalg.norm(ortho_dir)
    beta_rm_probe = (300.0 / C_KM_S) * (0.6 * cmb_axis + 0.8 * ortho_dir)

    pkt = pfk.source_frame_packet(beta_ro, beta_rm_probe)
    # Swapping arguments gives beta_{M in O}; comparing beta_MO against -beta_OM isolates noncollinear Wigner rotation.
    beta_om = pfk.relative_beta(beta_rm_probe, beta_ro)
    beta_mo = np.asarray(pkt["beta_MO"], dtype=float)
    wigner_vec_diff = float(np.linalg.norm(beta_mo + beta_om))
    speed_asym = float(abs(np.linalg.norm(beta_mo) - np.linalg.norm(beta_om)))
    u_mo = beta_mo / np.linalg.norm(beta_mo)
    u_neg_om = (-beta_om) / np.linalg.norm(beta_om)
    wigner_angle_rad = float(2.0 * np.arcsin(np.clip(0.5 * np.linalg.norm(u_mo - u_neg_om), 0.0, 1.0)))
    rap_sym_err = float(
        abs(pfk.rapidity_between(beta_ro, beta_rm_probe) - pfk.rapidity_between(beta_rm_probe, beta_ro))
    )

    grid_dirs = fib_axes(64)
    rad_op = pfk.radial_operator(grid_dirs)
    rad_sv = np.linalg.svd(rad_op, compute_uv=False)
    vort_w = np.array([0.12, -0.34, 0.56])
    vort_mat = pfk.antisymmetric_from_pseudovector(vort_w)
    vort_test_vec = np.array([-0.7, 0.2, 0.9])
    vort_identity_err = float(np.max(np.abs(vort_mat @ vort_test_vec - np.cross(vort_test_vec, vort_w))))
    vort_radial_null_maxabs = float(np.max(np.abs(np.einsum("ni,ij,nj->n", grid_dirs, vort_mat, grid_dirs))))
    assert speed_asym < 1e-15
    assert 1e-8 < wigner_angle_rad < 1e-5
    assert rap_sym_err < 1e-15
    assert vort_identity_err < 1e-15
    assert vort_radial_null_maxabs < 1e-15

    interp = json.loads(R63_INTERP.read_text(encoding="utf-8"))
    prefixes = ("log", "log_mono", "log_split", "log_survey")
    history_ranks: dict[str, dict] = {}
    with np.load(R63_FRAME_NPZ, allow_pickle=False) as zf:
        for pref in prefixes:
            cov32 = np.asarray(zf[f"{pref}__cov32"], dtype=float)
            eigs = np.linalg.eigvalsh(cov32)
            pref_block: dict[str, dict] = {
                "cov32_min_eigen": float(eigs[0]),
                "cov32_max_eigen": float(eigs[-1]),
                "cov32_condition": float(eigs[-1] / max(eigs[0], 1e-300)),
            }
            for order in ("J2", "J3"):
                rc = np.asarray(zf[f"{pref}__{order}__constant__response"], dtype=float)
                rf = np.asarray(zf[f"{pref}__{order}__free_history__response"], dtype=float)
                rr = np.asarray(zf[f"{pref}__{order}__rad_constant__response"], dtype=float)
                nb = np.asarray(zf[f"{pref}__{order}__endpoint_null_basis"], dtype=float)
                est_f = np.asarray(zf[f"{pref}__{order}__free_history__estimate"], dtype=float)
                cov_f = np.asarray(zf[f"{pref}__{order}__free_history__covariance"], dtype=float)
                pb = np.asarray(zf[f"{pref}__{order}__endpoint_pullback"], dtype=float)

                cf_rank = p4.source_conditional_local_global_rank(rc, rf, cov32)
                cr_rank = p4.source_conditional_local_global_rank(rc, rr, cov32)
                assert cf_rank["physical_Pi"] is None and cr_rank["physical_Pi"] is None

                # Keep theta_ep pullback/null-fibre checks separate from theta_f (V_p, W, d, K) global-history W=0 Wald test.
                pullback_rank = int(np.linalg.matrix_rank(pb))
                pullback_ortho_err = float(np.max(np.abs(pb @ nb)))
                assert pullback_ortho_err < 1e-11
                w_est = est_f[3:6]
                w_cov = cov_f[3:6, 3:6]
                w_wald_3dof = float(w_est.T @ np.linalg.solve(w_cov, w_est))

                order_entry = {
                    "constant_cols": int(rc.shape[1]),
                    "free_history_cols": int(rf.shape[1]),
                    "const_vs_free_history": cf_rank,
                    "const_vs_rad_constant": cr_rank,
                    "endpoint_pullback_rank": pullback_rank,
                    "endpoint_null_dim": int(nb.shape[1]),
                    "pullback_null_ortho_maxabs": pullback_ortho_err,
                    "free_history_W_wald_3dof": w_wald_3dof,
                }
                depth_key = f"{pref}__{order}__depth_calibration__response"
                if depth_key in zf.files:
                    rd = np.asarray(zf[depth_key], dtype=float)
                    cd_rank = p4.source_conditional_local_global_rank(rc, rd, cov32)
                    assert cd_rank["physical_Pi"] is None
                    order_entry["const_vs_depth_calibration"] = cd_rank
                pref_block[order] = order_entry
            history_ranks[pref] = pref_block

    return {
        "cmb_axis_icrs": cmb_axis.tolist(),
        "lorentz_fermi_identity_checks": {
            "beta_RO_norm": float(np.linalg.norm(beta_ro)),
            "rapidity_RO": float(pkt["rapidity_RO"]),
            "wigner_noncollinear_norm_diff": wigner_vec_diff,
            "wigner_speed_magnitude_asymmetry": speed_asym,
            "wigner_rotation_angle_rad": wigner_angle_rad,
            "rapidity_between_asymmetry": rap_sym_err,
            "physical_transfer_status": pkt["physical_transfer_status"],
            "radial_operator_shape": list(rad_op.shape),
            "radial_operator_rank_tol1e10": int(np.sum(rad_sv > 1e-10 * rad_sv[0])),
            "radial_operator_singular_values": rad_sv.tolist(),
            "antisymmetric_vorticity_null_dim": 3,
            "antisymmetric_cross_identity_maxerr": vort_identity_err,
            "antisymmetric_radial_null_maxabs": vort_radial_null_maxabs,
        },
        "r63_reference_summary": {
            "n_sources": interp["n_sources"],
            "z_range": interp["z_range"],
            "W_p_J2_original": interp["W_p_J2_original"],
            "W_p_J3_original": interp["W_p_J3_original"],
            "W_p_J2_corrected": interp["W_p_J2_corrected"],
            "W_p_J3_corrected": interp["W_p_J3_corrected"],
            "body_bound_km_s": interp["body"],
        },
        "frame_history_conditional_ranks": history_ranks,
        "physical_gate_status": "DIAGNOSTIC_COMPLETED_SCOPED",
        "physical_common_congruence_status": "BLOCKED_INPUT",
    }


def _run_mask_batch(
    name: str,
    directions: np.ndarray,
    groups_raw: np.ndarray,
    counts: np.ndarray,
    v_xy: np.ndarray,
    k_vec: np.ndarray,
    ax: np.ndarray,
) -> dict:
    """Prepare 3-bin ring carrier and evaluate 97-axis Fortran/NumPy batch_ring_occ."""
    _, groups = np.unique(groups_raw, return_inverse=True)
    # Verify non-zero bin counts per ring so conditioning denominator is well-posed.
    ring_count = int(groups.max()) + 1
    for b in range(counts.shape[0]):
        totals = np.bincount(groups, weights=counts[b], minlength=ring_count)
        assert np.all(totals > 0), f"{name} bin {b} has empty ring(s)"

    prep = p4.prepare_ring_source(directions, groups, counts, v_xy, k_vec)
    fast = p4.batch_ring_occ(directions, ax, prep, native_lib="auto", threads=THREADS)
    receipt = p4.last_p4_receipt()
    ref = p4.batch_ring_occ(directions, ax, prep, native_lib=None)
    err_f = float(np.max(np.abs(fast["F"] - ref["F"])))
    err_grad = float(np.max(np.abs(fast["gradient"] - ref["gradient"])))
    assert err_f < 2e-12 and err_grad < 2e-11, f"{name} parity failure: F={err_f}, grad={err_grad}"

    # Inspect peak directional gradient norm across the 96 quasi-uniform Fibonacci axes vs CMB axis.
    cmb_F = fast["F"][0].tolist()
    cmb_grad = fast["gradient"][0].tolist()
    grad_norms = np.linalg.norm(fast["gradient"][1:], axis=2)  # (96, 3)
    max_axis_idx = np.argmax(grad_norms, axis=0)
    max_grad_norms = [float(grad_norms[max_axis_idx[b], b]) for b in range(3)]
    cmb_grad_norms = [float(np.linalg.norm(fast["gradient"][0, b])) for b in range(3)]

    return {
        "pixels": int(len(directions)),
        "rings": ring_count,
        "flux_bin_totals": [int(counts[b].sum()) for b in range(3)],
        "k_vector": [float(x) for x in k_vec],
        "v_xy": v_xy.tolist(),
        "backend_receipt": receipt,
        "native_vs_numpy_maxabs": {"F": err_f, "gradient": err_grad},
        "cmb_axis": {
            "F": cmb_F,
            "gradient_3x3": cmb_grad,
            "gradient_bin_norms": cmb_grad_norms,
        },
        "fib96_summary": {
            "F_minmax": [float(np.min(fast["F"][1:])), float(np.max(fast["F"][1:]))],
            "max_gradient_norm_per_bin": max_grad_norms,
            "cmb_to_fib96_max_ratio_per_bin": [
                cmb_grad_norms[b] / max(max_grad_norms[b], 1e-30) for b in range(3)
            ],
        },
    }


def _disjoint_ring_subset(
    label: str,
    keep_ring_mask: np.ndarray,
    groups_inv: np.ndarray,
    directions: np.ndarray,
    counts: np.ndarray,
    v_xy: np.ndarray,
    k_vec: np.ndarray,
    ax_cmb_only: np.ndarray,
) -> dict:
    """Evaluate exact whole-ring subset preserving constant-declination conditioning strata."""
    px_mask = keep_ring_mask[groups_inv]
    sub_dirs = directions[px_mask]
    _, sub_groups = np.unique(groups_inv[px_mask], return_inverse=True)
    sub_counts = counts[:, px_mask]
    n_rings = int(sub_groups.max()) + 1
    prep = p4.prepare_ring_source(sub_dirs, sub_groups, sub_counts, v_xy, k_vec)
    res = p4.batch_ring_occ(sub_dirs, ax_cmb_only, prep, native_lib="auto", threads=THREADS)
    return {
        "label": label,
        "pixels": int(len(sub_dirs)),
        "rings": n_rings,
        "flux_bin_totals": [int(sub_counts[b].sum()) for b in range(3)],
        "cmb_F": res["F"][0].tolist(),
        "cmb_gradient_3x3": res["gradient"][0].tolist(),
        "cmb_gradient_bin_norms": [float(np.linalg.norm(res["gradient"][0, b])) for b in range(3)],
    }


def _sq_radio_diagnostics() -> dict:
    """SQ-RADIO: multi-mask/multi-selection NVSS ring scores + disjoint split + algebraic bridge."""
    cmb_axis = _cmb_axis_icrs()
    ax97 = np.vstack([cmb_axis, fib_axes(96)])
    r74 = json.loads(R74_RES.read_text(encoding="utf-8"))
    orig = json.loads(R65_ORIG.read_text(encoding="utf-8"))
    summ = json.loads(R65_SUMMARY.read_text(encoding="utf-8"))
    prov_res = json.loads(R65_PROV_RES.read_text(encoding="utf-8"))

    k_by_model = {t["model"]: np.asarray(t["peak_response_diagnostics"]["0.75"]["response"], dtype=float) for t in summ["nvss_tables"]}

    mask_runs: dict[str, dict] = {}
    with np.load(R65_CARRIER, allow_pickle=False) as zc:
        for mask_name in ("base64", "base32", "gal20", "clean64"):
            dirs = np.asarray(zc[f"{mask_name}_pixel_vectors"], dtype=float)
            groups_raw = np.asarray(zc[f"{mask_name}_groups"], dtype=np.int64)
            counts = np.asarray(zc[f"{mask_name}_counts"], dtype=np.int64)
            v_xy = np.array([q["estimate"][:2] for q in orig["models"][f"{mask_name}_dipole"]["independent_fits"]], dtype=float)
            k_vec = k_by_model[f"{mask_name}_dipole"]
            mask_runs[mask_name] = _run_mask_batch(mask_name, dirs, groups_raw, counts, v_xy, k_vec, ax97)

        # Verify exact base64 parity with R74_P4_SOURCE_SCORE_FIVEVIEW_20261119/RESULTS.json.
        r74_bins = r74["actual_R65_masked_F_response"]["source_geometry_and_exact_ring_z_null"]
        r74_parity = []
        for b in range(3):
            ref = r74_bins[f"bin_{b + 1}"]
            f_err = abs(mask_runs["base64"]["cmb_axis"]["F"][b] - float(ref["F_ring_predicted_at_beta0"]))
            g_err = float(
                np.max(
                    np.abs(
                        np.asarray(mask_runs["base64"]["cmb_axis"]["gradient_3x3"][b])
                        - np.asarray(ref["F_ring_kinematic_score_gradient"])
                    )
                )
            )
            assert f_err < 2e-13 and g_err < 2e-12
            r74_parity.append({"flux_bin": b + 1, "F_abs_err": f_err, "gradient_maxabs_err": g_err})

        # Disjoint whole-ring subsets on base64 geometry (preserving constant-declination ring strata).
        b64_dirs = np.asarray(zc["base64_pixel_vectors"], dtype=float)
        b64_counts = np.asarray(zc["base64_counts"], dtype=np.int64)
        _, b64_groups = np.unique(zc["base64_groups"], return_inverse=True)
        b64_v = np.array([q["estimate"][:2] for q in orig["models"]["base64_dipole"]["independent_fits"]], dtype=float)
        b64_k = k_by_model["base64_dipole"]
        n_b64_rings = int(b64_groups.max()) + 1
        ring_nz = np.array([float(np.mean(b64_dirs[b64_groups == ri, 2])) for ri in range(n_b64_rings)])
        ring_idx = np.arange(n_b64_rings)
        ax_cmb = cmb_axis[None, :]

        disjoint_splits = {
            "north_dec_ge_0": _disjoint_ring_subset("north_dec_ge_0", ring_nz >= 0.0, b64_groups, b64_dirs, b64_counts, b64_v, b64_k, ax_cmb),
            "south_dec_lt_0": _disjoint_ring_subset("south_dec_lt_0", ring_nz < 0.0, b64_groups, b64_dirs, b64_counts, b64_v, b64_k, ax_cmb),
            "even_rings": _disjoint_ring_subset("even_rings", (ring_idx % 2) == 0, b64_groups, b64_dirs, b64_counts, b64_v, b64_k, ax_cmb),
            "odd_rings": _disjoint_ring_subset("odd_rings", (ring_idx % 2) == 1, b64_groups, b64_dirs, b64_counts, b64_v, b64_k, ax_cmb),
        }

        # Provider peak vs integrated flux selection on aligned base64 geometry.
        with np.load(R65_PROV_CARRIER, allow_pickle=False) as zp:
            assert np.array_equal(zc["base64_pixel_indices"], zp["pixel_indices"])
            assert np.array_equal(zc["base64_groups"], zp["groups"])
            prov_runs = {}
            for p_key, m_key in (("provider_peak", "provider_peak_dipole"), ("provider_integrated", "provider_integrated_dipole")):
                p_counts = np.asarray(zp[f"{p_key}_counts"], dtype=np.int64)
                p_v = np.array([q["estimate"][:2] for q in prov_res["models"][m_key]["independent_fits"]], dtype=float)
                p_k = np.asarray(prov_res["models"][m_key]["conditional_peak_response_diagnostics"]["0.75"]["response"], dtype=float)
                prov_runs[p_key] = _run_mask_batch(p_key, b64_dirs, zc["base64_groups"], p_counts, p_v, p_k, ax97)

    # Kinematic second-order STF algebra bridge (algebraic identity only; source_qualified=False).
    beta_cmb = (CMB_SPEED_KM_S / C_KM_S) * cmb_axis
    stf_algebraic_bridge = {}
    for b in range(3):
        k_b = float(b64_k[b])
        for kappa_val in (0.0, 1.0):
            res = phy_fast.shared_beta_radio_photon(beta_cmb, k=k_b, kappa=kappa_val)
            stf_algebraic_bridge[f"bin_{b + 1}_kappa{int(kappa_val)}"] = {
                "k": k_b,
                "kappa": kappa_val,
                "A_selection": float(res["A_selection"]),
                "ratio_count_STF_to_photon_STF": float(res["ratio"]),
                "ratio_count_STF_to_log_count_STF": float(res["A_selection"] / (0.5 * (k_b + kappa_val))),
                "photon_chi": float(res["photon_chi"]),
                "photon_flux": res["photon_flux"].tolist(),
                "source_qualified": bool(res["source_qualified"]),
                "physical_Pi": res["physical_Pi"],
            }

    return {
        "mask_sensitivity_97axis": mask_runs,
        "provider_selection_97axis": prov_runs,
        "r74_base64_exact_parity": r74_parity,
        "base64_whole_ring_disjoint_splits": disjoint_splits,
        "provider_migration_and_paired_wald": {
            "migration_order": prov_res["migration_order"],
            "source_migration_counts_4x4": prov_res["source_migration_counts_4x4"],
            "paired_dipole_integrated_minus_peak": {
                k: prov_res["paired_comparisons"]["dipole"][k]
                for k in ("integrated_minus_peak", "marginal_sd", "poisson_source_linearized_wald", "df", "poisson_source_linearized_tail")
            },
            "paired_dipole_stf_integrated_minus_peak": {
                k: prov_res["paired_comparisons"]["dipole_stf"][k]
                for k in ("integrated_minus_peak", "marginal_sd", "poisson_source_linearized_wald", "df", "poisson_source_linearized_tail")
            },
        },
        "shared_beta_radio_photon_algebraic_check": stf_algebraic_bridge,
        "physical_gate_status": "DIAGNOSTIC_COMPLETED_SCOPED",
        "physical_LSS_and_joint_null_status": "BLOCKED_INPUT",
    }


def main() -> int:
    t0 = time.perf_counter()
    sq_frame = _sq_frame_diagnostics()
    sq_radio = _sq_radio_diagnostics()
    elapsed = time.perf_counter() - t0

    input_paths = (
        R63_FRAME_NPZ,
        R63_INTERP,
        R65_CARRIER,
        R65_ORIG,
        R65_SUMMARY,
        R65_PROV_CARRIER,
        R65_PROV_RES,
        R74_RES,
    )
    out = {
        "schema": "htt.r89.g04_radio_frame_bounded_source_diagnostics/1",
        "group_id": "G04_RADIO_FRAME",
        "node_ids": ["V01", "V02", "V03", "SQ-FRAME", "SQ-RADIO", "V04", "V05", "V06"],
        "source_sha256": {str(p.relative_to(ROOT)): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "threads": THREADS,
            "env_HTT_R84_SCORE_SO": os.environ.get("HTT_R84_SCORE_SO"),
        },
        "sq_frame_diagnostics": sq_frame,
        "sq_radio_diagnostics": sq_radio,
        "node_verdicts": {
            "V01": "REUSED_SCOPED",
            "V02": "REUSED_SCOPED",
            "V03": "REUSED_SCOPED",
            "SQ-FRAME": "DIAGNOSTIC_COMPLETED_SCOPED",
            "SQ-RADIO": "DIAGNOSTIC_COMPLETED_SCOPED",
            "V04": "BLOCKED_DEPENDENCY",
            "V05": "BLOCKED_DEPENDENCY",
            "V06": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "source-calibrated NVSS/RACS LSS clustering + flux-selection/multiplicity joint null covariance",
                "physical CF4/Gaia/NVSS common-congruence optical response and normal-frame velocity calibration",
                "certified CMB/radio joint null realization ensemble (blocking V04 -> V05 -> V06)",
            ],
            "next_action": "Obtain calibrated radio LSS/selection null and common-congruence frame transfer before V04-V06; proceed independently to G05_PLANCK verification",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")

    b64 = sq_radio["mask_sensitivity_97axis"]["base64"]
    print(json.dumps({
        "group_id": "G04_RADIO_FRAME",
        "elapsed_s": round(elapsed, 3),
        "maxrss_mib": round(out["runtime"]["maxrss_kib"] / 1024.0, 1),
        "sq_frame_log_J2_ranks": sq_frame["frame_history_conditional_ranks"]["log"]["J2"]["const_vs_free_history"],
        "sq_frame_log_J2_W_wald3": sq_frame["frame_history_conditional_ranks"]["log"]["J2"]["free_history_W_wald_3dof"],
        "nvss_base64_backend": b64["backend_receipt"]["used"],
        "nvss_base64_err": b64["native_vs_numpy_maxabs"],
        "r74_max_err_F": max(x["F_abs_err"] for x in sq_radio["r74_base64_exact_parity"]),
        "r74_max_err_grad": max(x["gradient_maxabs_err"] for x in sq_radio["r74_base64_exact_parity"]),
        "paired_dipole_wald": sq_radio["provider_migration_and_paired_wald"]["paired_dipole_integrated_minus_peak"]["poisson_source_linearized_wald"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
