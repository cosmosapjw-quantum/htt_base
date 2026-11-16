#!/usr/bin/env python3
"""R58: existing CF4 catalogue, seven nuisance models, one mixed tensor target.

No download, pair sum, old-result mutation, or data-dependent model selection.
The output is conditional on R54's selected catalogue, linear Gaussian law,
distance errors and fixed z=0 LCDM cosmic covariance. All seven models were
already run in R54. Their confidence union is a sensitivity set, not evidence
that these seven models exhaust calibration or selection uncertainty.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import linalg, stats

BASELINE = "77f61c17ba33ff28ff4f16a7d42621d8041e5ce4"
VARIANTS = ("log", "log_mono", "log_split", "log_survey", "log_mono_radial", "log_mono_galactic", "log_mono_error")
PARAMETERS = ["V_x_km_s", "V_y_km_s", "V_z_km_s", "dH_x", "dH_y", "dH_z"] + [f"kappa_{i}" for i in range(5)]
SCALE = np.array([300.0] * 3 + [0.01] * 8)
# Filled below by the implementation author from the read baseline. A changed
# frozen input must be explicitly reviewed and repinned, never silently reused.
PINS = {
  "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz": "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c",
  "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/audit_backup/derived/A_RAW_36x35970.npz": "e835df014bf0eb96fd715994c823eec9c8449f98d3f132b1dc736b760fd2772e",
  "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L04_COSMIC_COV.npz": "b6f92bff4d28affc68c0e41ad03ad02cf4a31aa4353a39710c7649cfba3e2a02",
  "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L04_SURVEY_LABELS.npz": "7b5cac5e296abaa811477c01912c0233e430682cd865f6a1e3262c891dfced95",
  "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L05_COSMIC_COV.npz": "f0acb8e1be3f09d212303967ff7678178fd59364ec0131ab12ba3f5149879cae",
  "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L04_RESULT.json": "1c057c92471b5ed0e9f5b58b07cd7f08cd340277938169c6d0db75d59f82b94c",
  "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L05_CF4_EXACT.json": "8f9535fa126164f72d5aaa4820283c228b4181b180feb54ce14df5a715d9beb8",
  "scripts/r54/run_r54_cf4_exact.py": "0d84ec958dfc964d28f39ac2edc506dd5c8ed8009ad1c12019cb425b15418300",
  "scripts/r54/run_r54_lowz_frames.py": "030ff65972be94b1f7a1d7f00b2c7f4e2b45592286dc1aae3c0af5eb2fa9a0c5",
  "htt/htt/htt/infer/r54_distance_estimators.py": "9640b9785d2c4a5164e75018c2bfd2d0c8f6eb8072cb1a445e4f7589f9876d50",
  "htt/htt/htt/infer/r54_lcdm_body.py": "a61e88bb012fedeff78e57a31278f1e62e9225c03cca5f10c29c23cf996b3085",
  "htt/htt/htt/infer/r54_survey.py": "57aa6a3834d4c9cb8c04c9ac5d15044135eaea37e6e9d9bcfe9f9ee51237485a",
  "htt/htt/htt/infer/r54_tensor_five_view.py": "4811340d211f2c4d2fa330bd5d6cf160fc83a04458b5eb9c3a259fd1cb731b6d",
  "tests/fixtures/r54/planck18_linear_pk_z0.csv": "f4f99b2817ee0ade6b4b4cba107843d95f46c13e82293fb3def061bc56d0a45d"
}


# R58 validates the finite-MC helper without changing any extraction function.
# The exact reviewed alternate is accepted; seven-model parity remains required.
ALLOWED_REPAIRED_HASHES = {
    "htt/htt/htt/infer/r54_tensor_five_view.py": ("47f9ab5fd40da9ffb8725ff9720a8d4cba7116c905a6a4c11e05b79f972e17a8",),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(obj):
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        if not np.isfinite(v):
            return "inf" if v > 0 else ("-inf" if v < 0 else None)
        return v
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def import_modules(root: Path, fit_module: Path | None):
    for p in (root / "htt", root / "htt/src", root, root / "scripts/r54"):
        sys.path.insert(0, str(p))
    from htt.htt.infer import r54_distance_estimators as de
    from htt.htt.infer import r54_tensor_five_view as fv
    import run_r54_cf4_exact as cf
    if fit_module is None:
        from htt.htt.infer import r58_mixed_tensor_likelihood as mt
    else:
        spec = importlib.util.spec_from_file_location("r58_fit", fit_module)
        mt = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mt
        spec.loader.exec_module(mt)
    return de, fv, cf, mt


def relative_error(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.max(np.abs(a - b)) / max(float(np.max(np.abs(b))), 1e-30))


def cached_rows(path: Path, ops: dict, g: np.ndarray, cf, n: np.ndarray, r: np.ndarray):
    names, labels, stack = [], [], []
    offset, layout = 0, {}
    for name, op in ops.items():
        names.append(name)
        labels.extend([f"{name}:{i}" for i in range(op.shape[0])])
        layout[name] = slice(offset, offset + op.shape[0])
        offset += op.shape[0]
        stack.append(op * g[None, :])
    stack = np.concatenate(stack, axis=0)
    with np.load(path, allow_pickle=False) as z:
        if list(z["labels"]) != labels or int(z["n_rows"]) != offset:
            raise ValueError(f"{path.name}: cached operator labels or row count differ")
        body = z["cosmic_linear"].copy()
        stored_fp, stored_model = str(z["operator_fingerprint"]), str(z["model_key"])
    grid = np.linspace(0.0, 2.0 * float(r.max()) * 1.001, 4001)
    actual_model = cf.model_key(n, r, grid)
    actual_fp = str(cf.operator_fingerprint(stack))
    # A model mismatch is not a QR-roundoff exception. No recalculation here.
    if stored_model != actual_model:
        raise ValueError(f"{path.name}: frozen cosmic-covariance model key differs")
    return body, layout, {
        "file": str(path.relative_to(cf.ROOT)), "operator_fingerprint_recorded": stored_fp,
        "operator_fingerprint_current": actual_fp, "exact_operator_bytes": stored_fp == actual_fp,
        "model_key_equal": True, "row_labels_equal": True, "n_rows": offset,
        "reuse_policy": "Pinned input/code/cache identity plus mandatory seven-model numerical parity; no pair-sum or cache write.",
    }


def marginal_summary(y36, c36, v36, fv, dip, quad):
    out = {}
    for name, rows in (("dipole", dip), ("quadrupole", quad), ("joint", np.sort(np.r_[dip, quad]))):
        y, c = y36[rows], c36[np.ix_(rows, rows)]
        out[name + "_null_chi2"] = float(y @ np.linalg.solve(c, y))
        out[name + "_null_p"] = float(stats.chi2.sf(out[name + "_null_chi2"], rows.size))
    qfit = fv.gls_fit(y36[quad], c36[np.ix_(quad, quad)], np.tile(np.eye(5), (4, 1)))
    afit = fv.gls_fit(y36[dip], c36[np.ix_(dip, dip)], np.tile(np.eye(3), (4, 1)))
    vfit = fv.gls_fit(y36[dip], c36[np.ix_(dip, dip)], v36[dip])
    out.update(quadrupole_constant_wald_5dof=qfit["wald"], A_wald_p=float(stats.chi2.sf(afit["wald"], 3)),
               V_only_km_s=float(np.linalg.norm(vfit["theta"])))
    return out


def compute(root: Path, output: Path, fit_module: Path | None = None):
    de, fv, cf, mt = import_modules(root, fit_module)
    identities = {p: sha256(root / p) for p in PINS}
    changed = [p for p in PINS if identities[p] != PINS[p] and identities[p] not in ALLOWED_REPAIRED_HASHES.get(p, ())]
    if changed:
        raise ValueError("frozen dependency changed: " + ", ".join(changed))
    resdir = cf.OUT_DIR
    l05 = json.loads((resdir / "R54_L05_CF4_EXACT.json").read_text())
    l04 = json.loads((resdir / "R54_L04_RESULT.json").read_text())
    data = cf.load()
    cat = data["cat"]
    n, z = cat["n_J2000"], cat["z_CMB"]
    lr = de.log_distance_ratio(cat["dmzp"], z, cf.OMEGA_M)
    eta, g = lr["eta"], lr["g_per_km_s"]
    tau2 = de.log_noise_variance(cat["e_dmzp"], g, cf.SIGMA_STAR)
    base, _ = cf.build_operators(cat, data["a_raw"], tau2)
    with np.load(resdir / "R54_L04_SURVEY_LABELS.npz", allow_pickle=False) as lab:
        if not np.array_equal(lab["group_id"], cat["group_id"]):
            raise ValueError("survey-label group IDs differ from catalogue order")
        survey = {"labels": lab["survey"].copy(), "raw_labels": lab["survey_unpooled"].copy(), "min_side": 100}
    all_ops, _ = cf.build_operators(cat, data["a_raw"], tau2, survey=survey)
    if any(not np.array_equal(v, all_ops[k]) for k, v in base.items()):
        raise ValueError("base operator changed when survey operators were appended")
    new = {k: v for k, v in all_ops.items() if k not in base}
    r = de.C_KM_S / cf.H_FID * lr["chi_hat"]
    body5, layout5, reuse5 = cached_rows(resdir / "R54_L05_COSMIC_COV.npz", base, g, cf, n, r)
    body4, layout4, reuse4 = cached_rows(resdir / "R54_L04_COSMIC_COV.npz", new, g, cf, n, r)
    dip = np.array([9*w+k for w in range(4) for k in (1, 2, 3)])
    quad = np.array([9*w+k for w in range(4) for k in range(4, 9)])
    rows = np.r_[dip, quad]  # concatenated irreps for the block-covariance ablation
    # Observable model: eta_i = nuisance_i + g_i n_i.V + n_i.dH + n_i.K.n_i.
    # Velocity leaks into STF window rows through the real survey operator.
    raw_design = np.column_stack((g[:, None] * n, de.multipole_basis(n)[:, 1:]))
    variants, arrays, parity = {}, {}, {}
    # Conditional Gaussian calibration of the covariance ablation, independent
    # of the observed y. Common random numbers reduce Monte Carlo noise in model
    # comparisons; this is not a new survey mock or an observational p-value.
    n_coverage = 20000
    z_coverage = np.random.default_rng(20261117).standard_normal((n_coverage, 11))
    c2_95 = float(stats.chi2.ppf(0.95, 11))
    reference_coverage = float(np.mean(np.sum(z_coverage**2, axis=1) <= c2_95))
    for name in VARIANTS:
        op = all_ops[name]
        sl, body = (layout5[name], body5) if name in base else (layout4[name], body4)
        y36 = op @ eta
        cw = de.white_covariance(op, tau2)
        cb = body[sl, sl]
        c36 = cw + cb
        design36 = op @ raw_design
        v36 = design36[:, :3]
        y, c, d = y36[rows], c36[np.ix_(rows, rows)], design36[rows]
        summary = marginal_summary(y36, c36, v36, fv, dip, quad)
        if name == "log":
            old = l05["log_distance"]["headline"]
            oldcar = l05["log_distance"]["carrier"]
            parity["pooled_carrier"] = {k: relative_error(a, oldcar[k]) for k, a in
                                        (("theta", y36), ("covariance_white", cw), ("covariance_body", cb), ("velocity_response_per_km_s", v36))}
        elif name == "log_mono":
            old = l05["zero_point_split"]["method_monopoles_only"]["headline"]
        elif name == "log_split":
            old = l05["zero_point_split"]["headline"]
        else:
            old = l04["nuisance_variants"]["local"][name]["headline"]
        errors = {k: abs(summary[k] - old[k]) for k in summary if k in old}
        parity[name] = errors
        if not errors or max(errors.values()) > 2e-7:
            raise ValueError(f"{name}: R54 marginal parity failed: {errors}")
        fit = mt.fit_linear(y, c, d, parameter_scale=SCALE)
        cbdiag = linalg.block_diag(c[:12, :12], c[12:, 12:])
        approx = mt.fit_linear(y, cbdiag, d, parameter_scale=SCALE)
        corr = c[:12, 12:] / np.sqrt(np.outer(np.diag(c)[:12], np.diag(c)[12:]))
        canon = np.linalg.solve(np.linalg.cholesky(c[:12, :12]), c[:12, 12:])
        canon = np.linalg.solve(np.linalg.cholesky(c[12:, 12:]), canon.T).T
        sv = np.linalg.svd(canon, compute_uv=False)
        est, cov = np.asarray(fit["estimate"]), np.asarray(fit["covariance"])
        aest, acov = np.asarray(approx["estimate"]), np.asarray(approx["covariance"])
        if fit["rank"] != 11 or approx["rank"] != 11:
            raise ValueError(f"{name}: full common target is not identified; handle cylinder before publication")
        linear_estimator = acov @ np.linalg.solve(cbdiag, d).T
        sandwich = linear_estimator @ c @ linear_estimator.T
        sandwich = 0.5 * (sandwich + sandwich.T)
        nominal_chol = np.linalg.cholesky(acov)
        ratio = np.linalg.solve(nominal_chol, sandwich)
        ratio = np.linalg.solve(nominal_chol, ratio.T).T
        eig_ratio = np.linalg.eigvalsh(0.5 * (ratio + ratio.T))
        coverage = float(np.mean((z_coverage**2) @ eig_ratio <= c2_95))
        delta = est - aest
        # This is a change normalized by full-fit sigma, not a significance test:
        # the two estimates are strongly correlated (same data).
        shifts = delta / np.sqrt(np.diag(cov))
        intervals = {p: mt.linear_interval(fit, np.eye(11)[i], level=0.95, simultaneous=True) for i, p in enumerate(PARAMETERS)}
        variants[name] = {
            "fit": fit, "same_response_block_diagonal_covariance_ablation": approx,
            "change_in_full_fit_sd_not_a_test": shifts,
            "max_abs_dipole_quadrupole_correlation": float(np.max(np.abs(corr))),
            "canonical_correlations": sv, "simultaneous_95_intervals": intervals,
            "block_diagonal_uncertainty_calibration": {
                "actual_sampling_covariance": sandwich,
                "actual_to_nominal_variance_eigenvalues": eig_ratio,
                "actual_to_nominal_component_sd": np.sqrt(np.diag(sandwich) / np.diag(acov)),
                "coverage_of_nominal_95_ellipsoid_under_full_covariance": coverage,
                "full_GLS_reference_coverage_same_draws": reference_coverage,
                "simulation": {"law": "11-dimensional zero-mean Gaussian parameter error with sandwich covariance; fixed design and covariance", "n": n_coverage, "seed": 20261117,
                               "mc_standard_error": float(np.sqrt(coverage * (1.0 - coverage) / n_coverage))},
            },
            "R54_marginal_reproduction": summary,
            "response_diagnostics": {
                "constant_dH_q_identity_max_abs_error": float(np.max(np.abs(design36[:, 3:] - np.tile(np.eye(9)[:, 1:], (4, 1))))),
                "velocity_to_quadrupole_max_abs_per_km_s": float(np.max(np.abs(v36[quad]))),
            },
        }
        for key, val in (("theta36", y36), ("white36", cw), ("body36", cb), ("response36x11", design36),
                         ("y32", y), ("cov32", c), ("response32x11", d), ("estimate11", est), ("cov11", cov)):
            arrays[f"{name}__{key}"] = val
    if max(parity["pooled_carrier"].values()) > 2e-10:
        raise ValueError("pooled carrier differs from R54 beyond numerical reuse tolerance")
    robust = {
        "rule": "union over the seven previously evaluated nuisance-model confidence ellipsoids; no model probabilities",
        "coverage_condition": "If one listed nuisance model and its fixed Gaussian covariance law is correct, its 95% ellipsoid is covered by the union. Unknown systematics and selection misspecification are outside this guarantee.",
        "max_null_p": max(float(v["fit"]["null_p"]) for v in variants.values()),
        "max_wald_p_common_theta_zero": max(float(v["fit"]["wald_p"]) for v in variants.values()),
        "coordinate_support_hull": {
            p: {"lower": min(v["simultaneous_95_intervals"][p]["lower"] for v in variants.values()),
                "upper": max(v["simultaneous_95_intervals"][p]["upper"] for v in variants.values())} for p in PARAMETERS
        },
        "interpretation": "Apparent Hubble-rate vector and tensor conditional on the selected CF4 catalogue; V is a coherent velocity component; dH is an apparent log-H dipole, not identified four-acceleration; kappa is an apparent log-H STF tensor, not uniquely cosmological shear.",
    }
    output.mkdir(parents=True, exist_ok=True)
    npz = output / "OWNED_TENSOR_CARRIERS.npz"
    np.savez_compressed(npz, row_indices32=rows, parameter_names=np.array(PARAMETERS), parameter_scale=SCALE, **arrays)
    try:
        code_head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except subprocess.CalledProcessError:
        code_head = "UNAVAILABLE"
    result = {
        "schema": "htt.r58.owned_mixed_tensor/1", "status": "NUMERICALLY_CHECKED_CONDITIONAL", "claim_tier": "C0",
        "baseline": BASELINE, "source_root_head": code_head, "n_groups": int(z.size), "n_models": len(VARIANTS),
        "parameter_names": PARAMETERS, "parameter_scale": SCALE,
        "model": "eta = nuisance + g(z) n.V + n.dH + n.K.n; X_m = O_m D, C_m = O_m C_noise O_m^T + pinned exact LCDM body",
        "variants": variants, "robust": robust, "reproduction": parity, "cache_reuse": [reuse5, reuse4],
        "inputs_sha256": identities, "carrier_file": npz.name, "carrier_sha256": sha256(npz),
        "implementation": {"runner_sha256": sha256(Path(__file__)), "fit_module_sha256": sha256(Path(mt.__file__)),
                           "python": platform.python_version(), "numpy": np.__version__},
        "limitations": [
            "Seven models are a declared sensitivity family, not all possible systematics; existing data motivated this investigation, so discovery claims need calibration of selection/forking paths.",
            "The cached cosmic covariance is reused with its original linear z=0 LCDM, redshift-space geometry and fixed fiducial assumptions; no new pair sum or independent cosmic-model validation is performed.",
            "The 32 compressed multipoles need not be sufficient for the raw 35970-object catalogue model. Information equivalence is tested only on this stated carrier.",
            "Model-specific likelihood ordinates are not compared across differing O_m transforms. No Bayes factor or AIC ranking across the seven experiments is computed.",
            "The block-diagonal covariance calculation is an ablation; the full covariance defines the reported conditional likelihood.",
        ],
    }
    path = output / "OWNED_TENSOR_RESULT.json"
    path.write_text(json.dumps(clean(result), indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fit-module", type=Path, help="Only for isolated scratch validation against a not-yet-installed module.")
    args = parser.parse_args()
    out = args.output.resolve()
    frozen = args.root.resolve() / "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
    if out == frozen or frozen in out.parents:
        raise SystemExit("R54 frozen results cannot be overwritten")
    res = compute(args.root.resolve(), out, args.fit_module)
    print(json.dumps(clean({"status": res["status"], "robust": res["robust"], "models": {
        k: {"rank": v["fit"]["rank"], "null_p": v["fit"]["null_p"], "wald_p": v["fit"]["wald_p"],
            "adequacy_p": v["fit"]["adequacy_p"], "canonical_correlation_max": v["canonical_correlations"][0]} for k, v in res["variants"].items()}}), indent=2))


if __name__ == "__main__":
    main()
