#!/usr/bin/env python3
"""Exploratory conditional location of the fixed Commander first48 E/B ensemble.

Consumes only hash-bound, already extracted JSON coefficient summaries. No FITS
reader, map transform, native solver, or original MC100 statistic is involved.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import __version__ as scipy_version
from scipy.linalg import solve_triangular
from scipy.stats import f, skew, kurtosis


ROOT = Path(__file__).resolve().parent
SOURCE = Path("/mnt/extdrive/workdir/htt_open_data/r36_commander_response_source_research/foreground_input_followup")
CONTRACT = SOURCE / "IMPLEMENTATION_CONTRACT.json"
INPUTS = SOURCE / "INPUTS_FIRST48.json"
RETURN = SOURCE / "RETURN.json"
FROZEN = {
    CONTRACT: "03976934ccfa65fcb9917830b4ea6fa77892db61ba4d564e3726200b9dfb1bfd",
    INPUTS: "04ddfc0c2bf908b87af7005585051fc4c3bdcd10641eecf68a1b756e84066079",
    RETURN: "6f00db77c0256715ddbc043ee074441528dabc481254ac718f2139d5d773f5a0",
}
EXPECTED_IDS = list(range(300, 348))
SCALE = 1e6  # internal microK_CMB for conditioning; JSON and CSV in K_CMB.


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def assert_frozen(path: Path, expected: str) -> None:
    if not path.is_file() or sha256(path) != expected:
        raise ValueError(f"immutable input missing or SHA mismatch: {path}")


def labels() -> list[str]:
    out = []
    for kind in ("E", "B"):
        for ell in (2, 3, 4):
            out.append(f"{kind}_l{ell}_m0_Re")
            for m in range(1, ell + 1):
                out += [f"{kind}_l{ell}_m{m}_sqrt2Re", f"{kind}_l{ell}_m{m}_minus_sqrt2Im"]
    assert len(out) == 42
    return out


def signed_alm_to_real(row: dict, tol: float = 1e-12) -> np.ndarray:
    vals = []
    signed_norm = 0.0
    for kind in ("E", "B"):
        carrier = row[f"{kind}_l2_l3_l4_full_signed_m"]
        if set(carrier) != {f"{ell},{m}" for ell in (2, 3, 4) for m in range(-ell, ell + 1)}:
            raise ValueError(f"{kind}: missing/extra signed-m coefficients")
        for ell in (2, 3, 4):
            z0 = complex(*carrier[f"{ell},0"])
            if not np.isfinite([z0.real, z0.imag]).all() or abs(z0.imag) > tol * max(abs(z0.real), 1e-30):
                raise ValueError(f"{kind} ell={ell}: invalid m=0 reality")
            vals.append(z0.real)
            signed_norm += abs(z0) ** 2
            for m in range(1, ell + 1):
                zp = complex(*carrier[f"{ell},{m}"])
                zn = complex(*carrier[f"{ell},{-m}"])
                if not np.isfinite([zp.real, zp.imag, zn.real, zn.imag]).all():
                    raise ValueError(f"{kind} ell={ell} m={m}: nonfinite")
                expected = (-1) ** m * zp.conjugate()
                if abs(zn - expected) > tol * max(abs(zp), abs(zn), 1e-30):
                    raise ValueError(f"{kind} ell={ell} m={m}: reality violation")
                vals.extend((math.sqrt(2) * zp.real, -math.sqrt(2) * zp.imag))
                signed_norm += abs(zp) ** 2 + abs(zn) ** 2
    vector = np.asarray(vals, dtype=np.float64)
    if vector.shape != (42,) or abs(float(vector @ vector) - signed_norm) > tol * max(signed_norm, 1e-60):
        raise ValueError("real-basis signed-m norm violation")
    return vector


def load_rows() -> tuple[np.ndarray, dict]:
    for path, digest in FROZEN.items():
        assert_frozen(path, digest)
    contract = json.loads(CONTRACT.read_text())
    manifest = json.loads(INPUTS.read_text())
    assert contract["selection"]["ids"] == EXPECTED_IDS
    assert contract["selection"]["n"] == 48 and contract["selection"]["p"] == 42
    entries = manifest["rows"]
    if [x["mc_id"] for x in entries] != EXPECTED_IDS:
        raise ValueError("fixed first48 IDs or order changed")
    vectors = []
    first = None
    for item in entries:
        path = Path(item["path"])
        assert_frozen(path, item["sha256"])
        row = json.loads(path.read_text())
        if row.get("kind") != "mc" or row.get("mc_id") != item["mc_id"]:
            raise ValueError(f"row identity mismatch: {path}")
        if row.get("input_identity") != contract["identity"]["existing_input_identity"] or row.get("contract_sha256") != contract["identity"]["existing_frozen_contract_sha256"]:
            raise ValueError(f"row frozen identity mismatch: {path}")
        if row.get("source") != item["upstream_map_declared_identity"]:
            raise ValueError(f"row source identity mismatch: {path}")
        if row.get("mask") != manifest["mask"]:
            raise ValueError(f"mask identity/geometry mismatch: {path}")
        op = row["operator"]
        for key, value in manifest["shared_operator"].items():
            if key != "input_conversion_to_K_CMB" and op.get(key) != value:
                raise ValueError(f"operator {key} mismatch: {path}")
        if op.get("input_conversion_to_K_CMB") != 1e-6 or op.get("units") != "K_CMB":
            raise ValueError(f"source unit conversion mismatch: {path}")
        if first is None:
            first = {"schema": row["schema"], "task_id": row["task_id"], "packet_id": row["packet_id"], "operator": op}
        elif any(row.get(k) != first[k] for k in ("schema", "task_id", "packet_id", "operator")):
            raise ValueError(f"mixed row operator/genealogy: {path}")
        vectors.append(signed_alm_to_real(row))
    Y = np.stack(vectors)
    if Y.shape != (48, 42) or not np.isfinite(Y).all():
        raise ValueError("invalid first48 42-coordinate matrix")
    return Y, {"contract": contract, "inputs": manifest, "row_common": first}


def descriptive(Y: np.ndarray) -> dict:
    n, p = Y.shape
    mean = Y.mean(axis=0)
    centered = Y - mean
    covariance = centered.T @ centered / (n - 1)
    return {"mean": mean, "covariance": covariance, "centered": centered,
            "estimated_se": np.sqrt(np.diag(covariance) / n),
            "row_quantiles_05_50_95": np.quantile(Y, [0.05, 0.5, 0.95], axis=0)}


def hotelling(Y: np.ndarray, mu0: np.ndarray | None = None) -> dict:
    """Return typed abstention if frozen full-rank and conditioning gates fail."""
    n, p = Y.shape
    d = descriptive(Y)
    mean, covariance, centered = d["mean"], d["covariance"], d["centered"]
    singular = np.linalg.svd(centered, compute_uv=False)
    rank_cut = 64 * np.finfo(float).eps * max(n, p) * singular[0] if singular[0] else 0.0
    rank = int(np.count_nonzero(singular > rank_cut))
    eigen = np.linalg.eigvalsh(covariance)
    condition = float(eigen[-1] / eigen[0]) if eigen[0] > 0 else math.inf
    diag = {"singular_values_centered_microK": singular.tolist(), "rank_cut_microK": float(rank_cut),
            "rank": rank, "eigenvalues_cov_microK2": eigen.tolist(),
            "lambda_min_microK2": float(eigen[0]), "lambda_max_microK2": float(eigen[-1]),
            "covariance_condition_number": condition, "n": n, "p": p}
    if n <= p or rank != p or not math.isfinite(condition) or condition > 1e10:
        return {"status": "NOT_EVALUABLE", "reason": "RANK_OR_CONDITION_GATE", "diagnostics": diag}
    try:
        L = np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError:
        return {"status": "NOT_EVALUABLE", "reason": "CHOLESKY_FAILURE", "diagnostics": diag}
    delta = mean if mu0 is None else mean - mu0
    z = solve_triangular(L, delta, lower=True)
    solution = solve_triangular(L.T, z, lower=False)
    residual = np.linalg.norm(covariance @ solution - delta) / (
        np.linalg.norm(covariance, 2) * np.linalg.norm(solution) + np.linalg.norm(delta))
    diag["normalized_solve_residual"] = float(residual)
    if not np.isfinite(residual) or residual > 1e-12:
        return {"status": "NOT_EVALUABLE", "reason": "SOLVE_RESIDUAL_GATE", "diagnostics": diag}
    T2 = float(n * z @ z)
    svd_solution = np.linalg.svd(covariance, full_matrices=False)
    U, s, Vt = svd_solution
    T2_svd = float(n * delta @ (Vt.T @ ((U.T @ delta) / s)))
    diff = abs(T2 - T2_svd)
    diag["T2_svd_crosscheck"] = T2_svd
    diag["T2_crosscheck_abs_difference"] = diff
    if diff > 1e-8 * (1 + abs(T2)):
        return {"status": "NOT_EVALUABLE", "reason": "FULL_SVD_CROSSCHECK_GATE", "diagnostics": diag}
    c = float(p * (n - 1) / (n - p) * f.ppf(0.95, p, n - p))
    radius = math.sqrt(c * eigen[-1] / n)
    projection_half = np.sqrt(c * np.diag(covariance) / n)
    norm_mean = float(np.linalg.norm(mean))
    F0 = float((n - p) * T2 / (p * (n - 1)))
    return {"status": "NOMINAL_GAUSSIAN_WORKING_LAW", "diagnostics": diag,
            "critical_c": c, "degrees_of_freedom": [p, n - p], "T2": T2,
            "F0": F0, "zero_mean_nominal_F_tail": float(f.sf(F0, p, n - p)),
            "zero_in_ellipsoid": bool(T2 <= c),
            "coordinate_projection_half_width_microK": projection_half.tolist(),
            "mean_norm_microK": norm_mean,
            "mean_norm_conservative_bounds_microK": [max(0.0, norm_mean - radius), norm_mean + radius],
            "norm_radius_microK": radius}


def coverage_control() -> dict:
    rng = np.random.default_rng(200704997)
    n, p, reps = 48, 42, 2000
    c = float(p * (n - 1) / (n - p) * f.ppf(0.95, p, n - p))
    contained = 0
    for _ in range(reps):
        X = rng.standard_normal((n, p))
        mean = X.mean(axis=0)
        C = X - mean
        S = C.T @ C / (n - 1)
        L = np.linalg.cholesky(S)
        z = solve_triangular(L, mean, lower=True)
        contained += int(n * (z @ z) <= c)
    fraction = contained / reps
    return {"seed": 200704997, "replications": reps, "covered": contained,
            "fraction": fraction, "acceptance_range": [0.925, 0.975],
            "status": "PASS" if 0.925 <= fraction <= 0.975 else "FAIL",
            "meaning": "one synthetic Gaussian implementation control; not real-pipeline validation"}


def sensitivity(Y: np.ndarray) -> dict:
    n = len(Y)
    full = descriptive(Y)
    full_mean, full_cov = full["mean"], full["covariance"]
    means, covs = [], []
    for i in range(n):
        leave = descriptive(np.delete(Y, i, axis=0))
        means.append(np.linalg.norm(leave["mean"] - full_mean))
        covs.append(np.linalg.norm(leave["covariance"] - full_cov, "fro"))
    return {"coordinate_skewness": skew(Y, axis=0, bias=False).tolist(),
            "coordinate_excess_kurtosis": kurtosis(Y, axis=0, fisher=True, bias=False).tolist(),
            "leave_one_out_mean_change_norm_max_microK": float(max(means)),
            "leave_one_out_mean_change_norm_by_id_microK": dict(zip(map(str, EXPECTED_IDS), map(float, means))),
            "leave_one_out_cov_change_frobenius_max_microK2": float(max(covs)),
            "leave_one_out_cov_change_frobenius_by_id_microK2": dict(zip(map(str, EXPECTED_IDS), map(float, covs))),
            "meaning": "descriptive sensitivity only; no trimming or Gaussianity certification"}


def write_figure(result: dict) -> None:
    means = np.asarray(result["mean_K_CMB"]) * SCALE
    half = result["model_region"].get("coordinate_projection_half_width_microK")
    fig = plt.figure(figsize=(15, 9), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.4, 1])
    ax = fig.add_subplot(gs[0])
    x = np.arange(42)
    if half is not None:
        ax.errorbar(x, means, yerr=half, fmt=".", markersize=5, elinewidth=0.9, capsize=1.5,
                    color="#244e86", ecolor="#7a9cc3", label="Mean and simultaneous 95% ellipsoid projections")
        ax.legend(loc="upper right", fontsize=9)
    else:
        ax.plot(x, means, ".", color="#244e86", label="Descriptive mean; model region abstained")
        ax.legend(loc="upper right", fontsize=9)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.axvline(20.5, color="gray", linewidth=0.7)
    ax.set_xlim(-1, 42)
    ax.set_ylabel("Coefficient (microK_CMB)")
    ax.set_xticks(x)
    ax.set_xticklabels(result["labels"], rotation=90, fontsize=6)
    ax.set_title("Commander FULL005a first48: conditional processed-map E/B ensemble location")
    ax2 = fig.add_subplot(gs[1])
    eig = np.asarray(result["model_region"]["diagnostics"]["eigenvalues_cov_microK2"])
    ax2.semilogy(np.arange(1, 43), eig, ".-", color="#9b4a34", linewidth=0.8)
    ax2.set_xlabel("Covariance eigenvalue index (ascending)")
    ax2.set_ylabel("Sample covariance eigenvalue (microK_CMB²)")
    ax2.grid(alpha=0.25)
    fig.text(0.5, -0.012,
             "Exploratory after-exposure design; iid Gaussian working law, n=48, p=42, denominator df=6. "
             "Intervals are simultaneous projections, not marginal intervals. Total processed-map mean; foreground attribution unavailable. "
             "GALACTIC/COSMO; fixed lifted Lollipop mask; no transfer or native-solver claim.",
             ha="center", va="top", fontsize=8, wrap=True)
    fig.savefig(ROOT / "FIGURE.png", dpi=180, bbox_inches="tight")
    fig.savefig(ROOT / "FIGURE.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    Y_K, source = load_rows()
    Y = Y_K * SCALE
    d = descriptive(Y)
    model = hotelling(Y)
    # Actual-data algebraic invariance controls, without changing sky or mask.
    rng = np.random.default_rng(424242)
    perm = rng.permutation(len(Y))
    d_perm = descriptive(Y[perm])
    row_perm_mean_error = float(np.max(np.abs(d_perm["mean"] - d["mean"])))
    row_perm_cov_error = float(np.max(np.abs(d_perm["covariance"] - d["covariance"])))
    sign_perm = rng.permutation(42)
    signs = rng.choice([-1.0, 1.0], size=42)
    Yp = Y[:, sign_perm] * signs
    cp = hotelling(Yp)
    # Units rescaling: K -> microK, covariance scales by 1e12; evaluate both.
    ck = hotelling(Y_K)
    controls = {"row_permutation_mean_max_abs_microK": row_perm_mean_error,
                "row_permutation_cov_max_abs_microK2": row_perm_cov_error,
                "unit_mean_max_abs_error_microK": float(np.max(np.abs(d["mean"] - descriptive(Y_K)["mean"] * SCALE))),
                "unit_cov_max_abs_error_microK2": float(np.max(np.abs(d["covariance"] - descriptive(Y_K)["covariance"] * SCALE**2))),
                "coordinate_signed_permutation_norm_error_microK": float(abs(np.linalg.norm(d["mean"]) - np.linalg.norm(descriptive(Yp)["mean"]))),
                "coordinate_signed_permutation_status": cp["status"], "unit_rescale_status": ck["status"]}
    if model["status"] == cp["status"] == ck["status"] == "NOMINAL_GAUSSIAN_WORKING_LAW":
        controls.update({"coordinate_signed_permutation_T2_error": abs(cp["T2"] - model["T2"]),
                         "unit_rescale_T2_error": abs(ck["T2"] - model["T2"]),
                         "coordinate_signed_permutation_norm_bounds_max_error_microK": float(np.max(np.abs(np.asarray(cp["mean_norm_conservative_bounds_microK"]) - np.asarray(model["mean_norm_conservative_bounds_microK"]))))})
    coverage = coverage_control()
    if coverage["status"] != "PASS":
        raise RuntimeError(f"prescribed Gaussian coverage failed: {coverage}")
    covK = d["covariance"] / SCALE**2
    meanK = d["mean"] / SCALE
    seK = d["estimated_se"] / SCALE
    result = {
        "status": "EXPLORATORY_CONDITIONAL_RESULT_PENDING_INDEPENDENT_REVIEW",
        "owner": "obsstat", "scope": "first48 total processed-map conditional ensemble location",
        "claim_tier": "diagnostic-only; no scientific admission", "artifact_mode": "exploratory after exposure",
        "allowed_use": "interpret total delivered-output mean under declared working law",
        "forbidden_uses": ["foreground-only residual", "physical nine-moment radius", "original MC100 rank", "native solver", "Bianchi family identification"],
        "transfer_source": "external NPIPE Commander FULL005a processed-map path; no native transfer",
        "null_mock_status": "one Gaussian synthetic coverage control only; physical null absent",
        "covariance_status": "full first48 sample covariance of total processed-map fluctuations; consumed once; no subtraction",
        "selection": {"ids": EXPECTED_IDS, "n": 48, "p": 42, "timing": "fixed after partial exposure; no trimming, retuning, or selection adjustment"},
        "input_identities": {str(k): v for k, v in FROZEN.items()},
        "row_input_identities": [{"mc_id": x["mc_id"], "path": x["path"], "sha256": x["sha256"]} for x in source["inputs"]["rows"]],
        "source_geometry": {"mask": source["inputs"]["mask"], "operator": source["row_common"]["operator"],
                            "frame": "GALACTIC", "polarization_convention": "COSMO"},
        "estimand": "mu_C=E[Y|C] of 42 signed-real E/B coefficients, with fixed foreground realization and observed-estimated mixing included in C",
        "units": {"mean": "K_CMB", "covariance": "K_CMB^2", "numeric_internal": "microK_CMB", "conversion": SCALE},
        "labels": labels(), "mean_K_CMB": meanK.tolist(), "covariance_K_CMB2": covK.tolist(),
        "estimated_se_K_CMB": seK.tolist(),
        "empirical_row_quantiles_05_50_95_K_CMB": (d["row_quantiles_05_50_95"] / SCALE).tolist(),
        "model_region": model,
        "controls": controls,
        "gaussian_coverage_control": coverage,
        "descriptive_diagnostics": sensitivity(Y),
        "observed_contrast": {"status": "OMITTED", "reason": "conditional independent-identical observed law not source established; optional contrast not needed"},
        "attribution_counterexample": {"witness": "Y=S_cmb+epsilon+f+b; (f,b) and (f+h,b-h) yield exactly the same Y distribution for any h; foreground norm is unbounded absent an independent bound on b", "processing_bias_bound": "UNKNOWN", "foreground_identified_set": "UNKNOWN"},
        "framework_coordinates": {k: "UNKNOWN" for k in ("x", "F", "Pi", "Q", "G_F")},
        "working_law": "conditional iid N_42(mu_C,Sigma_C), positive definite Sigma_C; declared working model, not release-established",
        "caveats": ["first48 design occurred after partial exposure; nominal fixed-sample model coverage is not selective coverage", "nonlinear pipeline output Gaussianity is unproven; skewness, kurtosis and LOO do not certify it", "only six denominator degrees of freedom", "C contains observed-estimated mixing; observed/MC conditional exchangeability is UNKNOWN", "sample covariance is total fluctuation with cross terms", "foreground and processing mean are not separately identifiable", "original R36-07 physical radius and 42 publication acceptances unchanged"],
        "runtime": {"requested_model": "gpt-6-sol", "requested_effort": "high", "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN"},
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy_version, "matplotlib": matplotlib.__version__},
    }
    if model["status"] == "NOMINAL_GAUSSIAN_WORKING_LAW":
        if max(controls.get("coordinate_signed_permutation_T2_error", 0), controls.get("unit_rescale_T2_error", 0)) > 1e-8 * (1 + abs(model["T2"])):
            raise RuntimeError("actual-data T2 invariance failed")
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    with (ROOT / "COORDINATES.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["label", "kind", "ell", "mean_K_CMB", "row_sd_K_CMB", "estimated_se_K_CMB", "row_q05_K_CMB", "row_q50_K_CMB", "row_q95_K_CMB", "simultaneous_projection_lower_K_CMB", "simultaneous_projection_upper_K_CMB"])
        half = model.get("coordinate_projection_half_width_microK")
        for i, label in enumerate(result["labels"]):
            h = half[i] / SCALE if half is not None else None
            writer.writerow([label, label[0], int(label.split("_l")[1].split("_")[0]), meanK[i], math.sqrt(covK[i, i]), seK[i], *(q[i] / SCALE for q in d["row_quantiles_05_50_95"]), meanK[i] - h if h is not None else "NOT_EVALUABLE", meanK[i] + h if h is not None else "NOT_EVALUABLE"])
    write_figure(result)
    statement = (
        "Using the fixed first 48 Commander FULL005a processed simulations (MC IDs 300–347), we estimated the conditional ensemble location of 42 signed-real E/B coefficients at ell=2–4 after the shared Galactic Lollipop-mask/spin-2 operator. "
        "The estimate includes any fixed foreground residual and processing/instrument mean and therefore does not isolate either contribution. "
        f"The sample mean has Euclidean norm {np.linalg.norm(meanK) * 1e6:.6g} microK_CMB. "
        + (f"Under a declared conditional iid Gaussian working law, the finite-sample 95% Hotelling ellipsoid has denominator df=6; its conservative bound on the norm of the total mean is [{model['mean_norm_conservative_bounds_microK'][0]:.6g}, {model['mean_norm_conservative_bounds_microK'][1]:.6g}] microK_CMB, and the zero-mean model contrast has nominal F-tail {model['zero_mean_nominal_F_tail']:.6g}. " if model["status"] == "NOMINAL_GAUSSIAN_WORKING_LAW" else "The frozen covariance checks did not permit a nominal Gaussian ellipsoid. ")
        + "This exploratory analysis was designed after partial exposure, and nonlinear release processing does not establish coefficient Gaussianity or observed/MC exchangeability. "
        "The result does not resolve the original physical foreground radius, a foreground-only contamination level, or Bianchi family identification; independent scientific review is pending.\n"
    )
    (ROOT / "MANUSCRIPT_PARAGRAPH.txt").write_text(statement)
    print(json.dumps({"status": result["status"], "model_region": model["status"],
                      "rank": model["diagnostics"]["rank"], "condition": model["diagnostics"]["covariance_condition_number"],
                      "mean_norm_microK": float(np.linalg.norm(d["mean"])),
                      "norm_bounds_microK": model.get("mean_norm_conservative_bounds_microK"),
                      "zero_mean_nominal_F_tail": model.get("zero_mean_nominal_F_tail"),
                      "coverage": coverage}, indent=2))


if __name__ == "__main__":
    main()
