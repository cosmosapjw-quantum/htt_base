#!/usr/bin/env python3
"""Owned CF4 full36 radial distance-rate experiment, with a fixed working law.

No new catalogue reduction, selection law, physical-H identification, or
independence claim is supplied by this script. It preserves actual O and C.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg, stats

PROGRAM = "docs/research_program/observational_publication_20261015"
R58 = PROGRAM + "/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS/OWNED_TENSOR_CARRIERS.npz"
EXPECTED_R58 = "42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d"
BASELINE = "33d87dd3e4a787e477327d37ee00b40e790211c9"
C = 299792.458
Z_EVAL = (.025, .04, .06, .08)
Z_REF = .04


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
            return "+infinity" if value > 0 else "-infinity" if value < 0 else "undefined"
        return float(value)
    return value


def dump(path, obj):
    Path(path).write_text(json.dumps(clean(obj), indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def save_fit(arrays, key, fit, x):
    fields = ("estimate", "covariance", "precision", "score", "q0", "likelihood_factor",
              "likelihood_offset", "parameter_scale", "null_basis", "singular_values_scaled",
              "singular_values_equilibrated", "_estimability_scale", "_estimability_null_basis",
              "_zero_design_columns")
    for f in fields:
        arrays[key + "__" + f] = np.asarray(fit[f])
    arrays[key + "__response"] = x
    return {k: fit[k] for k in ("rank", "rank_equilibrated", "n_parameters", "dof",
                                 "residual_chi2", "adequacy_p", "rank_rtol")}


def nested_angular_null(y, cov, x, degree, scale, fit, fit_linear):
    keep = np.r_[np.arange(12), [3 + 9*j for j in range(1, degree+1)]]
    null = fit_linear(y, cov, x[:, keep], scale[keep])
    delta = float(null["residual_chi2"] - fit["residual_chi2"])
    if delta < -1e-8:
        raise ValueError("nested mean spaces give a negative LR")
    delta = max(delta, 0.)
    rank = fit["rank"] - null["rank"]
    return {"delta_chi2": delta, "df": rank,
            "nominal_p": float(stats.chi2.sf(delta, rank)) if rank else None,
            "noise_reference_Q95": float(np.sqrt(delta/stats.chi2.ppf(.95, rank))) if rank else None,
            "null_rank": null["rank"], "null_residual_chi2": null["residual_chi2"],
            "null": "a_j dipole/STF = 0 for j>=1; free monopole history, constant angular field and coherent V",
            "law": "conditional fixed-C Gaussian linear mean; no physical isotropy or empirical-selection calibration"}


def conditional_holdout(y, cov, x, held, scale, fit_linear):
    """Exact Gaussian prediction after GLS training, including shared noise.

    Innovation e=y_h-C_ht C_tt^-1 y_t-(X_h-C_ht C_tt^-1 X_t) theta_hat_t.
    Its covariance is S+Xstar Cov(theta_hat_t) Xstar^T. Valid when training
    identifies the requested prediction and the fixed linear Gaussian law holds.
    """
    y, cov, x = np.asarray(y), np.asarray(cov), np.asarray(x)
    held = np.asarray(held, dtype=int)
    keep = np.setdiff1d(np.arange(len(y)), held)
    train = fit_linear(y[keep], cov[np.ix_(keep, keep)], x[keep], scale)
    a = linalg.solve(cov[np.ix_(keep, keep)], cov[np.ix_(keep, held)], assume_a="pos").T
    xs = x[held] - a @ x[keep]
    ns = xs @ train["null_basis"]
    if ns.size and linalg.norm(ns) > 1e-9*max(linalg.norm(xs*scale), 1e-300):
        return {"status": "UNIDENTIFIED_PREDICTION", "training_rank": train["rank"]}
    s = cov[np.ix_(held, held)] - a @ cov[np.ix_(keep, held)]
    predictive_cov = s + xs @ train["covariance"] @ xs.T
    predictive_cov = (predictive_cov + predictive_cov.T)/2
    error = y[held] - a @ y[keep] - xs @ train["estimate"]
    chi2 = float(error @ linalg.solve(predictive_cov, error, assume_a="pos"))
    return {"status": "IDENTIFIED", "training_rank": train["rank"],
            "chi2": chi2, "df": len(held), "nominal_p": float(stats.chi2.sf(chi2, len(held))),
            "error": error, "predictive_covariance": predictive_cov,
            "shared_noise_variance_included": True,
            "interpretation": "correlated internal leave-one-window check; overlapping source rows, not an independent tracer"}


def gain(fit):
    """Stable gain from whitened data to an estimator representative."""
    xw, scale = fit["likelihood_factor"], fit["parameter_scale"]
    u, s, vt = linalg.svd(xw*scale, full_matrices=False)
    r = fit["rank"]
    return (scale[:, None]*vt[:r].T/s[:r]) @ u[:, :r].T


def linear_images(fit, rows, mt):
    rows = np.asarray(rows)
    intervals = [mt.linear_interval(fit, r, .95, True) for r in rows]
    return {"intervals": intervals, "representative": rows @ fit["estimate"],
            "representative_covariance": rows @ fit["covariance"] @ rows.T,
            "identified": [v["identified"] for v in intervals],
            "warning": "Representative covariance is not bounded uncertainty in a null direction."}


def run(root, output):
    started = time.perf_counter()
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite an R64 execution")
    output.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root/"scripts/r58"), str(root/"htt"), str(root/"htt/src")]
    import run_r58_owned_tensor as old
    de, fv, cf, mt = old.import_modules(root, None)
    from htt.htt.infer import r64_directional_hubble as dh

    pins = {p: sha(root/p) for p in old.PINS}
    bad = [p for p, h in pins.items() if h != old.PINS[p] and h not in old.ALLOWED_REPAIRED_HASHES.get(p, ())]
    if bad:
        raise ValueError("pinned dependency changed: " + str(bad))
    source = root/R58
    if sha(source) != EXPECTED_R58:
        raise ValueError("original full36 carrier mismatch")
    saved = np.load(source, allow_pickle=False)
    data = cf.load()
    cat = data["cat"]
    n, z = cat["n_J2000"], cat["z_CMB"]
    lr = de.log_distance_ratio(cat["dmzp"], z, cf.OMEGA_M)
    eta, g = lr["eta"], lr["g_per_km_s"]
    smooth = dh.background_factors(z, cf.OMEGA_M)
    smooth_offset = np.log(smooth["chi_hat"]/lr["chi_hat"])
    tau2 = de.log_noise_variance(cat["e_dmzp"], g, cf.SIGMA_STAR)
    with np.load(cf.OUT_DIR/"R54_L04_SURVEY_LABELS.npz", allow_pickle=False) as lab:
        if not np.array_equal(lab["group_id"], cat["group_id"]):
            raise ValueError("survey/source row mismatch")
        survey = dict(labels=lab["survey"].copy(), raw_labels=lab["survey_unpooled"].copy(), min_side=100)
    ops, _ = cf.build_operators(cat, data["a_raw"], tau2, survey=survey)
    b = de.multipole_basis(n)
    source_designs = {j: dh.source_design(z, n, g, j) for j in (1, 2, 3)}

    raw4 = root/"workdir/raw/cf4_full/table4.dat.gz"
    raw = gzip.decompress(raw4.read_bytes())
    if hashlib.sha256(raw).hexdigest() != "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94":
        raise ValueError("published Table4 changed")
    records = {int(s[:7]): s for s in raw.splitlines() if s.strip()}
    selected = [records[int(i)] for i in cat["group_id"]]
    vh = np.array([float(s[27:32]) for s in selected])
    v3 = np.array([float(s[39:44]) for s in selected])
    if np.max(abs(v3/C-z)) > 1e-12:
        raise ValueError("published V3k no longer binds selected z")
    a = linalg.lstsq(n, v3-vh)[0]
    qactual = C*np.log1p((v3-vh)/(C+vh))
    deltaq = qactual - n @ a
    offset_raw = (g + 2/C)*deltaq
    axis = np.array([1., 2., 3.]); axis /= linalg.norm(axis)
    cos = n @ axis
    l3cal = .01*(5*cos**3-3*cos)/2
    cal = np.array([.02, .007, -.004, .005, -.002, .003, .001, -.006, .004])
    directions = np.vstack((np.eye(3), -np.eye(3), fv.fibonacci_sphere(48)))
    arrays, models, source_checks, operator_hashes = {}, {}, {}, {}

    for name in old.VARIANTS:
        op = ops[name]
        y_original = saved[name+"__theta36"]
        y = y_original + op @ smooth_offset
        cov = saved[name+"__white36"] + saved[name+"__body36"]
        parity_y = float(np.max(abs(op @ eta-y_original)))
        parity_c = float(np.max(abs(de.white_covariance(op, tau2)-saved[name+"__white36"])))
        if parity_y > 2e-10 or parity_c > 2e-10:
            raise ValueError("owned source/operator parity failed")
        arrays[name+"__y36"] = y
        arrays[name+"__original_y36"] = y_original
        arrays[name+"__smooth_reference_offset36"] = op @ smooth_offset
        arrays[name+"__cov36"] = cov
        arrays[name+"__q_offset36"] = op @ offset_raw
        source_checks[name] = {"eta_max_error": parity_y, "white_covariance_max_error": parity_c,
            "constant_angular_response_error": float(np.max(abs(op @ b-np.tile(np.eye(9), (4, 1))))),
            "radial_z_response_norm": float(linalg.norm(op @ z))}
        operator_hashes[name] = hashlib.sha256(np.ascontiguousarray(op).tobytes()).hexdigest()
        for degree in (1, 2, 3):
            x = op @ source_designs[degree]
            p = x.shape[1]
            scale = np.r_[np.full(3, 300.), np.full(p-3, .01)]
            fit = mt.fit_linear(y, cov, x, scale)
            key = name+f"__J{degree}"
            record = save_fit(arrays, key, fit, x)
            record["angular_radial_null"] = nested_angular_null(y, cov, x, degree, scale, fit, mt.fit_linear)
            chol = linalg.cholesky(cov, lower=True)
            k = gain(fit)
            rawgain = linalg.solve_triangular(chol.T, k.T, lower=False).T @ op
            # These witnesses compare actual source-calibration images, not
            # arbitrary independent coefficient offsets after compression.
            calshift = rawgain @ (b @ cal)
            expected_shift = np.zeros(p); expected_shift[3:12] = cal
            witness = fit["likelihood_factor"] @ (calshift-expected_shift)
            record["calibration"] = {
                "represented_shift_likelihood_error": float(linalg.norm(witness)),
                "raw_l3_amplitude": .01,
                "raw_l3_axis_ICRS": axis,
                "l3_parameter_representative_bias": rawgain @ l3cal,
                "constant_angular_scope": "represented l<=2 only; omitted angular calibration can leak into radial coefficients"}

            # Joint linear radial paths retain monopole, polar, STF and all
            # cross-depth covariance. The reference row is exactly zero.
            depth_rows = []
            for zz in (.025, .06, .08):
                pp, _, _ = dh.radial_jet(zz, degree)
                pr, _, _ = dh.radial_jet(Z_REF, degree)
                rr = np.zeros((9, p))
                for j in range(degree+1):
                    rr[:, 3+9*j:3+9*(j+1)] = (pp[j]-pr[j])*np.eye(9)
                depth_rows.extend(rr)
            depth_rows = np.array(depth_rows)
            images = linear_images(fit, depth_rows, mt)
            arrays[key+"__depth_map"] = depth_rows
            arrays[key+"__depth_estimate"] = depth_rows @ fit["estimate"]
            arrays[key+"__depth_representative_cov"] = depth_rows @ fit["covariance"] @ depth_rows.T
            record["depth_eta_image"] = images
            record["calibration"]["represented_identified_depth_max_error"] = max(
                [abs(v) for v, ok in zip(depth_rows @ calshift, images["identified"]) if ok] or [0.])
            record["calibration"]["omitted_l3_identified_depth_max_bias"] = max(
                [abs(v) for v, ok in zip(depth_rows @ rawgain @ l3cal, images["identified"]) if ok] or [0.])

            # Known actual-q affine offset: same source, operator, covariance,
            # parameter response and Gaussian information.
            dqtheta = rawgain @ offset_raw
            corrected = dict(fit); corrected["estimate"] = fit["estimate"]-dqtheta
            record["published_chart"] = {"parameter_shift": -dqtheta,
                "depth_eta_shift": -depth_rows @ dqtheta,
                "whitened_offset_norm": float(linalg.norm(linalg.solve_triangular(chol, op @ offset_raw, lower=True))),
                "scope": "first-order deterministic published-q correction; not distance-deboost qualification"}
            if name == "log" and degree in (1, 3):
                direct = mt.fit_linear(y-op@offset_raw, cov, x, scale)
                parity = float(np.max(abs((direct["estimate"]-corrected["estimate"])/scale)))
                if parity > 2e-7:
                    raise ValueError("actual full36 affine chart transport failed direct GLS parity")
                record["published_chart"]["direct_GLS_scaled_parity_error"] = parity
            arrays[key+"__corrected_estimate"] = corrected["estimate"]

            maps = []
            for iz, zz in enumerate(Z_EVAL):
                for idir, direction in enumerate(directions):
                    point = dh.point_image(fit["estimate"], zz, direction, degree, cf.OMEGA_M, cf.H_FID)
                    changed = dh.point_image(corrected["estimate"], zz, direction, degree, cf.OMEGA_M, cf.H_FID)
                    interval = dh.radial_hubble_interval(fit, zz, Z_REF, direction, degree, cf.OMEGA_M, cf.H_FID, .95)
                    qregion = dh.q_interval(fit, zz, direction, degree, cf.OMEGA_M, cf.H_FID, .95)
                    maps.append({"z_index": iz, "direction_index": idir,
                                 "point": point, "q_corrected_point": changed,
                                 "radial_ratio_region": interval, "q_region": qregion})
            record["directional_maps"] = maps
            record["null_space"] = {"nullity": p-fit["rank"],
                "max_whitened_scaled_null_residual": float(np.max(abs(fit["likelihood_factor"] @ fit["null_basis"]))) if fit["null_basis"].size else 0.,
                "interpretation": "minimum-norm representatives are not measurements of nonidentified functionals"}
            if fit["null_basis"].size:
                derivative_rows = np.array([dh.field_rows(.06, nn, degree)[1] for nn in directions])
                response = derivative_rows @ fit["null_basis"]
                ii, jj = np.unravel_index(np.argmax(abs(response)), response.shape)
                witness = fit["null_basis"][:, jj]
                record["null_space"]["derivative_witness"] = {
                    "z": .06, "direction_index": int(ii), "null_column": int(jj),
                    "delta_eta_z_per_unit_null_coordinate": float(response[ii, jj]),
                    "whitened_observation_change_norm": float(linalg.norm(fit["likelihood_factor"] @ witness)),
                    "parameter_displacement": witness,
                    "scope": "declared finite linear family and numerical rank; not a universal physical no-go"}
            if degree == 1:
                record["internal_predictive"] = [conditional_holdout(y, cov, x, np.arange(9*w, 9*(w+1)), scale, mt.fit_linear) for w in range(4)]
            else:
                record["internal_predictive"] = {"status": "NOT_RUN", "reason": "27 training rows do not generically identify this full parameter family; J1 checks are predeclared"}
            record["five_views"] = {
                "x": "full signed carrier and eta depth vectors/tensors; NPZ retains nulls and joint covariance",
                "Q": record["angular_radial_null"]["noise_reference_Q95"],
                "Q_anchor": "95% fixed-C noise reference in nested identifiable angular-radial mean quotient; not physical MES",
                "Pi": record["angular_radial_null"]["nominal_p"],
                "Pi_law": "upper chi-square tail for the same nested fixed-C null; not truth probability",
                "F": "joint-region signed support intervals in depth_eta_image; unbounded on null directions",
                "G_F": "full correlated eta(z)-eta(.04) vector/STF path; nonlinear H_D image additionally uses derivative denominator",
                "information": "five views of one likelihood; no added or multiplied independent information",
                "physical_anchor": "UNAVAILABLE"}
            models[key] = record
            print(json.dumps({"model": key, "rank": fit["rank"], "p": p,
                "dof": fit["dof"], "adequacy": fit["adequacy_p"],
                "radial_angular_p": record["angular_radial_null"]["nominal_p"]}), flush=True)

    arrays["directions_ICRS"] = directions
    arrays["z_evaluation"] = np.array(Z_EVAL)
    arrays["z_reference"] = np.array(Z_REF)
    np.savez_compressed(output/"DIRECTIONAL_HUBBLE_CARRIERS.npz", **arrays)
    result = {"schema": "htt.r64.directional_hubble/1", "baseline": BASELINE,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "source_carrier": {"path": R58, "sha256": EXPECTED_R58},
        "source_rows": len(z), "redshift_range": [float(z.min()), float(z.max())],
        "packing": "window-major4x[monopole,polar3,STF5]",
        "source_pins": pins, "source_checks": source_checks, "operator_sha256": operator_hashes,
        "code_sha256": {"runner": sha(__file__), "module": sha(dh.__file__)},
        "H0_reference_km_s_Mpc": cf.H_FID, "Omega_m_reference": cf.OMEGA_M,
        "eta_normalization": "eta_repo=ln(numerical H0)+eta_relative; H_D=E exp(eta_repo)/(1-E chi_hat eta_z)",
        "smooth_reference_transport": {"max_abs_raw_eta_offset": float(np.max(abs(smooth_offset))),
            "definition": "y_smooth=y_original+O ln(chi_GL64/chi_legacy_interpolated); same O,C, supplied legacy g response retained",
            "reason": "analytic distance derivatives require a smooth reference; no differentiation of piecewise-linear quadrature tables"},
        "mean_family": "g(z)n.V + sum P_j((z-.055)/.045) [monopole,polar3,STF5].a_j",
        "optical_image": "polynomial eta only, after declared coherent-V decomposition; distance-defined, not physical Hcal",
        "z_evaluation": Z_EVAL, "z_reference": Z_REF, "directions": directions,
        "working_law": "inherited white plus Planck18 linear-z0 correlated-PV covariance; no empirical selection/shared-calibration calibration",
        "models": models, "elapsed_s": time.perf_counter()-started,
        "publication_status": "NOT_READY_TO_SUBMIT"}
    dump(output/"DIRECTIONAL_HUBBLE_RESULT.json", result)
    print(json.dumps({"completed_models": len(models), "elapsed_s": result["elapsed_s"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.root, args.output)
