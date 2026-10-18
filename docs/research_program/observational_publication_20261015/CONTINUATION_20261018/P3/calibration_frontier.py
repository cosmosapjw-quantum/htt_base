"""H02 conditional spectral uncertainty frontier; no fitted observation centers.

Source geometry: retained min/max eigenvalues of actual method Gram matrices.
Noise law and deterministic calibration envelope remain explicit assumptions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

SOURCE_COMMIT = "967ef7c8f0b132ecaaba343045d333d4ebf299c1"
SOURCE_BLOB = "a2116a1f281300b488b5661ac5d28678801734d3"
SOURCE_NPZ_SHA = "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"
SOURCE_PATH = "docs/research_program/observational_publication_20261015/H02_L03_20261017/results/H02_ACTUAL_SELECTED_SOURCE_FISHER.json"
METHODS = ("FP", "TF", "SN", "OTHER")


def git_blob_sha1(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def read_pinned_source(path):
    raw = Path(path).read_bytes()
    actual_blob = git_blob_sha1(raw)
    if actual_blob != SOURCE_BLOB:
        raise ValueError(f"H02 input Git blob mismatch: expected {SOURCE_BLOB}, got {actual_blob}")
    return validate_source(json.loads(raw)), raw, actual_blob


def positive_finite(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive and finite")
    return value


def critical_value(alpha, comparisons, law):
    alpha = float(alpha)
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    if isinstance(comparisons, bool) or not isinstance(comparisons, int) or comparisons < 1:
        raise ValueError("comparisons must be a positive integer")
    if law == "gaussian_marginals":
        p = 1.0 - alpha / (2 * comparisons)
        if p >= 1:
            raise ValueError("tail probability underflows; choose a supported alpha")
        return NormalDist().inv_cdf(p)
    if law == "variance_only":
        return math.sqrt(comparisons / alpha)
    raise ValueError("unknown marginal uncertainty law")


def spectral_radius(eigen_min, alpha=0.05, comparisons=4, law="gaussian_marginals", contrast_norm=1.0):
    lam = positive_finite(eigen_min, "minimum Gram eigenvalue")
    norm = positive_finite(contrast_norm, "contrast norm")
    return critical_value(alpha, comparisons, law) * norm / math.sqrt(lam)


def compatible_interval(centers, noise_bounds, calibration_bounds):
    """Exact scalar box-model set; source callers must supply real centers.

    No centers are imputed by the source-geometry frontier runner. With coupled
    errors/calibrations this interval is an outer set, not a sharp projection.
    """
    if not centers or set(centers) != set(noise_bounds) or set(centers) != set(calibration_bounds):
        raise ValueError("nonempty identical method keys required")
    lows, highs = [], []
    for method, center in centers.items():
        center = float(center)
        q, delta = float(noise_bounds[method]), float(calibration_bounds[method])
        if not math.isfinite(center) or not math.isfinite(q) or not math.isfinite(delta) or q < 0 or delta < 0:
            raise ValueError("finite centers and nonnegative finite bounds required")
        lows.append(center - q - delta)
        highs.append(center + q + delta)
    lower, upper = max(lows), min(highs)
    return {"lower": lower, "upper": upper, "empty": lower > upper}


def validate_source(source):
    if source.get("source_sha256") != SOURCE_NPZ_SHA or source.get("selected_groups") != 35970:
        raise ValueError("unexpected original source identity")
    if set(source["method_gram_eigen_minmax"]) != set(METHODS):
        raise ValueError("method identities changed")
    if sum(source["conditional_method_counts"].values()) != 35970:
        raise ValueError("source method counts inconsistent")
    for method, pair in source["method_gram_eigen_minmax"].items():
        if len(pair) != 2:
            raise ValueError("min/max eigenvalues required")
        low, high = [positive_finite(x, "Gram eigenvalue") for x in pair]
        if low > high:
            raise ValueError("eigenvalue interval is inverted")
    return source


def compute(source, deltas=(0., .01, .02, .05), alpha=.05):
    validate_source(source)
    if not deltas or any(not math.isfinite(float(d)) or d < 0 for d in deltas):
        raise ValueError("nonnegative finite calibration grid required")
    rows = []
    for law in ("gaussian_marginals", "variance_only"):
        for n_contrasts in (1, 8):
            comparisons = len(METHODS) * n_contrasts
            crit = critical_value(alpha, comparisons, law)
            for method in METHODS:
                low, high = source["method_gram_eigen_minmax"][method]
                q = spectral_radius(low, alpha, comparisons, law)
                for delta in deltas:
                    rows.append({
                        "law": law, "predeclared_contrasts": n_contrasts,
                        "simultaneous_comparisons": comparisons, "method": method,
                        "selected_groups": source["conditional_method_counts"][method],
                        "lambda_min": low, "lambda_max": high,
                        "unit_contrast_se_lower": 1/math.sqrt(high),
                        "unit_contrast_se_upper": 1/math.sqrt(low),
                        "critical_value": crit, "noise_radius_upper_mag": q,
                        "assumed_calibration_delta_mag": float(delta),
                        "total_radius_upper_mag": q + float(delta),
                    })
    return {
        "schema": "htt.H02_spectral_calibration_frontier/1",
        "owner": "HTT observational working-law sensitivity; publications worker",
        "claim_tier": "ACTUAL_SOURCE_GEOMETRY_WITH_ASSUMED_MARGINAL_NOISE_AND_CALIBRATION_BOUNDS",
        "physical_inference": "NOT_PERFORMED", "transfer_source": "NO_NATIVE_TRANSFER",
        "source_commit": SOURCE_COMMIT, "expected_source_git_blob": SOURCE_BLOB,
        "input_identity_validation": "NOT_PERFORMED_BY_DICTIONARY_CALCULATION",
        "source_path": SOURCE_PATH, "original_selected_source_npz_sha256": SOURCE_NPZ_SHA,
        "selected_groups": 35970, "alpha": alpha,
        "contrast_scope": "predeclared Euclidean-unit contrast of raw shape8 coefficient vector, mag; not an invariant sky amplitude",
        "source_basis": ["nx", "ny", "nz", "nx^2-nz^2", "ny^2-nz^2", "2nxny", "2nxnz", "2nynz"],
        "calibration_scope": "absolute contrast error |c^T gamma_m| <= delta; not a bound on every sky direction",
        "dependence": "arbitrary cross-method and cross-contrast dependence; union bound only",
        "error_centering_assumption": "E[epsilon_m | fixed selected design]=0; any known bounded bias must be absorbed into calibration delta",
        "noise_laws": {"gaussian_marginals": "Centered Gaussian contrast errors with covariance G_m^-1", "variance_only": "Centered finite-variance contrast errors with covariance G_m^-1; Gaussianity not required"},
        "observation_centers": None, "observed_common_parameter_interval": None,
        "minimum_calibration_required_by_data": None,
        "missing_inputs": ["method angular coefficient estimates or centered X^T W y", "full G_m orientations for exact c-specific variance", "validated selected likelihood and marginal noise/calibration bounds"],
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).parent / "source" / "H02_ACTUAL_SELECTED_SOURCE_FISHER.json")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    source, raw, actual_blob = read_pinned_source(args.source)
    result = compute(source)
    result["input_identity_validation"] = "PINNED_GIT_BLOB_MATCH"
    result["source_git_blob"] = actual_blob
    result["read_input_git_blob"] = actual_blob
    result["read_input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "calibration_frontier.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    with (args.out / "calibration_frontier.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(result["rows"][0]))
        writer.writeheader(); writer.writerows(result["rows"])
    print(json.dumps({"rows": len(result["rows"]), "source_groups": result["selected_groups"], "centers_available": False, "claim_tier": result["claim_tier"]}))


if __name__ == "__main__":
    main()
