"""Saved-law, solver-free R37-02 consumer. Run from any working directory.

No source producer is executed. The E1/B1, E2, and optical laws remain separate.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
B = ROOT / "docs/research_program/observational_publication_20261015"
F = B / "CONVERGENCE_20261028/imports/foundations"
R36 = B / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products"
GAIA = F / "sources/gaia/METHOD_EXECUTION_20261023__k03_depth_moments__RESULT.json"
GAIA_PRE = F / "lanes/GAIA_INFO.json"
PM = R36 / "R36-03-PM-HISTORY/RESULT.json"
OPT = R36 / "R36-04-OPTICAL-JOINT/RESULT.json"
P6 = B / "PUBLICATION_ACCELERATION_20261025/products/R32-05-P6-OPTICAL/repair_01/report/generated/retained_tensor_region.json"


def read(path):
    raw = path.read_bytes()
    return json.loads(raw), {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest()}


def load_optical_module():
    path = R36 / "R36-04-OPTICAL-JOINT/optical_joint.py"
    spec = importlib.util.spec_from_file_location("r36_optical_joint_pure", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def safe_joint_test(mod, o, s, d, budget, **kwargs):
    """R37 consumer guard for R36's squared-norm zero underflow.

    The frozen R36 profiler still supplies the common physical-ball minimum.
    Only its inverse split is corrected when a representable nonzero S was
    mistaken for zero. An unrepresentable inverse is an explicit domain error.
    """
    s = mod.validate_s(s)
    scale = float(np.max(np.abs(s)))
    result = mod.joint_test(o, s, d, budget, **kwargs)
    if scale == 0 or result.get("physical_set_empty"):
        return result
    if result["branch"] == "S_ZERO_DIRECT_MEMBERSHIP":
        unit = mod.lift_matrix(s / scale)
        denominator = mod.KAPPA * scale
        with np.errstate(over="raise", divide="raise", invalid="raise"):
            try:
                rhs = np.asarray(o, float) / denominator
                inverse = np.linalg.solve(unit.T @ unit, unit.T @ rhs)
                if not np.isfinite(inverse).all():
                    raise FloatingPointError("nonfinite inverse")
                k = mod.KAPPA * mod.lift_matrix(s)
                perpendicular = np.asarray(o, float) - k @ inverse
                parallel = k @ (inverse - np.asarray(result["profiled_d"]))
                psq = float(perpendicular @ perpendicular)
                lsq = float(parallel @ parallel)
                if not np.isfinite([psq, lsq]).all():
                    raise FloatingPointError("nonfinite inverse decomposition")
            except (FloatingPointError, OverflowError) as exc:
                raise ValueError("nonrepresentable nonzero-S inverse arithmetic") from exc
        result.update(branch="INVERTIBLE_S", inverse_d=inverse.tolist(),
                      perpendicular_squared=psq, parallel_squared=lsq)
    if result["branch"] == "INVERTIBLE_S" and not np.isfinite(result["inverse_d"]).all():
        raise ValueError("nonrepresentable nonzero-S inverse arithmetic")
    return result


def history_response(k):
    return np.column_stack((float(k) * np.eye(5), -np.eye(5)))


def quotient_support(center, fisher, radius, direction, threshold):
    """Support interval for E95(center,F) plus an STF5 Frobenius ball."""
    v = np.asarray(direction, float)
    center = np.asarray(center, float)
    if v.shape != (5,) or not np.isfinite(v).all() or not np.isfinite(radius) or radius < 0:
        raise ValueError("finite direction and nonnegative rate radius required")
    halfwidth = float(np.sqrt(threshold * (v @ np.linalg.solve(fisher, v))) + radius * np.linalg.norm(v))
    location = float(v @ center)
    return [location - halfwidth, location + halfwidth]


def profile(y, j, c, n):
    """GLS on one covariance, with a free linear nuisance."""
    l = np.linalg.cholesky(c)
    wj = np.linalg.solve(l, j)
    wn = np.linalg.solve(l, n)
    wy = np.linalg.solve(l, y)
    u, s, _ = np.linalg.svd(wn, full_matrices=False)
    rank = int(np.count_nonzero(s > s[0] * 1e-11))
    q = np.eye(len(y)) - u[:, :rank] @ u[:, :rank].T
    bj = q @ wj
    f = bj.T @ bj
    theta = np.linalg.solve(f, bj.T @ q @ wy)
    cov = np.linalg.inv(f)
    return theta, cov, f, q, l


def gaia_product(src, prior):
    y = np.asarray(src["full24_state_uasyr"], float)
    c = np.asarray(src["full24_cov_uasyr2"], float)
    z = np.asarray(src["depth_c_reported_z_centers"], float)
    assert y.shape == (24,) and c.shape == (24, 24)
    j = np.vstack((np.zeros((18, 6)), np.eye(6)))
    n = np.vstack((np.eye(18), np.zeros((6, 18))))
    theta, cov, f, _, _ = profile(y, j, c, n)
    np.testing.assert_allclose(theta, y[18:], atol=1e-10)
    np.testing.assert_allclose(cov, c[18:, 18:], atol=1e-10)
    np.testing.assert_allclose(f, np.asarray(src["F"]), atol=1e-10)
    t = np.zeros((18, 24))
    for i, zi in enumerate(z):
        t[6*i:6*i+6, 6*i:6*i+6] = np.eye(6)
        t[6*i:6*i+6, 18:] = zi * np.eye(6)
    yy, cy = t @ y, t @ c @ t.T
    np.testing.assert_allclose(yy, src["Y18_state_uasyr"], atol=2e-13)
    n18 = np.tile(np.eye(6), (3, 1))
    jg = np.vstack([zi*np.eye(6) for zi in z])
    jg2 = np.vstack([zi**2*np.eye(6) for zi in z])
    th, cv, ff, q, l = profile(yy, jg, cy, n18)
    np.testing.assert_allclose(th, prior["experiment2_constrained_bin_depth_family"]["theta_joint"], atol=1e-9)
    # A shared Gaussian law and nuisance projection for both response families.
    w = q @ np.linalg.solve(l, yy)
    a = q @ np.linalg.solve(l, jg)
    b = q @ np.linalg.solve(l, jg2)
    u, sv, _ = np.linalg.svd(np.column_stack((a, b)), full_matrices=False)
    r = int(np.count_nonzero(sv > sv[0]*1e-11))
    u = u[:, :r]
    dev = lambda v, m: float(np.linalg.norm(v-m@np.linalg.lstsq(m, v, rcond=None)[0])**2)
    lr_full = dev(w, a)-dev(w, b)
    lr_common = dev(u.T@w, u.T@a)-dev(u.T@w, u.T@b)
    uone = np.linalg.svd(a, full_matrices=False)[0]
    lr_single = dev(uone.T@w, uone.T@a)-dev(uone.T@w, uone.T@b)
    assert r == 12 and abs(lr_full-lr_common) < 1e-9
    assert abs(lr_full-prior["experiment2_constrained_bin_depth_family"]["observed_profile_deviance_difference_g_minus_g2"]) < 1e-8
    signed = yy.reshape(3, 6)
    powers = [float(v @ np.linalg.solve(cy[6*i:6*i+6, 6*i:6*i+6], v)) for i, v in enumerate(signed)]
    p1 = prior["experiment1_original_free_bin_slopes"]
    p2 = prior["experiment2_constrained_bin_depth_family"]
    return {
        "scope": "saved E1 polar xyz / B1 axial xyz Gaussian working law; reported-z bins; centroid field",
        "source_rows_reused": src["rows"], "units": "microarcsec/year",
        "free_bin_slope": {"signed_six": theta.tolist(), "covariance_6x6": cov.tolist(),
            "scalar_power": float(theta@f@theta), "profile_information_rank": 6,
            "T24_to18_information_rank_with_free_bin_nuisance": 0,
            "sign_pair": p1["sign_pair"], "matched_power": p1["power_and_information"],
            "joint_coverage": p1["coverage95"], "separate95_intersection": p1["common_confidence_event"],
            "invertible_tensor_max_parameter_difference": p1["tensorized_coordinate_theta_max_difference"]},
        "constrained_bin_depth": {"signed_bins_3x6": signed.tolist(), "per_bin_scalar_powers": powers,
            "joint_signed_g_slope": th.tolist(), "joint_covariance_6x6": cv.tolist(),
            "joint_information_6x6": ff.tolist(), "joint_coverage": p2["coverage95"],
            "matched_power": p2["power_at_mahalanobis_2p5"],
            "common_spin_glide_invariance_error": p2["frame_spin_glide_profile_invariance_error"],
            "g_vs_g2_common_rank": r, "full_deviance_difference": lr_full,
            "common_carrier_deviance_difference": lr_common,
            "single_g_score_deviance_difference": lr_single,
            "discarded_adequacy_deviance": lr_full-lr_single,
            "correct_joint_GLS_information_ceiling": "common response carrier preserves pairwise LR, adds no information"},
        "unavailable_physical_response": ["centroid-to-matter calibration", "true-depth law", "spatial covariance", "selection coverage", "radio frame calibration"]}


def pm_product(src):
    f = np.asarray(src["gram"]["primary_spin_glide6"]["profile"]["information"], float)
    ev, basis = np.linalg.eigh(f)
    assert ev[0] > 0 and len(ev) == 5
    center = np.asarray(src["gram"]["primary_spin_glide6"]["joint"]["selected_sample_full5_coefficients_uasyr"], float)
    threshold = src["power_frontier"]["chi2_threshold"]
    assert abs(threshold - 11.070497693516351) < 1e-12
    radii = [0., .5, 1., 1.5, 2.]
    widths = [[float(np.sqrt(threshold / lam) + r) for lam in ev] for r in radii]
    rows = []
    for item in src["history_images"]:
        k = item["k"]
        a = np.asarray(item["response_5x10"], float)
        ns = np.asarray(item["null_columns_10x5"], float)
        assert a.shape == (5, 10) and np.linalg.norm(a@ns) < 1e-10
        np.testing.assert_allclose(a, history_response(k), atol=0)
        rows.append({"k": k, "response_rank": int(np.linalg.matrix_rank(a)),
                     "null_dimension": 5, "identified_combination": f"{k} q_STF5 - s_STF5",
                     "q_definition": "(B_o-B_s)/T_ref", "s_definition": "dot B_o",
                     "null_fibre": "for any q in R5, s=k*q-u; delta_s=k*delta_q"})
    return {"scope": "separate E2/STF5 fixed-design first-order response; no joint E1/B1 cross-law",
            "profile_information_eigenvalues": ev.tolist(), "history_images": rows,
            "physical_parameterization": {"q": "(B_o-B_s)/T_ref", "s": "dot B_o", "k": "2*c*T_ref/D", "u": "k*q-s", "observed_a": "u+e", "units": "q,s,u,e,a in microarcsec/year; B dimensionless", "k_zero": "distant fixed-endpoint limit", "separate_endpoints": "common B_o,B_s shift adds five null directions"},
            "quotient_image": {"center_a_hat_uasyr": center.tolist(), "fisher_units": "(microarcsec/year)^-2", "chi2_5_95_threshold": threshold,
                "assumed_remainder": "coefficient-level STF5 Frobenius ball ||e||<=r in microarcsec/year; sensitivity only",
                "set": "E95(a_hat,F) plus B5(r)", "radius_grid_uasyr": radii,
                "eigenmode_halfwidths_uasyr": widths,
                "eigenmode_basis_columns": basis.tolist(),
                "directional_support": "v^T a_hat +/- (sqrt(q95*v^T F^-1 v)+r*||v||)",
                "inverse_fibre": "for each u in image and arbitrary q in R5, s=k*q-u; five unbounded null directions"},
            "nuisance": {"spin_glide6_rank": 5, "all97_rank": 5, "free_E2_nuisance_rank": 0,
                         "common_B1_spin_falsifier": src["gram"]["common_b1_spin_falsifier"]},
            "power80_best_worst_uasyr": [src["power_frontier"]["rho80_best_uasyr"], src["power_frontier"]["rho80_worst_uasyr"]],
            "physical_interpretation": "Only five endpoint/history combinations under the stipulated k family; five null directions for each 10-coordinate pair. Matter history and geometric vorticity require a physical source and frame law."}


def optical_product(src, p6, mod):
    s = np.asarray(p6["tensor"], float)
    saved = src["synthetic_source_design"]
    v = np.asarray(saved["full_signed_summary"], float)
    c = np.asarray(saved["summary_covariance"], float)
    o, d = v[3:], v[:3]
    assert c.shape == (10, 10) and np.linalg.eigvalsh(c)[0] > 0
    cr = mod.residual_covariance(c, s)
    np.testing.assert_allclose(cr, saved["residual_covariance"], rtol=1e-8, atol=1e-15)
    q10 = float(chi2.ppf(.95, 10))
    ed = float(np.sqrt(q10*np.linalg.eigvalsh(c[:3, :3])[-1]))
    eo = float(np.sqrt(q10*np.linalg.eigvalsh(c[3:, 3:])[-1]))
    # All terms use one source event. Direct uncertainty enters the profile, never B again.
    dmax = .03
    epsilon = .08
    assert dmax + np.linalg.norm(s, 2) <= epsilon < 1
    budget = mod.joint_budget(epsilon, eo, 0., 0., 0., dmax)
    r = o - mod.KAPPA*mod.lift_matrix(s)@d
    result = safe_joint_test(mod, o, s, d, budget["total"], e_d=ed, d_max=dmax)
    controls = []
    kval = mod.KAPPA * mod.lift_matrix(s)
    sv_min = float(np.linalg.svd(kval, compute_uv=False)[-1])
    d_inverse = np.linalg.lstsq(kval, o, rcond=None)[0]
    perpendicular = float(np.linalg.norm(o-kval@d_inverse))
    for extra in [0., .0001, .0005, .001, .002]:
        bb = mod.joint_budget(epsilon, eo, extra, 0., 0., dmax)
        rr = safe_joint_test(mod, o, s, d, bb["total"], e_d=ed, d_max=dmax)
        controls.append({"assumed_finite_z_or_selection_radius_mag": extra, "shared_budget_mag": bb["total"],
                         "minimum_residual_mag": float(np.sqrt(rr["residual_squared"])), "compatible": rr["compatible"],
                         "inverse_center_d_norm": float(np.linalg.norm(d_inverse)),
                         "unconstrained_d_outer_radius": float(np.sqrt(max(bb["total"]**2-perpendicular**2, 0))/sv_min) if bb["total"] >= perpendicular else None,
                         "physical_d_cap": dmax})
    zero = safe_joint_test(mod, o, np.zeros((3, 3)), d, budget["total"], e_d=ed, d_max=dmax)
    small = safe_joint_test(mod, o, 1e-8*s, d, budget["total"], e_d=ed, d_max=dmax)
    tiny = safe_joint_test(mod, o, 1e-200*s, d, budget["total"], e_d=ed, d_max=dmax)
    return {"scope": "96-direction selected-source mathematical control, newly stipulated 10D Gaussian scenario and shared optical outer budget",
            "frame": "observer rest-frame, signature (-+++), outward source direction",
            "tensor_S_full_3x3": s.tolist(), "signed_summary_d3_O7": v.tolist(),
            "full_summary_covariance_10x10": c.tolist(), "residual_covariance_7x7": cr.tolist(),
            "residual_cross_block_frobenius": float(np.linalg.norm(c[:3, 3:])),
            "fixed_S_residual_chi2_descriptive": float(r@np.linalg.solve(cr, r)),
            "joint_event": {"working_law": "new conditional N(mean,C10) synthetic control; R36 supplied covariance, not a probability law", "dimension": 10, "coverage_under_stipulated_law": .95,
                            "chi2_radius_squared": q10, "direct_outer_radius": ed, "octupole_outer_radius": eo,
                            "cross_covariance_retained": True},
            "uniform_domain": {"Dmax": dmax, "epsilon": epsilon, "S_operator_norm": float(np.linalg.norm(s, 2))},
            "fixed_S_identified_image": {"inverse_d_center": d_inverse.tolist(), "perpendicular_residual_mag": perpendicular,
                "minimum_singular_value": sv_min, "physical_intersection": "inverse ellipsoid intersect direct ball and Dmax ball"},
            "shared_budget": budget, "minimum_compatibility": result, "remainder_frontier": controls,
            "S_zero": zero, "S_small_nonzero": small, "S_representable_tiny_nonzero": tiny,
            "perpendicular_space": "seven-component residual in four-dimensional orthogonal complement for nonzero S; all seven directions at S=0",
            "physical_image": "d=-A/(cH), S=sigma/H only if the same emitting congruence and response are qualified; present inputs are apparent/synthetic",
            "unknown_physical_terms": ["actual CF4 joint law", "finite-z bound", "selection/calibration bound", "same-congruence response", "H normalization"]}


def chirality(mod):
    q = np.diag([-1/np.sqrt(2), 0., 1/np.sqrt(2)])
    o = mod.stf3(np.einsum("i,jk->ijk", np.array([np.sqrt(10)/4, 1., np.sqrt(10)/4]), q))
    v = np.einsum("ijk,jk->i", o, q)
    m = np.sum(q*q)*np.eye(3)/3 + 2*q@q/5
    radii = np.abs(v)/np.sqrt(np.diag(m))
    i = int(np.argmin(radii))
    delta = -v[i]/m[i, i]*mod.stf3(np.einsum("i,jk->ijk", np.eye(3)[i], q))
    assert abs(np.einsum("ijk,jk->i", o+delta, q)[i]) < 1e-12
    return {"domain": "fixed simple-spectrum Q, chi(Q,O) != 0, ambient STF3 Frobenius ball",
            "Q": q.tolist(), "O_full_3x3x3": o.tolist(), "rho_sign": float(radii[i]),
            "three_hyperplane_radii": radii.tolist(), "attaining_delta_norm": float(np.linalg.norm(delta)),
            "theorem": "min_i |(C_Q O)_i|/sqrt((||Q||_F^2/3 I + 2Q^2/5)_ii) in oriented Q eigenframe",
            "joint_Q_O_uncertainty": "not sharp under this fixed-Q theorem"}


def write_csv(name, rows):
    with (HERE/name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def plots(g, pm, opt, ch):
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42})
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    rr = opt["remainder_frontier"]
    ax[0].plot([1000*x["assumed_finite_z_or_selection_radius_mag"] for x in rr], [x["shared_budget_mag"] for x in rr], "o-", label="one shared B")
    ax[0].axhline(rr[0]["minimum_residual_mag"], color="firebrick", ls="--", label="profiled residual")
    ax[0].set(xlabel="Assumed additional finite-z/selection radius [mmag]", ylabel="STF3 radius [mag]")
    ax[0].legend()
    ax[1].bar(["perpendicular", "parallel", "combined"], [np.sqrt(opt["minimum_compatibility"]["perpendicular_squared"]), np.sqrt(opt["minimum_compatibility"]["parallel_squared"]), np.sqrt(opt["minimum_compatibility"]["residual_squared"])])
    ax[1].axhline(opt["shared_budget"]["total"], color="firebrick", ls="--")
    ax[1].set(ylabel="Profiled residual [mag]", title="One budget; direct ball profiled once")
    fig.suptitle("Conditional selected-source optical compatibility; no empirical CF4 law")
    fig.tight_layout();fig.savefig(HERE/"optical_joint_compatibility.pdf");plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.4))
    ev = pm["profile_information_eigenvalues"]
    ax[0].plot(range(1, 6), ev, "o-"); ax[0].set(xlabel="Identified E2/STF5 mode", ylabel="Profile Fisher eigenvalue [(uas/yr)^-2]", title="Separate PM law")
    image = pm["quotient_image"]
    rad = image["radius_grid_uasyr"]
    ax[1].plot(rad, [x[0] for x in image["eigenmode_halfwidths_uasyr"]], "o-", label="least-informed mode")
    ax[1].plot(rad, [x[-1] for x in image["eigenmode_halfwidths_uasyr"]], "s-", label="most-informed mode")
    ax[1].set(xlabel="Assumed STF5 remainder r [uas/yr]", ylabel="E95+B5 halfwidth [uas/yr]", title="Five null directions remain")
    ax[1].legend()
    rr = opt["remainder_frontier"]
    ax[2].plot([1000*x["assumed_finite_z_or_selection_radius_mag"] for x in rr],
               [x["unconstrained_d_outer_radius"] for x in rr], "o-", label="inverse outer radius")
    ax[2].axhline(opt["uniform_domain"]["Dmax"], color="firebrick", ls="--", label="declared physical cap")
    ax[2].set(xlabel="Assumed extra optical remainder [mmag]", ylabel="Dimensionless d radius", title="Fixed S; intersect direct and physical balls")
    ax[2].legend(fontsize=7)
    fig.tight_layout();fig.savefig(HERE/"physical_region_vs_remainder.pdf");plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    cc = g["constrained_bin_depth"]
    cov = cc["joint_coverage"]
    ax[0].bar(range(3), [x["rate"] for x in cov.values()]); ax[0].set_xticks(range(3), ["joint GLS", "separate nominal", "separate sandwich"])
    ax[0].set(ylabel="Matched 95% coverage", ylim=(0,1.05))
    ax[1].bar(["full", "12D common", "6D one-family"], [cc["full_deviance_difference"], cc["common_carrier_deviance_difference"], cc["single_g_score_deviance_difference"]])
    ax[1].set(ylabel="g minus g² profiled deviance", title="Same saved law")
    fig.suptitle("E1/B1 comparison: no information beyond correct joint GLS")
    fig.tight_layout();fig.savefig(HERE/"GLS_tensor_scalar_comparison.pdf");plt.close(fig)
    fig, ax = plt.subplots(figsize=(5, 3.3))
    ax.bar(range(3), ch["three_hyperplane_radii"]);ax.axhline(ch["rho_sign"], color="firebrick", ls="--")
    ax.set(xlabel="Zero-chirality hyperplane", ylabel="Ambient STF3 distance", title="Fixed Q and simple spectrum")
    fig.tight_layout();fig.savefig(HERE/"chirality_radius.pdf");plt.close(fig)


def main():
    inputs = {}
    vals = {}
    for key, path in [("gaia24", GAIA), ("gaia_prior", GAIA_PRE), ("pm_e2", PM), ("optical", OPT), ("p6_tensor", P6)]:
        vals[key], inputs[key] = read(path)
    mod = load_optical_module()
    g = gaia_product(vals["gaia24"], vals["gaia_prior"])
    p = pm_product(vals["pm_e2"])
    o = optical_product(vals["optical"], vals["p6_tensor"], mod)
    ch = chirality(mod)
    result = {"schema": "htt.r37.kinematic_image/1", "task_id": "R37-02-KINEMATICS",
              "claim_tier": "C0_CONDITIONAL_METHOD", "transfer_source": "none", "inputs": inputs,
              "gaia_E1_B1": g, "pm_E2_STF5": p, "optical": o, "fixed_Q_sign_radius": ch,
              "original42_acceptance": "17/42; analytic alternate 18/42 unchanged", "scientific_admission": "pending independent scoped review"}
    (HERE/"KINEMATIC_IMAGE_RESULT.json").write_text(json.dumps(result, indent=2)+"\n")
    (HERE/"COMPRESSION_COMPARISON.json").write_text(json.dumps(g, indent=2)+"\n")
    (HERE/"OPTICAL_COMPATIBILITY.json").write_text(json.dumps({"optical": o, "fixed_Q_sign_radius": ch}, indent=2)+"\n")
    power_names = {"joint_GLS_and_tensorized": "joint_GLS_and_tensorized",
                   "independent_bin_nominal": "independent_bin_nominal",
                   "independent_point_estimator_with_correct_joint_sandwich": "independent_with_correct_sandwich"}
    cc = g["constrained_bin_depth"]
    write_csv("information_comparison.csv", [{"method": k, "coverage95": v["rate"], "MCSE": v["MCSE"],
         "power_at_2p5": cc["matched_power"][power_names[k]]["rate"]} for k, v in cc["joint_coverage"].items()])
    write_csv("E2_identified_combinations.csv", p["history_images"])
    write_csv("optical_joint_budget.csv", o["remainder_frontier"])
    (HERE/"nullspaces.json").write_text(json.dumps({"gaia_free_bin_T24_to18_lost_slopes": 6, "gaia_common_nuisance": "spin/glide6",
        "gaia_g_g2_common_carrier_rank": 12, "pm_history_each_null_dimension": 5, "pm_free_E2_nuisance_identified_rank": 0,
        "pm_parameter_coordinates": "q=(B_o-B_s)/T_ref, s=dot B_o; u=kq-s, k=2cT_ref/D",
        "pm_inverse_fibre": "for every identified u and arbitrary q in R5, s=kq-u; five unbounded directions delta_s=k*delta_q",
        "pm_separate_endpoint_common_shift": "B_o and B_s shifted by the same STF5 tensor adds five null directions",
        "optical_S_zero_inverse": "undefined; direct membership only", "geometric_vorticity": "unidentified without frame-spin/source law"}, indent=2)+"\n")
    plots(g, p, o, ch)
    print(json.dumps({"gaia_full_vs_common_LR_error": abs(g["constrained_bin_depth"]["full_deviance_difference"]-g["constrained_bin_depth"]["common_carrier_deviance_difference"]),
        "pm_min_eigenvalue": p["profile_information_eigenvalues"][0], "optical_compatible": o["minimum_compatibility"]["compatible"], "fixed_Q_sign_radius": ch["rho_sign"]}))


if __name__ == "__main__":
    main()
