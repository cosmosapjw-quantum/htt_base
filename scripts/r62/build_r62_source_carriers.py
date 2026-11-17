#!/usr/bin/env python3
"""Source-bound tensor-series carriers from the existing CF4/R58 experiment.

The finite Legendre-z mean is a phenomenological response, not a GR shear
history. Reuses the actual source operators and fixed full R58 covariance;
does not compute a new catalogue-size covariance or a Boltzmann transfer.
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
from scipy.spatial.transform import Rotation

BASELINE = "c118982e56ee50d68dd0446aa10f16ffe65bd02b"
PROGRAM = "docs/research_program/observational_publication_20261015"
SOURCE = PROGRAM + "/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS"
R61 = PROGRAM + "/R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json"
Z_CENTRE, Z_SCALE = .055, .045


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


def commutator_norms(coefficients, basis):
    matrices = np.einsum("ka,aij->kij", coefficients, basis)
    return [float(linalg.norm(a @ b - b @ a))
            for i, a in enumerate(matrices) for b in matrices[i + 1:]]


def run(root, output):
    start = time.perf_counter()
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite source results")
    output.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root / "scripts/r58"), str(root / "htt"), str(root / "htt/src")]
    import run_r58_owned_tensor as old
    de, _, cf, mt = old.import_modules(root, None)
    from htt.htt.infer.r61_kinematic_images import stf_basis

    checked = {p: sha(root / p) for p in old.PINS}
    bad = [p for p, h in checked.items()
           if h != old.PINS[p] and h not in old.ALLOWED_REPAIRED_HASHES.get(p, ())]
    if bad:
        raise ValueError("R58 pinned dependency changed: " + str(bad))
    source = root / SOURCE / "OWNED_TENSOR_CARRIERS.npz"
    reference = json.loads((root / SOURCE / "OWNED_TENSOR_RESULT.json").read_text())
    if sha(source) != reference["carrier_sha256"]:
        raise ValueError("R58 carrier hash differs")
    previous = json.loads((root / R61).read_text())
    # Results in the retained R61 receipt are keyed by model under variants.
    previous_variants = previous["variants"]
    saved = np.load(source, allow_pickle=False)
    data = cf.load()
    cat = data["cat"]
    n, z = cat["n_J2000"], cat["z_CMB"]
    lr = de.log_distance_ratio(cat["dmzp"], z, cf.OMEGA_M)
    eta, g = lr["eta"], lr["g_per_km_s"]
    tau2 = de.log_noise_variance(cat["e_dmzp"], g, cf.SIGMA_STAR)
    with np.load(cf.OUT_DIR / "R54_L04_SURVEY_LABELS.npz", allow_pickle=False) as lab:
        if not np.array_equal(lab["group_id"], cat["group_id"]):
            raise ValueError("survey labels out of order")
        survey = dict(labels=lab["survey"].copy(), raw_labels=lab["survey_unpooled"].copy(), min_side=100)
    ops, _ = cf.build_operators(cat, data["a_raw"], tau2, survey=survey)
    angular = de.multipole_basis(n)[:, 1:]
    original_design = np.column_stack((g[:, None] * n, angular))
    polynomials = np.polynomial.legendre.legvander((z - Z_CENTRE) / Z_SCALE, 3)
    raw_design = np.column_stack((g[:, None] * n, angular[:, :3],
                                 *(polynomials[:, j, None] * angular[:, 3:] for j in range(4))))
    rows = saved["row_indices32"]
    expected_rows = np.r_[[9 * w + a for w in range(4) for a in (1, 2, 3)],
                          [9 * w + a for w in range(4) for a in range(4, 9)]]
    if not np.array_equal(rows, expected_rows):
        raise ValueError("unexpected dipole12/STF20 packing")

    E = stf_basis()
    R = Rotation.from_rotvec([.37, -.41, .29]).as_matrix()
    # Three commuting, nonproportional source coefficients, with zero polar terms.
    diagonal = np.array([[.018, -.011, -.007], [.009, .006, -.015], [-.007, .013, -.006]])
    K_true = np.array([R @ np.diag(d) @ R.T for d in diagonal])
    k_true = np.einsum("kij,aij->ka", K_true, E)
    injection21 = np.r_[np.zeros(6), k_true.ravel()]
    source_injection = raw_design[:, :21] @ injection21
    calibration = np.r_[np.zeros(3), [.013, -.021, .008], [.017, -.011, .009, .023, -.006]]
    source_calibration = angular @ calibration[3:]
    arrays, variants = {}, {}
    for name in old.VARIANTS:
        op = ops[name][rows]
        y, C, X11 = (saved[name + suffix] for suffix in ("__y32", "__cov32", "__response32x11"))
        parity = {
            "y_max_abs": np.max(np.abs(op @ eta - y)),
            "design_scaled_max_abs": np.max(np.abs((op @ original_design - X11) * saved["parameter_scale"])),
            "monopole_response_max_abs": np.max(np.abs(op @ np.ones(len(z))))}
        if max(parity.values()) > 2e-10:
            raise ValueError("source/operator parity failed: " + name)
        X26 = op @ raw_design
        fits, model_results = {}, {}
        for degree in (1, 2, 3):
            p = 6 + 5 * (degree + 1)
            scales = np.r_[saved["parameter_scale"], np.full(5 * degree, .01)]
            X = X26[:, :p]
            fit = mt.fit_linear(y, C, X, scales)
            if fit["rank"] != p or fit["rank_equilibrated"] != p:
                raise ValueError(f"unresolved source response rank {name}/J{degree}")
            fits[degree] = fit
            h, V = fit["estimate"], fit["covariance"]
            # Validate common angular calibration cancellation in the actual operator.
            shift = np.r_[calibration, np.zeros(5 * degree)]
            delta_y = op @ source_calibration
            injected = mt.fit_linear(y + delta_y, C, X, scales)
            cancellation = float(np.max(np.abs(injected["estimate"][11:] - h[11:])))
            coefficient_shift_error = float(np.max(np.abs((injected["estimate"] - h - shift) / scales)))
            if cancellation > 2e-10 or coefficient_shift_error > 2e-8:
                raise ValueError("source common-calibration invariance failed")
            varying = h[11:]
            w = float(varying @ linalg.solve(V[11:, 11:], varying, assume_a="pos"))
            model_results[str(degree)] = {
                "dimension": p, "rank": fit["rank"], "rank_equilibrated": fit["rank_equilibrated"],
                "estimate": h, "covariance": V,
                "condition_scaled": fit["singular_values_scaled"][0] / fit["singular_values_scaled"][-1],
                "condition_equilibrated": fit["singular_values_equilibrated"][0] / fit["singular_values_equilibrated"][-1],
                "residual_chi2": fit["residual_chi2"], "residual_dof": fit["dof"], "adequacy_p": fit["adequacy_p"],
                "varying_tensor_zero_wald": w, "varying_tensor_zero_df": 5 * degree,
                "varying_tensor_zero_p": stats.chi2.sf(w, 5 * degree),
                "constant_calibration_varying_max_abs": cancellation,
                "constant_calibration_scaled_shift_error": coefficient_shift_error}
            if degree >= 2:
                prefix = name + f"__J{degree}"
                arrays[prefix + "__estimate"] = h
                arrays[prefix + "__covariance"] = V
                arrays[prefix + "__response"] = X
                arrays[prefix + "__precision"] = fit["precision"]
                arrays[prefix + "__score"] = fit["score"]
                arrays[prefix + "__q0"] = np.array(fit["q0"])
                arrays[prefix + "__likelihood_factor"] = fit["likelihood_factor"]
                arrays[prefix + "__likelihood_offset"] = fit["likelihood_offset"]
                arrays[prefix + "__parameter_scale"] = scales

        # Exact affine coordinate change from the owned R61 source mean.
        T = np.eye(16)
        T[6:11, 11:16] = .1 * np.eye(5)
        T[11:16, 11:16] = .9 * np.eye(5)
        h61, V61 = np.array(previous_variants[name]["estimate16"]), np.array(previous_variants[name]["covariance16"])
        scale16 = np.r_[saved["parameter_scale"], np.full(5, .01)]
        control_h = float(np.max(np.abs((fits[1]["estimate"] - T @ h61) / scale16)))
        control_v = float(np.max(np.abs((fits[1]["covariance"] - T @ V61 @ T.T) / scale16[:, None] / scale16[None, :])))
        if control_h > 1e-7 or control_v > 1e-7:
            raise ValueError("R61 basis-change control failed")
        nested = {}
        for degree in (2, 3):
            h, V = fits[degree]["estimate"], fits[degree]["covariance"]
            w = float(h[-5:] @ linalg.solve(V[-5:, -5:], h[-5:], assume_a="pos"))
            delta = float(fits[degree - 1]["residual_chi2"] - fits[degree]["residual_chi2"])
            if abs(w - delta) > 2e-7:
                raise ValueError("nested source Wald/LR identity failed")
            nested[f"J{degree}_over_J{degree - 1}"] = dict(wald=w, delta_chi2=delta, df=5, nominal_p=stats.chi2.sf(w, 5))

        projected = op @ source_injection
        rec = mt.fit_linear(projected, C, X26[:, :21], np.r_[saved["parameter_scale"], np.full(10, .01)])
        recovery = float(np.max(np.abs((rec["estimate"] - injection21) / np.r_[saved["parameter_scale"], np.full(10, .01)])))
        if recovery > 2e-8:
            raise ValueError("noise-free actual-operator source recovery failed")
        apparent_norms = commutator_norms(projected[12:].reshape(4, 5), E)
        recovered_norms = commutator_norms(rec["estimate"][6:].reshape(3, 5), E)
        arrays[name + "__y32"] = y
        arrays[name + "__cov32"] = C
        arrays[name + "__injection21"] = injection21
        arrays[name + "__injection_y32"] = projected
        arrays[name + "__injection_recovered21"] = rec["estimate"]
        variants[name] = {
            "source_parity": parity, "fits": model_results, "nested_linear_tests": nested,
            "R61_coordinate_control": {"estimate_scaled_max_abs": control_h, "covariance_scaled_max_abs": control_v},
            "actual_operator_commuting_source_injection": {
                "source_tensor_coefficients": k_true, "source_commutator_norms": commutator_norms(k_true, E),
                "apparent_window_tensor_coefficients": projected[12:].reshape(4, 5),
                "apparent_commutator_norms": apparent_norms,
                "recovered_source_commutator_norms": recovered_norms,
                "scaled_parameter_recovery_max_abs": recovery,
                "interpretation": "Noise-free constructed source through actual survey operators; not a survey realization or a measured physical frame rotation."}}
        print(f"{name}: source ranks 21/26, basis parity {control_h:.3g}, max apparent commutator {max(apparent_norms):.6g}", flush=True)

    arrays["row_indices32"] = rows
    arrays["STF_basis"] = E
    destination = output / "SOURCE_TENSOR_CARRIERS.npz"
    np.savez_compressed(destination, **arrays)
    result = {
        "schema": "htt.r62.source_tensor_carriers/1", "baseline_commit": BASELINE,
        "execution_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "source_hashes": {str(source.relative_to(root)): sha(source), R61: sha(root / R61), **checked},
        "script_sha256": sha(__file__), "carrier_sha256": sha(destination),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "seconds": time.perf_counter() - start},
        "n_sources": len(z), "source_z_min_max": [float(z.min()), float(z.max())],
        "units": {"V": "km/s", "d_and_k": "dimensionless log-distance response coefficients", "z": "dimensionless CMB-frame observed catalogue redshift"},
        "response": "eta=g(z)*n.V+n.d+sum_j P_j((z-.055)/.045)*n.K_j.n; J2 primary, J3 sensitivity",
        "probability": "Fixed full R58 Gaussian covariance, observed catalogue design and each nuisance operator conditional. No new covariance calibration or GR kinematic identification.",
        "operator_models": "Seven declared nuisance experiments; correlated views, never independent likelihood factors or selection among p-values.",
        "variants": variants}
    (output / "SOURCE_TENSOR_RESULT.json").write_text(json.dumps(clean(result), indent=2) + "\n")
    print(json.dumps({"carrier_sha256": result["carrier_sha256"], "seconds": result["runtime"]["seconds"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.root, args.output)
