#!/usr/bin/env python3
"""Actual CF4 local-frame/history response experiment, conditional fixed law.

Reuses the original R58 y32/C32 and actual source operators. The data reduction
does not certify the complete observer flux/frame contract; physical subcases
below are conditional response models, never a global-tilt detection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg, stats

BASELINE = "f29bbab420a33aecb1c398ddd961fd45097f536b"
PROGRAM = "docs/research_program/observational_publication_20261015"
R58 = PROGRAM + "/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS"
R62 = PROGRAM + "/R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/SOURCE"
EXPECTED_R58 = "42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d"
EXPECTED_R62 = "1d0f3c353ea9189bffbab5728f295264c6925d4a3d82561c4457e48746beefd2"
C_KM_S = 299792.458


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            raise ValueError("nonfinite JSON output")
        return float(value)
    return value


def save_fit(arrays, key, fit, response):
    for name in ("estimate", "covariance", "precision", "score", "q0",
                 "likelihood_factor", "likelihood_offset", "parameter_scale",
                 "null_basis", "singular_values_scaled", "singular_values_equilibrated"):
        arrays[key + "__" + name] = np.asarray(fit[name])
    arrays[key + "__response"] = response
    return {
        "rank": fit["rank"], "parameters": fit["n_parameters"],
        "residual_chi2": fit["residual_chi2"], "dof": fit["dof"],
        "adequacy_p": fit["adequacy_p"],
        "condition_scaled": float(fit["singular_values_scaled"][0] / fit["singular_values_scaled"][-1]),
        "condition_equilibrated": float(fit["singular_values_equilibrated"][0] / fit["singular_values_equilibrated"][-1]),
        "carrier_key": key,
    }


def wald_block(fit, positions):
    h = fit["estimate"][positions]
    v = fit["covariance"][positions, positions]
    w = float(h @ linalg.solve(v, h, assume_a="pos"))
    return {"estimate": h, "covariance": v, "wald": w,
            "df": len(h), "nominal_p": float(stats.chi2.sf(w, len(h)))}


def gaussian_schur_identity(cov, design):
    """The actual data-block innovation, before parameter nuisance profiling."""
    cp, cs, csp = cov[:12, :12], cov[12:, 12:], cov[12:, :12]
    a = linalg.solve(cp, csp.T, assume_a="pos").T
    innovation_cov = cs - a @ csp.T
    innovation_design = design[12:] - a @ design[:12]
    jp = design[:12].T @ linalg.solve(cp, design[:12], assume_a="pos")
    js = innovation_design.T @ linalg.solve(innovation_cov, innovation_design, assume_a="pos")
    j = design.T @ linalg.solve(cov, design, assume_a="pos")
    error = float(linalg.norm(j - jp - js) / linalg.norm(j))
    if error > 2e-11:
        raise ValueError("actual polar/STF innovation identity failed")
    return {"relative_precision_error": error,
            "conditional_STF_covariance": innovation_cov,
            "conditional_STF_response": innovation_design,
            "interpretation": "Same full law, not independent extra data; profile common nuisance after adding both precision contributions."}


def run(root, output):
    started = time.perf_counter()
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite an existing R63 execution")
    output.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root / "scripts/r58"), str(root / "htt"), str(root / "htt/src")]
    import run_r58_owned_tensor as old
    import build_r58_views as views
    de, _, cf, mt = old.import_modules(root, None)
    from htt.htt.infer import r63_frame_history as fh

    pins = {p: sha(root / p) for p in old.PINS}
    bad = [p for p, h in pins.items()
           if h != old.PINS[p] and h not in old.ALLOWED_REPAIRED_HASHES.get(p, ())]
    if bad:
        raise ValueError("pinned dependency changed: " + str(bad))
    r58path = root / R58 / "OWNED_TENSOR_CARRIERS.npz"
    r62path = root / R62 / "SOURCE_TENSOR_CARRIERS.npz"
    if sha(r58path) != EXPECTED_R58 or sha(r62path) != EXPECTED_R62:
        raise ValueError("owned carrier identity mismatch; do not substitute replay")
    saved = np.load(r58path, allow_pickle=False)
    previous = np.load(r62path, allow_pickle=False)
    data = cf.load()
    cat = data["cat"]
    n, z = cat["n_J2000"], cat["z_CMB"]
    lr = de.log_distance_ratio(cat["dmzp"], z, cf.OMEGA_M)
    eta, g = lr["eta"], lr["g_per_km_s"]
    tau2 = de.log_noise_variance(cat["e_dmzp"], g, cf.SIGMA_STAR)
    with np.load(cf.OUT_DIR / "R54_L04_SURVEY_LABELS.npz", allow_pickle=False) as lab:
        if not np.array_equal(lab["group_id"], cat["group_id"]):
            raise ValueError("survey source order mismatch")
        survey = dict(labels=lab["survey"].copy(), raw_labels=lab["survey_unpooled"].copy(), min_side=100)
    ops, _ = cf.build_operators(cat, data["a_raw"], tau2, survey=survey)
    angular = de.multipole_basis(n)[:, 1:]
    if np.max(np.abs(angular[:, :3] - n)) > 2e-14:
        raise ValueError("source polar convention differs")
    legendre = np.polynomial.legendre.legvander((z - .055) / .045, 3)
    tensor = np.column_stack([legendre[:, j, None] * angular[:, 3:] for j in range(4)])
    src_baseline = np.column_stack((g[:, None] * n, n, tensor))
    src_free = np.column_stack((g[:, None] * n, (z * g)[:, None] * n, n, tensor))
    rows = saved["row_indices32"]
    expected_rows = np.r_[[9*w+a for w in range(4) for a in (1,2,3)],
                         [9*w+a for w in range(4) for a in range(4,9)]]
    if not np.array_equal(rows, expected_rows):
        raise ValueError("expected polar12 then STF20")

    omega_r, beta_star = 1e-4, .01
    bg = fh.background_factors(z, cf.OMEGA_M, omega_r, quadrature_order=64)
    bg_ref = fh.background_factors(z, cf.OMEGA_M, omega_r, quadrature_order=96)
    bg_zero_r = fh.background_factors(z, cf.OMEGA_M, 0., quadrature_order=64)
    refine = float(np.max(np.abs(bg["chi_hat"] / bg_ref["chi_hat"] - 1)))
    if refine > 2e-13:
        raise ValueError("distance quadrature refinement failed")
    ratio = 3 * cf.OMEGA_M / (4 * omega_r)
    fraction = 1 / (1 + ratio)
    umax = float(fh.compensated_velocity_bound(cf.OMEGA_M, omega_r, float(z.max()), beta_star))
    wmax = umax / (1 + ratio)
    gr = bg["g_per_km_s"]
    background_offset = np.log(lr["chi_hat"] / bg["chi_hat"])
    rad_const = np.column_stack((gr[:, None] * n, n, tensor))
    rad_history = (z * gr)[:, None] * n
    rad_tied = rad_const.copy()
    rad_tied[:, :3] += fraction * rad_history
    tpath = views.depth_path_matrix()
    arrays, variants = {}, {}
    covariance_hashes, operator_hashes = {}, {}

    for name in old.VARIANTS:
        op = ops[name][rows]
        y, cov = (saved[name + suffix] for suffix in ("__y32", "__cov32"))
        xbase26, xfree29 = op @ src_baseline, op @ src_free
        xrad26, xtied26 = op @ rad_const, op @ rad_tied
        xzhist, off = op @ rad_history, op @ background_offset
        y_rad = y - off
        if np.max(np.abs(op @ eta - y)) > 2e-10:
            raise ValueError("actual operator/data parity failed")
        arrays[name + "__y32"] = y
        arrays[name + "__cov32"] = cov
        arrays[name + "__rad_background_offset32"] = off
        arrays[name + "__path32"] = tpath @ y
        arrays[name + "__path_cov32"] = tpath @ cov @ tpath.T
        covariance_hashes[name] = hashlib.sha256(np.ascontiguousarray(cov).tobytes()).hexdigest()
        operator_hashes[name] = hashlib.sha256(np.ascontiguousarray(op).tobytes()).hexdigest()
        models = {}
        for degree in (2, 3):
            p, pf = 6 + 5 * (degree + 1), 9 + 5 * (degree + 1)
            scale = np.r_[np.full(3, 300.), np.full(p-3, .01)]
            scalef = np.r_[np.full(6, 300.), np.full(pf-6, .01)]
            xb, xf = xbase26[:, :p], xfree29[:, :pf]
            xr, xt = xrad26[:, :p], xtied26[:, :p]
            baseline = mt.fit_linear(y, cov, xb, scale)
            free = mt.fit_linear(y, cov, xf, scalef)
            bulk = mt.fit_linear(y_rad, cov, xr, scale)
            tied = mt.fit_linear(y_rad, cov, xt, scale)
            if any(f["rank"] != f["n_parameters"] for f in (baseline, free, bulk, tied)):
                raise ValueError("unresolved rank in selected finite mean family")
            key = name + f"__J{degree}"
            parity_h = float(np.max(np.abs((baseline["estimate"] - previous[key + "__estimate"]) / scale)))
            parity_c = float(np.max(np.abs((baseline["covariance"] - previous[key + "__covariance"]) / scale[:, None] / scale[None, :])))
            if max(parity_h, parity_c) > 2e-8:
                raise ValueError("R62 baseline parity failed")
            bf = save_fit(arrays, key + "__constant", baseline, xb)
            ff = save_fit(arrays, key + "__free_history", free, xf)
            rf = save_fit(arrays, key + "__rad_constant", bulk, xr)
            tf = save_fit(arrays, key + "__rad_tied", tied, xt)
            ff["W"] = wald_block(free, slice(3,6))
            ff["Vp"] = wald_block(free, slice(0,3))
            bf["V"] = wald_block(baseline, slice(0,3))
            tf["U"] = wald_block(tied, slice(0,3))
            tf["W_dust_normal"] = {"estimate": tied["estimate"][:3] * fraction,
                "covariance": tied["covariance"][:3,:3] * fraction**2}
            delta = baseline["residual_chi2"] - free["residual_chi2"]
            if abs(delta - ff["W"]["wald"]) > 2e-6:
                raise ValueError("nested W Wald/LR identity failed")
            nuisance = np.column_stack((xf[:, :3], xf[:, 6:]))
            info = fh.residualized_response(cov, nuisance, xf[:, 3:6])
            info_polar = fh.residualized_response(cov[:12,:12], nuisance[:12], xf[:12,3:6])
            jw = info["information"]
            inverse_w_cov = linalg.solve(free["covariance"][3:6,3:6], np.eye(3), assume_a="pos")
            schur_error = float(linalg.norm(jw - inverse_w_cov) / linalg.norm(jw))
            if schur_error > 2e-7:
                raise ValueError("profile W precision disagrees with full covariance")
            discrimination = fh.residualized_response(cov, xr, xzhist)
            h_response = op @ (-bg["h"][:, None]*n/C_KM_S)
            h_projection = fh.residualized_response(cov, xr, h_response)
            h_error = float(linalg.norm(discrimination["residual"]-h_projection["residual"])
                            / linalg.norm(discrimination["residual"]))
            if h_error > 2e-8:
                raise ValueError("calibration quotient z*g = -h/c identity failed")
            # Form the small difference response directly; no cancellation of
            # nearly equal inverse Fisher matrices or rounded mean templates.
            ds = fraction * discrimination["residual"]
            separation = ds.T @ ds
            lam_max = max(float(linalg.eigvalsh(separation)[-1]), 0.)
            u_hat = tied["estimate"][:3]
            dist_hat = float(linalg.norm(ds @ u_hat))
            dist300 = 300 * np.sqrt(lam_max)
            distbody = umax * np.sqrt(lam_max)
            arrays[key + "__history_information"] = jw
            arrays[key + "__history_residual"] = info["residual"]
            arrays[key + "__separation_information"] = separation
            arrays[key + "__separation_residual"] = ds
            # Unrestricted constant endpoint coordinates (Vs,Vo,a_cal,K) have
            # an exact 3-vector fibre. Fixed catalogue corrections are offsets.
            pullback = np.zeros((p,p+3))
            pullback[:3,:3] = np.eye(3)
            pullback[:3,3:6] = -np.eye(3)
            pullback[3:6,3:6] = -np.eye(3)/C_KM_S
            pullback[3:6,6:9] = np.eye(3)
            pullback[6:,9:] = np.eye(p-6)
            physical_scale = np.r_[np.full(6,300.),np.full(p-3,.01)]
            physical = mt.fit_linear(y,cov,xb @ pullback,physical_scale)
            if physical["rank"] != p:
                raise ValueError("constant endpoint pullback has unexpected rank")
            witness = np.zeros(p+3)
            dv = np.array([173.,-91.,47.])
            witness[:3] = dv
            witness[3:6] = dv
            witness[6:9] = dv/C_KM_S
            fibre_error = float(linalg.norm(xb @ pullback @ witness))
            if fibre_error > 2e-12:
                raise ValueError("constant source/observer/calibration fibre failed")
            arrays[key + "__endpoint_pullback"] = pullback
            arrays[key + "__endpoint_null_basis"] = physical["null_basis"]
            # Small physical normal-tilt injection through the real operators.
            injected = np.zeros(pf)
            injected[:3] = [125., -83., 47.]
            injected[3:6] = [.20, -.11, .07]
            injected[6:9] = [.003,-.002,.001]
            injected[9:14] = [.002,-.001,.0005,.0012,-.0007]
            rec = mt.fit_linear(op @ (src_free[:, :pf] @ injected), cov, xf, scalef)
            injection_error = float(np.max(np.abs((rec["estimate"]-injected)/scalef)))
            if injection_error > 2e-7:
                raise ValueError("noise-free actual source-history recovery failed")
            cal_shift = np.array([.011, -.008, .004])
            shifted = mt.fit_linear(y + op @ (n @ cal_shift), cov, xf, scalef)
            expected_shift = np.zeros(pf)
            expected_shift[6:9] = cal_shift
            cal_error = float(np.max(np.abs((shifted["estimate"]-free["estimate"]-expected_shift)/scalef)))
            if cal_error > 2e-7:
                raise ValueError("common dipole calibration invariance failed")
            transformed = mt.fit_linear(tpath@y, tpath@cov@tpath.T, tpath@xf, scalef)
            path_error = abs(mt.gaussian_log_likelihood(free, free["estimate"])
                             - mt.gaussian_log_likelihood(transformed, free["estimate"]))
            if path_error > 2e-7:
                raise ValueError("five-view path likelihood invariance failed")
            c95 = float(stats.chi2.ppf(.95,3))
            wh, vw = free["estimate"][3:6],free["covariance"][3:6,3:6]
            support = {}
            for i, label in enumerate("xyz"):
                radius = np.sqrt(c95*vw[i,i])
                support[label] = {"lower_km_s": wh[i]-radius,"upper_km_s":wh[i]+radius,
                                  "null_reference_support_km_s":radius,
                                  "signed_support_ratio_plus":1+wh[i]/radius,
                                  "signed_support_ratio_minus":1-wh[i]/radius}
            linear_ball_change = 2*wmax*linalg.norm(jw @ wh)+wmax*wmax*float(linalg.eigvalsh(jw)[-1])
            numerical_mean_error = op @ ((g - bg_zero_r["g_per_km_s"])[:,None]*n)
            whitened_numerical = linalg.solve_triangular(linalg.cholesky(cov,lower=True),numerical_mean_error,lower=True)
            models[str(degree)] = {
                "R62_parity": {"estimate_scaled_max":parity_h,"covariance_scaled_max":parity_c},
                "constant_bulk":bf,"free_history":ff,"radiation_background_bulk":rf,"tied_compensated":tf,
                "W_zero_test":{"delta_chi2":delta,"df":3,"nominal_p":ff["W"]["nominal_p"],
                    "law":"exact nested linear Gaussian test for fixed covariance/design; not calibrated physical-tilt probability"},
                "observer_endpoint_fibre":{"rank":physical["rank"],"parameters":p+3,"nullity":3,
                    "response_error":fibre_error,"individual_source_and_observer":"UNBOUNDED without an added frame/calibration contract",
                    "identified":"Vs-Vo and a_cal-Vo/c, plus known fixed catalogue offsets"},
                "history_geometry":{"information":jw,"singular_values_per_km_s":info["singular_values"],
                    "target_rank":info["target_rank"],"nuisance_rank":info["nuisance_rank"],
                    "inverse_covariance_relative_error":schur_error,
                    "dipole_only_target_rank":info_polar["target_rank"],"dipole_only_nuisance_rank":info_polar["nuisance_rank"],
                    "dipole_only_information":info_polar["information"]},
                "same_law_STF_innovation":gaussian_schur_identity(cov,xf),
                "tied_vs_bulk":{"residual_chi2_tied_minus_bulk":tied["residual_chi2"]-bulk["residual_chi2"],
                    "not_a_calibrated_model_p_or_Bayes_factor":True,"separation_information":separation,
                    "distance_at_fitted_U":dist_hat,"max_distance_at_300_km_s":dist300,
                    "max_distance_in_matter_radiation_body":distbody,
                    "oracle_power_alpha_0p1_at_fitted_U":fh.oracle_power(dist_hat,alpha=.1),
                    "oracle_power_alpha_0p1_max_300":fh.oracle_power(dist300,alpha=.1),
                    "oracle_power_alpha_0p1_max_body":fh.oracle_power(distbody,alpha=.1),
                    "scope":"nearest-null Gaussian simple-pair upper bound for tests uniformly controlling type-I error over the constant-bulk nuisance family; only this linear fixed-C experiment"},
                "physical_body":{"beta_star":beta_star,"U_bound_matter_radiation_km_s":umax,"W_bound_km_s":wmax,
                    "observer_and_finite_redshift_remainder":"separate obligations; this is a necessary matter/radiation superset",
                    "free_W_profile_max_abs_delta_chi2_from_zero_in_body_bound":float(linear_ball_change)},
                "checks":{"injection_scaled_error":injection_error,"calibration_scaled_error":cal_error,
                    "path_log_likelihood_error":path_error,
                    "history_h_quotient_relative_error":h_error,
                    "legacy_background_numerical_mean_norm_bound_at_300_km_s":float(300*linalg.svdvals(whitened_numerical)[0])},
                "five_views":{
                    "x":{"carrier":key+"__free_history","typed_blocks":"Vp,W [km/s]; d,STF coefficients [dimensionless]"},
                    "Q":{"value":np.sqrt(ff["W"]["wald"]/c95),"anchor":"3D profiled W coefficient-noise ellipsoid","physical_MES":"UNAVAILABLE"},
                    "Pi":{"value":ff["W"]["nominal_p"],"scalarization":"W profile Wald","law":"chi2_3 survival under W=0 and declared fixed Gaussian law","posterior_probability":False},
                    "F":{"support":support,"occupancy":"UNAVAILABLE; support is not occupancy"},
                    "G_F":{"data_key":name+"__path32","covariance_key":name+"__path_cov32","common_level_retained":True,
                        "likelihood_error":path_error,"time_derivative":False},
                    "one_likelihood":True}}
            if degree == 2:
                # One prespecified calibration sensitivity: an additional
                # z-dependent dipole. No arbitrary angular immunity is claimed.
                xdepth = op @ (z[:,None]*n)
                expanded = np.column_stack((xf,xdepth))
                expfit = mt.fit_linear(y,cov,expanded,np.r_[scalef,[.01]*3])
                if expfit["rank"] != expanded.shape[1]:
                    raise ValueError("unresolved expanded-calibration mean rank")
                expinfo = fh.residualized_response(cov,np.column_stack((nuisance,xdepth)),xf[:,3:6])
                expanded_sep = fh.residualized_response(cov,np.column_stack((xr,xdepth)),xzhist)
                expanded_bound = umax*fraction*linalg.svdvals(expanded_sep["residual"])[0]
                models[str(degree)]["depth_calibration_sensitivity"] = {
                    **save_fit(arrays,key+"__depth_calibration",expfit,expanded),
                    "W":wald_block(expfit,slice(3,6)),"history_information":expinfo["information"],
                    "history_target_rank":expinfo["target_rank"],
                    "max_distance_body":float(expanded_bound),
                    "oracle_power_alpha_0p1_max_body":fh.oracle_power(float(expanded_bound),alpha=.1)}
            print(f"{name}/J{degree}: W p={ff['W']['nominal_p']:.6g}, ranks {free['rank']}/{pf}, max tied-vs-bulk distance={distbody:.6g}",flush=True)
        variants[name] = {"models":models}

    arrays["path_transform"] = tpath
    arrays["row_indices32"] = rows
    destination = output / "FRAME_HISTORY_CARRIERS.npz"
    np.savez_compressed(destination,**arrays)
    summary = {
        "schema":"htt.r63.local_boost_global_tilt/1","baseline_commit":BASELINE,
        "execution_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
        "source_hashes":{R58+"/OWNED_TENSOR_CARRIERS.npz":sha(r58path),R62+"/SOURCE_TENSOR_CARRIERS.npz":sha(r62path),**pins},
        "script_sha256":sha(__file__),"module_sha256":sha(root/"htt/htt/htt/infer/r63_frame_history.py"),
        "carrier_sha256":sha(destination),"covariance_byte_hashes":covariance_hashes,
        "source_operator_byte_hashes":operator_hashes,
        "runtime":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"seconds":time.perf_counter()-started},
        "source":{"groups":len(z),"z_min_max":[z.min(),z.max()],"frame":"published CMB redshift; J2000 directions","distance":"calibrated heterogeneous CF4 luminosity-distance modulus",
            "physical_reduction_contract":"q/p and method mixing not fully reconstructed; inherited working response, physical interpretation conditional"},
        "benchmark":{"omega_m":cf.OMEGA_M,"omega_r":omega_r,"R":ratio,"fraction":fraction,
            "choice":"declared finite benchmark, not measured radiation density","background_offset":"ln(chi_old/chi_rad)",
            "quadrature_refinement_relative_error":refine,"covariance":"fixed R58 Gaussian working law; not recalibrated for two-fluid universe"},
        "comparison":"pure local observer after calibration; constant coherent bulk; free history diagnostic; physically tied compensated subcase under additional CMB-reference contract",
        "claim_tier":"C0 conditional actual-data response experiment; no global-tilt detection, universal no-go, independent CMB likelihood, or physical remainder certification",
        "variants":variants,
        "robust_same_null_max_p":{
            "W_zero_J2":max(v["models"]["2"]["W_zero_test"]["nominal_p"] for v in variants.values()),
            "W_zero_J3":max(v["models"]["3"]["W_zero_test"]["nominal_p"] for v in variants.values()),
            "pure_observer_remaining_V_zero_J2":max(v["models"]["2"]["constant_bulk"]["V"]["nominal_p"] for v in variants.values()),
            "interpretation":"union-null p envelope if at least one declared nuisance experiment is valid; no independence or universal systematic coverage"}}
    (output/"FRAME_HISTORY_RESULT.json").write_text(json.dumps(clean(summary),indent=2,allow_nan=False)+"\n")
    print(json.dumps({"carrier_sha256":summary["carrier_sha256"],"seconds":summary["runtime"]["seconds"],"groups":len(z)}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",default=".")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    run(args.root,args.output)
